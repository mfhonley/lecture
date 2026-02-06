"""
Авторизация: email/пароль и GitHub OAuth.
Все эндпоинты возвращают пару access + refresh токенов.
"""
from datetime import datetime, timezone
from urllib.parse import urlencode

import httpx
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm

from app.core.config import settings
from app.core.database import get_users_collection
from app.core.security import (
    create_token_pair,
    decode_refresh_token,
    get_current_user,
    hash_password,
    verify_password,
)
from app.schemas.common import ErrorResponse, SuccessResponse
from app.schemas.user import RefreshRequest, Token, User, UserCreate

router = APIRouter(prefix="/auth", tags=["auth"])


def _doc_to_user(doc: dict) -> User:
    """Конвертировать документ MongoDB в User."""
    return User(
        id=str(doc["_id"]),
        email=doc["email"],
        full_name=doc.get("full_name"),
        avatar_url=doc.get("avatar_url"),
        provider=doc["provider"],
        subscription_tier=doc.get("subscription_tier", "free"),
        last_login=doc.get("last_login"),
        created_at=doc["created_at"],
    )


def _update_last_login(users, user_id) -> None:
    """Обновить last_login при входе."""
    users.update_one(
        {"_id": user_id},
        {"$set": {"last_login": datetime.now(timezone.utc)}},
    )


# ==================== Email/Password ====================


@router.post(
    "/register",
    response_model=SuccessResponse[Token],
    status_code=status.HTTP_201_CREATED,
    responses={400: {"model": ErrorResponse}},
)
async def register(data: UserCreate):
    """Регистрация через email и пароль."""
    users = get_users_collection()

    if users.find_one({"email": data.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    now = datetime.now(timezone.utc)
    user_doc = {
        "email": data.email,
        "password_hash": hash_password(data.password),
        "full_name": data.full_name,
        "avatar_url": None,
        "provider": "email",
        "github_id": None,
        "subscription_tier": "free",
        "last_login": now,
        "created_at": now,
        "updated_at": now,
    }
    result = users.insert_one(user_doc)

    access, refresh = create_token_pair(str(result.inserted_id))
    return SuccessResponse(data=Token(access_token=access, refresh_token=refresh))


@router.post(
    "/login",
    response_model=SuccessResponse[Token],
    responses={401: {"model": ErrorResponse}},
)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Вход через email и пароль. OAuth2 форма (username = email)."""
    users = get_users_collection()

    user = users.find_one({"email": form_data.username})
    if not user or not user.get("password_hash"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(form_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    _update_last_login(users, user["_id"])

    access, refresh = create_token_pair(str(user["_id"]))
    return SuccessResponse(data=Token(access_token=access, refresh_token=refresh))


@router.post(
    "/refresh",
    response_model=SuccessResponse[Token],
    responses={401: {"model": ErrorResponse}},
)
async def refresh(data: RefreshRequest):
    """Обновить токены по refresh_token. Возвращает новую пару."""
    payload = decode_refresh_token(data.refresh_token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    user = get_users_collection().find_one({"_id": ObjectId(user_id)})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    access, new_refresh = create_token_pair(user_id)
    return SuccessResponse(data=Token(access_token=access, refresh_token=new_refresh))


@router.get(
    "/me",
    response_model=SuccessResponse[User],
    responses={401: {"model": ErrorResponse}},
)
async def me(current_user: dict = Depends(get_current_user)):
    """Получить текущего пользователя."""
    return SuccessResponse(data=_doc_to_user(current_user))


# ==================== GitHub OAuth ====================

GITHUB_AUTHORIZE_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"


@router.get("/github")
async def github_login():
    """Редирект на GitHub для OAuth авторизации."""
    if not settings.GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="GitHub OAuth not configured",
        )

    params = {
        "client_id": settings.GITHUB_CLIENT_ID,
        "scope": "user:email",
    }
    return RedirectResponse(f"{GITHUB_AUTHORIZE_URL}?{urlencode(params)}")


@router.get("/github/callback")
async def github_callback(code: str | None = None, error: str | None = None):
    """Callback от GitHub OAuth."""
    if error:
        return RedirectResponse(f"{settings.FRONTEND_URL}/auth/error?error={error}")

    if not code:
        return RedirectResponse(f"{settings.FRONTEND_URL}/auth/error?error=no_code")

    # Обменять code на access_token
    async with httpx.AsyncClient() as client:
        token_response = await client.post(
            GITHUB_TOKEN_URL,
            data={
                "client_id": settings.GITHUB_CLIENT_ID,
                "client_secret": settings.GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        token_data = token_response.json()

    if "access_token" not in token_data:
        return RedirectResponse(
            f"{settings.FRONTEND_URL}/auth/error?error=token_exchange_failed"
        )

    github_token = token_data["access_token"]

    # Получить данные пользователя
    async with httpx.AsyncClient() as client:
        headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/json",
        }
        user_response = await client.get(GITHUB_USER_URL, headers=headers)
        github_user = user_response.json()

        emails_response = await client.get(GITHUB_EMAILS_URL, headers=headers)
        emails = emails_response.json()

    # Найти primary email
    email = None
    if isinstance(emails, list):
        for e in emails:
            if e.get("primary") and e.get("verified"):
                email = e["email"]
                break
        if not email and emails:
            email = emails[0].get("email")

    if not email:
        email = github_user.get("email")

    if not email:
        return RedirectResponse(
            f"{settings.FRONTEND_URL}/auth/error?error=no_email"
        )

    github_id = str(github_user["id"])
    users = get_users_collection()

    user = users.find_one({"github_id": github_id})
    if not user:
        user = users.find_one({"email": email})

    now = datetime.now(timezone.utc)

    if user:
        users.update_one(
            {"_id": user["_id"]},
            {
                "$set": {
                    "github_id": github_id,
                    "full_name": github_user.get("name") or user.get("full_name"),
                    "avatar_url": github_user.get("avatar_url"),
                    "last_login": now,
                    "updated_at": now,
                }
            },
        )
        user_id = str(user["_id"])
    else:
        user_doc = {
            "email": email,
            "password_hash": None,
            "full_name": github_user.get("name"),
            "avatar_url": github_user.get("avatar_url"),
            "provider": "github",
            "github_id": github_id,
            "subscription_tier": "free",
            "last_login": now,
            "created_at": now,
            "updated_at": now,
        }
        result = users.insert_one(user_doc)
        user_id = str(result.inserted_id)

    access, refresh_tok = create_token_pair(user_id)

    return RedirectResponse(
        f"{settings.FRONTEND_URL}/auth/callback?access_token={access}&refresh_token={refresh_tok}"
    )
