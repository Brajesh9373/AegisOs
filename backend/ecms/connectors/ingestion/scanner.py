"""Streaming, bounded repository file discovery."""

from __future__ import annotations

import asyncio
import os
from collections.abc import AsyncIterator
from dataclasses import dataclass
from pathlib import Path

from ecms.connectors.ingestion.git_runtime import IngestionCancelledError

IGNORED_DIRECTORIES = frozenset(
    {".git", ".next", ".venv", "__pycache__", "build", "dist", "node_modules", "venv"}
)
IGNORED_EXTENSIONS = frozenset(
    {
        ".avi",
        ".class",
        ".dll",
        ".eot",
        ".exe",
        ".gif",
        ".gz",
        ".ico",
        ".jar",
        ".jpeg",
        ".jpg",
        ".mov",
        ".mp3",
        ".mp4",
        ".o",
        ".png",
        ".pyc",
        ".pyo",
        ".so",
        ".svg",
        ".tar",
        ".ttf",
        ".war",
        ".webp",
        ".woff",
        ".woff2",
        ".zip",
    }
)


@dataclass(frozen=True)
class ScanLimits:
    """Hard resource ceilings for a single repository scan."""

    chunk_size: int = 100
    max_files: int = 250_000
    max_file_bytes: int = 2 * 1024 * 1024
    max_total_bytes: int = 2 * 1024 * 1024 * 1024


@dataclass(frozen=True)
class ScannedFile:
    """One decoded source file ready for normalization."""

    relative_path: str
    content: str
    size_bytes: int


async def scan_repository(
    root: Path,
    *,
    limits: ScanLimits,
    cancel: asyncio.Event,
) -> AsyncIterator[list[ScannedFile]]:
    """Yield bounded chunks without materializing the repository in memory."""
    chunk: list[ScannedFile] = []
    discovered = 0
    total_bytes = 0
    for directory, directories, files in os.walk(root):
        directories[:] = sorted(item for item in directories if item not in IGNORED_DIRECTORIES)
        for filename in sorted(files):
            if cancel.is_set():
                raise IngestionCancelledError("repository scan cancelled")
            path = Path(directory) / filename
            if path.suffix.lower() in IGNORED_EXTENSIONS:
                continue
            try:
                size = path.stat().st_size
            except OSError:
                continue
            if size == 0 or size > limits.max_file_bytes:
                continue
            discovered += 1
            total_bytes += size
            if discovered > limits.max_files:
                raise RuntimeError(f"repository exceeds {limits.max_files} files")
            if total_bytes > limits.max_total_bytes:
                raise RuntimeError(f"repository exceeds {limits.max_total_bytes} scannable bytes")
            try:
                payload = await asyncio.to_thread(path.read_bytes)
                if b"\x00" in payload:
                    continue
                content = payload.decode("utf-8", errors="strict")
            except (OSError, UnicodeDecodeError):
                continue
            if not content.strip():
                continue
            chunk.append(ScannedFile(path.relative_to(root).as_posix(), content, size))
            if len(chunk) >= limits.chunk_size:
                yield chunk
                chunk = []
                await asyncio.sleep(0)
    if chunk:
        yield chunk
