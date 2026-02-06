"""
Схемы для загрузки файлов.
"""
from pydantic import BaseModel, Field


class PresignedUrlRequest(BaseModel):
    """Запрос на генерацию presigned URL."""

    file_name: str = Field(min_length=1)
    content_type: str = "image/png"
    upload_type: str = Field(description="avatar | screenshot | pdf")


class PresignedUrlResponse(BaseModel):
    """Ответ с presigned URL."""

    upload_url: str
    file_key: str
