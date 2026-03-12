"""R2/S3-compatible object storage for generated files."""

import logging
import os
from typing import Optional

import boto3
from botocore.config import Config

logger = logging.getLogger(__name__)


class StorageService:
    """Upload and delete files from R2 (S3-compatible) storage."""

    def __init__(
        self, endpoint_url: str, access_key_id: str, secret_access_key: str, bucket_name: str, public_url: str
    ):
        self.bucket_name = bucket_name
        self.public_url = public_url.rstrip("/")
        self._client = boto3.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=access_key_id,
            aws_secret_access_key=secret_access_key,
            config=Config(signature_version="s3v4"),
            region_name="auto",
        )

    def upload_file(self, local_path: str, key: str) -> str:
        """Upload a local file to R2 and return the public URL."""
        content_types = {
            ".mid": "audio/midi",
            ".wav": "audio/wav",
            ".mp3": "audio/mpeg",
        }
        ext = os.path.splitext(local_path)[1].lower()
        content_type = content_types.get(ext, "application/octet-stream")

        self._client.upload_file(
            local_path,
            self.bucket_name,
            key,
            ExtraArgs={"ContentType": content_type},
        )
        url = f"{self.public_url}/{key}"
        logger.info(f"Uploaded {key} to R2 ({os.path.getsize(local_path)} bytes)")
        return url

    def delete_file(self, key: str) -> None:
        """Delete a file from R2."""
        self._client.delete_object(Bucket=self.bucket_name, Key=key)
        logger.info(f"Deleted {key} from R2")


_instance: Optional[StorageService] = None


def get_storage(settings) -> Optional[StorageService]:
    """Get or create the StorageService singleton. Returns None if R2 is not configured."""
    global _instance
    if _instance is not None:
        return _instance
    if not settings.r2_enabled:
        return None
    _instance = StorageService(
        endpoint_url=settings.r2_endpoint_url,
        access_key_id=settings.r2_access_key_id,
        secret_access_key=settings.r2_secret_access_key,
        bucket_name=settings.r2_bucket_name,
        public_url=settings.r2_public_url,
    )
    return _instance
