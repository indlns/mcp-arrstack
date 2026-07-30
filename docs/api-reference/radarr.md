# Radarr API v3 Reference

**Base URL:** `http://<host>:7878/api/v3`
**Auth:** `X-Api-Key` header
**Docs:** https://radarr.video/docs/api/

---

## Endpoints Used by MCP ARR Stack

### Movies

#### `GET /api/v3/movie` — List all movies in library

Returns all movies currently in Radarr.

**Query params:** None (returns all).

**Response:** `200 OK` — JSON array of movie objects.

```json
[
  {
    "id": 1,
    "title": "The Matrix",
    "year": 1999,
    "tmdbId": 603,
    "imdbId": "tt0133093",
    "status": "released",
    "path": "/data/movies/The Matrix",
    "qualityProfileId": 1,
    "monitored": true,
    "sizeOnDisk": 2147483648
  }
]
```

**⚠️ Common mistake:** `?term=X` on this endpoint is NOT a valid search param. Use `/movie/lookup` for TMDB search.

---

#### `GET /api/v3/movie/lookup?term=X` — Search TMDB for movies

Searches external databases (TMDB/IMDb) for new movies to add.

**Query params:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `term` | string | **Yes** | Search query (title or IMDb ID) |

**Alternative endpoints:**
- `GET /api/v3/movie/lookup/tmdb?tmdbId={id}` — lookup by TMDb ID
- `GET /api/v3/movie/lookup/imdb?imdbId={id}` — lookup by IMDb ID

**Response:** `200 OK` — JSON array of movie objects from TMDB.

```json
[
  {
    "title": "The Matrix",
    "year": 1999,
    "tmdbId": 603,
    "imdbId": "tt0133093",
    "status": "released",
    "overview": "Set in the 22nd century...",
    "images": [...]
  }
]
```

**Note:** Results are NOT yet in Radarr — they are lookup results for adding.

---

#### `GET /api/v3/movie/{id}` — Get movie by ID

**Response:** Single movie object with full details.

---

#### `POST /api/v3/movie` — Add a new movie

**Request body:**
```json
{
  "tmdbId": 603,
  "title": "The Matrix",
  "rootFolderPath": "/data/movies",
  "qualityProfileId": 1,
  "monitored": true,
  "minimumAvailability": "released"
}
```

**Required fields:** `tmdbId`, `title`, `rootFolderPath`, `qualityProfileId`

**`minimumAvailability` values:** `announced`, `cinemas`, `released`, `preDB`

**Response:** `200 OK` — Created movie object.

---

#### `DELETE /api/v3/movie/{id}` — Delete a movie

**Query params:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `deleteFiles` | boolean | `false` | Also delete files from disk |
| `addImportListExclusion` | boolean | `false` | Add to import list exclusion |

**Response:** `200 OK` (empty body on success).

---

### Quality Profiles

#### `GET /api/v3/qualityprofile` — List all quality profiles

#### `GET /api/v3/qualityprofile/{id}` — Get specific profile

---

### Root Folders

#### `GET /api/v3/rootfolder` — List available root folders

---

### Commands (Task Queue)

#### `POST /api/v3/command` — Queue a command

**Request body:**
```json
{
  "name": "MoviesSearch",
  "movieIds": [1, 2, 3]
}
```

**Available command names:**
| Name | Params | Description |
|------|--------|-------------|
| `MoviesSearch` | `movieIds[]` (array) | Search for all missing movies |
| `RefreshMovie` | `movieIds[]` | Refresh movie metadata |
| `RescanMovie` | `movieIds[]` | Rescan movie files |

**⚠️ Common mistakes:**
- Command name is `MoviesSearch` (plural), NOT `SearchMovie`
- Parameter is `movieIds` (plural, array), NOT `movieId` (singular, scalar)

---

## MCP Tools Mapping

| MCP Tool | API Endpoint | Notes |
|----------|-------------|-------|
| `radarr_search_movie` | `GET /movie/lookup?term=X` | External TMDB search |
| `radarr_get_movies` | `GET /movie` or `GET /movie/{id}` | Local library |
| `radarr_add_movie` | `POST /movie` | |
| `radarr_delete_movie` | `DELETE /movie/{id}` | |
| `radarr_get_quality_profile` | `GET /qualityprofile` | |
| `radarr_get_root_folder` | `GET /rootfolder` | |
| `radarr_get_movie_status` | `GET /movie/{id}` | Composite |

---

## Known Gotchas

1. **`/movie` vs `/movie/lookup`**: `/movie` lists your library; `/movie/lookup` searches TMDB.
2. **`MoviesSearch` not `SearchMovie`**: Command name is plural.
3. **`movieIds` not `movieId`**: Parameter is an array, not a scalar.
4. **`minimumAvailability`**: Controls when movie becomes available (announced/cinemas/released/preDB).
5. **`deleteFiles`**: Must be passed as query param on DELETE, not in body.
