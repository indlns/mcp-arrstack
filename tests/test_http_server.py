"""Tests for the Streamable HTTP transport module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from starlette.testclient import TestClient


class TestApiKeyMiddleware:
    """Tests for ApiKeyMiddleware ASGI middleware."""

    def _make_app(self, api_key: str = ""):
        """Create a minimal ASGI app wrapped with ApiKeyMiddleware."""
        from src.http_server import ApiKeyMiddleware

        async def dummy_app(scope, receive, send):
            await send(
                {
                    "type": "http.response.start",
                    "status": 200,
                    "headers": [(b"content-type", b"text/plain")],
                }
            )
            await send(
                {
                    "type": "http.response.body",
                    "body": b"ok",
                }
            )

        if api_key:
            return ApiKeyMiddleware(dummy_app, api_key=api_key)
        return dummy_app

    def _make_request(self, headers: dict | None = None):
        """Create a minimal ASGI scope for an HTTP request."""
        return {
            "type": "http",
            "method": "GET",
            "path": "/",
            "headers": [(k.encode(), v.encode()) for k, v in (headers or {}).items()],
        }

    @pytest.mark.asyncio
    async def test_no_api_key_allows_request(self):
        """When no API key is configured, all requests pass."""
        app = self._make_app(api_key="")
        client = TestClient(app)
        resp = client.get("/")
        assert resp.status_code == 200
        assert resp.text == "ok"

    @pytest.mark.asyncio
    async def test_valid_bearer_token_passes(self):
        """A valid Bearer token allows the request through."""
        app = self._make_app(api_key="secret-key")
        client = TestClient(app)
        resp = client.get("/", headers={"Authorization": "Bearer secret-key"})
        assert resp.status_code == 200
        assert resp.text == "ok"

    @pytest.mark.asyncio
    async def test_missing_authorization_header_rejected(self):
        """Request without Authorization header is rejected with 401."""
        app = self._make_app(api_key="secret-key")
        client = TestClient(app)
        resp = client.get("/")
        assert resp.status_code == 401
        assert "Unauthorized" in resp.text

    @pytest.mark.asyncio
    async def test_wrong_bearer_token_rejected(self):
        """A wrong Bearer token is rejected with 401."""
        app = self._make_app(api_key="secret-key")
        client = TestClient(app)
        resp = client.get("/", headers={"Authorization": "Bearer wrong-token"})
        assert resp.status_code == 401
        assert "Unauthorized" in resp.text

    @pytest.mark.asyncio
    async def test_non_bearer_auth_rejected(self):
        """Non-Bearer Authorization schemes are rejected."""
        app = self._make_app(api_key="secret-key")
        client = TestClient(app)
        resp = client.get("/", headers={"Authorization": "Basic dXNlcjpwYXNz"})
        assert resp.status_code == 401


class TestHealthCheck:
    """Tests for the health_check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check_returns_ok(self):
        """GET /health returns 200 with status ok."""
        from src.http_server import health_check
        from starlette.testclient import TestClient
        from starlette.applications import Starlette
        from starlette.routing import Route

        app = Starlette(routes=[Route("/health", endpoint=health_check)])
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestCreateHttpApp:
    """Tests for create_http_app factory function."""

    @pytest.fixture
    def mock_mcp_server(self):
        """Create a mock MCP Server instance."""
        mock = MagicMock()
        mock.list_tools = AsyncMock()
        mock.call_tool = AsyncMock()
        mock.create_initialization_options = MagicMock(return_value={})
        return mock

    def test_create_http_app_returns_tuple(self, mock_mcp_server):
        """create_http_app returns a (Starlette app, session_manager) tuple."""
        from src.http_server import create_http_app

        app, session_manager = create_http_app(mock_mcp_server)
        assert app is not None
        assert session_manager is not None

    def test_health_endpoint_accessible(self, mock_mcp_server):
        """Health endpoint is accessible and returns 200."""
        from src.http_server import create_http_app

        app, _ = create_http_app(mock_mcp_server)
        client = TestClient(app)
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


class TestConfigIntegration:
    """Tests verifying config HTTP fields are loaded correctly."""

    def test_default_http_config(self):
        """Default HTTP config values are sensible."""
        from src.config import AppConfig

        cfg = AppConfig()
        assert cfg.http_host == "0.0.0.0"
        assert cfg.http_port == 8080
        assert cfg.http_api_key == ""
        assert cfg.http_cors_origins == "*"
        assert cfg.http_ssl_certfile == ""
        assert cfg.http_ssl_keyfile == ""

    def test_http_config_from_env(self, monkeypatch):
        """HTTP config is loaded from environment variables."""
        monkeypatch.setenv("HTTP_HOST", "127.0.0.1")
        monkeypatch.setenv("HTTP_PORT", "9999")
        monkeypatch.setenv("HTTP_API_KEY", "test-key")
        monkeypatch.setenv("HTTP_CORS_ORIGINS", "http://localhost:3000")
        monkeypatch.setenv("HTTP_SSL_CERTFILE", "/path/to/cert.pem")
        monkeypatch.setenv("HTTP_SSL_KEYFILE", "/path/to/key.pem")

        from src.config import load_config

        cfg = load_config()
        assert cfg.http_host == "127.0.0.1"
        assert cfg.http_port == 9999
        assert cfg.http_api_key == "test-key"
        assert cfg.http_cors_origins == "http://localhost:3000"
        assert cfg.http_ssl_certfile == "/path/to/cert.pem"
        assert cfg.http_ssl_keyfile == "/path/to/key.pem"
