# API Reference — ARR Stack Services

This directory contains the **canonical API documentation** for all services used by MCP ARR Stack. Every API call in the codebase **must** conform to the endpoints and parameters documented here.

---

## Services Overview

| Service | API Version | Base URL | Auth Method | Docs |
|---------|------------|----------|-------------|------|
| [Sonarr](./sonarr.md) | v3 | `/api/v3` | `X-Api-Key` header | https://sonarr.tv/docs/api/ |
| [Radarr](./radarr.md) | v3 | `/api/v3` | `X-Api-Key` header | https://radarr.video/docs/api/ |
| [Lidarr](./lidarr.md) | **v1** | `/api/v1` | `X-Api-Key` header | https://wiki.servarr.com/lidarr/api |
| [Prowlarr](./prowlarr.md) | **v1** | `/api/v1` | `X-Api-Key` header | https://wiki.servarr.com/prowlarr/api |
| [Readarr](./readarr.md) | **v1** | `/api/v1` | `X-Api-Key` header | https://wiki.servarr.com/readarr/api |
| [Seerr](./seerr.md) | v1 | `/api/v1` | `X-Api-Key` header | https://docs.seerr.dev/ |
| [Tautulli](./tautulli.md) | v2 | `/api/v2` | `apikey` query param | https://github.com/Tautulli/Tautulli/wiki/API |
| [Plex](./plex.md) | — | `/` (root) | `X-Plex-Token` header | https://developer.plex.tv/pms/ |

---

## Client Layer Mapping

| Client Class | Services | API Prefix |
|-------------|----------|------------|
| `BaseARRClient` | Sonarr, Radarr | `/api/v3` |
| `BaseARRClient` (overridden) | Lidarr, Readarr | `/api/v1` |
| `BaseARRClient` | Prowlarr | `/api/v1` |
| `SeerrClient` | Seerr | `/api/v1` |
| `TautulliClient` | Tautulli | `/api/v2` (cmd-based) |
| `PlexClient` | Plex | (no prefix) |

---

## Critical Endpoints Quick Reference

### External Search (for adding new content)

| Service | Correct Endpoint | Wrong (common mistake) |
|---------|-----------------|----------------------|
| Sonarr | `GET /series/lookup?term=X` | `GET /series?term=X` |
| Radarr | `GET /movie/lookup?term=X` | `GET /movie?term=X` |
| Lidarr | `GET /artist/lookup?term=X` | `GET /search/artist?term=X` |
| Readarr | `GET /author/lookup?term=X` | `GET /search/author?term=X` |
| Prowlarr | `GET /search?query=X` | `GET /search?term=X` |

### Task Queue Commands

| Service | Correct Command | Wrong (common mistake) |
|---------|----------------|----------------------|
| Radarr | `MoviesSearch` + `movieIds[]` | `SearchMovie` + `movieId` |
| Lidarr | `ArtistSearch` + `artistId` | `SearchMissing` |
| Sonarr | `SeriesSearch` + `seriesId` | `SearchSeries` |

### System Endpoints

| Service | Correct Endpoint | Wrong (common mistake) |
|---------|-----------------|----------------------|
| Prowlarr status | `GET /system/status` | `GET /status` |
| Prowlarr test | `POST /indexer/test` (full body) | `POST /indexer/{id}/test` |

---

## Rules for Adding New API Calls

1. **Always check this documentation first** before writing any API call.
2. **Never guess endpoints** — if it's not documented here, verify against official docs.
3. **Test endpoint names carefully** — many *arr services have similar but different conventions.
4. **Respect API versioning** — Lidarr/Readarr/Prowlarr use v1, Sonarr/Radarr use v3.
5. **Pass parameters correctly** — check param names, types, and whether they go in query/body.
6. **Handle response format** — Tautulli wraps in `response.data`, Plex wraps in `MediaContainer`.

---

*Last verified: 2026-07-13*
