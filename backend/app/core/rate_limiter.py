"""
Enhanced rate limiting for API endpoints with Redis backend.
Includes decorators for notifications and TMDB API protection.
"""

from functools import wraps
from typing import Callable, Optional
from fastapi import Request, HTTPException
from redis import asyncio as aioredis
import time
import logging

from app.core.config import settings


logger = logging.getLogger(__name__)


class RateLimiter:
    """Redis-based rate limiter with sliding window algorithm."""

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize rate limiter with Redis connection.

        Args:
            redis_url: Redis connection URL (defaults to settings.REDIS_URL)
        """
        self.redis_url = redis_url or settings.REDIS_URL
        self._redis: Optional[aioredis.Redis] = None

    async def get_redis(self) -> aioredis.Redis:
        """Get or create Redis connection."""
        if self._redis is None:
            self._redis = await aioredis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
        return self._redis

    async def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int
    ) -> tuple[bool, int, int]:
        """
        Check if request is within rate limit using sliding window.

        Args:
            key: Unique identifier for the rate limit (e.g., user_id:endpoint)
            max_requests: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            Tuple of (allowed, requests_made, retry_after_seconds)
        """
        redis = await self.get_redis()
        now = time.time()
        window_start = now - window_seconds

        # Use sorted set for sliding window
        pipe = redis.pipeline()

        # Remove old entries outside the window
        pipe.zremrangebyscore(key, 0, window_start)

        # Count requests in current window
        pipe.zcard(key)

        # Add current request with timestamp as score
        pipe.zadd(key, {str(now): now})

        # Set expiration
        pipe.expire(key, window_seconds)

        results = await pipe.execute()
        current_requests = results[1]

        if current_requests < max_requests:
            return True, current_requests + 1, 0

        # Calculate retry after (time until oldest request expires)
        oldest = await redis.zrange(key, 0, 0, withscores=True)
        if oldest:
            retry_after = int(oldest[0][1] + window_seconds - now) + 1
        else:
            retry_after = window_seconds

        # Remove the request we just added since it's over limit
        await redis.zrem(key, str(now))

        return False, current_requests, retry_after

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()


# Global rate limiter instance
_rate_limiter: Optional[RateLimiter] = None


def get_rate_limiter() -> RateLimiter:
    """Get or create global rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = RateLimiter()
    return _rate_limiter


def rate_limit(
    max_requests: int,
    window_seconds: int,
    key_prefix: str = "rl"
):
    """
    Decorator for rate limiting endpoints.

    Args:
        max_requests: Maximum requests allowed
        window_seconds: Time window in seconds
        key_prefix: Prefix for Redis key

    Example:
        @rate_limit(max_requests=100, window_seconds=60)
        async def get_notifications(request: Request, user_id: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract request and user_id from arguments
            request = None
            user_id = None

            for arg in args:
                if isinstance(arg, Request):
                    request = arg
                    # Try to get user_id from request state (set by auth middleware)
                    user_id = getattr(request.state, 'user_id', None)
                    break

            if 'request' in kwargs:
                request = kwargs['request']
                user_id = getattr(request.state, 'user_id', None)

            if 'user_id' in kwargs:
                user_id = kwargs['user_id']

            if not user_id:
                # Fallback to IP-based limiting if no user_id
                user_id = request.client.host if request else 'unknown'

            # Create rate limit key
            rate_limit_key = f"{key_prefix}:{func.__name__}:{user_id}"

            # Check rate limit
            limiter = get_rate_limiter()
            allowed, requests_made, retry_after = await limiter.check_rate_limit(
                rate_limit_key,
                max_requests,
                window_seconds
            )

            if not allowed:
                logger.warning(
                    f"Rate limit exceeded for {user_id} on {func.__name__}",
                    extra={
                        'user_id': user_id,
                        'endpoint': func.__name__,
                        'requests_made': requests_made,
                        'retry_after': retry_after
                    }
                )
                raise HTTPException(
                    status_code=429,
                    detail=f"Rate limit exceeded. Retry after {retry_after} seconds.",
                    headers={"Retry-After": str(retry_after)}
                )

            # Execute the function
            return await func(*args, **kwargs)

        return wrapper
    return decorator


def tmdb_rate_limit(max_requests: int = 40, window_seconds: int = 10):
    """
    Rate limiter specifically for TMDB API calls (40 req/10s).

    Args:
        max_requests: Maximum TMDB API requests (default 40)
        window_seconds: Time window (default 10 seconds)

    Example:
        @tmdb_rate_limit()
        async def search_tv(self, query: str):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Use global key for TMDB (not per-user)
            rate_limit_key = f"tmdb:api:{func.__name__}"

            limiter = get_rate_limiter()
            allowed, requests_made, retry_after = await limiter.check_rate_limit(
                rate_limit_key,
                max_requests,
                window_seconds
            )

            if not allowed:
                logger.warning(
                    f"TMDB rate limit exceeded for {func.__name__}",
                    extra={
                        'endpoint': func.__name__,
                        'requests_made': requests_made,
                        'retry_after': retry_after
                    }
                )
                # Return empty result instead of raising exception
                # This allows graceful degradation
                return [] if func.__name__.startswith('search') else None

            return await func(*args, **kwargs)

        return wrapper
    return decorator


# Notification-specific rate limits (100 req/min per user)
notification_rate_limit = lambda: rate_limit(
    max_requests=100,
    window_seconds=60,
    key_prefix="notifications"
)
