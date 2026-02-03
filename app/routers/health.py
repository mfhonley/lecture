"""
Health check: жив ли сервис, доступна ли БД.

Эндпоинт для оркестраторов (Docker, k8s) и мониторинга.
"""
from fastapi import APIRouter

from app.core.database import get_client
from app.schemas.common import SuccessResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=SuccessResponse[dict])
def health():
    """Проверка живости сервиса и MongoDB."""
    try:
        get_client().admin.command("ping")
        mongo = "connected"
    except Exception:
        mongo = "disconnected"
    return SuccessResponse(data={"status": "ok", "mongo": mongo})
