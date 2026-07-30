"""Tests for utils module."""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import (
    get_cache_key,
    clear_cache,
    safe_execute,
    RateLimiter,
    cache_get,
    cache_set,
    _cache,
    _cache_lock,
)


class TestCacheKey:
    """Tests for get_cache_key function."""

    def test_basic_key(self):
        key = get_cache_key("sonarr", "/series")
        assert key == "sonarr:/series"

    def test_key_with_params(self):
        key = get_cache_key("sonarr", "/series", {"term": "test"})
        assert "sonarr:/series" in key
        assert "term=test" in key

    def test_key_deterministic(self):
        """Cache key should be deterministic."""
        params1 = {"b": 2, "a": 1}
        params2 = {"a": 1, "b": 2}
        key1 = get_cache_key("service", "/endpoint", params1)
        key2 = get_cache_key("service", "/endpoint", params2)
        assert key1 == key2


class TestClearCache:
    """Tests for clear_cache function."""

    def test_clear_cache(self):
        """Test that cache can be cleared."""
        # Populate some fake cache data
        import sys
        from pathlib import Path
        src_path = str(Path(__file__).parent.parent / "src")
        if src_path not in sys.path:
            sys.path.insert(0, src_path)

        # Import the module's cache
        import utils
        utils._cache["test:key"] = ({"data": 1}, 1234567890)
        assert "test:key" in utils._cache

        clear_cache()
        assert utils._cache == {}


class TestSafeExecute:
    """Tests for safe_execute function."""

    @pytest.mark.asyncio
    async def test_safe_execute_success(self):
        """Test successful execution."""
        async def success_func():
            return "success"

        result = await safe_execute(success_func, "test")
        assert result == "success"

    @pytest.mark.asyncio
    async def test_safe_execute_failure(self):
        """Test graceful failure with fallback."""
        async def failing_func():
            raise ValueError("Test error")

        result = await safe_execute(failing_func, "test", fallback="fallback")
        assert result == "fallback"

    @pytest.mark.asyncio
    async def test_safe_execute_default_fallback(self):
        """Test default fallback is None."""
        async def failing_func():
            raise ValueError("Test error")

        result = await safe_execute(failing_func, "test")
        assert result is None

    def test_safe_execute_sync(self):
        """Test with synchronous function."""
        def sync_func():
            return "sync success"

        result = asyncio.run(safe_execute(sync_func, "test"))
        assert result == "sync success"


class TestRateLimiter:
    """Tests for RateLimiter class."""

    @pytest.mark.asyncio
    async def test_rate_limiter_allows_within_limit(self):
        """Test that requests within limit are allowed."""
        limiter = RateLimiter(max_requests=5, window_seconds=60)

        for _ in range(5):
            result = await limiter.acquire("test")
            assert result is True

    @pytest.mark.asyncio
    async def test_rate_limiter_blocks_exceeding(self):
        """Test that requests exceeding limit are blocked."""
        limiter = RateLimiter(max_requests=3, window_seconds=60)

        for _ in range(3):
            await limiter.acquire("test")

        result = await limiter.acquire("test")
        assert result is False

    @pytest.mark.asyncio
    async def test_rate_limiter_separate_keys(self):
        """Test that different keys have separate limits."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        await limiter.acquire("key1")
        await limiter.acquire("key1")
        assert await limiter.acquire("key1") is False  # key1 exhausted

        assert await limiter.acquire("key2") is True  # key2 still available

    @pytest.mark.asyncio
    async def test_rate_limiter_default_key(self):
        """Test default rate limiter key."""
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        await limiter.acquire()  # Uses "default" key
        await limiter.acquire()  # Uses "default" key

        result = await limiter.acquire()
        assert result is False


class TestCacheGetSet:
    """Tests for cache_get / cache_set helpers with asyncio.Lock."""

    @pytest.mark.asyncio
    async def test_cache_set_and_get(self):
        """Test basic cache write and read."""
        clear_cache()
        await cache_set("mykey", {"data": 42})
        result = await cache_get("mykey")
        assert result == {"data": 42}

    @pytest.mark.asyncio
    async def test_cache_get_missing_key(self):
        """Test that missing key returns None."""
        clear_cache()
        result = await cache_get("nonexistent")
        assert result is None

    @pytest.mark.asyncio
    async def test_cache_overwrite(self):
        """Test that overwriting a key updates the value."""
        clear_cache()
        await cache_set("key", "first")
        await cache_set("key", "second")
        result = await cache_get("key")
        assert result == "second"

    @pytest.mark.asyncio
    async def test_concurrent_cache_access(self):
        """Test that concurrent coroutines can safely access the cache.

        This verifies asyncio.Lock protects against race conditions.
        """
        clear_cache()
        num_coroutines = 20

        async def write_many(i: int):
            key = f"concurrent_key_{i % 5}"
            await cache_set(key, {"idx": i})

        await asyncio.gather(*[write_many(i) for i in range(num_coroutines)])

        # All 5 keys should exist with valid data
        for i in range(5):
            key = f"concurrent_key_{i}"
            result = await cache_get(key)
            assert result is not None
            assert "idx" in result

    @pytest.mark.asyncio
    async def test_cache_set_preserves_timestamp(self):
        """Test that cache_set stores a valid timestamp."""
        import time as _time
        clear_cache()
        now = _time.time()
        await cache_set("ts_key", "data")
        # Verify the entry exists in the raw cache
        assert "ts_key" in _cache
        data, ts = _cache["ts_key"]
        assert data == "data"
        assert ts >= now

    @pytest.mark.asyncio
    async def test_cache_lock_is_asyncio_lock(self):
        """Test that _cache_lock is an asyncio.Lock instance."""
        assert isinstance(_cache_lock, asyncio.Lock)
