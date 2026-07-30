# MCP ARR Stack — Agent Instructions

## Purpose
MCP (Model Context Protocol) server providing LLM tools for ARR Stack media automation services: Sonarr, Radarr, Lidarr, Prowlarr, Readarr, Seerr, Tautulli, Plex.

## Directory Structure
```
src/
  server.py          # Main entry point — tool definitions, dispatch table, MCP server factory
  config.py          # Dataclass configs per service; load_config() reads env vars
  client.py          # Async HTTP clients: BaseARRClient (v3 API), SeerrClient (v1), TautulliClient (/api/v2), PlexClient
  http_server.py     # ASGI app: Starlette + StreamableHTTPSessionManager, API key auth middleware, CORS
  utils.py           # In-memory cache, rate limiter, safe_execute helper
  tools/
    sonarr_tools.py
    radarr_tools.py
    lidarr_tools.py
    prowlarr_tools.py
    readarr_tools.py   # Exists as config but no tool file yet — add src/tools/readarr_tools.py when needed
    seerr_tools.py
    tautulli_tools.py
    plex_tools.py
tests/               # pytest tests (conftest has env-var isolation + mock fixtures)
```

## Build, Test, Lint Commands
> **Важно:** Python не установлен на хост-машине. Все команды должны выполняться внутри Docker-контейнера.

```bash
# Install deps (editable) — inside container
docker compose exec mcp-arr-stack pip install -e ".[dev]"

# Run tests — inside container
docker compose exec mcp-arr-stack pytest tests/ -v
docker compose exec mcp-arr-stack pytest tests/ -v --cov=src --cov-report=term-missing

# Format — inside container
docker compose exec mcp-arr-stack black src/ tests/
docker compose exec mcp-arr-stack ruff check src/ tests/
docker compose exec mcp-arr-stack ruff check src/ tests/ --fix
```

### Быстрый запуск тестов
```bash
# Все тесты
docker compose exec mcp-arr-stack pytest tests/ -v

# Один файл
docker compose exec mcp-arr-stack pytest tests/test_sonarr_tools.py -v

# С покрытием
docker compose exec mcp-arr-stack pytest tests/ -v --cov=src --cov-report=term-missing

# Только упавшие (last failures)
docker compose exec mcp-arr-stack pytest tests/ -v --lf
```

## Git Commit Convention

### Общие правила
- **Не пушить и не коммитить** изменения без явного запроса пользователя.
- Перед каждым коммитом и пушем обязательно проверять все внесённые изменения.
- Используйте [Conventional Commits](https://www.conventionalcommits.org/) формат для сообщений коммитов.

### Форматы сообщений коммитов

#### Исправление багов (bugfix)
При изменениях, связанных с исправлением багов, обязательно укажите номер бага:
```
fix(<service>): BUG-N — краткое содержание исправления
```
Пример:
```
fix(seerr): BUG-34 — корректная кодировка пробелов в query params
```

#### Найденные баги в проекте (bug)
При изменениях, связанных с найденными багами, обязательно укажите номер бага:
```
bug(<service>): BUG-N — краткое содержание бага
```
Пример:
```
bug(seerr): BUG-34 — Tool-определение не содержит параметр `series_type` (`standard`/`daily`/`anime`). LLM не может указать тип сериала.
```

#### Добавление функционала (feature)
При изменениях, связанных с добавлением нового функционала, обязательно укажите номер фичи:
```
feature(<service>): FEATURE-N — краткое содержание добавления
```
Пример:
```
feature(sonarr): FEATURE-55 — добавлен инструмент sonarr_get_queue
```

#### Рефакторинг (refactor)
При изменениях, связанных с рефакторингом кода или структуры проекта:
```
refactor: краткое описание изменений
```
Пример:
```
refactor: вынесение HTTP логики в отдельный модуль client.py
```

#### Удаление файлов (delete)
При удалении файлов или компонентов:
```
delete: краткое описание удаления
```
Пример:
```
delete: удаление устаревшего middleware auth_legacy.py
```

### Правила именования сервисов в префиксах
Используйте короткие имена сервисов: `sonarr`, `radarr`, `lidarr`, `prowlarr`, `readarr`, `seerr`, `tautulli`, `plex`, `server`, `http_server`, `docker`, `utils`.

## Architecture Rules

### Transport Selection
- **stdio** (default): `MCP_TRANSPORT=stdio` — standard MCP client invocation, keeps stdin open.
- **http**: `MCP_TRANSPORT=http` — Streamable HTTP via Starlette/Uvicorn on configured port.
- Also overridable via CLI: `python -m src.server --transport http`.

### Tool Registration Pattern (must be followed when adding new services)
1. Create `src/tools/<service>_tools.py` with a class matching the service name (e.g. `SonarrTools`).
2. Each method maps to an MCP tool named `<service>_<method_name>` (e.g. `sonarr_get_series` → `SonarrTools.get_series`).
3. Define `Tool` objects in `src/server.py` under a module-level constant (e.g. `SONARR_TOOLS = [Tool(...), ...]`).
4. Add a factory `_make_<service>_tools(client)` in `server.py`.
5. Register the service in `SERVICE_MAP` dict in `server.py`.
6. If it's a new ARR service, add a config dataclass to `src/config.py` (follow `SonarrConfig` pattern) and wire it in `load_config()` and `get_enabled_services()`.
7. Create client class in `src/client.py` if the API differs from `BaseARRClient` (different base URL prefix or auth pattern).

### Client Layer
- `BaseARRClient`: uses `/api/v3` prefix, `X-Api-Key` header. Shared by Sonarr, Radarr, Lidarr, Prowlarr, Readarr.
- `SeerrClient`: uses `/api/v1`, manual URL-encoding for query params (Seerr rejects `+` in place of `%20`).
- `TautulliClient`: uses `/api/v2` with `cmd` + `apikey` query params.
- `PlexClient`: uses `X-Plex-Token` header, no API prefix.

### Logging
- Uses Python `logging` module, configured via `setup_logging()` in `server.py`.
- Format: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`.
- Log level controlled by `LOG_LEVEL` env var (default `INFO`).
- Tool errors are caught and returned as JSON error strings to the MCP client — exceptions are also logged with `exc_info=True`.

### MCP Protocol & Tool Dispatch

**Full documentation:** [`docs/mcp-architecture.md`](./docs/mcp-architecture.md)

**Dispatch flow:** LLM → `call_tool(name, args)` → `_dispatch_tool()` → `TOOL_HANDLERS[name]` → `factory(client)` → `method(**args)` → HTTP to service → JSON response → `TextContent`

**Registration chain:**
1. `SONARR_TOOLS = [Tool(name="sonarr_search_series", ...)]` — tool definitions
2. `SERVICE_MAP["sonarr"] = (SONARR_TOOLS, _make_sonarr_tools, "sonarr")` — service binding
3. `_register_handlers()` — builds `TOOL_HANDLERS["sonarr_search_series"] = ("sonarr", "search_series")`
4. `create_mcp_server(clients)` — registers only enabled services with MCP SDK

**Key rule:** Tool name `<service>_<method>` maps to `<ServiceTools>.<method>()`. The `_register_handlers()` function strips the `<service>_` prefix automatically.

### Versioning

- **Canonical source:** `pyproject.toml` (`version = "X.Y.Z"`)
- **Version history:** [`CHANGELOG.md`](./CHANGELOG.md) — каждая выпущенная версия имеет секцию с датой (например `## [0.1.0] — 2026-07-13`)
- **Also update:** `src/client.py:368` — `X-Plex-Version` header (must match)
- **Scheme:** [Semantic Versioning](https://semver.org/spec/v2.0.0.html) — `MAJOR.MINOR.PATCH`

| Component | Increment when... |
|-----------|-------------------|
| **MAJOR** | Breaking changes to MCP tool names, parameters, or response formats that require LLM client reconfiguration |
| **MINOR** | New tools, services, or features are added in a backward-compatible way |
| **PATCH** | Bug fixes, documentation updates, dependency bumps, or internal refactoring |

**Release checklist:**
1. Update `pyproject.toml` and `src/client.py` version
2. Verify `CHANGELOG.md` has a versioned section (not `[Unreleased]`)
3. Run tests: `pytest tests/ -v`
4. Run lint: `ruff check src/ tests/`
5. Commit: `git commit -am "release: vX.Y.Z"`
6. Tag: `git tag -a vX.Y.Z -m "Release vX.Y.Z"`
7. Push: `git push origin main --tags`

## Configuration
- All config is environment-driven. See `.env.example` for all variables.
- Services are **enabled/disabled** based on whether their host + API key env vars are non-empty (see each config dataclass `.enabled` property).
- Only enabled services get clients instantiated and tools registered at startup.

## Bug Tracking & Changelog

### ISSUES - Баги

- **GitLab Integration:** Все зафиксированные и найденные баги должны быть созданы как issues в репозитории GitLab с использованием инструментов MCP.
- Формат заголовка бага: **`BUG-N-<service>`**, где `N` — последовательный номер (начиная с 1), `<service>` — имя сервиса (например `seerr`, `sonarr`, `tautulli`, `server`, `http_server`, `docker`).
- При обнаружении бага:
  1. Создайте соответствующий issue в GitLab с использованием инструментов MCP:
     - Заголовок: `BUG-N-<service>` — краткое описание бага
     - Приоритет: `КРИТИЧЕСКИЙ`, `СРЕДНЕВАЖНЫЙ`, `НИЗКОПРИОРИТЕТНЫЙ`
     - Описание: опишите проблему, укажите файлы и строки с кодом
     - Метки: добавьте соответствующие метки для классификации (например, `bug`, `<service>`, `priority:<уровень>`)
  2. Укажите приоритет: `КРИТИЧЕСКИЙ`, `СРЕДНЕВАЖНЫЙ`, `НИЗКОПРИОРИТЕТНЫЙ`.
  3. После исправления бага:
     - Закоммитьте и запушьте изменения в репозиторий только с явного разрешения пользователя
     - Зафиксируйте коммит к соответствующему issue
     - Закройте соответствующий issue в GitLab через инструменты MCP.
- Нумерация багов — глобальная последовательная, не привязана к сервису. Следующий номер берётся на единицу больше максимального существующего

### CHANGELOG.md — Журнал изменений

- **Файл:** [`CHANGELOG.md`](./CHANGELOG.md) — суммарная история всех изменений проекта.
- Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/) и [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
- **Формат релиза:** каждая версия имеет секцию `## [X.Y.Z] — YYYY-MM-DD` с кратким описанием в курсиве.
- **Разделы внутри релиза:**
  - `### Added` — новый функционал, сгруппированный по сервису (`**Service**: описание`).
  - `### Fixed` — исправления, сгруппированные по сервису (`**Service**: описание`).
  - `### Changed` — изменения существующего поведения.
  - `### Documentation` — изменения в документации.
- **Правила ведения:**
  - Записи краткие, группированные по сервису — без детальных описаний каждого BUG-N.
  - Детали исправлений и добавлений находятся в GitLab Issues и commit-ах.
  - `[Unreleased]` — пустая секция в конце файла для будущих изменений.

### Взаимосвязь документов

| Документ | Содержимое | Связи |
|---|---|---|
| `GitLab Issues` | Трекер багов и задач | Создание/обновление/закрытие через MCP инструменты |
| `CHANGELOG.md` | Суммарная история проекта | Группированные по сервису Added / Fixed / Changed / Documentation |

---

## Docker
```bash
# Build & run (stdio transport, default)
docker compose up -d mcp-arr-stack

# HTTP transport variant
docker compose up -d mcp-arr-stack-http

# View logs
docker compose logs -f mcp-arr-stack
```

## API Reference Documentation

**All API calls in the codebase MUST conform to the canonical documentation in `docs/api-reference/`.**

Before writing or modifying any API call:
1. Read the relevant service doc in `docs/api-reference/<service>.md`.
2. Use the **exact endpoint names** documented there (not guesses).
3. Respect API versioning (v1 for Lidarr/Readarr/Prowlarr, v3 for Sonarr/Radarr).
4. Check the "Critical Endpoints Quick Reference" in `docs/api-reference/README.md` for common mistakes.

### Documentation Structure
```
docs/
  api-reference/
    README.md          # Quick reference + common mistakes table
    sonarr.md          # Sonarr v3 API — endpoints, params, response formats
    radarr.md          # Radarr v3 API
    lidarr.md          # Lidarr v1 API (NOT v3!)
    prowlarr.md        # Prowlarr v1 API (Newznab-compatible)
    readarr.md         # Readarr v1 API (NOT v3!)
    seerr.md           # Seerr/Jellyseerr v1 API
    tautulli.md        # Tautulli v2 API (cmd-based, query auth)
    plex.md            # Plex API (no /api/ prefix, MediaContainer wrapper)
  mcp-architecture.md  # MCP protocol, tool dispatch, registration, error handling
  plan.md              # General project plan
  PLAN_HTTP_TRANSPORT.md  # HTTP transport design doc
  plan-bugfix-2026-07-11.md         # Bugfix plan
  plan-seerr-api-audit-2026-07-11.md  # Seerr audit plan
```

### Key API Gotchas (from docs)
- **Sonarr/Radarr**: `/series/lookup` and `/movie/lookup` for external search, NOT `/series?term` or `/movie?term`
- **Lidarr/Readarr/Prowlarr**: Use `/api/v1`, NOT `/api/v3`
- **Prowlarr**: Search param is `query`, NOT `term`; status endpoint is `/system/status`, NOT `/status`
- **Seerr**: Percent-encode spaces as `%20` (not `+`); `mediaId` not `tmdbId` for requests
- **Tautulli**: Auth via `apikey` query param; responses wrapped in `{"response": {"data": ...}}`
- **Plex**: No `/api/` prefix; `type` filter is integer (1=movie, 2=show); `MediaContainer` wrapper
- **Radarr command**: `MoviesSearch` (plural) + `movieIds[]` (array), NOT `SearchMovie` + `movieId`

## Design Docs / Planning
- `README.md` — Project overview and usage.
- `docs/mcp-architecture.md` — MCP protocol, tool dispatch, registration flow.
- `CHANGELOG.md` — Version history and release notes.
