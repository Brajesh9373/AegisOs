"""Filesystem connector (SECTION 85/115).

A reference connector that observes a directory tree, emitting one discovered
object per file. It reads content only; it never modifies the filesystem.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from ecms.providers.domain.connector import DiscoveredObject
from ecms.providers.infrastructure.base import BaseConnector

__all__ = ["FilesystemConnector"]


class FilesystemConnector(BaseConnector):
    """Observes files under a root directory and emits UKOs (SECTION 85)."""

    name = "filesystem"
    provider = "filesystem"

    def __init__(self, root: Path, *, pattern: str = "*") -> None:
        """Initialize the connector rooted at ``root`` with a glob ``pattern``."""
        self._root = root.resolve()
        self._pattern = pattern

    async def discover(self) -> list[DiscoveredObject]:
        """Return one discovered object per matching file under the root."""
        return await asyncio.to_thread(self._discover)

    async def collect(self, object_id: str) -> DiscoveredObject | None:
        """Fetch a single file by path, if it lies within the root."""
        return await asyncio.to_thread(self._collect, object_id)

    def _discover(self) -> list[DiscoveredObject]:
        return [
            self._describe(path)
            for path in sorted(self._root.rglob(self._pattern))
            if path.is_file()
        ]

    def _collect(self, object_id: str) -> DiscoveredObject | None:
        path = Path(object_id).resolve()
        if path.is_file() and path.is_relative_to(self._root):
            return self._describe(path)
        return None

    def _describe(self, path: Path) -> DiscoveredObject:
        return DiscoveredObject(
            object_id=str(path),
            object_type="file",
            title=path.name,
            content=path.read_text(encoding="utf-8", errors="ignore"),
            metadata={"suffix": path.suffix, "parent": path.parent.name},
        )
