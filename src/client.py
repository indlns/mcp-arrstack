"""Base HTTP client for ARR Stack services."""

import logging
from typing import Any, Optional
from urllib.parse import quote

import httpx

from .utils import RateLimiter, cache_get, cache_set

logger = logging.getLogger(__name__)


class BaseARRClient:
    """Base async HTTP client for ARR stack services.

    Supports optional rate limiting and response caching via
    ``RateLimiter`` and ``cache_get``/``cache_set`` from ``utils``.
    """

    API_PREFIX = "/api/v3"

    def __init__(
        self,
        base_url: str,
        api_key: str,
        timeout: float = 30.0,
        rate_limiter: RateLimiter | None = None,
        cache_ttl: int = 0,
        service_name: str = "",
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.rate_limiter = rate_limiter
        self.cache_ttl = cache_ttl
        self.service_name = service_name or self.API_PREFIX.lstrip("/").split("/")[0]
        self.headers = {
            "X-Api-Key": api_key,
            "Content-Type": "application/json",
        }
        self._client: httpx.AsyncClient | None = None

    def _build_cache_key(self, endpoint: str, params: dict | None = None) -> str:
        """Build a deterministic cache key from endpoint and query params."""
        parts = [endpoint.lstrip("/")]
        if params:
            for k, v in sorted(params.items()):
                parts.append(f"{k}={v}")
        return ":".join(parts)

    async def _acquire_rate_limit(self, service_name: str) -> bool:
        """Acquire a rate-limit slot before making an API request.

        Returns ``True`` if allowed, ``False`` if the limit was exceeded.
        """
        if self.rate_limiter is None:
            return True
        allowed = await self.rate_limiter.acquire(service_name)
        if not allowed:
            logger.warning(
                "Rate limit exceeded for %s — request throttled", service_name
            )
        return allowed

    @property
    def client(self) -> httpx.AsyncClient:
        """Return a lazily-initialized async HTTP client.

        The client is created once and reused across all requests,
        enabling connection pooling and keep-alive.
        """
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self.headers,
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def get(
        self,
        endpoint: str,
        params: dict | None = None,
        cache_ttl: int | None = None,
    ) -> dict | list:
        """Send GET request to API with optional caching and rate limiting.

        Rate limiting is applied **before every request**.  Caching is
        applied only when ``cache_ttl > 0`` — the cached value is checked
        before the rate limiter and the HTTP call; on success the result
        is stored in cache.

        Args:
            endpoint: API endpoint path (e.g. ``"/series"``).
            params: Optional query parameters.
            cache_ttl: Per-request TTL override (seconds).  Falls back to
                ``self.cache_ttl`` when ``None`` or ``0``.

        Returns:
            Parsed JSON response.
        """
        url = f"{self.API_PREFIX}/{endpoint.lstrip('/')}"
        effective_ttl = cache_ttl if cache_ttl else self.cache_ttl

        # 1. Try cache first (if enabled)
        if effective_ttl > 0:
            cache_key = self._build_cache_key(endpoint, params)
            cached = await cache_get(cache_key)
            if cached is not None:
                logger.debug("Cache hit for GET %s", url)
                return cached

        # 2. Rate limit check (skip only when no limiter configured)
        allowed = await self._acquire_rate_limit(self.service_name)
        if not allowed:
            raise RuntimeError(
                f"Rate limit exceeded for {url} — request throttled"
            )

        try:
            resp = await self.client.get(url, params=params)
            resp.raise_for_status()
            result = resp.json()
            logger.debug(f"GET {url} -> {resp.status_code}")

            # 3. Store in cache on success (if enabled)
            if effective_ttl > 0:
                await cache_set(cache_key, result)

            return result
        except httpx.HTTPStatusError as e:
            logger.error(f"GET {url} failed: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"GET {url} request error: {e}")
            raise

    async def post(self, endpoint: str, data: dict | None = None) -> dict | list:
        """Send POST request to API."""
        url = f"{self.API_PREFIX}/{endpoint.lstrip('/')}"
        try:
            resp = await self.client.post(url, json=data)
            resp.raise_for_status()
            logger.debug(f"POST {url} -> {resp.status_code}")
            return resp.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"POST {url} failed: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"POST {url} request error: {e}")
            raise

    async def put(self, endpoint: str, data: dict | None = None) -> dict:
        """Send PUT request to API."""
        url = f"{self.API_PREFIX}/{endpoint.lstrip('/')}"
        try:
            resp = await self.client.put(url, json=data)
            resp.raise_for_status()
            logger.debug(f"PUT {url} -> {resp.status_code}")
            return resp.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"PUT {url} failed: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"PUT {url} request error: {e}")
            raise

    async def delete(self, endpoint: str, item_id: int, params: dict | None = None) -> int:
        """Send DELETE request to API."""
        url = f"{self.API_PREFIX}/{endpoint.lstrip('/')}/{item_id}"
        try:
            resp = await self.client.delete(url, params=params)
            logger.debug(f"DELETE {url} -> {resp.status_code}")
            return resp.status_code
        except httpx.HTTPStatusError as e:
            logger.error(f"DELETE {url} failed: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"DELETE {url} request error: {e}")
            raise


class ProwlarrClient(BaseARRClient):
    """Client for Prowlarr (uses /api/v1 instead of /api/v3)."""

    API_PREFIX = "/api/v1"


class LidarrClient(BaseARRClient):
    """Client for Lidarr (uses /api/v1 instead of /api/v3)."""

    API_PREFIX = "/api/v1"


class ReadarrClient(BaseARRClient):
    """Client for Readarr (uses /api/v1 instead of /api/v3)."""

    API_PREFIX = "/api/v1"


class SeerrClient:
    """Client for Seerr (uses /api/v1 instead of /api/v3)."""

    API_PREFIX = "/api/v1"

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Return a lazily-initialized async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "X-Api-Key": self.api_key,
                    "Content-Type": "application/json",
                },
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def get(self, endpoint: str, params: dict | None = None) -> dict | list:
        """Send GET request to Seerr API.

        Query parameter values are manually URL-encoded using percent-encoding
        (spaces become %20, not +) because Seerr rejects reserved characters.
        The full URL is constructed manually to avoid double-encoding by httpx.
        """
        url = f"{self.API_PREFIX}/{endpoint.lstrip('/')}"
        # Manually encode params to ensure %20 for spaces (Seerr rejects +)
        # Only apply URL encoding to string values; numeric types (int/float)
        # must be passed as-is — encoding them (e.g. 50 → %35%30) breaks
        # Seerr's query parser and causes 400 Bad Request errors.
        if params:
            query_parts = []
            for k, v in params.items():
                encoded_key = quote(str(k), safe="")
                if isinstance(v, (int, float)):
                    encoded_val = str(v)
                else:
                    encoded_val = quote(str(v), safe="")
                query_parts.append(f"{encoded_key}={encoded_val}")
            url += "?" + "&".join(query_parts)

        try:
            resp = await self.client.get(url)
            resp.raise_for_status()
            logger.debug(f"Seerr GET {url} -> {resp.status_code}")
            return resp.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Seerr GET {url} failed: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Seerr GET {url} request error: {e}")
            raise

    async def post(self, endpoint: str, data: dict | None = None) -> dict | list:
        """Send POST request to Seerr API."""
        url = f"{self.API_PREFIX}/{endpoint.lstrip('/')}"
        try:
            resp = await self.client.post(url, json=data)
            resp.raise_for_status()
            logger.debug(f"Seerr POST {url} -> {resp.status_code}")
            return resp.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Seerr POST {url} failed: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Seerr POST {url} request error: {e}")
            raise

    async def put(self, endpoint: str, data: dict | None = None) -> dict:
        """Send PUT request to Seerr API."""
        url = f"{self.API_PREFIX}/{endpoint.lstrip('/')}"
        try:
            resp = await self.client.put(url, json=data)
            resp.raise_for_status()
            logger.debug(f"Seerr PUT {url} -> {resp.status_code}")
            return resp.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Seerr PUT {url} failed: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Seerr PUT {url} request error: {e}")
            raise


class TautulliClient:
    """Client for Tautulli (uses different API pattern)."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Return a lazily-initialized async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={"Content-Type": "application/json"},
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def get(self, method: str, params: dict | None = None) -> dict | list:
        """Send GET request to Tautulli API.

        Args:
            method: Tautulli API method name (e.g., 'get_activity').
            params: Additional query parameters.
        """
        default_params = {
            "apikey": self.api_key,
            "cmd": method,
        }
        if params:
            default_params.update(params)

        try:
            resp = await self.client.get("/api/v2", params=default_params)
            resp.raise_for_status()
            result = resp.json()
            logger.debug(f"Tautulli GET cmd={method} -> {resp.status_code}")
            return result.get("response", {}).get("data", result)
        except httpx.HTTPStatusError as e:
            logger.error(f"Tautulli GET {method} failed: {e.response.status_code}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Tautulli GET {method} request error: {e}")
            raise


class PlexClient:
    """Client for Plex Media Server."""

    def __init__(self, base_url: str, plex_token: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.plex_token = plex_token
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Return a lazily-initialized async HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers={
                    "Accept": "application/json",
                    "X-Plex-Token": self.plex_token,
                    "X-Plex-Product": "MCP-ARR-Stack",
                    "X-Plex-Version": "0.1.1",
                },
                timeout=httpx.Timeout(self.timeout),
            )
        return self._client

    async def get(self, endpoint: str, params: dict | None = None) -> dict | list:
        """Send GET request to Plex API."""
        url = f"/{endpoint.lstrip('/')}"
        if params is None:
            params = {}

        try:
            resp = await self.client.get(url, params=params)
            resp.raise_for_status()
            logger.debug(f"Plex GET {url} -> {resp.status_code}")
            return resp.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Plex GET {url} failed: {e.response.status_code}")
            raise
        except httpx.RequestError as e:
            logger.error(f"Plex GET {url} request error: {e}")
            raise
