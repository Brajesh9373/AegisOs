from __future__ import annotations

from datetime import UTC, datetime

import pytest
from fastapi import HTTPException

from ecms.api.rest.knowledge_graph_snapshots import _parse_range, _snapshot_manifest
from ecms.persistence.models.knowledge_graph_snapshot import KnowledgeGraphSnapshot


def _ready_snapshot() -> KnowledgeGraphSnapshot:
    return KnowledgeGraphSnapshot(
        id="snapshot-1",
        organization_id="default",
        version="v1",
        state="ready",
        is_current=True,
        points_object_key="default/v1/points.arrow",
        links_object_key="default/v1/links.arrow",
        points_checksum="a" * 64,
        links_checksum="b" * 64,
        point_count=10,
        link_count=20,
        points_bytes=100,
        links_bytes=200,
        completed_at=datetime(2026, 7, 28, tzinfo=UTC),
    )


def test_manifest_keeps_last_good_while_new_build_is_running() -> None:
    current = _ready_snapshot()
    building = KnowledgeGraphSnapshot(
        id="snapshot-2",
        organization_id="default",
        version="v2",
        state="building",
        is_current=False,
    )

    manifest = _snapshot_manifest(current, building)

    assert manifest["state"] == "building"
    assert manifest["stale"] is True
    assert manifest["snapshot"]["version"] == "v1"
    assert manifest["snapshot"]["points_url"].endswith("/v1/points")
    assert manifest["snapshot"]["capacity"] == {
        "supported": True,
        "max_nodes": 100_000,
        "max_links": 200_000,
    }


@pytest.mark.parametrize(
    ("header", "expected"),
    [
        (None, None),
        ("bytes=0-99", (0, 99)),
        ("bytes=50-", (50, 199)),
        ("bytes=190-300", (190, 199)),
    ],
)
def test_parse_supported_ranges(
    header: str | None,
    expected: tuple[int, int] | None,
) -> None:
    assert _parse_range(header, 200) == expected


@pytest.mark.parametrize("header", ["bytes=-10", "items=0-1", "bytes=300-400", "bytes=x-y"])
def test_rejects_unsupported_ranges(header: str) -> None:
    with pytest.raises(HTTPException) as exc_info:
        _parse_range(header, 200)
    assert exc_info.value.status_code == 416
