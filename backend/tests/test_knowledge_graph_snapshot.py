from __future__ import annotations

import hashlib

import pyarrow.ipc as ipc
import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ecms.persistence.models.knowledge_graph_snapshot import KnowledgeGraphSnapshot
from ecms.persistence.repositories.knowledge_graph_snapshot import (
    KnowledgeGraphSnapshotRepository,
)
from ecms.visualization.knowledge_graph_snapshot import (
    LINKS_SCHEMA,
    POINTS_SCHEMA,
    build_arrow_artifacts,
    read_and_validate_artifact,
)


def test_arrow_snapshot_is_deterministic_and_referentially_valid() -> None:
    nodes = [
        {"id": "b", "label": "Beta", "group": "file", "source_group": "connection:1"},
        {"id": "a", "label": "Alpha", "group": "file", "source_group": "connection:1"},
    ]
    edges = [{"id": "edge-1", "source": "a", "target": "b", "label": "imports"}]

    first = build_arrow_artifacts(nodes, edges)
    second = build_arrow_artifacts(list(reversed(nodes)), edges)

    assert first == second
    assert first.points.checksum == hashlib.sha256(first.points.data).hexdigest()
    points = read_and_validate_artifact(first.points.data, POINTS_SCHEMA)
    links = read_and_validate_artifact(first.links.data, LINKS_SCHEMA)
    assert points.column("id").to_pylist() == [
        "a",
        "b",
        "connection:1",
        "knowledge-source:root",
    ]
    assert links.column("source").to_pylist()[0] == 0
    assert links.column("target").to_pylist()[0] == 1
    assert first.points.row_count == 4
    assert first.links.row_count == 4
    assert set(links.column("label").to_pylist()) == {
        "imports",
        "contains",
        "indexes",
    }


def test_arrow_snapshot_rejects_missing_endpoint_and_corruption() -> None:
    with pytest.raises(ValueError, match="missing endpoint"):
        build_arrow_artifacts(
            [{"id": "a"}],
            [{"source": "a", "target": "missing"}],
        )
    with pytest.raises(ValueError, match="invalid Arrow"):
        read_and_validate_artifact(b"not-arrow", POINTS_SCHEMA)


@pytest.mark.asyncio
async def test_atomic_activation_retains_last_good_on_failure() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(
            lambda sync_connection: KnowledgeGraphSnapshot.__table__.create(sync_connection)
        )

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        repository = KnowledgeGraphSnapshotRepository(session)
        first = await repository.create_build(
            snapshot_id="snapshot-1",
            organization_id="org-1",
            version="v1",
        )
        await repository.activate(
            first,
            points_object_key="org-1/v1/points.arrow",
            links_object_key="org-1/v1/links.arrow",
            points_checksum="a" * 64,
            links_checksum="b" * 64,
            point_count=2,
            link_count=1,
            points_bytes=100,
            links_bytes=50,
        )
        second = await repository.create_build(
            snapshot_id="snapshot-2",
            organization_id="org-1",
            version="v2",
        )
        await repository.fail(second, error_summary="source unavailable")
        await session.commit()

        current = await repository.get_current("org-1")
        assert current is not None
        assert current.id == "snapshot-1"
        assert second.state == "failed"
        assert second.is_current is False

    await engine.dispose()


def test_arrow_file_can_be_opened_by_standard_reader() -> None:
    artifact = build_arrow_artifacts([{"id": "a"}], []).points
    table = ipc.open_file(artifact.data).read_all()
    assert table.num_rows == 1
