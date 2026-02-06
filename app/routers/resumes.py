"""
CRUD для резюме. Все эндпоинты защищены JWT.
Пользователь видит/редактирует только свои резюме.
Soft delete: DELETE ставит deleted_at, не удаляет документ.
"""
from copy import deepcopy
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from fastapi import APIRouter, Depends, HTTPException, Query

from app.core.database import get_resumes_collection
from app.core.security import get_current_user
from app.schemas.common import ErrorResponse, SuccessResponse
from app.schemas.resume import Resume, ResumeCreate, ResumeUpdate

router = APIRouter(prefix="/resumes", tags=["resumes"])


def _doc_to_resume(doc: dict) -> Resume:
    return Resume(
        id=str(doc["_id"]),
        user_id=str(doc["user_id"]),
        title=doc["title"],
        content=doc.get("content", {}),
        theme_config=doc.get("theme_config", {}),
        thumbnail_url=doc.get("thumbnail_url"),
        is_public=doc.get("is_public", False),
        slug=doc.get("slug"),
        created_at=doc["created_at"],
        updated_at=doc["updated_at"],
    )


def _get_own_resume(resume_id: str, user_id: ObjectId) -> dict:
    """Получить резюме, проверив владельца. 404 если не найдено или чужое."""
    try:
        oid = ObjectId(resume_id)
    except InvalidId:
        raise HTTPException(404, detail="Resume not found")

    doc = get_resumes_collection().find_one(
        {"_id": oid, "user_id": user_id, "deleted_at": None}
    )
    if not doc:
        raise HTTPException(404, detail="Resume not found")
    return doc


@router.get("", response_model=SuccessResponse[list[Resume]])
async def list_resumes(
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_current_user),
):
    """Список резюме текущего пользователя (pagination)."""
    coll = get_resumes_collection()
    cursor = (
        coll.find({"user_id": current_user["_id"], "deleted_at": None})
        .sort("created_at", -1)
        .skip(offset)
        .limit(limit)
    )
    data = [_doc_to_resume(doc) for doc in cursor]
    return SuccessResponse(data=data)


@router.post(
    "",
    response_model=SuccessResponse[Resume],
    status_code=201,
    responses={400: {"model": ErrorResponse}},
)
async def create_resume(
    data: ResumeCreate,
    current_user: dict = Depends(get_current_user),
):
    """Создать новое резюме."""
    now = datetime.now(timezone.utc)
    doc = {
        "user_id": current_user["_id"],
        "title": data.title,
        "content": {},
        "theme_config": {"template_id": data.template_id} if data.template_id else {},
        "thumbnail_url": None,
        "is_public": False,
        "slug": None,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None,
    }
    coll = get_resumes_collection()
    result = coll.insert_one(doc)
    doc["_id"] = result.inserted_id
    return SuccessResponse(data=_doc_to_resume(doc))


@router.get("/{resume_id}", response_model=SuccessResponse[Resume])
async def get_resume(
    resume_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Получить конкретное резюме."""
    doc = _get_own_resume(resume_id, current_user["_id"])
    return SuccessResponse(data=_doc_to_resume(doc))


@router.put("/{resume_id}", response_model=SuccessResponse[Resume])
async def update_resume(
    resume_id: str,
    data: ResumeUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Обновить резюме (content, theme_config, title, slug, is_public)."""
    doc = _get_own_resume(resume_id, current_user["_id"])

    update_fields: dict = {"updated_at": datetime.now(timezone.utc)}
    for field in ("title", "content", "theme_config", "is_public", "slug"):
        value = getattr(data, field)
        if value is not None:
            update_fields[field] = value

    # Проверить уникальность slug
    if data.slug is not None:
        coll = get_resumes_collection()
        existing = coll.find_one({"slug": data.slug, "_id": {"$ne": doc["_id"]}})
        if existing:
            raise HTTPException(400, detail="Slug already taken")

    get_resumes_collection().update_one(
        {"_id": doc["_id"]},
        {"$set": update_fields},
    )
    updated = get_resumes_collection().find_one({"_id": doc["_id"]})
    return SuccessResponse(data=_doc_to_resume(updated))


@router.delete("/{resume_id}", response_model=SuccessResponse[None])
async def delete_resume(
    resume_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Soft delete: ставит deleted_at."""
    doc = _get_own_resume(resume_id, current_user["_id"])
    get_resumes_collection().update_one(
        {"_id": doc["_id"]},
        {"$set": {"deleted_at": datetime.now(timezone.utc)}},
    )
    return SuccessResponse(data=None)


@router.post(
    "/{resume_id}/duplicate",
    response_model=SuccessResponse[Resume],
    status_code=201,
)
async def duplicate_resume(
    resume_id: str,
    current_user: dict = Depends(get_current_user),
):
    """Клонировать резюме."""
    doc = _get_own_resume(resume_id, current_user["_id"])

    now = datetime.now(timezone.utc)
    new_doc = {
        "user_id": current_user["_id"],
        "title": f"{doc['title']} (copy)",
        "content": deepcopy(doc.get("content", {})),
        "theme_config": deepcopy(doc.get("theme_config", {})),
        "thumbnail_url": None,
        "is_public": False,
        "slug": None,
        "created_at": now,
        "updated_at": now,
        "deleted_at": None,
    }
    coll = get_resumes_collection()
    result = coll.insert_one(new_doc)
    new_doc["_id"] = result.inserted_id
    return SuccessResponse(data=_doc_to_resume(new_doc))
