"""
Схемы для пользователей и авторизации.
"""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    """Регистрация через email."""

    email: EmailStr
    password: str = Field(min_length=8)
    name: str | None = None


class UserLogin(BaseModel):
    """Вход через email."""

    email: EmailStr
    password: str


class User(BaseModel):
    """Пользователь в ответах API."""

    id: str
    email: str
    name: str | None = None
    avatar_url: str | None = None
    provider: str  # "email" | "github"
    created_at: datetime


class Token(BaseModel):
    """JWT токен."""

    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Данные из токена."""

    user_id: str
