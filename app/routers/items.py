"""
CRUD для ресурса items.

Роутер принимает запрос, вызывает БД (или сервис), возвращает структурированный ответ.
Конвертация doc ↔ Pydantic — здесь или в сервисе.
"""
from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, HTTPException

from app.core.database import get_items_collection
from app.schemas.common import SuccessResponse
from app.schemas.item import Item, ItemCreate

router = APIRouter(prefix="/items", tags=["items"])


def _doc_to_item(doc: dict) -> Item:
    """Документ из Mongo → Pydantic. _id → id (строка)."""
    return Item(
        id=str(doc["_id"]),
        name=doc["name"],
        description=doc.get("description") or "",
        price=doc["price"],
    )


@router.post("", response_model=SuccessResponse[Item])
def create(item: ItemCreate):
    """Create: добавить запись в коллекцию."""
    coll = get_items_collection()
    body = item.model_dump()
    result = coll.insert_one(body)
    doc = coll.find_one({"_id": result.inserted_id})
    return SuccessResponse(data=_doc_to_item(doc))


@router.get("", response_model=SuccessResponse[list[Item]])
def list_items():
    """Read: список всех записей."""
    coll = get_items_collection()
    data = [_doc_to_item(doc) for doc in coll.find()]
    return SuccessResponse(data=data)


@router.get("/{item_id}", response_model=SuccessResponse[Item])
def get_item(item_id: str):
    """Read: одна запись по id."""
    try:
        oid = ObjectId(item_id)
    except InvalidId:
        raise HTTPException(404, detail={"error": "not_found", "message": "Item not found"})
    coll = get_items_collection()
    doc = coll.find_one({"_id": oid})
    if not doc:
        raise HTTPException(404, detail={"error": "not_found", "message": "Item not found"})
    return SuccessResponse(data=_doc_to_item(doc))


@router.put("/{item_id}", response_model=SuccessResponse[Item])
def update(item_id: str, item: ItemCreate):
    """Update: обновить запись по id."""
    try:
        oid = ObjectId(item_id)
    except InvalidId:
        raise HTTPException(404, detail={"error": "not_found", "message": "Item not found"})
    coll = get_items_collection()
    result = coll.update_one(
        {"_id": oid},
        {"$set": item.model_dump()},
    )
    if result.matched_count == 0:
        raise HTTPException(404, detail={"error": "not_found", "message": "Item not found"})
    doc = coll.find_one({"_id": oid})
    return SuccessResponse(data=_doc_to_item(doc))


@router.delete("/{item_id}", response_model=SuccessResponse[None])
def delete(item_id: str):
    """Delete: удалить запись по id."""
    try:
        oid = ObjectId(item_id)
    except InvalidId:
        raise HTTPException(404, detail={"error": "not_found", "message": "Item not found"})
    coll = get_items_collection()
    result = coll.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(404, detail={"error": "not_found", "message": "Item not found"})
    return SuccessResponse(data=None)
