from __future__ import annotations

from dataclasses import replace

import pytest

from ecms.connectors.ingestion.manifest import ManifestSource, build_manifest
from ecms.connectors.ingestion.partitioning import (
    partition_manifest,
    validate_partition_coverage,
)


def _manifest():
    return build_manifest(
        [
            ManifestSource("large.py", b"x" * 100),
            ManifestSource("medium.py", b"x" * 60),
            ManifestSource("small-a.py", b"x" * 20),
            ManifestSource("small-b.py", b"x" * 20),
            ManifestSource("tiny.py", b"x"),
        ]
    )


def test_partitioning_is_deterministic_balanced_and_complete() -> None:
    manifest = _manifest()

    first = partition_manifest(manifest, 3)
    second = partition_manifest(manifest, 3)

    assert first == second
    assert [partition.total_weight for partition in first] == [100, 60, 41]
    validate_partition_coverage(manifest, first)
    assigned = [entry.relative_path for partition in first for entry in partition.entries]
    assert sorted(assigned) == sorted(entry.relative_path for entry in manifest.entries)


def test_partitioning_has_stable_tie_breakers() -> None:
    manifest = build_manifest(
        [
            ManifestSource("c.py", b"x"),
            ManifestSource("a.py", b"x"),
            ManifestSource("b.py", b"x"),
        ]
    )

    partitions = partition_manifest(manifest, 2)

    assert [[entry.relative_path for entry in item.entries] for item in partitions] == [
        ["a.py", "c.py"],
        ["b.py"],
    ]


def test_partitioning_can_represent_idle_workers() -> None:
    manifest = build_manifest([ManifestSource("only.py", b"x")])

    partitions = partition_manifest(manifest, 3)

    assert len(partitions) == 3
    assert [len(partition.entries) for partition in partitions] == [1, 0, 0]
    assert len({partition.checksum for partition in partitions}) == 3
    validate_partition_coverage(manifest, partitions)


def test_partition_validation_detects_overlap_and_omission() -> None:
    manifest = _manifest()
    partitions = partition_manifest(manifest, 2)
    overlap = (
        partitions[0],
        replace(
            partitions[1],
            entries=(*partitions[1].entries, partitions[0].entries[0]),
        ),
    )

    with pytest.raises(ValueError, match="overlapping"):
        validate_partition_coverage(manifest, overlap)
    with pytest.raises(ValueError, match="exactly cover"):
        validate_partition_coverage(manifest, partitions[:1])


@pytest.mark.parametrize("count", [0, -1])
def test_partitioning_rejects_invalid_partition_count(count: int) -> None:
    with pytest.raises(ValueError, match="positive"):
        partition_manifest(_manifest(), count)


def test_partitioning_rejects_invalid_custom_weights() -> None:
    with pytest.raises(ValueError, match="positive"):
        partition_manifest(_manifest(), 2, weight=lambda _entry: 0)
    with pytest.raises(TypeError, match="integer"):
        partition_manifest(_manifest(), 2, weight=lambda _entry: 1.5)  # type: ignore[return-value]
