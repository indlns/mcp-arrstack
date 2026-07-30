# MCP Architecture — Protocol & Tool Dispatch

This document describes how the MCP server registers tools, dispatches calls from LLM clients, and routes them to service backends.

---

## MCP Protocol Basics

**Model Context Protocol (MCP)** is a standard for exposing tools to LLMs. The server advertises available tools and their schemas; the LLM invokes them by name with JSON arguments.

### Core Concepts

| Concept | Description |
|---------|-------------|
| **Tool** | A named function with a JSON Schema input definition, exposed to LLM |
| **Server** | The MCP process that registers tools and handles requests |
| **Transport** | Communication channel: `stdio` (stdin/stdout) or `http` (Streamable HTTP) |
| **Client** | The LLM application calling tools (OpenWebUI, Claude, etc.) |

### Protocol Flow

```
LLM Client                    MCP Server                    ARR Service
    │                              │                              │
    │  1. list_tools()             │                              │
    │─────────────────────────────>│                              │
    │  [Tool schema, Tool schema]  │                              │
    │<─────────────────────────────│                              │
    │                              │                              │
    │  2. call_tool("sonarr_search_series", {title: "Breaking"})  │
    │─────────────────────────────>│                              │
    │                              │  GET /api/v3/series/lookup   │
    │                              │  ?term=Breaking              │
    │                              │─────────────────────────────>│
    │                              │  [{id:1, title:"Breaking.."}]│
    │                              │<─────────────────────────────│
    │  [{type:"text", text:"..."}] │                              │
    │<─────────────────────────────│                              │
```

---

## Tool Registration

Tools are registered at server startup via three structures in `src/server.py`:

### 1. Tool Definitions (`SONARR_TOOLS`, etc.)

Each tool is a `mcp.types.Tool` with a name, description, and JSON Schema input:

```python
SONARR_TOOLS = [
    Tool(
        name="sonarr_search_series",          # MCP tool name
        description="Search for TV series...", # What the LLM sees
        inputSchema={                         # JSON Schema for arguments
            "type": "object",
            "properties": {
                "title": {"type": "string", "description": "Series title"}
            },
            "required": ["title"]
        },
    ),
    # ... more tools
]
```

### 2. Service Map (`SERVICE_MAP`)

Links service names to their tool definitions, factory functions, and config keys:

```python
SERVICE_MAP = {
    "sonarr": (SONARR_TOOLS, _make_sonarr_tools, "sonarr"),
    "radarr": (RADARR_TOOLS, _make_radarr_tools, "radarr"),
    # ...
}
```

### 3. Handler Registry (`TOOL_HANDLERS`)

Auto-built mapping from tool name to (service, method):

```python
TOOL_HANDLERS = {
    "sonarr_search_series": ("sonarr", "search_series"),
    "sonarr_get_series":    ("sonarr", "get_series"),
    "radarr_add_movie":    ("radarr", "add_movie"),
    # ...
}
```

Built by `_register_handlers()` which strips the `{service}_` prefix from tool names.

### Registration at Startup

```python
def create_mcp_server(clients):
    app = Server("mcp-arr-stack")
    available_tools = []
    for service_name, (tools, _, _) in SERVICE_MAP.items():
        if service_name in clients:        # Only enabled services
            available_tools.extend(tools)

    @app.list_tools()
    async def list_tools():
        return available_tools              # LLM sees only enabled tools
```

---

## Tool Dispatch Flow

When an LLM calls a tool, the request flows through these layers:

### Step 1: MCP Handler

```python
@app.call_tool()
async def call_tool(name, arguments):
    # Arguments can be dict, list, or None
    if arguments is None:
        arguments = {}
    if isinstance(arguments, list):
        return [TextContent(type="text", text="Error: expects keyword args")]
    return await _dispatch_tool(name, arguments, clients)
```

### Step 2: Dispatch (`_dispatch_tool`)

```python
async def _dispatch_tool(name, args, clients):
    # 1. Lookup handler
    service_name, method_name = TOOL_HANDLERS[name]

    # 2. Check service is configured
    if service_name not in clients:
        return error("Service not configured")

    # 3. Create tools instance via factory
    factory_fn = SERVICE_MAP[service_name][1]
    tools_instance = factory_fn(client)

    # 4. Call the method with kwargs
    method = getattr(tools_instance, method_name)
    result = await method(**args)

    # 5. Serialize and return
    return [TextContent(type="text", text=json.dumps(result))]
```

### Step 3: Tools Class

The tools class method makes the actual HTTP call:

```python
class SonarrTools:
    async def search_series(self, title: str):
        results = await self.client.get("/series/lookup", {"term": title})
        return results
```

### Step 4: Client Layer

The client builds the full URL and makes the HTTP request:

```python
class BaseARRClient:
    async def get(self, endpoint, params=None):
        url = f"{self.API_PREFIX}/{endpoint.lstrip('/')}"
        # -> GET http://sonarr:8989/api/v3/series/lookup?term=Breaking
        resp = await c.get(url, params=params)
        return resp.json()
```

---

## Complete Example: `sonarr_search_series`

```
1. LLM calls: call_tool("sonarr_search_series", {"title": "Breaking Bad"})

2. _dispatch_tool:
   TOOL_HANDLERS["sonarr_search_series"] = ("sonarr", "search_series")
   → service_name = "sonarr"
   → method_name = "search_series"

3. Factory: _make_sonarr_tools(clients["sonarr"])
   → SonarrTools(BaseARRClient("http://sonarr:8989", "abc123"))

4. Method call: tools_instance.search_series(title="Breaking Bad")

5. HTTP call: self.client.get("/series/lookup", {"term": "Breaking Bad"})
   → GET http://sonarr:8989/api/v3/series/lookup?term=Breaking%20Bad

6. Response: [{tvdbId: 81189, title: "Breaking Bad", year: 2008, ...}]

7. Serialization: json.dumps(result) → "[{\"tvdbId\": 81189, ...}]"

8. Return to LLM: [TextContent(type="text", text="[...]")]
```

---

## Adding a New Tool

### For an existing service

1. Add `Tool(...)` to the service's tool list in `server.py` (e.g., `SONARR_TOOLS`)
2. Add the method to the tools class (e.g., `SonarrTools`)
3. Done — `_register_handlers()` auto-maps the new tool name

### For a new service

Follow the full pattern (see `Architecture Rules` in AGENTS.md):

```
1. src/config.py         — Add <Service>Config dataclass + load_config() entry
2. src/client.py          — Add client class (if API differs from BaseARRClient)
3. src/tools/<svc>_tools.py — Create <Service>Tools class with methods
4. src/server.py          — Add TOOL definitions, factory, SERVICE_MAP entry
5. src/server.py          — Add client instantiation in run_server()
```

---

## Error Handling

All errors are caught and returned as text to the LLM:

```python
async def _dispatch_tool(name, args, clients):
    try:
        # ... dispatch logic ...
    except Exception as e:
        logger.error(f"Error handling tool '{name}': {e}", exc_info=True)
        return [TextContent(type="text", text=f"Error: {str(e)}")]
```

The LLM receives a human-readable error message and can retry or inform the user.

---

## Client Types

| Client | Auth | API Prefix | Use Case |
|--------|------|------------|----------|
| `BaseARRClient` | `X-Api-Key` header | `/api/v3` | Sonarr, Radarr |
| `BaseARRClient` (overridden) | `X-Api-Key` header | `/api/v1` | Lidarr, Readarr, Prowlarr |
| `SeerrClient` | `X-Api-Key` header | `/api/v1` | Seerr (manual URL encoding) |
| `TautulliClient` | `apikey` query param | `/api/v2` | Tautulli (cmd-based) |
| `PlexClient` | `X-Plex-Token` header | (none) | Plex |

### URL Construction

```
BaseARRClient.get("/series/lookup", {"term": "X"})
→ URL: /api/v3/series/lookup?term=X
→ Full: http://sonarr:8989/api/v3/series/lookup?term=X

SeerrClient.get("/search", {"query": "X"})
→ URL: /api/v1/search?query=X  (manually encoded: %20 not +)
→ Full: http://seerr:5055/api/v1/search?query=X

TautulliClient.get("get_activity", {"count": 10})
→ URL: /api/v2?cmd=get_activity&apikey=KEY&count=10
→ Full: http://tautulli:8181/api/v2?cmd=get_activity&apikey=KEY&count=10

PlexClient.get("/search", {"query": "X"})
→ URL: /search?query=X
→ Full: http://plex:32400/search?query=X
```

---

## Transport Layer

### stdio (default)

```
LLM Client ──stdin──> MCP Server ──stdout──> LLM Client
```

- Uses `mcp.server.stdio.stdio_server()`
- Requires `stdin_open: true` and `tty: true` in Docker
- Standard for local MCP client integration

### HTTP

```
LLM Client ──HTTP POST──> Starlette ──> StreamableHTTPSessionManager ──> MCP Server
```

- Uses `StreamableHTTPSessionManager` + uvicorn
- API key auth via `ApiKeyMiddleware`
- CORS support via Starlette middleware
- Health check at `GET /health`
- Requires `MCP_TRANSPORT=http` env var
