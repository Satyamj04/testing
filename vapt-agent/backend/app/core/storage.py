"""
MinIO / S3-compatible object storage client.
"""
import io
from typing import Optional
import structlog
from minio import Minio
from minio.error import S3Error

from app.core.config import settings

logger = structlog.get_logger(__name__)


class StorageClient:
    """Async-friendly wrapper around MinIO client."""

    def __init__(self):
        self._client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
        self.buckets = [
            settings.MINIO_BUCKET_EVIDENCE,
            settings.MINIO_BUCKET_REPORTS,
        ]

    async def initialize_buckets(self):
        """Create required buckets if they don't exist."""
        for bucket in self.buckets:
            try:
                if not self._client.bucket_exists(bucket):
                    self._client.make_bucket(bucket)
                    logger.info("bucket_created", bucket=bucket)
            except S3Error as e:
                logger.error("bucket_create_failed", bucket=bucket, error=str(e))

    def put_object(self, bucket: str, object_name: str, data: bytes, content_type: str = "application/octet-stream") -> str:
        """Upload bytes and return the object path."""
        self._client.put_object(
            bucket,
            object_name,
            io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        return f"{bucket}/{object_name}"

    def get_object(self, bucket: str, object_name: str) -> Optional[bytes]:
        """Download object bytes."""
        try:
            response = self._client.get_object(bucket, object_name)
            return response.read()
        except S3Error:
            return None

    def get_presigned_url(self, bucket: str, object_name: str, expires_hours: int = 1) -> str:
        """Generate a presigned URL for temporary access."""
        from datetime import timedelta
        return self._client.presigned_get_object(
            bucket, object_name, expires=timedelta(hours=expires_hours)
        )

    def delete_object(self, bucket: str, object_name: str):
        try:
            self._client.remove_object(bucket, object_name)
        except S3Error as e:
            logger.warning("object_delete_failed", error=str(e))


storage_client = StorageClient()
