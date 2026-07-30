# Sonarr API v3 Reference

**Base URL:** `http://<host>:8989/api/v3`
**Auth:** `X-Api-Key` header
**Docs:** https://sonarr.tv/docs/api/

---

## Endpoints Used by MCP ARR Stack

### Series

#### `GET /api/v3/series` — List all series in library

Returns all series currently monitored by Sonarr.

**Query params:** None (returns all).

**Response:** `200 OK` — JSON array of series objects.

```json
[
  {
    "id": 1,
    "title": "Breaking Bad",
    "year": 2008,
    "tvdbId": 81189,
    "status": "continuing",
    "path": "/data/series/Breaking Bad",
    "qualityProfileId": 1,
    "monitored": true,
    "seasonCount": 5,
    "statistics": { ... }
  }
]
```

**⚠️ Common mistake:** Using `?term=X` on this endpoint only filters the local library. For external search, use `/series/lookup`.

---

#### `GET /api/v3/series/lookup?term=X` — Search TVDB for series

Searches external databases (TVDB) for new series to add.

**Query params:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `term` | string | **Yes** | Search query (title) |

**Response:** `200 OK` — JSON array of series objects from TVDB.

```json
[
  {
    "title": "Breaking Bad",
    "year": 2008,
    "tvdbId": 81189,
    "status": "ended",
    "overview": "A high school chemistry teacher...",
    "network": "AMC",
    "images": [...]
  }
]
```

**Note:** Results are NOT yet in Sonarr — they are lookup results for adding.

---

#### `GET /api/v3/series/{id}` — Get series by ID

**Response:** Single series object with full details.

---

#### `POST /api/v3/series` — Add a new series

**Request body:**
```json
{
  "tvdbId": 81189,
  "title": "Breaking Bad",
  "rootFolderPath": "/data/series",
  "qualityProfileId": 1,
  "languageProfileId": 1,
  "monitored": true,
  "seasonFolders": true,
  "seriesType": "standard",
  "addOptions": {
    "searchForMissingEpisodes": false
  }
}
```

**Required fields:** `tvdbId`, `title`, `rootFolderPath`, `qualityProfileId`

**`seriesType` values:** `standard`, `daily`, `anime`

**Response:** `200 OK` — Created series object.

---

#### `DELETE /api/v3/series/{id}` — Delete a series

**Query params:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `deleteFiles` | boolean | `false` | Also delete files from disk |
| `addImportListExclusion` | boolean | `false` | Add to import list exclusion |

**Response:** `200 OK` (empty body on success).

---

### Episodes

#### `GET /api/v3/episode` — Get episodes

**Query params:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `seriesId` | integer | **Yes** | Series ID |
| `seasonNumber` | integer | No | Filter by season |
| `episodeIds` | string | No | Comma-separated episode IDs |
| `includeSeries` | boolean | No | Include series info |
| `includeEpisodeFile` | boolean | No | Include file info |
| `includeImages` | boolean | No | Include images |

**Response:** `200 OK` — JSON array of episode objects.

```json
[
  {
    "id": 1,
    "seriesId": 1,
    "seasonNumber": 1,
    "episodeNumber": 1,
    "title": "Pilot",
    "airDate": "2008-01-20",
    "hasFile": true,
    "monitored": true,
    "grabbed": false
  }
]
```

**Note:** There is NO `aired` parameter in the Sonarr v3 API. Filter by `hasFile` or `monitored` instead.

---

### Quality Profiles

#### `GET /api/v3/qualityprofile` — List all quality profiles

**Response:** JSON array of quality profile objects.

#### `GET /api/v3/qualityprofile/{id}` — Get specific profile

---

### Root Folders

#### `GET /api/v3/rootfolder` — List available root folders

**Response:** JSON array of root folder objects with `path` and `freeSpace`.

---

### Commands (Task Queue)

#### `POST /api/v3/command` — Queue a command

**Request body:**
```json
{
  "name": "SeriesSearch",
  "seriesId": 1
}
```

**Available command names:**
| Name | Params | Description |
|------|--------|-------------|
| `SeriesSearch` | `seriesId` | Search for all missing episodes in a series |
| `EpisodeSearch` | `episodeIds[]` | Search for specific episodes |
| `RefreshSeries` | `seriesId` | Refresh series metadata |
| `RescanSeries` | `seriesId` | Rescan series files |

---

## MCP Tools Mapping

| MCP Tool | API Endpoint | Notes |
|----------|-------------|-------|
| `sonarr_search_series` | `GET /series/lookup?term=X` | External TVDB search |
| `sonarr_get_series` | `GET /series` or `GET /series/{id}` | Local library |
| `sonarr_get_episodes` | `GET /episode?seriesId=X` | |
| `sonarr_add_series` | `POST /series` | |
| `sonarr_delete_series` | `DELETE /series/{id}` | |
| `sonarr_get_quality_profile` | `GET /qualityprofile` | |
| `sonarr_get_root_folder` | `GET /rootfolder` | |
| `sonarr_get_series_status` | `GET /series/{id}` + `GET /episode` | Composite |

---

## Known Gotchas

1. **`/series` vs `/series/lookup`**: `/series` lists your library; `/series/lookup` searches TVDB.
2. **No `aired` parameter**: Episodes API does not support `aired` filter. Use `hasFile` or client-side filtering.
3. **`SearchMovie` ≠ correct command**: For searching, use `SeriesSearch` (not `SearchSeries`).
4. **`addOptions` is nested**: `searchForMissingEpisodes` goes inside `addOptions`, not at root level.
5. **`languageProfileId`**: Required by some Sonarr versions; default is usually 1.
