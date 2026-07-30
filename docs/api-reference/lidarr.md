# Lidarr API v1 Reference

**Base URL:** `http://<host>:8686/api/v1`
**Auth:** `X-Api-Key` header
**Docs:** https://wiki.servarr.com/lidarr/api

**⚠️ Important:** Lidarr uses `/api/v1`, NOT `/api/v3`.

---

## Endpoints Used by MCP ARR Stack

### Artists

#### `GET /api/v1/artist` — List all artists

Returns all artists in Lidarr.

**Response:** `200 OK` — JSON array of artist objects.

```json
[
  {
    "id": 1,
    "artistName": "Pink Floyd",
    "title": "Pink Floyd",
    "musicBrainzArtistId": "83ad989a-7bde-4d26-a8f0-571f297965dd",
    "path": "/data/music/Pink Floyd",
    "qualityProfileId": 1,
    "monitored": true,
    "statistics": { ... }
  }
]
```

---

#### `GET /api/v1/artist/lookup?term=X` — Search MusicBrainz for artists

Searches MusicBrainz for new artists to add.

**Query params:**
| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `term` | string | **Yes** | Search query (artist name) |

**Response:** `200 OK` — JSON array of artist objects from MusicBrainz.

**⚠️ Common mistake:** `/search/artist` does NOT exist. Use `/artist/lookup`.

---

#### `GET /api/v1/artist/{id}` — Get artist by ID

---

#### `POST /api/v1/artist` — Add a new artist

**Request body:**
```json
{
  "musicBrainzArtistId": "83ad989a-7bde-4d26-a8f0-571f297965dd",
  "title": "Pink Floyd",
  "rootFolderPath": "/data/music",
  "qualityProfileId": 1,
  "monitored": true
}
```

**Required fields:** `musicBrainzArtistId`, `title`, `rootFolderPath`, `qualityProfileId`

---

#### `DELETE /api/v1/artist/{id}` — Delete an artist

**Query params:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `deleteFiles` | boolean | `false` | Also delete files from disk |
| `addImportListExclusion` | boolean | `false` | Add to import list exclusion |

---

### Commands (Task Queue)

#### `POST /api/v1/command` — Queue a command

**Request body:**
```json
{
  "name": "ArtistSearch",
  "artistId": 1
}
```

**Available command names:**
| Name | Params | Description |
|------|--------|-------------|
| `ArtistSearch` | `artistId` | Search for missing albums by artist |
| `AlbumSearch` | `albumIds[]` | Search for specific albums |
| `MissingAlbumSearch` | (none) | Search all missing albums across all artists |
| `RefreshArtist` | `artistId` | Refresh artist metadata |

**⚠️ Common mistake:** `SearchMissing` does NOT exist. Use `ArtistSearch` for per-artist or `MissingAlbumSearch` globally.

---

## MCP Tools Mapping

| MCP Tool | API Endpoint | Notes |
|----------|-------------|-------|
| `lidarr_search_artist` | `GET /artist/lookup?term=X` | MusicBrainz search |
| `lidarr_get_artist` | `GET /artist` or `GET /artist/{id}` | |
| `lidarr_add_artist` | `POST /artist` | |
| `lidarr_delete_artist` | `DELETE /artist/{id}` | |

---

## Known Gotchas

1. **API prefix is `/api/v1`**: NOT `/api/v3` like Sonarr/Radarr.
2. **`/artist/lookup` not `/search/artist`**: The search endpoint is `/artist/lookup`.
3. **`musicBrainzArtistId`**: Uses MusicBrainz IDs, not TMDb/TVDB.
4. **`ArtistSearch` not `SearchMissing`**: Command names differ from other *arr services.
5. **Shared client mutation**: `LidarrTools` sets `client.API_PREFIX = "/api/v1"` which mutates the shared client object.
