"""
Подключение к MongoDB (облако: Atlas и т.д.).

Один клиент на приложение, подключение при старте (lifespan в main),
получение БД/коллекции через функции. URI только из config (.env).
"""
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

from app.core.config import settings

# Клиент создаётся при старте приложения (main.py lifespan), здесь только ссылка
_client: MongoClient | None = None


def get_client() -> MongoClient:
    """Вернуть клиент MongoDB. Вызывать после connect_to_mongo()."""
    if _client is None:
        raise RuntimeError("MongoDB not connected. Call connect_to_mongo() first.")
    return _client


def get_db() -> Database:
    """Вернуть экземпляр БД. Используй в роутерах/сервисах."""
    return get_client()[settings.MONGO_DB_NAME]


def get_items_collection() -> Collection:
    """Коллекция items. Для другой сущности — скопируй и переименуй (tasks, waitlist и т.д.)."""
    return get_db()["items"]


def get_users_collection() -> Collection:
    """Коллекция users для авторизации."""
    return get_db()["users"]


def get_resumes_collection() -> Collection:
    """Коллекция resumes."""
    return get_db()["resumes"]


def get_portfolios_collection() -> Collection:
    """Коллекция portfolios."""
    return get_db()["portfolios"]


def connect_to_mongo() -> None:
    """Подключиться к MongoDB. Вызывается в lifespan при старте."""
    global _client  # noqa: PLW0603
    _client = MongoClient(settings.MONGO_URI)
    # Проверка доступности
    _client.admin.command("ping")


def close_mongo_connection() -> None:
    """Закрыть соединение. Вызывается в lifespan при остановке."""
    global _client
    if _client:
        _client.close()
        _client = None
