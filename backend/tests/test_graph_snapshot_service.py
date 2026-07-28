from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ecms.infrastructure.storage.object_store import InMemoryObjectStore
from ecms.persistence.models.knowledge_graph_snapshot import KnowledgeGraphSnapshot
from ecms.persistence.repositories.knowledge_graph_snapshot import (
    KnowledgeGraphSnapshotRepository,
)
from ecms.visualization.snapshot_service import GraphSnapshotService


class FixtureGraphSource:
    async def load(self) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
        return (
            [
                {"id": "a", "label": "Alpha", "group": "file"},
                {"id": "b", "label": "Beta", "group": "file"},
            ],
            [{"id": "ab", "source": "a", "target": "b", "label": "imports"}],
        )


class FailingGraphSource:
    async def load(self) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
        raise ConnectionError("FalkorDB interrupted")


@pytest.mark.asyncio
async def test_service_uploads_then_atomically_activates() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(
            lambda sync_connection: KnowledgeGraphSnapshot.__table__.create(sync_connection)
        )
    factory = async_sessionmaker(engine, expire_on_commit=False)
    store = InMemoryObjectStore()

    async with factory() as session:
        service = GraphSnapshotService(
            session=session,
            object_store=store,
            graph_source=FixtureGraphSource(),
        )
        snapshot = await service.build(organization_id="org-1", source_watermark="revision-7")
        await session.commit()
        current = await KnowledgeGraphSnapshotRepository(session).get_current("org-1")

    assert current is not None
    assert current.id == snapshot.id
    assert current.point_count == 2
    assert current.link_count == 1
    assert await store.list_objects("knowledge-graph/org-1/") == [
        current.links_object_key,
        current.points_object_key,
    ]
    await engine.dispose()


@pytest.mark.asyncio
async def test_failed_rebuild_keeps_last_known_good_snapshot_current() -> None:
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as connection:
        await connection.run_sync(
            lambda sync_connection: KnowledgeGraphSnapshot.__table__.create(sync_connection)
        )
    factory = async_sessionmaker(engine, expire_on_commit=False)
    store = InMemoryObjectStore()

    async with factory() as session:
        successful = GraphSnapshotService(
            session=session,
            object_store=store,
            graph_source=FixtureGraphSource(),
        )
        ready = await successful.build(organization_id="org-1")
        await session.commit()

        failing = GraphSnapshotService(
            session=session,
            object_store=store,
            graph_source=FailingGraphSource(),
        )
        with pytest.raises(ConnectionError, match="FalkorDB interrupted"):
            await failing.build(organization_id="org-1")
        await session.commit()

        repository = KnowledgeGraphSnapshotRepository(session)
        current = await repository.get_current("org-1")
        latest = await repository.get_latest("org-1")

    assert current is not None and current.id == ready.id
    assert latest is not None and latest.state == "failed"
    assert latest.is_current is False
    assert await store.list_objects("knowledge-graph/org-1/") == [
        ready.links_object_key,
        ready.points_object_key,
    ]
    await engine.dispose()
