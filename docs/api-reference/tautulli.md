# Tautulli API v2 Reference

**Base URL:** `http://<host>:8181/api/v2`
**Auth:** `apikey` query parameter
**Docs:** https://github.com/Tautulli/Tautulli/wiki/Tautulli-API-Reference

**⚠️ Important:** Tautulli uses a different auth pattern — API key is passed as a query parameter, NOT a header.

---

## Authentication

All requests include `apikey` as a query parameter:
```
GET /api/v2?cmd=get_activity&apikey=YOUR_API_KEY
```

---

## Response Format

All Tautulli responses are wrapped in:
```json
{
  "response": {
    "result": "success",
    "data": { ... }
  }
}
```

The `TautulliClient` automatically unwraps `response.data`.

---

## Endpoints Used by MCP ARR Stack

### Activity

#### `GET /api/v2?cmd=get_activity` — Get current activity

Returns currently active streams on the PMS.

**Optional params:**
| Param | Type | Description |
|-------|------|-------------|
| `session_key` | int | Session key for the session info to return |
| `session_id` | str | Session ID for the session info to return |

**Response data:**
```json
{
  "stream_count": "1",
  "stream_count_direct_play": 1,
  "stream_count_direct_stream": 0,
  "stream_count_transcode": 0,
  "total_bandwidth": 25318,
  "lan_bandwidth": 25318,
  "wan_bandwidth": 0,
  "sessions": [
    {
      "session_id": "helf15l3rxgw01xxe0jf3l3d",
      "session_key": "27",
      "user": "LordCommanderSnow",
      "user_id": 133788,
      "friendly_name": "Jon Snow",
      "full_title": "Game of Thrones - The Red Woman",
      "media_type": "episode",
      "progress_percent": "0",
      "state": "playing",
      "ip_address": "10.10.10.1",
      "platform": "Plex Media Player",
      "player": "Castle-PC",
      "quality_profile": "Original",
      "video_resolution": "1080",
      "video_codec": "h264",
      "audio_codec": "ac3",
      "container": "mkv",
      "bandwidth": "25318",
      "location": "lan"
    }
  ]
}
```

---

### Library

#### `GET /api/v2?cmd=get_libraries` — Get library list

Returns a list of all libraries on the server with counts.

**Response data:**
```json
[
  {
    "section_id": "1",
    "section_name": "Movies",
    "section_type": "movie",
    "count": "887",
    "parent_count": null,
    "child_count": null,
    "is_active": 1,
    "art": "/:/resources/movie-fanart.jpg",
    "thumb": "/:/resources/movie.png"
  },
  {
    "section_id": "2",
    "section_name": "TV Shows",
    "section_type": "show",
    "count": "62",
    "parent_count": "240",
    "child_count": "3745",
    "is_active": 1,
    "art": "/:/resources/show-fanart.jpg",
    "thumb": "/:/resources/show.png"
  }
]
```

---

### History

#### `GET /api/v2?cmd=get_history` — Get watch history

Returns Tautulli watch history in DataTables format.

**Optional params:**
| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `grouping` | int | `0` | `0` or `1` — group multi-episode watches |
| `include_activity` | int | `0` | `0` or `1` — include activity data |
| `user` | str | — | Filter by username, e.g. `"Jon Snow"` |
| `user_id` | int | — | Filter by user ID |
| `rating_key` | int | — | Filter by rating key |
| `parent_rating_key` | int | — | Filter by parent rating key |
| `grandparent_rating_key` | int | — | Filter by grandparent rating key |
| `start_date` | str | — | History for exact date, `"YYYY-MM-DD"` |
| `before` | str | — | History before and including date, `"YYYY-MM-DD"` |
| `after` | str | — | History after and including date, `"YYYY-MM-DD"` |
| `section_id` | int | — | Filter by library section ID |
| `media_type` | str | — | `"movie"`, `"episode"`, `"track"`, `"live"`, `"collection"`, `"playlist"` |
| `transcode_decision` | str | — | `"direct play"`, `"copy"`, `"transcode"` |
| `guid` | str | — | Plex guid, e.g. `"com.plexapp.agents.thetvdb://121361/6/1"` |
| `order_column` | str | `"date"` | `"date"`, `"friendly_name"`, `"ip_address"`, `"platform"`, `"player"`, `"full_title"`, `"started"`, `"paused_counter"`, `"stopped"`, `"duration"` |
| `order_dir` | str | `"desc"` | `"asc"` or `"desc"` |
| `start` | int | `0` | Row to start from |
| `length` | int | `25` | Number of items to return |
| `search` | str | — | Search string |

**Response data:**
```json
{
  "draw": 1,
  "recordsTotal": 1000,
  "recordsFiltered": 250,
  "total_duration": "42 days 5 hrs 18 mins",
  "filter_duration": "10 hrs 12 mins",
  "data": [
    {
      "row_id": 1124,
      "date": 1462687607,
      "friendly_name": "Mother of Dragons",
      "user": "DanyKhaleesi69",
      "user_id": 8008135,
      "full_title": "Game of Thrones - The Red Woman",
      "media_type": "episode",
      "rating_key": 4348,
      "started": 1462688107,
      "stopped": 1462688370,
      "duration": 263,
      "percent_complete": 84,
      "ip_address": "xxx.xxx.xxx.xxx",
      "platform": "Windows",
      "player": "Castle-PC",
      "transcode_decision": "transcode"
    }
  ]
}
```

**Note:** The response has nested `data.data` — `TautulliClient` unwraps one level, but `get_history` may need to extract `data.get("data", [])`.

---

### User Watch Time Stats

#### `GET /api/v2?cmd=get_user_watch_time_stats` — Get user watch time statistics

Returns watch time stats for a specific user over different time periods.

**Required params:**
| Param | Type | Description |
|-------|------|-------------|
| `user_id` | str | The id of the Plex user |

**Optional params:**
| Param | Type | Description |
|-------|------|-------------|
| `grouping` | int | `0` or `1` |
| `query_days` | str | Comma separated days, e.g. `"1,7,30,0"` |

**Response data:**
```json
[
  {"query_days": 1, "total_plays": 0, "total_time": 0},
  {"query_days": 7, "total_plays": 3, "total_time": 15694},
  {"query_days": 30, "total_plays": 35, "total_time": 63054},
  {"query_days": 0, "total_plays": 508, "total_time": 1183080}
]
```

---

### Library User Stats

#### `GET /api/v2?cmd=get_library_user_stats` — Get library user statistics

Returns per-user statistics for a specific library section.

**Required params:**
| Param | Type | Description |
|-------|------|-------------|
| `section_id` | str | The id of the Plex library section |

**Optional params:**
| Param | Type | Description |
|-------|------|-------------|
| `grouping` | int | `0` or `1` |

**Response data:**
```json
[
  {
    "friendly_name": "Jon Snow",
    "user_id": 133788,
    "user_thumb": "https://plex.tv/users/k10w42309cynaopq/avatar",
    "username": "LordCommanderSnow",
    "total_plays": 170,
    "total_time": 349618
  }
]
```

---

### Recently Added

#### `GET /api/v2?cmd=get_recently_added` — Get recently added content

Returns items recently added to Plex.

**Required params:**
| Param | Type | Description |
|-------|------|-------------|
| `count` | str | Number of items to return |

**Optional params:**
| Param | Type | Description |
|-------|------|-------------|
| `start` | str | The item number to start at |
| `media_type` | str | `"movie"`, `"show"`, or `"artist"` |
| `section_id` | str | The id of the Plex library section |

**Response data:**
```json
{
  "recently_added": [
    {
      "rating_key": 153037,
      "title": "The Red Woman",
      "full_title": "Game of Thrones - The Red Woman",
      "media_type": "episode",
      "added_at": "1461572396",
      "grandparent_title": "Game of Thrones",
      "year": "2016"
    }
  ]
}
```

---

## MCP Tools Mapping

| MCP Tool | Tautulli Command | Notes |
|----------|-----------------|-------|
| `tautulli_get_activity` | `get_activity` | |
| `tautulli_get_library_stats` | `get_libraries` | Returns list with counts per section |
| `tautulli_get_history` | `get_history` | Unwraps `data.data` |
| `tautulli_get_user_stats` | `get_user_watch_time_stats` | Per-user watch time over periods |
| `tautulli_get_recently_added` | `get_recently_added` | Unwraps `recently_added` |

---

## Known Gotchas

1. **Auth via query param**: `apikey` goes in URL, NOT in header.
2. **Wrapped response**: All data is inside `{"response": {"data": ...}}`.
3. **Double nesting**: Some endpoints return `{"response": {"data": {"data": [...]}}}` — need to extract `data.data`.
4. **`recently_added` key**: Recently added items are under `recently_added`, not `data`.
5. **`grouping` not `group_by`**: History uses `grouping` (0/1), not `group_by`.
6. **`length` not `limit`**: History pagination uses `length`, not `limit`.
7. **`order_column` not `order_by`**: History sorting uses `order_column`, not `order_by`.
8. **`recently_added` requires `count`**: The `count` param is required (not optional).
9. **No `get_user_stats` endpoint**: Use `get_user_watch_time_stats` or `get_library_user_stats` instead.
10. **No `get_library_overview` endpoint**: Use `get_libraries` for library list with counts.
