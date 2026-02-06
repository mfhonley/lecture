"""
Схемы для пользователей и авторизации.
"""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Регистрация через email."""

    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str | None = None


class UserLogin(BaseModel):
    """Вход через email."""

    email: EmailStr
    password: str


class User(BaseModel):
    """Пользователь в ответах API."""

    id: str
    email: str
    full_name: str | None = None
    avatar_url: str | None = None
    provider: str  # "email" | "github"
    subscription_tier: str = "free"  # "free" | "pro" | "enterprise"
    last_login: datetime | None = None
    created_at: datetime


class Token(BaseModel):
    """Пара JWT токенов."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    """Запрос на обновление токенов."""

    refresh_token: str
