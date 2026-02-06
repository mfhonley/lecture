"""
Конфигурация приложения из переменных окружения.

Один класс Settings (pydantic-settings), все секреты и настройки читаются из .env.
В коде используем только settings.*, не os.getenv.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки из env. Добавляй поля под свой проект."""

    # MongoDB — всегда облако (Atlas и т.д.). URI из .env.
    MONGO_URI: str = ""
    MONGO_DB_NAME: str = "app"

    # CORS: список origin через запятую в .env
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Rate limit: запросов с одного IP за окно (например, "100/minute" — 100 в минуту)
    RATE_LIMIT: str = "100/minute"

    # Логирование
    LOG_LEVEL: str = "INFO"

    # JWT Access Token
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 15  # 15 минут

    # JWT Refresh Token
    JWT_REFRESH_SECRET: str = "change-me-refresh-in-production"
    JWT_REFRESH_EXPIRE_DAYS: int = 30  # 30 дней

    # GitHub OAuth
    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    # Frontend URL для редиректа после OAuth
    FRONTEND_URL: str = "http://localhost:3000"

    # S3 / MinIO
    S3_ENDPOINT: str = ""       # http://localhost:9000 для MinIO
    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_BUCKET: str = "uploads"
    S3_REGION: str = "us-east-1"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
        extra="ignore",
    )

    def cors_list(self) -> list[str]:
        """CORS origins как список для CORSMiddleware."""
        return [x.strip() for x in self.CORS_ORIGINS.split(",") if x.strip()]

    def rate_limit_parsed(self) -> tuple[int, int]:
        """RATE_LIMIT разобрать в (max_requests, window_seconds). Пример: '100/minute' -> (100, 60)."""
        s = self.RATE_LIMIT.strip().lower().replace(" ", "")
        if "/" not in s:
            return 100, 60
        part, window = s.split("/", 1)
        try:
            max_req = int(part)
        except ValueError:
            return 100, 60
        if window in ("minute", "min", "m"):
            return max_req, 60
        if window in ("hour", "h"):
            return max_req, 3600
        if window in ("second", "sec", "s"):
            return max_req, 1
        return max_req, 60


# Глобальный экземпляр — импортируй: from app.core.config import settings
settings = Settings()
