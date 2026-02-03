"""
Схемы для ресурса Item (CRUD).

Отдельно модель для тела запроса (create/update) и модель ответа (с id).
Для своей сущности — скопируй, переименуй Item → Task/Waitlist и поменяй поля.
"""
from pydantic import BaseModel, Field


class ItemCreate(BaseModel):
    """Тело запроса при создании и при обновлении (PUT)."""

    name: str = Field(..., min_length=1)
    description: str | None = None
    price: float = Field(..., ge=0)


class Item(ItemCreate):
    """Ответ API: сущность с id. id в MongoDB — ObjectId, в API отдаём строкой."""

    id: str
    description: str = ""  # при ответе всегда строка (None → "")
