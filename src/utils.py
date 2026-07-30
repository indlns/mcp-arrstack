"""Utility functions for MCP ARR Stack server."""

import asyncio
import functools
import logging
import time
from typing import Any, Callable, TypeVar

logger = logging.getLogger(__name__)

# Cache storage: {(service, endpoint, params_key): (response_data, timestamp)}
_cache: dict[str, tuple[Any, float]] = {}

# Lock for thread-safe cache access during concurrent requests.
# Protects _cache dict from race conditions in async context.
_cache_lock = asyncio.Lock()


def get_cache_key(service: str, endpoint: str, params: dict | None = None) -> str:
    """Generate a cache key from service, endpoint and parameters."""
    key = f"{service}:{endpoint}"
    if params:
        sorted_params = "&".join(f"{k}={v}" for k, v in sorted(params.items()))
        key += f":{sorted_params}"
    return key


async def cached_get(
    config_key: str,
    cache_ttl: int = 300,
) -> Callable:
    """Decorator for caching async function results.

    Uses asyncio.Lock for thread-safe cache access during concurrent requests.

    Args:
        config_key: Prefix for the cache key (e.g., service name).
        cache_ttl: Time-to-live in seconds (default: 300).

    Returns:
        A decorator that caches the async function's return value.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            if not config_key:
                return await func(*args, **kwargs)

            # Generate cache key from function name and arguments
            key_parts = [config_key, func.__name__]
            for arg in args[1:]:  # Skip self
                if isinstance(arg, (str, int, float, bool)):
                    key_parts.append(str(arg))
            for k, v in sorted(kwargs.items()):
                key_parts.append(f"{k}={v}")

            cache_key = "|".join(key_parts)
            now = time.time()

            # Thread-safe cache read with lock
            async with _cache_lock:
                if cache_key in _cache:
                    data, timestamp = _cache[cache_key]
                    if now - timestamp < cache_ttl:
                        logger.debug(f"Cache hit for {cache_key}")
                        return data

            result = await func(*args, **kwargs)

            # Thread-safe cache write with lock
            async with _cache_lock:
                _cache[cache_key] = (result, now)

            logger.debug(f"Cache set for {cache_key}, TTL={cache_ttl}s")
            return result
        return wrapper
    return decorator


async def cache_get(cache_key: str) -> Any | None:
    """Safely read from cache with lock protection.

    Args:
        cache_key: The cache key to look up.

    Returns:
        Cached value if present and not expired, else None.
    """
    async with _cache_lock:
        if cache_key in _cache:
            data, timestamp = _cache[cache_key]
            return data
    return None


async def cache_set(cache_key: str, data: Any) -> None:
    """Safely write to cache with lock protection.

    Args:
        cache_key: The cache key to store under.
        data: The data to cache.
    """
    async with _cache_lock:
        _cache[cache_key] = (data, time.time())


def clear_cache() -> None:
    """Clear all cached data."""
    global _cache
    _cache.clear()


T = TypeVar("T")


async def safe_execute(
    func: Callable[..., T],
    service_name: str,
    fallback: Any = None,
) -> T | Any:
    """Safely execute a function with error handling.

    Returns fallback value if the function raises an exception.
    """
    try:
        if asyncio.iscoroutinefunction(func):
            return await func()
        return func()
    except Exception as e:
        logger.error(f"Error executing {service_name}: {e}", exc_info=True)
        return fallback


class RateLimiter:
    """Simple in-memory rate limiter."""

    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = {}

    async def acquire(self, key: str = "default") -> bool:
        """Try to acquire a rate limit slot. Returns True if allowed."""
        now = time.time()
        if key not in self._requests:
            self._requests[key] = []

        # Clean old requests outside the window
        self._requests[key] = [
            t for t in self._requests[key]
            if now - t < self.window_seconds
        ]

        if len(self._requests[key]) >= self.max_requests:
            logger.warning(f"Rate limit exceeded for {key}")
            return False

        self._requests[key].append(now)
        return True


# Module-level rate limiter instance
default_rate_limiter = RateLimiter(max_requests=20, window_seconds=60)
