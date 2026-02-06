"""
Схемы для резюме.
"""
from datetime import datetime

from pydantic import BaseModel, Field


class ResumeCreate(BaseModel):
    """Создание резюме."""

    title: str = Field(min_length=1, max_length=255)
    template_id: str | None = None


class ResumeUpdate(BaseModel):
    """Обновление резюме (частичное)."""

    title: str | None = None
    content: dict | None = None
    theme_config: dict | None = None
    is_public: bool | None = None
    slug: str | None = None


class Resume(BaseModel):
    """Резюме в ответах API."""

    id: str
    user_id: str
    title: str
    content: dict = {}
    theme_config: dict = {}
    thumbnail_url: str | None = None
    is_public: bool = False
    slug: str | None = None
    created_at: datetime
    updated_at: datetime
