# Plex Media Server API Reference

**Base URL:** `http://<host>:32400`
**Auth:** `X-Plex-Token` header (or `?X-Plex-Token=` query param)
**Docs:** https://developer.plex.tv/pms/

**⚠️ Important:** Plex API has NO `/api/` prefix — endpoints start at root.

---

## Authentication

Token is passed via header:
```
GET /library/sections
X-Plex-Token: YOUR_PLEX_TOKEN
```

Or as query parameter (less preferred):
```
GET /library/sections?X-Plex-Token=YOUR_PLEX_TOKEN
```

---

## Response Format

All Plex responses are wrapped in a `MediaContainer`:
```json
{
  "MediaContainer": {
    "size": 10,
    "totalSize": 500,
    "offset": 0,
    "Metadata": [ ... ]
  }
}
```

---

## Pagination

Plex uses custom headers for pagination:

**Request headers:**
| Header | Description |
|--------|-------------|
| `X-Plex-Container-Start` | Starting offset (0-based) |
| `X-Plex-Container-Size` | Number of items to return |

**Response headers:**
| Header | Description |
|--------|-------------|
| `X-Plex-Container-Start` | Offset of first returned item |
| `X-Plex-Container-Total-Size` | Total number of items in collection |

Alternatively, the `limit` query parameter can be used to limit results without retrieving the total count (more efficient).

---

## Endpoints Used by MCP ARR Stack

### Search

#### `GET /hubs/search/?query=X` — Search across all libraries

**Query params:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | **Yes** | Search query |
| `limit` | integer | No | Max results per hub (default: 3) |
| `sectionId` | integer | No | Restrict search to a specific library section |

**Response:**
```json
{
  "MediaContainer": {
    "size": 5,
    "Hub": [
      {
        "title": "Movies",
        "type": "movie",
        "hubIdentifier": "movie",
        "size": 3,
        "more": 0,
        "Video": [
          {
            "ratingKey": "12345",
            "title": "The Matrix",
            "type": "movie",
            "year": 1999,
            "score": 0.95,
            "Media": [ ... ]
          }
        ]
      }
    ]
  }
}
```

**Note:** Results are grouped into `Hub` elements by type (movie, show, actor, etc.). Each hub contains its matching items.

---

### Library Sections

#### `GET /library/sections` — List all library sections

**Response:**
```json
{
  "MediaContainer": {
    "Directory": [
      {
        "key": "1",
        "title": "Movies",
        "type": "movie",
        "agent": "com.plexapp.agents.imdb",
        "scanner": "Plex Movie Scanner",
        "size": 1500
      },
      {
        "key": "2",
        "title": "TV Shows",
        "type": "show",
        "agent": "com.plexapp.agents.thetvdb",
        "scanner": "Plex TV Series",
        "size": 200
      }
    ]
  }
}
```

**Key fields:**
- `key`: Section ID (used in other endpoints)
- `type`: `"movie"`, `"show"`, `"artist"`, etc.
- `size`: Number of items

---

#### `GET /library/sections/{key}/all` — Get all items in a section

**Query params:**
| Param | Type | Description |
|-------|------|-------------|
| `type` | integer | Content type filter |
| `limit` | integer | Max results |

**⚠️ Important:** The `type` param for filtering is an **integer**, not a string:
| Value | Type |
|-------|------|
| 1 | Movie |
| 2 | Show |
| 3 | Season |
| 4 | Episode |
| 8 | Artist |
| 9 | Album |
| 10 | Track |

**Response:**
```json
{
  "MediaContainer": {
    "size": 50,
    "Metadata": [
      {
        "ratingKey": "12345",
        "title": "The Matrix",
        "type": "movie",
        "year": 1999
      }
    ]
  }
}
```

---

### Recently Added

#### `GET /library/sections/{key}/recentlyAdded` — Get recently added content in a section

**Path params:**
| Param | Type | Description |
|-------|------|-------------|
| `key` | string | Section key (from `/library/sections`) |

**Response:**
```json
{
  "MediaContainer": {
    "size": 10,
    "librarySectionTitle": "Movies",
    "viewGroup": "movie",
    "Metadata": [
      {
        "ratingKey": "12345",
        "title": "New Movie",
        "type": "movie",
        "addedAt": 1705312800
      }
    ]
  }
}
```

**Note:** This endpoint is **per-section** — you must pass the section `key` in the path. For movies use the movies section key, for TV shows use the TV shows section key. Case-sensitive: `recentlyAdded` (capital A), not `recentlyadded`.

---

### Playlists

#### `GET /playlists` — List all playlists

**Response:**
```json
{
  "MediaContainer": {
    "Directory": [
      {
        "ratingKey": "5678",
        "title": "My Playlist",
        "playlistType": "video",
        "smart": false
      }
    ]
  }
}
```

---

### Server Info

#### `GET /` — Get server info

**Response:**
```json
{
  "MediaContainer": {
    "title": "My Plex Server",
    "version": "1.40.0.0000",
    "platform": "Linux",
    "size": 0
  }
}
```

---

## MCP Tools Mapping

| MCP Tool | API Endpoint | Notes |
|----------|-------------|-------|
| `plex_search` | `GET /hubs/search/?query=X` | Results grouped by Hub |
| `plex_library_sections` | `GET /library/sections` | |
| `plex_recently_added` | `GET /library/sections/{key}/recentlyAdded` | Per-section, case-sensitive |
| `plex_playlists` | `GET /playlists` | |
| `plex_library` | `GET /library/sections/{key}/all` | `type` is integer |
| `plex_get_status` | `GET /` | |

---

## Known Gotchas

1. **No `/api/` prefix**: Plex endpoints start at root (`/library/sections`, not `/api/library/sections`).
2. **`MediaContainer` wrapper**: All responses are nested inside `MediaContainer`.
3. **`type` is integer**: For filtering, `type=1` (movie), `type=2` (show), NOT string `"movie"`.
4. **`key` not `id`**: Section identifiers are called `key`, not `id`.
5. **`ratingKey` not `id`**: Media item identifiers are `ratingKey`.
6. **Token in header**: Use `X-Plex-Token` header, not query param (cleaner).
7. **Recently Added is per-section**: Use `/library/sections/{key}/recentlyAdded` with the section key. The `A` in `recentlyAdded` must be uppercase.
8. **`Directory` vs `Metadata`**: Sections use `Directory`, items use `Metadata`.
9. **Search returns Hubs**: `/hubs/search/` groups results by type in `Hub` elements, not flat `Metadata`.
10. **JSON by default**: Set `Accept: application/json` header; Plex defaults to XML.
