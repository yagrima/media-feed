"""
Redis-based caching layer for API responses and expensive computations.
Primary use: TMDB API response caching to prevent rate limit abuse.
"""

from functools import wraps
from typing import Any, Callable, Optional
import json
from redis import asyncio as aioredis
import logging

from app.core.config import settings


logger = logging.getLogger(__name__)


class CacheManager:
    """Redis-based cache manager with TTL support."""

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize cache manager.

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

    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found/expired
        """
        try:
            redis = await self.get_redis()
            value = await redis.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}", extra={'key': key})
            return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = 3600
    ) -> bool:
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache (must be JSON-serializable)
            ttl_seconds: Time to live in seconds (default 1 hour)

        Returns:
            True if successful
        """
        try:
            redis = await self.get_redis()
            serialized = json.dumps(value)
            await redis.setex(key, ttl_seconds, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}", extra={'key': key})
            return False

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key to delete

        Returns:
            True if key existed and was deleted
        """
        try:
            redis = await self.get_redis()
            result = await redis.delete(key)
            return result > 0
        except Exception as e:
            logger.error(f"Cache delete error: {e}", extra={'key': key})
            return False

    async def clear_pattern(self, pattern: str) -> int:
        """
        Clear all keys matching pattern.

        Args:
            pattern: Redis key pattern (e.g., "tmdb:*")

        Returns:
            Number of keys deleted
        """
        try:
            redis = await self.get_redis()
            keys = await redis.keys(pattern)
            if keys:
                return await redis.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache clear pattern error: {e}", extra={'pattern': pattern})
            return 0

    async def close(self):
        """Close Redis connection."""
        if self._redis:
            await self._redis.close()


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager() -> CacheManager:
    """Get or create global cache manager instance."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager


def cached(
    key_prefix: str,
    ttl_seconds: int = 3600,
    key_args: Optional[list] = None
):
    """
    Decorator for caching function results.

    Args:
        key_prefix: Prefix for cache key
        ttl_seconds: Cache TTL in seconds (default 1 hour)
        key_args: List of argument names to include in cache key

    Example:
        @cached(key_prefix="tmdb:search", ttl_seconds=86400, key_args=['query', 'year'])
        async def search_tv(query: str, year: Optional[int] = None):
            ...
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Build cache key from function name and specified arguments
            cache_key_parts = [key_prefix, func.__name__]

            if key_args:
                # Use specified arguments
                for arg_name in key_args:
                    if arg_name in kwargs:
                        cache_key_parts.append(str(kwargs[arg_name]))
            else:
                # Use all arguments
                cache_key_parts.extend(str(arg) for arg in args)
                cache_key_parts.extend(f"{k}={v}" for k, v in kwargs.items())

            # Create cache key
            key_str = ":".join(str(p) for p in cache_key_parts if p is not None)
            if len(key_str) > 200:
                # Truncate long keys to keep Redis key size reasonable
                truncated_key = key_str[:180]
                cache_key = f"{key_prefix}:{truncated_key}"
            else:
                cache_key = key_str

            # Try to get from cache
            cache_mgr = get_cache_manager()
            cached_result = await cache_mgr.get(cache_key)

            if cached_result is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_result

            # Cache miss - execute function
            logger.debug(f"Cache miss: {cache_key}")
            result = await func(*args, **kwargs)

            # Store in cache
            if result is not None:
                await cache_mgr.set(cache_key, result, ttl_seconds)

            return result

        return wrapper
    return decorator


def tmdb_cached(ttl_seconds: int = 86400):
    """
    TMDB-specific cache decorator (24h TTL by default).

    Args:
        ttl_seconds: Cache TTL (default 24 hours)

    Example:
        @tmdb_cached()
        async def search_tv(self, query: str, year: Optional[int] = None):
            ...
    """
    return cached(key_prefix="tmdb", ttl_seconds=ttl_seconds, key_args=['query', 'year'])
