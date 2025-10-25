"""
Me Feed - Main FastAPI Application
Security-Enhanced Media Tracking Platform
"""
# Setup logging FIRST (before other imports)
from app.core.logging_config import setup_logging
import logging

setup_logging()
logger = logging.getLogger(__name__)

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.middleware import (
    limiter,
    security_headers_middleware,
    audit_logging_middleware,
    request_id_middleware,
    origin_validation_middleware,
    rate_limit_exceeded_handler
)
from app.api import auth
from app.api import import_api
from app.api import media_api
from app.api import notification_api
from slowapi.errors import RateLimitExceeded


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Application starting", extra={
        "app_name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "debug": settings.DEBUG
    })
    yield
    # Shutdown
    logger.info("Application shutting down")


# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Personal media consumption tracker with automated update monitoring",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# Add rate limiter to app state
app.state.limiter = limiter

# Exception handler for rate limiting
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

# CORS Middleware (MUST be added BEFORE other middlewares)
# In DEBUG mode, allow all origins
if settings.DEBUG:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Allow all origins in development
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"],
        max_age=3600,
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-Process-Time"],
        max_age=3600,
    )

# Trusted Host Middleware
if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=settings.allowed_hosts_list
    )

# Custom Security Middlewares (order matters - LIFO execution)
# Skip origin_validation_middleware in DEBUG mode to avoid CORS issues
if not settings.DEBUG:
    app.middleware("http")(origin_validation_middleware)
app.middleware("http")(security_headers_middleware)
app.middleware("http")(audit_logging_middleware)
app.middleware("http")(request_id_middleware)


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint for monitoring

    Returns service status and version
    """
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION
    }


# Root endpoint
@app.get("/", tags=["root"])
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": settings.APP_VERSION,
        "docs": "/docs" if settings.DEBUG else "Documentation disabled in production"
    }


# Include routers
app.include_router(auth.router, prefix="/api")
app.include_router(import_api.router, prefix="/api")
app.include_router(media_api.router)
# TODO: Fix notification_service async/sync issues before enabling
# app.include_router(notification_api.router)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler to prevent information leakage

    Args:
        request: FastAPI request
        exc: Exception

    Returns:
        Generic error response
    """
    # Log the error with context
    logger.error("Unhandled exception", extra={
        "exception": str(exc),
        "exception_type": type(exc).__name__,
        "path": request.url.path,
        "method": request.method
    })

    # Don't leak error details in production
    if settings.DEBUG:
        detail = str(exc)
    else:
        detail = "An internal error occurred"

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": detail}
    )


# Startup message
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
