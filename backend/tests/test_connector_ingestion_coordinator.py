from __future__ import annotations

import asyncio

import pytest

from ecms.connectors.ingestion.coordinator import plan_repository
from ecms.connectors.ingestion.git_runtime import IngestionCancelledError
from ecms.connectors.ingestion.scanner import ScanLimits


async def test_plan_repository_is_reproducible_and_exact(tmp_path) -> None:
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "large.py").write_text("x = 1\n" * 100)
    (tmp_path / "small.ts").write_text("export const x = 1\n")
    (tmp_path / "README.md").write_text("# Repo\n")

    kwargs = {
        "limits": ScanLimits(max_files=10, max_total_bytes=100_000),
        "partition_count": 2,
        "cancel": asyncio.Event(),
    }
    first = await plan_repository(tmp_path, **kwargs)
    second = await plan_repository(tmp_path, **kwargs)

    assert first == second
    assert len(first.partitions) == 2
    paths = [entry.relative_path for partition in first.partitions for entry in partition.entries]
    assert sorted(paths) == ["README.md", "small.ts", "src/large.py"]
    assert len(paths) == len(set(paths))


async def test_plan_repository_obeys_limits(tmp_path) -> None:
    (tmp_path / "one.py").write_text("one")
    (tmp_path / "two.py").write_text("two")

    with pytest.raises(RuntimeError, match="exceeds 1 files"):
        await plan_repository(
            tmp_path,
            limits=ScanLimits(max_files=1),
            partition_count=2,
            cancel=asyncio.Event(),
        )


async def test_plan_repository_honours_cancellation(tmp_path) -> None:
    (tmp_path / "one.py").write_text("one")
    cancel = asyncio.Event()
    cancel.set()

    with pytest.raises(IngestionCancelledError):
        await plan_repository(
            tmp_path,
            limits=ScanLimits(),
            partition_count=1,
            cancel=cancel,
        )
