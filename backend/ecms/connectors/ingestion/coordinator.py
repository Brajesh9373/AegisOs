"""Clone-once manifest planning for partitioned connector ingestion."""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path

from ecms.connectors.ingestion.git_runtime import IngestionCancelledError
from ecms.connectors.ingestion.manifest import (
    ManifestEntry,
    ManifestSource,
    RepositoryManifest,
    create_manifest_entry,
    manifest_checksum,
)
from ecms.connectors.ingestion.partitioning import (
    ManifestPartition,
    partition_manifest,
    validate_partition_coverage,
)
from ecms.connectors.ingestion.scanner import (
    IGNORED_DIRECTORIES,
    IGNORED_EXTENSIONS,
    ScanLimits,
)


@dataclass(frozen=True, slots=True)
class IngestionPlan:
    """One reproducible manifest and its disjoint extraction partitions."""

    manifest: RepositoryManifest
    partitions: tuple[ManifestPartition, ...]


async def plan_repository(
    root: Path,
    *,
    limits: ScanLimits,
    partition_count: int,
    cancel: asyncio.Event,
) -> IngestionPlan:
    """Read an acquired revision once and create deterministic partition work.

    Only manifest metadata is retained. File contents are released after their
    hashes are calculated and extraction workers later reopen their assigned
    paths from the immutable, read-only revision directory.
    """
    entries: list[ManifestEntry] = []
    discovered = 0
    total_bytes = 0
    resolved_root = await asyncio.to_thread(root.resolve)

    for directory, directories, files in os.walk(resolved_root):
        directories[:] = sorted(item for item in directories if item not in IGNORED_DIRECTORIES)
        for filename in sorted(files):
            if cancel.is_set():
                raise IngestionCancelledError("repository manifest cancelled")
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
                content = await asyncio.to_thread(path.read_bytes)
            except OSError:
                continue
            if b"\x00" in content:
                continue
            entries.append(
                create_manifest_entry(
                    ManifestSource(
                        relative_path=path.relative_to(resolved_root).as_posix(),
                        content=content,
                    )
                )
            )
            del content
            # Yield between files so cancellation and API work are not starved.
            await asyncio.sleep(0)

    ordered_entries = tuple(sorted(entries, key=lambda entry: entry.relative_path))
    manifest = RepositoryManifest(
        entries=ordered_entries,
        checksum=manifest_checksum(ordered_entries),
        total_bytes=sum(entry.size_bytes for entry in ordered_entries),
    )
    partitions = partition_manifest(manifest, partition_count)
    validate_partition_coverage(manifest, partitions)
    return IngestionPlan(manifest=manifest, partitions=partitions)
