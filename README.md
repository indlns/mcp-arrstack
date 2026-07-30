# 🔧 MCP Server for ARR Stack

**Model Context Protocol server** для управления домашним медиастеком (Radarr, Sonarr, Prowlarr, Readarr, Lidarr, Seerr, Tautulli, Plex).

Позволяет **локальным LLM моделям** (Ollama, OpenWebUI и др.) напрямую взаимодействовать с вашими сервисами через стандартизированный MCP интерфейс.

---

## 📦 Возможности

| Сервис | Возможности |
|--------|-------------|
| **Sonarr** | Поиск/добавление/удаление сериалов, управление эпизодами, профили качества |
| **Radarr** | Поиск/добавление/удаление фильмов, управление коллекциями |
| **Lidarr** | Управление музыкой — артисты, альбомы, качество |
| **Prowlarr** | Поиск по индексам, управление трекерами, тестирование подключений |
| **Readarr** | Управление книгами и авторами |
| **Seerr** | Запросы медиаконтента, одобрение/отклонение запросов |
| **Tautulli** | Статистика просмотров, история, активность пользователей |
| **Plex** | Поиск в медиатеке, управление библиотеками, плейлисты |

---

## 🚀 Быстрый старт (Docker)

### 1. Клонирование репозитория

```bash
git clone <your-repo-url> mcp-arr-stack
cd mcp-arr-stack
```

### 2. Настройка окружения

```bash
cp .env.example .env
```

Отредактируйте `.env` — укажите адреса и API ключи ваших сервисов:

```env
# Sonarr (сериалы)
SONARR_HOST=http://sonarr:8989
SONARR_API_KEY=your_sonarr_api_key_here

# Radarr (фильмы)
RADARR_HOST=http://radarr:7878
RADARR_API_KEY=your_radarr_api_key_here

# Lidarr (музыка)
LIDARR_HOST=http://lidarr:8686
LIDARR_API_KEY=your_lidarr_api_key_here

# Prowlarr (поиск/индексы)
PROWLARR_HOST=http://prowlarr:9696
PROWLARR_API_KEY=your_prowlarr_api_key_here

# Seerr (запросы)
SEERR_HOST=http://seerr:5055
SEERR_API_KEY=your_seerr_api_key_here

# Tautulli (статистика Plex)
TAUTULLI_HOST=http://tautulli:8181
TAUTULLI_API_KEY=your_tautulli_api_key_here

# Plex Media Server
PLEX_HOST=http://plex:32400
PLEX_TOKEN=your_plex_token_here
```

> **Важно:** Если сервис не нужен — просто оставьте его поля пустыми. Сервер автоматически отключит недоступные сервисы.

### 3. Запуск через Docker Compose

```bash
docker compose up -d --build
```

### 4. Проверка работы

```bash
# Просмотр логов
docker compose logs -f mcp-arr-stack

# Проверка статуса
docker compose ps
```

---

## 🌐 HTTP Transport

Сервер поддерживает **Streamable HTTP** транспорт для внешних MCP клиентов. Позволяет подключаться через HTTP/SSE вместо stdio.

### Быстрый старт

```bash
# Через переменную окружения
MCP_TRANSPORT=http python -m src.server

# Через CLI флаг
python -m src.server --transport http
```

### Конфигурация

| Переменная | По умолчанию | Описание |
|------------|-------------|----------|
| `MCP_TRANSPORT` | `stdio` | Транспорт (`stdio` или `http`) |
| `HTTP_HOST` | `0.0.0.0` | Адрес привязки сервера |
| `HTTP_PORT` | `8080` | Порт сервера |
| `HTTP_API_KEY` | (пусто) | Bearer token для аутентификации клиентов |
| `HTTP_CORS_ORIGINS` | `*` | CORS разрешённые origins (через запятую или `*`) |
| `HTTP_SSL_CERTFILE` | (пусто) | Путь к SSL сертификату (опционально) |
| `HTTP_SSL_KEYFILE` | (пусто) | Путь к SSL приватному ключу (опционально) |

### Конфигурация клиента

Пример для MCP-совместимых клиентов:

```json
{
  "mcpServers": {
    "arr-stack": {
      "url": "http://localhost:8080",
      "headers": {
        "Authorization": "Bearer your-api-key"
      }
    }
  }
}
```

### Конечные точки (Endpoints)

| Endpoint | Method | Описание |
|----------|--------|----------|
| `/` | POST | MCP Streamable HTTP endpoint (JSON-RPC, SSE) |
| `/health` | GET | Health check — возвращает `{"status": "ok"}` |

### Docker Compose (HTTP режим)

```bash
# Запуск в режиме HTTP
docker compose up -d mcp-arr-stack-http

# Просмотр логов
docker compose logs -f mcp-arr-stack-http
```

---

## 🔌 Подключение к LLM

### OpenWebUI

В настройках OpenWebUI добавьте MCP сервер:

```json
{
  "mcp_servers": {
    "arr-stack": {
      "command": "docker",
      "args": [
        "exec", "-i", "mcp-arr-stack",
        "python", "-m", "src.server"
      ],
      "env": {}
    }
  }
}
```

### Ollama (через MCP CLI)

```bash
# Запуск через docker exec
docker exec -i mcp-arr-stack python -m src.server

# Или подключите через MCP CLI
npx -y @modelcontextprotocol/cli --server "docker exec -i mcp-arr-stack python -m src.server"
```

### Прямой запуск (для разработки)

```bash
# Создание виртуального окружения
python -m venv .venv
source .venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Запуск
python -m src.server
```

---

## 🛠 Доступные инструменты MCP

### Sonarr (TV Series)

| Инструмент | Описание |
|------------|----------|
| `sonarr_search_series` | Поиск сериалов по названию |
| `sonarr_get_series` | Получить детали сериала или список всех |
| `sonarr_get_episodes` | Список эпизодов с статусами |
| `sonarr_add_series` | Добавить новый сериал |
| `sonarr_delete_series` | Удалить сериал |
| `sonarr_get_quality_profile` | Профили качества |
| `sonarr_get_root_folder` | Доступные папки на диске |
| `sonarr_get_series_status` | Статус сериала (сколько эпизодов скачано) |

### Radarr (Movies)

| Инструмент | Описание |
|------------|----------|
| `radarr_search_movie` | Поиск фильмов по названию |
| `radarr_get_movies` | Получить детали фильма или список всех |
| `radarr_add_movie` | Добавить новый фильм |
| `radarr_delete_movie` | Удалить фильм |
| `radarr_get_quality_profile` | Профили качества для фильмов |
| `radarr_get_root_folder` | Доступные папки на диске |
| `radarr_get_movie_status` | Статус фильма (размер, качество) |

### Prowlarr (Indexers)

| Инструмент | Описание |
|------------|----------|
| `prowlarr_search` | Поиск по всем индексам |
| `prowlarr_get_indexers` | Список трекеров |
| `prowlarr_test_indexers` | Тестирование соединения со всеми трекерами |
| `prowlarr_get_status` | Общий статус Prowlarr |

### Seerr (Requests)

| Инструмент | Описание |
|------------|----------|
| `seerr_search` | Поиск медиа через TMDB/TVDB |
| `seerr_get_requests` | Список запросов |
| `seerr_request_media` | Запрос фильма/сериала |
| `seerr_approve` | Одобрить запрос |
| `seerr_reject` | Отклонить запрос |

### Tautulli (Plex Statistics)

| Инструмент | Описание |
|------------|----------|
| `tautulli_get_activity` | Текущая активность просмотров |
| `tautulli_get_library_stats` | Статистика медиатеки |
| `tautulli_get_history` | История просмотров |
| `tautulli_get_user_stats` | Статистика по пользователям |
| `tautulli_get_recently_added` | Недавно добавленный контент |

### Plex (Media Server)

| Инструмент | Описание |
|------------|----------|
| `plex_search` | Поиск в медиатеке |
| `plex_library_sections` | Список библиотек |
| `plex_recently_added` | Недавно добавленное |
| `plex_playlists` | Плейлисты |
| `plex_library` | Элементы библиотеки |
| `plex_get_status` | Статус сервера Plex |

### Lidarr (Music)

| Инструмент | Описание |
|------------|----------|
| `lidarr_search_artist` | Поиск артистов/альбомов |
| `lidarr_get_artist` | Детали артиста или список всех |
| `lidarr_add_artist` | Добавить нового артиста |
| `lidarr_delete_artist` | Удалить артиста |

---

## 💡 Примеры использования

### Для LLM (примеры промптов)

```
"Какие новые сезоны сериалов вышли на этой неделе?"
"Что мне посмотреть? Я люблю научную фантастику."
"Проверь, какие фильмы из моего списка ожидания ещё не скачались."
"Кто сейчас смотрит что-то дома?"
"Покажи статистику просмотров за последний месяц."
"Добавь сериал 'Black Mirror' в Sonarr."
"Какие трекеры в Prowlarr имеют проблемы?"
```

### Пример ответа LLM с данными Sonarr

**Пользователь:** "Сколько эпизодов осталось посмотреть в Breaking Bad?"

**LLM (через MCP):**
1. Вызывает `sonarr_get_series(title="Breaking Bad")` → получает series_id=12345
2. Вызывает `sonarr_get_episodes(series_id=12345)` → получает список эпизодов
3. Анализирует статус каждого эпизода
4. Формулирует ответ: "В Breaking Bad 62 эпизода всего. Скачано 58, осталось 4."

---

## 📁 Структура проекта

```
mcp-arr-stack/
├── src/
│   ├── __init__.py
│   ├── server.py              # Основной MCP сервер
│   ├── http_server.py         # Streamable HTTP транспорт (ASGI, SSE)
│   ├── config.py              # Конфигурация (загрузка из .env)
│   ├── client.py              # HTTP клиенты для сервисов
│   ├── utils.py               # Утилиты (кэш, rate limiting)
│   └── tools/
│       ├── __init__.py
│       ├── sonarr_tools.py    # Инструменты Sonarr
│       ├── radarr_tools.py    # Инструменты Radarr
│       ├── lidarr_tools.py    # Инструменты Lidarr
│       ├── prowlarr_tools.py  # Инструменты Prowlarr
│       ├── readarr_tools.py   # Инструменты Readarr
│       ├── seerr_tools.py   # Инструменты Seerr
│       ├── tautulli_tools.py  # Инструменты Tautulli
│       └── plex_tools.py      # Инструменты Plex
├── tests/
│   ├── conftest.py            # Общие фикстуры
│   ├── __init__.py
│   ├── test_config.py         # Тесты конфигурации
│   ├── test_client.py         # Тесты клиентов
│   ├── test_utils.py          # Тесты утилит
│   ├── test_http_server.py    # Тесты HTTP транспорта
│   ├── test_sonarr_tools.py   # Тесты Sonarr
│   ├── test_radarr_tools.py   # Тесты Radarr
│   ├── test_lidarr_tools.py   # Тесты Lidarr
│   ├── test_readarr_tools.py  # Тесты Readarr
│   ├── test_seerr_tools.py    # Тесты Seerr
│   ├── test_tautulli_tools.py # Тесты Tautulli
│   └── test_plex_tools.py     # Тесты Plex
├── .env.example               # Шаблон переменных окружения
├── .gitignore
├── docker-compose.yml         # Docker Compose конфигурация
├── Dockerfile                 # Сборка Docker образа
├── requirements.txt           # Python зависимости
└── pyproject.toml             # Настройки проекта (pytest, black, ruff)
```

---

## 📚 API Reference

Полная документация по API всех сервисов доступна в [`docs/api-reference/`](./docs/api-reference/):

| Документ | Сервис |
|----------|--------|
| [`sonarr.md`](./docs/api-reference/sonarr.md) | Sonarr v3 API |
| [`radarr.md`](./docs/api-reference/radarr.md) | Radarr v3 API |
| [`lidarr.md`](./docs/api-reference/lidarr.md) | Lidarr v1 API |
| [`prowlarr.md`](./docs/api-reference/prowlarr.md) | Prowlarr v1 API |
| [`readarr.md`](./docs/api-reference/readarr.md) | Readarr v1 API |
| [`seerr.md`](./docs/api-reference/seerr.md) | Seerr v1 API |
| [`tautulli.md`](./docs/api-reference/tautulli.md) | Tautulli v2 API |
| [`plex.md`](./docs/api-reference/plex.md) | Plex API |

---

## 🔒 Безопасность

- Все API ключи хранятся в `.env` файле (не коммитится в Git)
- Сервер работает от **непривилегированного пользователя** в Docker
- По умолчанию используется stdio транспорт — нет открытых портов
- HTTP транспорт поддерживает Bearer token аутентификацию (`HTTP_API_KEY`)
- CORS middleware для контроля доступа к HTTP endpoint'ам
- Rate limiting для защиты от перегрузки
- Graceful degradation — недоступный сервис не ломает остальные

---

## 🧪 Тестирование

```bash
# Установка зависимостей для разработки
pip install -r requirements.txt[dev]

# Запуск всех тестов
pytest

# С отчётом о покрытии
pytest --cov=src --cov-report=html

# Лinting и форматирование
ruff check src/ tests/
black --check src/ tests/
```

---

## 🛠 Troubleshooting

### Сервис не подключается

1. Проверьте `.env` — правильные ли адреса и ключи
2. Убедитесь, что сервисы доступны из Docker сети:
   ```bash
   docker compose exec mcp-arr-stack ping sonarr
   ```
3. Проверьте логи:
   ```bash
   docker compose logs mcp-arr-stack
   ```

### MCP инструменты не появляются в LLM

1. Убедитесь, что сервер запущен:
   ```bash
   docker compose ps
   ```
2. Проверьте подключение в интерфейсе вашего LLM клиента
3. Перезапустите сервер:
   ```bash
   docker compose restart mcp-arr-stack
   ```

### Ошибки при сборке Docker

```bash
# Полная пересборка
docker compose build --no-cache

# Проверка сборки
docker compose config
```

---

## 📝 Лицензия

MIT License — см. файл [LICENSE](LICENSE)

---

## 🤝 Вклад

Принимаю PR и issues! Для больших изменений сначала создайте issue для обсуждения.

---

*Создано с ❤️ для домашних медиастеков*
