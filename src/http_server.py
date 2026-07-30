"""Streamable HTTP transport for MCP ARR Stack server.

Provides ASGI application with MCP Streamable HTTP session management,
API key authentication middleware, CORS support, and health check endpoint.
"""

import json
import logging
import os
from typing import Any

from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route, Mount

try:
    from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
except ImportError:
    StreamableHTTPSessionManager = None  # type: ignore[misc,assignment]


logger = logging.getLogger(__name__)


class ApiKeyMiddleware:
    """Simple API Key Bearer token middleware (ASGI).

    Validates the Authorization header against a configured API key.
    Skipped entirely if no API key is configured (api_key == "").
    """

    def __init__(self, app: Any, api_key: str) -> None:
        self.app = app
        self.api_key = api_key

    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if not self.api_key:
            await self.app(scope, receive, send)
            return

        request = Request(scope, receive)
        auth = request.headers.get("authorization", "")

        if not auth.startswith("Bearer "):
            await send({
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"content-type", b"application/json"),
                ],
            })
            await send({
                "type": "http.response.body",
                "body": json.dumps({"error": "Unauthorized"}).encode(),
            })
            return

        if auth[7:] != self.api_key:
            await send({
                "type": "http.response.start",
                "status": 401,
                "headers": [
                    (b"content-type", b"application/json"),
                ],
            })
            await send({
                "type": "http.response.body",
                "body": json.dumps({"error": "Unauthorized"}).encode(),
            })
            return

        await self.app(scope, receive, send)


async def health_check(request: Request) -> Response:
    """Simple health check endpoint."""
    return Response(
        content='{"status": "ok"}',
        media_type="application/json",
    )


def create_http_app(
    mcp_server: Any,
    host: str = "0.0.0.0",
    port: int = 8080,
    api_key: str = "",
    cors_origins: str = "*",
) -> tuple[Starlette, StreamableHTTPSessionManager]:  # type: ignore[misc]
    """Create a Starlette ASGI application with MCP Streamable HTTP transport.

    Args:
        mcp_server: Configured MCP Server instance.
        host: Bind address for the server.
        port: Bind port for the server.
        api_key: Optional Bearer token for client authentication.
        cors_origins: Comma-separated list of allowed origins or "*" for all.

    Returns:
        Tuple of (Starlette app, StreamableHTTPSessionManager).
    """
    middleware: list[Middleware] = []

    # CORS middleware (outermost — must wrap everything)
    if cors_origins == "*":
        middleware.append(Middleware(CORSMiddleware, allow_origins=["*"]))
    else:
        origins = [o.strip() for o in cors_origins.split(",") if o.strip()]
        middleware.append(Middleware(CORSMiddleware, allow_origins=origins))

    # API Key middleware (only if key is configured)
    if api_key:
        middleware.append(Middleware(ApiKeyMiddleware, api_key=api_key))

    # Create session manager
    if StreamableHTTPSessionManager is None:  # type: ignore[unreachable]
        raise RuntimeError(
            "mcp.server.streamable_http_manager is not available. "
            "Ensure mcp>=1.0.0 is installed."
        )

    session_manager = StreamableHTTPSessionManager(app=mcp_server)  # type: ignore[call-arg]

    # Build routes — health check at /health
    routes: list[Any] = [
        Route("/health", endpoint=health_check),
    ]

    app = Starlette(routes=routes, middleware=middleware)

    # Mount the session manager ASGI app at root path.
    # Use a wrapper to ensure the object is callable as an ASGI app,
    # since StreamableHTTPSessionManager does not implement __call__
    # and must delegate to handle_request instead.
    class _SessionManagerASGI:
        """ASGI wrapper around StreamableHTTPSessionManager."""

        def __init__(self, manager: Any) -> None:
            self._manager = manager

        async def __call__(self, scope: Any, receive: Any, send: Any) -> None:  # type: ignore[override]
            await self._manager.handle_request(scope, receive, send)

    app.mount("/", _SessionManagerASGI(session_manager))

    return app, session_manager


async def run_http_server(mcp_server: Any, config: Any) -> None:  # type: ignore[misc]
    """Entry point for HTTP transport — starts uvicorn server.

    Args:
        mcp_server: Configured MCP Server instance.
        config: AppConfig instance with HTTP settings.
    """
    import uvicorn

    logger.info(
        "Starting MCP HTTP server on %s:%d",
        config.http_host,
        config.http_port,
    )

    app, session_manager = create_http_app(
        mcp_server=mcp_server,
        host=config.http_host,
        port=config.http_port,
        api_key=config.http_api_key,
        cors_origins=config.http_cors_origins,
    )

    config_uvicorn = uvicorn.Config(
        app,
        host=config.http_host,
        port=config.http_port,
        log_level="info",
    )

    # SSL support (optional) — only if both paths are non-empty AND files exist
    if (config.http_ssl_certfile and config.http_ssl_keyfile
            and os.path.isfile(config.http_ssl_certfile)
            and os.path.isfile(config.http_ssl_keyfile)):
        logger.info("SSL enabled: cert=%s, key=%s",
                    config.http_ssl_certfile, config.http_ssl_keyfile)
        config_uvicorn.ssl_certfile = config.http_ssl_certfile
        config_uvicorn.ssl_keyfile = config.http_ssl_keyfile
    else:
        logger.info("SSL disabled (no valid cert/key pair)")

    server = uvicorn.Server(config_uvicorn)

    # Run the session manager context and the server concurrently
    async with session_manager.run():
        await server.serve()
