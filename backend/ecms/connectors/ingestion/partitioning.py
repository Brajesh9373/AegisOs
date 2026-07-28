"""Deterministic weighted partitioning for repository manifests."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass

from ecms.connectors.ingestion.manifest import ManifestEntry, RepositoryManifest

EntryWeight = Callable[[ManifestEntry], int]


@dataclass(frozen=True, slots=True)
class ManifestPartition:
    """A disjoint, content-addressed unit of manifest work."""

    index: int
    entries: tuple[ManifestEntry, ...]
    total_weight: int
    checksum: str


def partition_manifest(
    manifest: RepositoryManifest,
    partition_count: int,
    *,
    weight: EntryWeight | None = None,
) -> tuple[ManifestPartition, ...]:
    """Assign every manifest entry once using deterministic greedy balancing.

    Largest files are assigned first to the currently lightest partition. Stable
    path and partition-index tie breakers make the result reproducible across
    processes and independent of source discovery order.
    """
    if partition_count <= 0:
        raise ValueError("partition_count must be positive")
    weight_of = weight or _byte_weight
    weighted_entries: list[tuple[ManifestEntry, int]] = []
    for entry in manifest.entries:
        entry_weight = weight_of(entry)
        if isinstance(entry_weight, bool) or not isinstance(entry_weight, int):
            raise TypeError("entry weight must be an integer")
        if entry_weight <= 0:
            raise ValueError("entry weight must be positive")
        weighted_entries.append((entry, entry_weight))

    assignments: list[list[ManifestEntry]] = [[] for _ in range(partition_count)]
    totals = [0] * partition_count
    for entry, entry_weight in sorted(
        weighted_entries,
        key=lambda item: (-item[1], item[0].relative_path, item[0].content_hash),
    ):
        target = min(range(partition_count), key=lambda index: (totals[index], index))
        assignments[target].append(entry)
        totals[target] += entry_weight

    return tuple(
        _build_partition(
            index=index,
            entries=tuple(sorted(entries, key=lambda entry: entry.relative_path)),
            total_weight=totals[index],
            manifest_checksum=manifest.checksum,
        )
        for index, entries in enumerate(assignments)
    )


def validate_partition_coverage(
    manifest: RepositoryManifest,
    partitions: tuple[ManifestPartition, ...],
) -> None:
    """Raise if partitions overlap, omit entries, or reference foreign entries."""
    expected = [(entry.relative_path, entry.checksum) for entry in manifest.entries]
    actual = [
        (entry.relative_path, entry.checksum)
        for partition in partitions
        for entry in partition.entries
    ]
    if len(actual) != len(set(actual)):
        raise ValueError("partitions contain overlapping manifest entries")
    if sorted(actual) != sorted(expected):
        raise ValueError("partitions do not exactly cover the manifest")


def _byte_weight(entry: ManifestEntry) -> int:
    return max(1, entry.size_bytes)


def _build_partition(
    *,
    index: int,
    entries: tuple[ManifestEntry, ...],
    total_weight: int,
    manifest_checksum: str,
) -> ManifestPartition:
    payload = {
        "manifest_checksum": manifest_checksum,
        "partition_index": index,
        "entries": [entry.checksum for entry in entries],
        "total_weight": total_weight,
    }
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return ManifestPartition(
        index=index,
        entries=entries,
        total_weight=total_weight,
        checksum=hashlib.sha256(serialized).hexdigest(),
    )
