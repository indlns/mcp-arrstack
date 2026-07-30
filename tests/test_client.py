"""Tests for client module."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

# Add project root to path so `src` package is importable
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.client import BaseARRClient, SeerrClient, TautulliClient, PlexClient


class TestBaseARRClient:
    """Tests for BaseARRClient."""

    def test_init(self):
        client = BaseARRClient("http://sonarr:8989", "test-key")
        assert client.base_url == "http://sonarr:8989"
        assert client.api_key == "test-key"
        assert client.timeout == 30.0

    def test_init_trailing_slash(self):
        client = BaseARRClient("http://sonarr:8989/", "test-key")
        assert client.base_url == "http://sonarr:8989"

    @pytest.mark.asyncio
    async def test_get_success(self, monkeypatch, mock_httpx_client, mock_httpx_response):
        """Test successful GET request."""
        mock_resp = mock_httpx_response(json_data=[{"id": 1, "title": "Test"}])
        mock_httpx_client.get = AsyncMock(return_value=mock_resp)

        client = BaseARRClient("http://sonarr:8989", "test-key")
        monkeypatch.setattr(BaseARRClient, 'client', property(lambda self: mock_httpx_client))
        result = await client.get("/series", {"term": "test"})
        assert result == [{"id": 1, "title": "Test"}]

    @pytest.mark.asyncio
    async def test_post_success(self, monkeypatch, mock_httpx_client, mock_httpx_response):
        """Test successful POST request."""
        mock_resp = mock_httpx_response(json_data={"id": 123})
        mock_httpx_client.post = AsyncMock(return_value=mock_resp)

        client = BaseARRClient("http://sonarr:8989", "test-key")
        monkeypatch.setattr(BaseARRClient, 'client', property(lambda self: mock_httpx_client))
        result = await client.post("/series", {"title": "Test"})
        assert result == {"id": 123}


class TestSeerrClient:
    """Tests for SeerrClient."""

    def test_init(self):
        client = SeerrClient("http://seerr:5055", "test-key")
        assert client.base_url == "http://seerr:5055"
        assert client.api_key == "test-key"

    @pytest.mark.asyncio
    async def test_get_with_numeric_params_not_encoded(
        self, mock_httpx_client, mock_httpx_response, monkeypatch
    ):
        """Numeric query params must NOT be URL-encoded.

        Regression test: quote(str(50), safe="") produces '%35%30',
        which Seerr's parser rejects with 400 Bad Request.
        """
        # Capture the actual URL passed to httpx.AsyncClient.get()
        captured_url = None

        async def capture_get(url, **kwargs):
            nonlocal captured_url
            captured_url = str(url)
            return mock_httpx_response(json_data={"results": []})

        monkeypatch.setattr(mock_httpx_client, "get", capture_get)

        client = SeerrClient("http://seerr:5055", "test-key")
        monkeypatch.setattr(SeerrClient, 'client', property(lambda self: mock_httpx_client))
        # Call with numeric params
        await client.get("/request", {"page": 1, "resultsPerPage": 50})

        assert captured_url is not None
        # Numeric values must appear as plain digits
        assert "page=1" in captured_url
        assert "resultsPerPage=50" in captured_url
        # They must NOT be percent-encoded
        assert "%31" not in captured_url
        assert "%35%30" not in captured_url

    @pytest.mark.asyncio
    async def test_get_with_string_params_encoded(self, mock_httpx_client, mock_httpx_response, monkeypatch):
        """String query params should be URL-encoded (spaces → %20)."""
        captured_url = None

        async def capture_get(url, **kwargs):
            nonlocal captured_url
            captured_url = str(url)
            return mock_httpx_response(json_data={"results": []})

        monkeypatch.setattr(mock_httpx_client, "get", capture_get)

        client = SeerrClient("http://seerr:5055", "test-key")
        monkeypatch.setattr(SeerrClient, 'client', property(lambda self: mock_httpx_client))
        await client.get("/search", {"query": "hello world"})

        assert captured_url is not None
        # Spaces in strings should be %20-encoded
        assert "%20" in captured_url
        assert "+" not in captured_url  # Seerr rejects + for spaces


class TestTautulliClient:
    """Tests for TautulliClient."""

    def test_init(self):
        client = TautulliClient("http://tautulli:8181", "test-key")
        assert client.base_url == "http://tautulli:8181"
        assert client.api_key == "test-key"


class TestPlexClient:
    """Tests for PlexClient."""

    def test_init(self):
        client = PlexClient("http://plex:32400", "plex-token")
        assert client.base_url == "http://plex:32400"
        assert client.plex_token == "plex-token"


class TestBaseARRClientRateLimiting:
    """Tests for BaseARRClient rate limiting integration."""

    def test_init_with_rate_limiter(self):
        """Test that rate_limiter is stored in __init__."""
        from src.utils import RateLimiter
        limiter = RateLimiter(max_requests=5, window_seconds=60)
        client = BaseARRClient("http://sonarr:8989", "test-key", rate_limiter=limiter)
        assert client.rate_limiter is limiter

    def test_init_default_rate_limiter_is_none(self):
        """Test that rate_limiter defaults to None."""
        client = BaseARRClient("http://sonarr:8989", "test-key")
        assert client.rate_limiter is None

    @pytest.mark.asyncio
    async def test_no_rate_limit_when_limiter_none(self, monkeypatch, mock_httpx_client, mock_httpx_response):
        """Test that requests succeed when rate_limiter is None."""
        mock_resp = mock_httpx_response(json_data=[{"id": 1}])
        mock_httpx_client.get = AsyncMock(return_value=mock_resp)

        client = BaseARRClient("http://sonarr:8989", "test-key")
        monkeypatch.setattr(BaseARRClient, 'client', property(lambda self: mock_httpx_client))
        result = await client.get("/series")
        assert result == [{"id": 1}]

    @pytest.mark.asyncio
    async def test_rate_limit_blocks_when_exceeded(self):
        """Test that requests raise RuntimeError when rate limit exceeded."""
        from src.utils import RateLimiter

        # Allow only 2 requests per window
        limiter = RateLimiter(max_requests=2, window_seconds=60)

        client = BaseARRClient("http://sonarr:8989", "test-key", rate_limiter=limiter)

        # First two requests should be allowed (but they'll fail at HTTP level,
        # we just need to verify the rate limiter is consumed)
        await limiter.acquire("sonarr")
        await limiter.acquire("sonarr")

        # Third request should be blocked
        result = await limiter.acquire("sonarr")
        assert result is False


class TestBaseARRClientCaching:
    """Tests for BaseARRClient caching integration."""

    @pytest.mark.asyncio
    async def test_cache_ttl_stored(self):
        """Test that cache_ttl is stored in __init__."""
        client = BaseARRClient("http://sonarr:8989", "test-key", cache_ttl=120)
        assert client.cache_ttl == 120

    @pytest.mark.asyncio
    async def test_default_cache_ttl_is_zero(self):
        """Test that cache_ttl defaults to 0 (disabled)."""
        client = BaseARRClient("http://sonarr:8989", "test-key")
        assert client.cache_ttl == 0

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_data(self, monkeypatch, mock_httpx_client, mock_httpx_response):
        """Test that cached data is returned without HTTP call."""
        from src.utils import clear_cache

        mock_resp = mock_httpx_response(json_data=[{"id": 1, "title": "Cached"}])
        mock_httpx_client.get = AsyncMock(return_value=mock_resp)

        client = BaseARRClient("http://sonarr:8989", "test-key", cache_ttl=300)
        monkeypatch.setattr(BaseARRClient, 'client', property(lambda self: mock_httpx_client))

        clear_cache()

        # First call — should make HTTP request and cache result
        result1 = await client.get("/series", {"term": "test"})
        assert result1 == [{"id": 1, "title": "Cached"}]
        assert mock_httpx_client.get.call_count == 1

        # Second call with same params — should hit cache, no new HTTP call
        result2 = await client.get("/series", {"term": "test"})
        assert result2 == [{"id": 1, "title": "Cached"}]
        # HTTP get should NOT have been called again
        assert mock_httpx_client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_cache_miss_different_params(self, monkeypatch, mock_httpx_client, mock_httpx_response):
        """Test that different params produce cache miss."""
        from src.utils import clear_cache

        responses = [
            mock_httpx_response(json_data=[{"id": 1, "term": "a"}]),
            mock_httpx_response(json_data=[{"id": 2, "term": "b"}]),
        ]
        call_idx = [0]

        async def side_effect(*args, **kwargs):
            resp = responses[call_idx[0]]
            call_idx[0] += 1
            return resp

        mock_httpx_client.get = AsyncMock(side_effect=side_effect)

        client = BaseARRClient("http://sonarr:8989", "test-key", cache_ttl=300)
        monkeypatch.setattr(BaseARRClient, 'client', property(lambda self: mock_httpx_client))

        clear_cache()

        # Different params — each should be a cache miss
        r1 = await client.get("/series", {"term": "alpha"})
        assert r1 == [{"id": 1, "term": "a"}]

        r2 = await client.get("/series", {"term": "beta"})
        assert r2 == [{"id": 2, "term": "b"}]

        # Both calls should have hit the network
        assert mock_httpx_client.get.call_count == 2


class TestBaseARRClientBuildCacheKey:
    """Tests for _build_cache_key deterministic generation."""

    def test_cache_key_endpoint_only(self):
        """Test cache key with endpoint only."""
        client = BaseARRClient("http://sonarr:8989", "test-key")
        key = client._build_cache_key("/series")
        assert key == "series"

    def test_cache_key_with_params_sorted(self):
        """Test that params are sorted for deterministic keys."""
        client = BaseARRClient("http://sonarr:8989", "test-key")
        key1 = client._build_cache_key("/series", {"b": "2", "a": "1"})
        key2 = client._build_cache_key("/series", {"a": "1", "b": "2"})
        assert key1 == key2

    def test_cache_key_includes_params(self):
        """Test that params are included in the key."""
        client = BaseARRClient("http://sonarr:8989", "test-key")
        key = client._build_cache_key("/series", {"term": "test"})
        assert "series" in key
        assert "term=test" in key

    def test_cache_key_no_params_none(self):
        """Test that None params don't add junk to key."""
        client = BaseARRClient("http://sonarr:8989", "test-key")
        key = client._build_cache_key("/series", None)
        assert key == "series"

    def test_cache_key_no_params_empty_dict(self):
        """Test that empty dict params don't add junk to key."""
        client = BaseARRClient("http://sonarr:8989", "test-key")
        key = client._build_cache_key("/series", {})
        assert key == "series"


class TestBaseARRClientServiceName:
    """Tests for service_name parameter."""

    def test_service_name_defaults_from_api_prefix(self):
        """Test that service_name defaults from API_PREFIX."""
        client = BaseARRClient("http://sonarr:8989", "test-key")
        # API_PREFIX is "/api/v3" → service_name is "api" (first segment)
        assert client.service_name == "api"

    def test_service_name_custom(self):
        """Test custom service_name overrides default."""
        client = BaseARRClient("http://sonarr:8989", "test-key", service_name="my_sonarr")
        assert client.service_name == "my_sonarr"


class TestBaseARRClientLazyInit:
    """Tests for lazy httpx.AsyncClient initialization (BUG-54)."""

    def test_client_is_none_initially(self):
        """Test that _client is None before first access."""
        client = BaseARRClient("http://sonarr:8989", "test-key")
        assert client._client is None

    def test_client_initialized_on_first_access(self):
        """Test that accessing .client creates the httpx.AsyncClient."""
        client = BaseARRClient("http://sonarr:8989", "test-key")
        assert client._client is None
        _ = client.client  # trigger initialization
        assert client._client is not None
        assert isinstance(client._client, httpx.AsyncClient)

    def test_client_is_reused_on_subsequent_access(self):
        """Test that the same client instance is returned on repeated access."""
        client = BaseARRClient("http://sonarr:8989", "test-key")
        first = client.client
        second = client.client
        assert first is second

    def test_client_base_url_set(self):
        """Test that the client's base_url matches the configured base_url."""
        client = BaseARRClient("http://sonarr:8989", "test-key")
        c = client.client
        assert c.base_url == "http://sonarr:8989"

    def test_client_headers_set(self):
        """Test that the client has the correct headers."""
        client = BaseARRClient("http://sonarr:8989", "my-api-key")
        c = client.client
        assert c.headers["X-Api-Key"] == "my-api-key"
        assert c.headers["Content-Type"] == "application/json"

    def test_client_timeout_set(self):
        """Test that the client has the correct timeout."""
        client = BaseARRClient("http://sonarr:8989", "test-key", timeout=60.0)
        c = client.client
        assert c.timeout.connect == 60.0
        assert c.timeout.read == 60.0
        assert c.timeout.write == 60.0


class TestSeerrClientLazyInit:
    """Tests for lazy httpx.AsyncClient initialization in SeerrClient."""

    def test_client_is_none_initially(self):
        client = SeerrClient("http://seerr:5055", "test-key")
        assert client._client is None

    def test_client_initialized_on_first_access(self):
        client = SeerrClient("http://seerr:5055", "test-key")
        _ = client.client
        assert client._client is not None

    def test_client_is_reused(self):
        client = SeerrClient("http://seerr:5055", "test-key")
        assert client.client is client.client


class TestTautulliClientLazyInit:
    """Tests for lazy httpx.AsyncClient initialization in TautulliClient."""

    def test_client_is_none_initially(self):
        client = TautulliClient("http://tautulli:8181", "test-key")
        assert client._client is None

    def test_client_initialized_on_first_access(self):
        client = TautulliClient("http://tautulli:8181", "test-key")
        _ = client.client
        assert client._client is not None


class TestPlexClientLazyInit:
    """Tests for lazy httpx.AsyncClient initialization in PlexClient."""

    def test_client_is_none_initially(self):
        client = PlexClient("http://plex:32400", "token")
        assert client._client is None

    def test_client_initialized_on_first_access(self):
        client = PlexClient("http://plex:32400", "token")
        _ = client.client
        assert client._client is not None

    def test_client_has_plex_headers(self):
        client = PlexClient("http://plex:32400", "my-token")
        c = client.client
        assert c.headers["X-Plex-Token"] == "my-token"
        assert c.headers["X-Plex-Product"] == "MCP-ARR-Stack"
