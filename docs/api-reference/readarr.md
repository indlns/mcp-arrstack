# Readarr API v1 Reference

**Base URL:** `http://<host>:8787/api/v1`
**Auth:** `X-Api-Key` header
**Docs:** https://wiki.servarr.com/readarr/api

**⚠️ Important:** Readarr uses `/api/v1`, NOT `/api/v3`.

---

## Endpoints Used by MCP ARR Stack

### Authors

#### `GET /api/v1/author` — List all authors

Returns all authors in Readarr.

**Response:** `200 OK` — JSON array of author objects.

```json
[
  {
    "id": 1,
    "title": "William Gibson",
    "foreignAuthorId": "287915",
    "path": "/data/books/William Gibson",
    "qualityProfileId": 1,
    "monitored": true,
    "statistics": { ... }
  }
]
```

---

#### `GET /api/v1/author/lookup?term=X` — Search for authors

Searches external metadata providers for new authors to add.

**Query params:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `term` | string | **Yes** | Search query (author name) |

**Response:** `200 OK` — JSON array of author objects.

**⚠️ Common mistake:** `/search/author` does NOT exist. Use `/author/lookup`.

**Alternative:** `GET /api/v1/book/lookup?term=X` for book-specific search (supports `isbn:`, `asin:`, `goodreads:` prefixes).

---

#### `GET /api/v1/author/{id}` — Get author by ID

---

#### `POST /api/v1/author` — Add a new author

**Request body:**
```json
{
  "foreignAuthorId": "287915",
  "title": "William Gibson",
  "rootFolderPath": "/data/books",
  "qualityProfileId": 1,
  "monitored": true
}
```

**Required fields:** `foreignAuthorId`, `title`, `rootFolderPath`, `qualityProfileId`

**`foreignAuthorId`**: External metadata provider ID (e.g., Goodreads author ID). This is a **string**, not an integer.

---

#### `DELETE /api/v1/author/{id}` — Delete an author

**Query params:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `deleteFiles` | boolean | `false` | Also delete files from disk |
| `addImportListExclusion` | boolean | `false` | Add to import list exclusion |

---

### Commands (Task Queue)

#### `POST /api/v1/command` — Queue a command

**Available command names:**
| Name | Params | Description |
|------|--------|-------------|
| `AuthorSearch` | `authorId` | Search for missing books by author |
| `BookSearch` | `bookIds[]` | Search for specific books |
| `MissingBookSearch` | (none) | Search all missing books |
| `RefreshAuthor` | `authorId` | Refresh author metadata |

---

## MCP Tools Mapping

| MCP Tool | API Endpoint | Notes |
|----------|-------------|-------|
| `readarr_search_author` | `GET /author/lookup?term=X` | Metadata provider search |
| `readarr_get_author` | `GET /author` or `GET /author/{id}` | |
| `readarr_add_author` | `POST /author` | Uses `foreignAuthorId` (string) |
| `readarr_delete_author` | `DELETE /author/{id}` | |

---

## Known Gotchas

1. **API prefix is `/api/v1`**: NOT `/api/v3`.
2. **`/author/lookup` not `/search/author`**: The search endpoint is `/author/lookup`.
3. **`foreignAuthorId` is a string**: Uses Goodreads/Metadata IDs, NOT TMDb. Type must be `str`, not `int`.
4. **Shared client mutation**: `ReadarrTools` sets `client.API_PREFIX = "/api/v1"` which mutates the shared client object.
5. **Readarr is beta**: API may have inconsistencies with other *arr services.
