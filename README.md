# Backend Boilerplate

FastAPI + Poetry + MongoDB (в облаке). Бойлерплейт под свой MVP.

## Структура

```
app/
├── main.py           # Точка входа: FastAPI, lifespan, CORS, роутеры
├── core/             # Конфиг и БД
│   ├── config.py     # Настройки из .env (pydantic-settings)
│   └── database.py   # Подключение к MongoDB, get_db, get_items_collection
├── schemas/          # Pydantic: тело запроса и ответа
│   └── item.py       # ItemCreate, Item
└── routers/          # Эндпоинты
    ├── health.py     # GET /health
    └── items.py      # CRUD /items

Dockerfile             # Образ приложения
docker-compose.yml     # Только app; MongoDB в облаке
.dockerignore
```

Подробно — в **DOCS.md** в папке `lecture/`.

## MongoDB — в облаке

Используй облачный кластер (MongoDB Atlas и т.д.). Строку подключения возьми в консоли кластера и пропиши в `.env` как `MONGO_URI`. Локальный или Docker-Mongo в бойлерплейте не предусмотрен.

## Запуск (локально)

```bash
cp .env.example .env
# Заполни MONGO_URI строкой подключения к облачному MongoDB

poetry install
poetry run uvicorn app.main:app --reload
```

Документация API: http://127.0.0.1:8000/docs

## Запуск (Docker)

```bash
cp .env.example .env
# Заполни MONGO_URI строкой подключения к облачному MongoDB

docker compose up --build
```

API: http://127.0.0.1:8000, документация: http://127.0.0.1:8000/docs

При изменении зависимостей в `pyproject.toml` выполни `poetry lock` и пересобери образ.

## Под свой MVP

1. Переименуй сущность: `items` → `tasks` / `waitlist` / что нужно.
2. В `schemas/item.py` — поменяй поля под свою модель.
3. В `core/database.py` — добавь `get_*_collection()` для своей коллекции.
4. В `routers/` — скопируй `items.py` в `tasks.py`, поменяй префикс и схемы.
5. В `main.py` — подключи новый роутер.

Можно использовать AI: «переименуй items в waitlist, поля: email, name».
