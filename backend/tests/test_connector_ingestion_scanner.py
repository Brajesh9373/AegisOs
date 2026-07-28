from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from ecms.connectors.ingestion.git_runtime import IngestionCancelledError
from ecms.connectors.ingestion.scanner import ScanLimits, scan_repository


async def test_scanner_yields_chunks_and_ignores_dependencies(tmp_path: Path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "a.py").write_text("a = 1", encoding="utf-8")
    (tmp_path / "src" / "b.py").write_text("b = 2", encoding="utf-8")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "large.js").write_text("ignored", encoding="utf-8")

    chunks = [
        chunk
        async for chunk in scan_repository(
            tmp_path,
            limits=ScanLimits(chunk_size=1),
            cancel=asyncio.Event(),
        )
    ]

    assert [[item.relative_path for item in chunk] for chunk in chunks] == [
        ["src/a.py"],
        ["src/b.py"],
    ]


async def test_scanner_stops_when_cancelled(tmp_path: Path) -> None:
    (tmp_path / "file.py").write_text("content", encoding="utf-8")
    cancel = asyncio.Event()
    cancel.set()

    with pytest.raises(IngestionCancelledError):
        async for _ in scan_repository(
            tmp_path, limits=ScanLimits(), cancel=cancel
        ):
            pass


async def test_scanner_enforces_total_bytes(tmp_path: Path) -> None:
    (tmp_path / "file.py").write_text("content", encoding="utf-8")

    with pytest.raises(RuntimeError, match="scannable bytes"):
        async for _ in scan_repository(
            tmp_path,
            limits=ScanLimits(max_total_bytes=2),
            cancel=asyncio.Event(),
        ):
            pass


async def test_scanner_rejects_binary_content_even_with_text_extension(
    tmp_path: Path,
) -> None:
    (tmp_path / "binary.ts").write_bytes(b"prefix\x00suffix")
    (tmp_path / "invalid.ts").write_bytes(b"\xff\xfe\xfa")
    (tmp_path / "image.webp").write_bytes(b"RIFFbinary")

    chunks = [
        chunk
        async for chunk in scan_repository(
            tmp_path,
            limits=ScanLimits(),
            cancel=asyncio.Event(),
        )
    ]

    assert chunks == []
