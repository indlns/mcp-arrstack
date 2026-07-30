# Seerr (Jellyseerr) API v1 Reference

**Base URL:** `http://<host>:5055/api/v1`
**Auth:** `X-Api-Key` header
**Docs:** https://docs.seerr.dev/

**⚠️ Important:** Seerr rejects `+` in query params — use `%20` for spaces (percent-encoding).

---

## Endpoints Used by MCP ARR Stack

### Search

#### `GET /api/v1/search?query=X` — Search for media

Searches TMDB/TVDB for movies and TV shows.

**Query params:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | **Yes** | Search query |
| `page` | integer | No | Page number (default: 1) |
| `language` | string | No | Language code (e.g., `en`) |

**Response:** `200 OK` — Object with `results` array.

```json
{
  "page": 1,
  "totalResults": 10,
  "results": [
    {
      "id": 456,
      "mediaType": "movie",
      "title": "The Matrix",
      "releaseDate": "1999-03-31",
      "mediaInfo": {
        "tmdbId": 603,
        "status": 4
      }
    }
  ]
}
```

**Key fields in results:**
- `id`: Seerr internal media ID (used for requests)
- `mediaType`: `"movie"` or `"tv"`
- `mediaInfo.tmdbId`: TMDb ID for matching

---

### Requests

#### `GET /api/v1/request` — List requests

**Query params:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `take` | integer | 20 | Number of results |
| `skip` | integer | 0 | Offset for pagination |
| `filter` | string | — | `all`, `approved`, `available`, `pending`, `processing`, `unavailable`, `failed`, `deleted`, `completed` |
| `sort` | string | `added` | `added` or `modified` |
| `sortDirection` | string | `desc` | `asc` or `desc` |
| `requestedBy` | integer | — | Filter by user ID |
| `mediaType` | string | — | `movie`, `tv`, or `all` |

**Response:** `200 OK` — Object with `pageInfo` and `results`.

```json
{
  "pageInfo": {
    "page": 1,
    "pages": 5,
    "results": 100
  },
  "results": [
    {
      "id": 1,
      "status": 2,
      "media": { ... },
      "createdAt": "2024-01-15T12:00:00Z"
    }
  ]
}
```

**Status codes:** 1=pending, 2=approved, 3=available, 4=failed, 5=processing

---

#### `GET /api/v1/request/{id}` — Get request details

---

#### `POST /api/v1/request` — Create a request

**Request body (movie):**
```json
{
  "mediaType": "movie",
  "mediaId": 456,
  "profileId": 1,
  "rootFolder": "/data/movies",
  "ignoreQuota": false
}
```

**Request body (TV):**
```json
{
  "mediaType": "tv",
  "mediaId": 789,
  "profileId": 1,
  "rootFolder": "/data/tv",
  "ignoreQuota": false,
  "seasons": [1, 2, 3]
}
```

**`seasons` values:** Array of season numbers, or `"all"` string.

**Key fields:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `mediaType` | string | **Yes** | `"movie"` or `"tv"` |
| `mediaId` | integer | **Yes** | Seerr internal media ID (from search) |
| `profileId` | integer | No | Quality profile ID |
| `rootFolder` | string | No | Root folder path |
| `ignoreQuota` | boolean | No | Ignore quota limits |
| `seasons` | array/string | No | Season numbers or `"all"` for TV |

**⚠️ Important:** `mediaId` is Seerr's internal DB ID, NOT `tmdbId`. Get it from search results (`results[].id`).

---

#### `POST /api/v1/request/{id}/approve` — Approve a request

No request body required.

**Response:** Updated request object.

---

#### `POST /api/v1/request/{id}/decline` — Decline a request

No request body required.

**Response:** Updated request object.

**⚠️ Common mistakes:**
- Use POST, NOT PUT
- Endpoint is `/decline`, NOT `/reject`
- No request body needed (pass `None`, not `{}`)

---

## MCP Tools Mapping

| MCP Tool | API Endpoint | Notes |
|----------|-------------|-------|
| `seerr_search` | `GET /search?query=X` | |
| `seerr_get_requests` | `GET /request` | Uses `take`/`skip` |
| `seerr_request_media` | `POST /request` | Requires `mediaId` from search |
| `seerr_approve` | `POST /request/{id}/approve` | No body |
| `seerr_reject` | `POST /request/{id}/decline` | `/decline` not `/reject` |
| `seerr_get_request` | `GET /request/{id}` | |

---

## URL Encoding

Seerr rejects `+` in query parameters. All values must use `%20` for spaces.

The `SeerrClient` handles this manually:
```python
# Manual encoding — don't use httpx's default params=
encoded_val = quote(str(v), safe="")  # "hello world" → "hello%20world"
```

Numeric values are NOT encoded (passed as-is).

---

## Known Gotchas

1. **`mediaId` not `tmdbId`**: POST /request requires Seerr's internal ID, not TMDb ID.
2. **`/decline` not `/reject`**: The decline endpoint is `/decline`.
3. **POST not PUT**: Approve/decline use POST.
4. **No body for approve/decline**: Pass `None`, not `{}`.
5. **`take`/`skip` not `page`/`count`**: Pagination uses offset-based params.
6. **Percent-encoding**: Spaces must be `%20`, not `+`.
7. **`seasons`**: Can be array `[1,2,3]` or string `"all"`.
