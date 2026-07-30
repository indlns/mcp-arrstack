"""Shared fixtures for tests."""

import os
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

import pytest


# Point to the project root (tests/../)
PROJECT_ROOT = Path(__file__).parent.parent


@pytest.fixture(autouse=True)
def _mock_env():
    """Ensure environment variables don't interfere with tests."""
    # Remove all ARR-related env vars during tests
    arr_vars = [
        "SONARR_HOST", "SONARR_API_KEY",
        "RADARR_HOST", "RADARR_API_KEY",
        "LIDARR_HOST", "LIDARR_API_KEY",
        "PROWLARR_HOST", "PROWLARR_API_KEY",
        "READARR_HOST", "READARR_API_KEY",
        "SEERR_HOST", "SEERR_API_KEY",
        "TAUTULLI_HOST", "TAUTULLI_API_KEY",
        "PLEX_HOST", "PLEX_TOKEN",
    ]
    original = {}
    for var in arr_vars:
        original[var] = os.environ.pop(var, None)
    yield
    for var, val in original.items():
        if val is not None:
            os.environ[var] = val
        elif var in os.environ:
            del os.environ[var]


@pytest.fixture
def mock_httpx_response():
    """Factory fixture for creating mock httpx responses.

    raise_for_status() checks status_code and raises httpx.HTTPStatusError
    for 4xx/5xx responses, so error-handling paths in tools are actually tested.
    """
    def _create(status_code=200, json_data=None):
        mock_resp = MagicMock()
        mock_resp.status_code = status_code
        mock_resp.json.return_value = json_data or {}

        def _raise_for_status():
            if status_code >= 400:
                from httpx import HTTPStatusError, Request
                req = Request("GET", "http://localhost/test")
                from httpx import Response
                real_resp = Response(status_code, request=req)
                raise HTTPStatusError("Error", request=req, response=real_resp)

        mock_resp.raise_for_status = _raise_for_status
        return mock_resp
    return _create


@pytest.fixture
def mock_httpx_client(mock_httpx_response):
    """Create a mock httpx.AsyncClient."""
    async def _mock_get(*args, **kwargs):
        return mock_httpx_response()
    async def _mock_post(*args, **kwargs):
        return mock_httpx_response()
    async def _mock_put(*args, **kwargs):
        return mock_httpx_response()
    async def _mock_delete(*args, **kwargs):
        return mock_httpx_response()

    mock_client = AsyncMock()
    mock_client.get = _mock_get
    mock_client.post = _mock_post
    mock_client.put = _mock_put
    mock_client.delete = _mock_delete
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock()
    return mock_client
