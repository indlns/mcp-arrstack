# Changelog

Все значимые изменения этого проекта документируются в этом файле.

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/),
версии привязаны к [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [0.1.1] — 2026-07-13

_Исправление критического бага: HTTP-клиенты больше не закрываются после первого запроса._

### Fixed

- **Client**: Убрано некорректное использование `async with self.client as c:` — `httpx.AsyncClient` закрывался после каждого запроса, делая невозможным повторное использование. Исправлены методы `get/post/put/delete` в `BaseARRClient`, `SeerrClient`, `get` в `TautulliClient` и `PlexClient`.

---

## [0.1.0] — 2026-07-13

_Первый релиз — 8 сервисов, 30+ MCP инструментов, stdio + HTTP транспорт._

### Added

- **Server**: MCP-сервер со stdio-транспортом, фабричная система сервисов, динамическая регистрация инструментов, диспетчеризация, логирование, CLI-аргументы, выбор транспорта
- **HTTP Transport**: Streamable HTTP endpoint, middleware аутентификации (Bearer token), CORS, health check (`/health`), SSL/TLS поддержка
- **Sonarr**: Поиск, получение, добавление, удаление сериалов; эпизоды; профили качества; корневые папки; статус сериала
- **Radarr**: Поиск, получение, добавление, удаление фильмов; профили качества; корневые папки; статус фильма; команда поиска
- **Lidarr**: Поиск, получение, добавление, удаление артистов; команда поиска пропущенных
- **Prowlarr**: Поиск по индексам, список трекеров, тестирование всех индексеров, история, системный статус
- **Readarr**: Поиск, получение, добавление, удаление авторов книг
- **Seerr**: Поиск медиа, список запросов, запрос медиа (фильмы/сериалы), одобрение/отклонение запросов
- **Tautulli**: Текущая активность, статистика библиотеки, история просмотров, статистика пользователей, недавно добавленное
- **Plex**: Поиск в медиатеке, секции библиотеки, недавно добавленное, плейлисты, элементы библиотеки, статус сервера
- **Client Layer**: `BaseARRClient` (ARR v3), `SeerrClient` (v1), `TautulliClient` (v2), `PlexClient` — connection pooling, кэширование, rate limiting
- **Configuration**: Environment-driven dataclass'ы для 8 сервисов, HTTP-конфигурация, автоматическая фильтрация включённых сервисов
- **Models**: Pydantic модели (APIResponse, SonarrSeries, RadarrMovie и др.), форматирование сводок
- **Utils**: TTL-based кэш с asyncio-lock, sliding window rate limiter, safe_execute
- **Tests**: 140+ тестов для всех 8 сервисов, тесты клиентов, утилит, HTTP транспорта
- **Docker**: Многоступенчатая сборка, docker-compose (stdio + http сервисы), 26+ переменных окружения

### Fixed

- **API-аудит**: Исправлены все невалидные API-вызовы (25 багов из аудита) — неверные endpoints, параметры, имена команд, типы данных
- **Seerr**: Пагинация (`take`/`skip`), обработка ответа, поиск по TMDb ID, валидный POST body, методы approve/reject
- **Sonarr/Radarr**: Внешний поиск через `/lookup` вместо локальной библиотеки, передача `deleteFiles`, команды поиска
- **Lidarr/Readarr**: Правильные lookup endpoints, передача `deleteFiles`, исправлена мутация shared API_PREFIX
- **Prowlarr**: Правильный endpoint статуса (`/system/status`), параметр поиска (`query`), массовое тестирование индексеров
- **Tautulli**: Корректная обработка вложенного ответа API (`response.data.data`)
- **Plex**: Типы section_key/section_type, удаление мёртвого кода, дублирование токена
- **Server**: Относительные импорты, отсечение префикса `{service}_`, обработка SSL, обновление MCP SDK, anyio
- **HTTP Transport**: Обёртка ASGI для SessionManager, middleware на уровне Starlette
- **Docker**: Исправление портов, stdin_open/tty для stdio режима
- **Utils**: Интеграция кэша и rate limiter в клиент, потокобезопасность кэша
- **Tests**: Coverage для всех сервисов (51 новый тест), реальный HTTPStatusError в моках

### Changed

- **Импорт**: Все модули переключены на относительные импорты
- **call_tool**: Расширена поддержка типов аргументов (`list | dict | None`)
- **Dockerfile**: Добавлена `EXPOSE 8080`, переменная `MCP_TRANSPORT`

### Documentation

- **README.md**: Секция HTTP Transport, таблица конфигурации, примеры клиентов, endpoints, структура проекта, API Reference
- **.env.example**: Секция HTTP Transport Configuration
- **docs/api-reference/**: Документация по API всех 8 сервисов, quick reference, common mistakes

---

## [Unreleased]

_Изменения, находящиеся в разработке и ещё не вошедшие в релиз._
