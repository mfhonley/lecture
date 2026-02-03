"""
Структура ответов API: единый формат для успеха и ошибок.

Успех: { "success": true, "data": <payload> }
Ошибка: { "success": false, "error": "<code>", "message": "<text>" }
"""
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    """Успешный ответ: success=true, data — полезная нагрузка."""

    success: bool = True
    data: T | None = Field(default=None, description="Тело ответа")


class ErrorResponse(BaseModel):
    """Ответ с ошибкой: success=false, error и message."""

    success: bool = False
    error: str = Field(..., description="Код ошибки (например, not_found, validation_error)")
    message: str = Field(..., description="Человекочитаемое сообщение")
