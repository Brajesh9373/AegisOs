"""In-memory object store and port (SECTION 106)."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable

from ecms.shared.exceptions import NotFoundError

__all__ = ["InMemoryObjectStore", "ObjectInfo", "ObjectStore"]


@dataclass(frozen=True)
class ObjectInfo:
    """Metadata needed for immutable HTTP delivery."""

    key: str
    size: int
    content_type: str
    etag: str | None = None


@runtime_checkable
class ObjectStore(Protocol):
    """A binary object store.

    Operations:
        put_object: Store bytes under a key.
        get_object: Retrieve bytes by key.
        delete_object: Remove an object.
        list_objects: List keys under a prefix.
    """

    async def put_object(self, key: str, data: bytes) -> None: ...
    async def get_object(self, key: str) -> bytes: ...
    async def delete_object(self, key: str) -> None: ...
    async def list_objects(self, prefix: str = "") -> list[str]: ...
    async def put_file(
        self, key: str, path: Path, *, content_type: str = "application/octet-stream"
    ) -> None: ...
    async def stat_object(self, key: str) -> ObjectInfo: ...
    def iter_object(
        self,
        key: str,
        *,
        chunk_size: int = 1024 * 1024,
        start: int = 0,
        end: int | None = None,
    ) -> AsyncIterator[bytes]: ...
    async def ensure_bucket(self) -> None: ...
    def presign_get(self, key: str, *, expires_seconds: int = 300) -> str | None: ...


class InMemoryObjectStore:
    """In-memory object store for development and tests."""

    def __init__(self) -> None:
        """Initialize an empty object store."""
        self._objects: dict[str, bytes] = {}
        self._content_types: dict[str, str] = {}

    async def put_object(self, key: str, data: bytes) -> None:
        """Store bytes under a key."""
        self._objects[key] = data

    async def get_object(self, key: str) -> bytes:
        """Retrieve an object's bytes.

        Raises:
            NotFoundError: If the object does not exist.
        """
        if key not in self._objects:
            raise NotFoundError(f"object not found: {key}")
        return self._objects[key]

    async def delete_object(self, key: str) -> None:
        """Remove an object."""
        self._objects.pop(key, None)
        self._content_types.pop(key, None)

    async def list_objects(self, prefix: str = "") -> list[str]:
        """List keys under a prefix, sorted."""
        return sorted(key for key in self._objects if key.startswith(prefix))

    async def put_file(
        self,
        key: str,
        path: Path,
        *,
        content_type: str = "application/octet-stream",
    ) -> None:
        """Store a file without requiring callers to materialize it as bytes."""
        self._objects[key] = await asyncio.to_thread(path.read_bytes)
        self._content_types[key] = content_type

    async def stat_object(self, key: str) -> ObjectInfo:
        """Return immutable object metadata."""
        data = await self.get_object(key)
        return ObjectInfo(
            key=key,
            size=len(data),
            content_type=self._content_types.get(key, "application/octet-stream"),
        )

    async def iter_object(
        self,
        key: str,
        *,
        chunk_size: int = 1024 * 1024,
        start: int = 0,
        end: int | None = None,
    ) -> AsyncIterator[bytes]:
        """Yield bounded chunks from an in-memory object."""
        data = await self.get_object(key)
        stop = len(data) if end is None else min(end + 1, len(data))
        for offset in range(start, stop, chunk_size):
            yield data[offset : min(offset + chunk_size, stop)]

    async def ensure_bucket(self) -> None:
        """In-memory storage is always ready."""

    def presign_get(self, key: str, *, expires_seconds: int = 300) -> str | None:
        """In-memory storage has no browser-reachable signed endpoint."""
        return None
