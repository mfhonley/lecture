"""
CRUD для портфолио. Все эндпоинты защищены JWT.
Пользователь видит/редактирует только свои портфолио.
"""
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException

from app.core.database import get_portfolios_collection
from app.core.security import get_current_user
from app.schemas.common import ErrorResponse, SuccessResponse
from app.schemas.portfolio import Portfolio, PortfolioCreate, PortfolioUpdate

router = APIRouter(prefix="/portfolios", tags=["portfolios"])


def _doc_to_portfolio(doc: dict) -> Portfolio:
    return Portfolio(
        id=str(doc["_id"]),
        user_id=str(doc["user_id"]),
        title=doc["title"],
        subdomain=doc["subdomain"],
        custom_domain=doc.get("custom_domain"),
        content=doc.get("content", {}),
        theme_config=doc.get("theme_config", {}),
        is_published=doc.get("is_published", False),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


def _get_own_portfolio(portfolio_id: str, user_id: ObjectId) -> dict:
    """Получить портфолио, проверив владельца."""
    try:
        oid = ObjectId(portfolio_id)
    except InvalidId:
        raise HTTPException(404, detail="Portfolio not found")

    doc = get_portfolios_collection().find_one({"_id": oid, "user_id": user_id})
    if not doc:
        raise HTTPException(404, detail="Portfolio not found")
    return doc


@router.get("", response_model=SuccessResponse[list[Portfolio]])
async def list_portfolios(current_user: dict = Depends(get_current_user)):
    """Список портфолио текущего пользователя."""
    coll = get_portfolios_collection()
    cursor = coll.find({"user_id": current_user["_id"]}).sort("created_at", -1)
    data = [_doc_to_portfolio(doc) for doc in cursor]
    return SuccessResponse(data=data)


@router.post(
    "",
    response_model=SuccessResponse[Portfolio],
    status_code=201,
    responses={400: {"model": ErrorResponse}},
)
async def create_portfolio(
    data: PortfolioCreate,
    current_user: dict = Depends(get_current_user),
):
    """Создать портфолио."""
    coll = get_portfolios_collection()

    # Проверить уникальность subdomain
    if coll.find_one({"subdomain": data.subdomain}):
        raise HTTPException(400, detail="Subdomain already taken")

    now = datetime.now(timezone.utc)
    doc = {
        "user_id": current_user["_id"],
        "title": data.title,
        "subdomain": data.subdomain,
        "custom_domain": None,
        "content": {"projects": [], "about": "", "contact": {}},
        "theme_config": {},
        "is_published": False,
        "created_at": now,
        "updated_at": now,
    }
    result = coll.insert_one(doc)
    doc["_id"] = result.inserted_id
    return SuccessResponse(data=_doc_to_portfolio(doc))


@router.get("/{portfolio_id}", response_model=SuccessResponse[Portfolio])
async def get_portfolio(
    portfolio_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Получить портфолио."""
    doc = _get_own_portfolio(portfolio_id, current_user["_id"])
    return SuccessResponse(data=_doc_to_portfolio(doc))


@router.put("/{portfolio_id}", response_model=SuccessResponse[Portfolio])
async def update_portfolio(
    portfolio_id: str,
    data: PortfolioUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Обновить портфолио."""
    doc = _get_own_portfolio(portfolio_id, current_user["_id"])

    update_fields: dict = {"updated_at": datetime.now(timezone.utc)}
    for field in ("title", "content", "theme_config", "is_published"):
        value = getattr(data, field)
        if value is not None:
            update_fields[field] = value

    # Проверить уникальность subdomain
    if data.subdomain is not None:
        coll = get_portfolios_collection()
        existing = coll.find_one({"subdomain": data.subdomain, "_id": {"$ne": doc["_id"]}})
        if existing:
            raise HTTPException(400, detail="Subdomain already taken")
        update_fields["subdomain"] = data.subdomain

    get_portfolios_collection().update_one(
        {"_id": doc["_id"]},
        {"$set": update_fields},
    )
    updated = get_portfolios_collection().find_one({"_id": doc["_id"]})
    return SuccessResponse(data=_doc_to_portfolio(updated))


@router.delete("/{portfolio_id}", response_model=SuccessResponse[None])
async def delete_portfolio(
    portfolio_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Удалить портфолио."""
    doc = _get_own_portfolio(portfolio_id, current_user["_id"])
    get_portfolios_collection().delete_one({"_id": doc["_id"]})
    return SuccessResponse(data=None)
