"""
Security middleware: rate limiting, headers, audit logging
"""
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import redis.asyncio as redis
from typing import Callable
import time
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)


# Initialize Redis client for rate limiting
redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)


def get_rate_limit_key(request: Request) -> str:
    """
    Generate rate limit key based on user or IP

    Args:
        request: FastAPI request

    Returns:
        Rate limit key string
    """
    # Use user ID if authenticated
    user = getattr(request.state, "user", None)
    if user:
        return f"rate_limit:user:{user.id}"

    # Fall back to IP address
    return f"rate_limit:ip:{get_remote_address(request)}"


# Initialize rate limiter
limiter = Limiter(
    key_func=get_rate_limit_key,
    default_limits=[
        f"{settings.RATE_LIMIT_PER_MINUTE}/minute",
        f"{settings.RATE_LIMIT_PER_HOUR}/hour"
    ],
    storage_uri=settings.REDIS_URL
)


async def security_headers_middleware(request: Request, call_next: Callable):
    """
    Add security headers to all responses

    Args:
        request: FastAPI request
        call_next: Next middleware in chain

    Returns:
        Response with security headers
    """
    response = await call_next(request)

    # Security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

    # HSTS (only in production with HTTPS)
    if settings.ENFORCE_HTTPS:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    # Content Security Policy
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline'; "
        "style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data: https:; "
        "font-src 'self' data:; "
        "connect-src 'self'"
    )

    return response


async def audit_logging_middleware(request: Request, call_next: Callable):
    """
    Log security-relevant requests for audit trail

    Args:
        request: FastAPI request
        call_next: Next middleware in chain

    Returns:
        Response
    """
    # Security-sensitive endpoints to log
    sensitive_paths = [
        "/api/auth/login",
        "/api/auth/register",
        "/api/auth/logout",
        "/api/import/csv",
        "/api/admin"
    ]

    should_log = any(request.url.path.startswith(path) for path in sensitive_paths)

    if should_log:
        # Log will be created in the route handler with full context
        request.state.audit_log = True

    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time

    # Add processing time header
    response.headers["X-Process-Time"] = str(process_time)

    return response


async def request_id_middleware(request: Request, call_next: Callable):
    """
    Add unique request ID for tracking

    Args:
        request: FastAPI request
        call_next: Next middleware in chain

    Returns:
        Response with request ID
    """
    import uuid
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response


async def origin_validation_middleware(request: Request, call_next: Callable):
    """
    Validate Origin/Referer headers for state-changing requests

    Mitigates CSRF attacks when JWT tokens could be leaked to malicious sites.

    Args:
        request: FastAPI request
        call_next: Next middleware in chain

    Returns:
        Response or 403 if invalid origin
    """
    # Skip origin validation for browser extension endpoints
    # These are designed to work with chrome-extension:// origins
    # Security: Still requires valid JWT auth token + rate limiting
    extension_paths = [
        '/api/audible/import-from-extension',
        '/api/audible/extension/status'
    ]
    
    if any(request.url.path.startswith(path) for path in extension_paths):
        return await call_next(request)
    
    # Only validate state-changing methods
    if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
        origin = request.headers.get('origin')
        referer = request.headers.get('referer')

        # Check if origin or referer is present
        header_value = origin or referer

        if header_value:
            # Validate against allowed origins
            is_valid = any(
                header_value.startswith(allowed_origin)
                for allowed_origin in settings.allowed_origins_list
            )

            if not is_valid:
                # Log security event
                client_ip = request.client.host if request.client else 'unknown'
                logger.warning("Invalid origin blocked", extra={
                    "origin": header_value,
                    "client_ip": client_ip,
                    "method": request.method,
                    "path": request.url.path
                })

                return JSONResponse(
                    status_code=status.HTTP_403_FORBIDDEN,
                    content={"detail": "Invalid request origin"}
                )

    return await call_next(request)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    """
    Custom handler for rate limit exceeded

    Args:
        request: FastAPI request
        exc: RateLimitExceeded exception

    Returns:
        JSON error response
    """
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={
            "detail": "Rate limit exceeded. Please try again later.",
            "retry_after": exc.retry_after if hasattr(exc, 'retry_after') else 60
        }
    )
