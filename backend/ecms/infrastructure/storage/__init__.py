"""Object/blob storage adapters (S3/MinIO)."""

from ecms.infrastructure.storage.object_store import InMemoryObjectStore, ObjectStore
from ecms.infrastructure.storage.s3 import S3ObjectStore

__all__ = ["InMemoryObjectStore", "ObjectStore", "S3ObjectStore"]
