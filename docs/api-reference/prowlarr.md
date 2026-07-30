# Prowlarr API v1 Reference

**Base URL:** `http://<host>:9696/api/v1`
**Auth:** `X-Api-Key` header
**Docs:** https://wiki.servarr.com/prowlarr/api

**⚠️ Important:** Prowlarr uses `/api/v1`, NOT `/api/v3`.

---

## Endpoints Used by MCP ARR Stack

### Search

#### `GET /api/v1/search?query=X` — Search across indexers

Searches all configured indexers for content.

**Query params:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | **Yes** | Search query |
| `type` | string | No | Search type: `search`, `tvsearch`, `moviesearch`, `booksearch`, `audiosearch` |
| `limit` | integer | No | Max results (default: varies) |
| `offset` | integer | No | Offset for pagination |

**Response:** `200 OK` — JSON array of search result objects.

```json
[
  {
    "guid": "...",
    "title": "Example.Release.2024.1080p.BluRay",
    "indexer": "1337x",
    "indexerId": 1,
    "size": 5000000000,
    "seeders": 10,
    "peers": 20,
    "downloadUrl": "...",
    "infoUrl": "...",
    "publishDate": "2024-01-15T12:00:00Z"
  }
]
```

**⚠️ Common mistake:** Parameter is `query`, NOT `term`. Prowlarr uses Newznab-compatible API.

---

### Indexers

#### `GET /api/v1/indexer` — List all indexers

**Response:** JSON array of indexer configuration objects.

```json
[
  {
    "id": 1,
    "name": "1337x",
    "enable": true,
    "protocol": "torrent",
    "priority": 1,
    "supportsRss": true,
    "supportsSearch": true
  }
]
```

**Note:** The enabled field is `enable` (not `enabled`).

---

#### `POST /api/v1/indexer/test` — Test an indexer

**Request body:** Full indexer configuration object.

**⚠️ Important:** There is NO per-indexer test endpoint like `/indexer/{id}/test`. Testing requires the full configuration in the body. Consider using `POST /api/v1/indexer/testall` to test all indexers.

---

### System

#### `GET /api/v1/system/status` — Get system status

**Response:** System info object with version, build info, connection status.

**⚠️ Common mistake:** The endpoint is `/system/status`, NOT `/status`.

---

### History

#### `GET /api/v1/history` — Get download history

**Query params:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `limit` | integer | 100 | Max results |

---

## MCP Tools Mapping

| MCP Tool | API Endpoint | Notes |
|----------|-------------|-------|
| `prowlarr_search` | `GET /search?query=X` | `query` not `term` |
| `prowlarr_get_indexers` | `GET /indexer` | `enable` field for status |
| `prowlarr_test_indexer` | N/A | No simple per-indexer test endpoint |
| `prowlarr_get_status` | `GET /system/status` | `/system/status` not `/status` |

---

## Known Gotchas

1. **API prefix is `/api/v1`**: NOT `/api/v3`.
2. **`query` not `term`**: Search parameter is `query`.
3. **`/system/status` not `/status`**: System endpoint includes `/system/` prefix.
4. **No per-indexer test by ID**: `POST /indexer/test` requires full config body.
5. **`enable` not `enabled`**: The field name in indexer objects is `enable`.
6. **Newznab-compatible**: Search follows Newznab API conventions.
