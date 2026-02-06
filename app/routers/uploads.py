"""
Загрузка файлов через S3 presigned URL.
"""
import uuid

from fastapi import APIRouter, Depends, HTTPException

from app.core.config import settings
from app.core.security import get_current_user
from app.core.storage import generate_presigned_upload_url
from app.schemas.common import SuccessResponse
from app.schemas.upload import PresignedUrlRequest, PresignedUrlResponse

router = APIRouter(prefix="/uploads", tags=["uploads"])

ALLOWED_UPLOAD_TYPES = {"avatar", "screenshot", "pdf"}


@router.post("presigned-url", response_model=SuccessResponse[PresignedUrlResponse])
async def get_presigned_url(
    data: PresignedUrlRequest,
    current_user: dict = Depends(get_current_user),
):
    """Сгенерировать presigned URL для клиентской загрузки в S3."""
    if not settings.S3_ACCESS_KEY:
        raise HTTPException(501, detail="S3 storage not configured")

    if data.upload_type not in ALLOWED_UPLOAD_TYPES:
        raise HTTPException(400, detail=f"upload_type must be one of: {', '.join(ALLOWED_UPLOAD_TYPES)}")

    # Генерируем уникальный ключ: uploads/{type}/{user_id}/{uuid}.{ext}
    user_id = str(current_user["_id"])
    ext = data.file_name.rsplit(".", 1)[-1] if "." in data.file_name else "bin"
    file_key = f"uploads/{data.upload_type}/{user_id}/{uuid.uuid4().hex}.{ext}"

    upload_url = generate_presigned_upload_url(
        key=file_key,
        content_type=data.content_type,
    )

    return SuccessResponse(
        data=PresignedUrlResponse(upload_url=upload_url, file_key=file_key)
    )
