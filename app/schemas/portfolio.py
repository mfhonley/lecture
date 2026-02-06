"""
Схемы для портфолио.
"""
from datetime import datetime

from pydantic import BaseModel, Field


class PortfolioCreate(BaseModel):
    """Создание портфолио."""

    title: str = Field(min_length=1, max_length=255)
    subdomain: str = Field(min_length=1, max_length=63)


class PortfolioUpdate(BaseModel):
    """Обновление портфолио (частичное)."""

    title: str | None = None
    subdomain: str | None = None
    content: dict | None = None
    theme_config: dict | None = None
    is_published: bool | None = None


class Portfolio(BaseModel):
    """Портфолио в ответах API."""

    id: str
    user_id: str
    title: str
    subdomain: str
    custom_domain: str | None = None
    content: dict = {}
    theme_config: dict = {}
    is_published: bool = False
    created_at: datetime
    updated_at: datetime
