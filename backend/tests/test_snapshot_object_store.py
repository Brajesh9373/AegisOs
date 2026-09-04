from __future__ import annotations

from pathlib import Path

import pytest

from ecms.infrastructure.storage.object_store import InMemoryObjectStore


@pytest.mark.asyncio
async def test_snapshot_object_store_streams_bounded_chunks(tmp_path: Path) -> None:
    source = tmp_path / "snapshot.arrow"
    source.write_bytes(b"0123456789")
    store = InMemoryObjectStore()

    await store.put_file(
        "org/v1/points.arrow",
        source,
        content_type="application/vnd.apache.arrow.file",
    )
    info = await store.stat_object("org/v1/points.arrow")
    chunks = [chunk async for chunk in store.iter_object("org/v1/points.arrow", chunk_size=4)]

    assert info.size == 10
    assert info.content_type == "application/vnd.apache.arrow.file"
    assert chunks == [b"0123", b"4567", b"89"]
