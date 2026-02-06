"""
S3 / MinIO клиент для загрузки файлов.
Генерация presigned URL для клиентской загрузки.
"""
import boto3
from botocore.config import Config

from app.core.config import settings

_s3_client = None


def get_s3_client():
    """Вернуть S3 клиент (singleton)."""
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT or None,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
            config=Config(signature_version="s3v4"),
        )
    return _s3_client


def generate_presigned_upload_url(
    key: str,
    content_type: str = "application/octet-stream",
    expires_in: int = 300,
) -> str:
    """Сгенерировать presigned URL для PUT загрузки (5 мин по умолчанию)."""
    client = get_s3_client()
    return client.generate_presigned_url(
        "put_object",
        Params={
            "Bucket": settings.S3_BUCKET,
            "Key": key,
            "ContentType": content_type,
        },
        ExpiresIn=expires_in,
    )
