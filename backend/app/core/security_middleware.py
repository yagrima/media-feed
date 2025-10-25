"""
Security middleware for additional protections.
Includes Origin validation (CSRF), user ownership verification, and audit logging.
"""

from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import logging

from app.core.config import settings


logger = logging.getLogger(__name__)


class OriginValidationMiddleware(BaseHTTPMiddleware):
    """
    Validates Origin header for state-changing requests (CSRF protection).
    Complements CORS by ensuring Origin matches allowed list.
    """

    async def dispatch(self, request: Request, call_next: Callable):
        """
        Validate Origin header for POST, PUT, PATCH, DELETE requests.

        Args:
            request: Incoming request
            call_next: Next middleware/handler

        Returns:
            Response from next handler or 403 if Origin invalid
        """
        # Only validate state-changing methods
        if request.method in {'POST', 'PUT', 'PATCH', 'DELETE'}:
            origin = request.headers.get('origin')
            referer = request.headers.get('referer')

            # For API requests, require Origin or Referer
            if request.url.path.startswith('/api/'):
                # Allow requests without Origin/Referer for development
                # In production, should be stricter
                if origin:
                    # Extract domain from origin
                    if not self._is_allowed_origin(origin):
                        logger.warning(
                            f"Rejected request with invalid origin: {origin}",
                            extra={
                                'origin': origin,
                                'path': request.url.path,
                                'method': request.method,
                                'ip': request.client.host
                            }
                        )
                        return JSONResponse(
                            status_code=status.HTTP_403_FORBIDDEN,
                            content={"detail": "Invalid origin"}
                        )

                elif referer:
                    # Check referer if origin not present
                    if not any(allowed in referer for allowed in settings.allowed_origins_list):
                        logger.warning(
                            f"Rejected request with invalid referer: {referer}",
                            extra={'referer': referer, 'path': request.url.path}
                        )
                        return JSONResponse(
                            status_code=status.HTTP_403_FORBIDDEN,
                            content={"detail": "Invalid referer"}
                        )

        response = await call_next(request)
        return response

    def _is_allowed_origin(self, origin: str) -> bool:
        """
        Check if origin is in allowed list.

        Args:
            origin: Origin header value

        Returns:
            True if allowed
        """
        return origin in settings.allowed_origins_list


def verify_user_ownership(resource_user_id: str, request_user_id: str, resource_type: str = "resource"):
    """
    Verify that the requesting user owns the resource.
    Raises HTTPException if ownership check fails.

    Args:
        resource_user_id: User ID associated with the resource
        request_user_id: User ID from the request (authenticated user)
        resource_type: Type of resource for error message

    Raises:
        HTTPException: 403 if user doesn't own resource, 401 if not authenticated
    """
    if not request_user_id:
        logger.warning(
            f"Unauthenticated access attempt to {resource_type}",
            extra={'resource_type': resource_type}
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )

    if str(resource_user_id) != str(request_user_id):
        logger.warning(
            f"Unauthorized access attempt to {resource_type}",
            extra={
                'resource_user_id': str(resource_user_id),
                'request_user_id': str(request_user_id),
                'resource_type': resource_type
            }
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"You don't have permission to access this {resource_type}"
        )


async def log_security_event(
    event_type: str,
    user_id: str = None,
    request: Request = None,
    metadata: dict = None
):
    """
    Log security-relevant events for audit trail.

    Args:
        event_type: Type of security event
        user_id: User ID if applicable
        request: FastAPI request object
        metadata: Additional event metadata
    """
    log_data = {
        'event_type': event_type,
        'user_id': user_id,
        'metadata': metadata or {}
    }

    if request:
        log_data.update({
            'ip_address': request.client.host,
            'user_agent': request.headers.get('user-agent'),
            'path': request.url.path,
            'method': request.method
        })

    logger.info(f"Security event: {event_type}", extra=log_data)
