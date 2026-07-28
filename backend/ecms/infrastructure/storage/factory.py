"""Object-store construction from typed application settings."""

from __future__ import annotations

from ecms.configuration.schemas.settings import AppSettings
from ecms.infrastructure.storage.s3 import S3ObjectStore

__all__ = ["create_snapshot_object_store"]


def create_snapshot_object_store(settings: AppSettings) -> S3ObjectStore:
    """Create the S3/MinIO adapter used for immutable graph snapshots."""
    return S3ObjectStore(
        bucket=settings.s3_bucket,
        endpoint_url=settings.s3_endpoint_url,
        public_endpoint_url=settings.s3_public_endpoint_url,
        region=settings.s3_region,
        access_key=settings.s3_access_key,
        secret_key=settings.s3_secret_key,
    )
