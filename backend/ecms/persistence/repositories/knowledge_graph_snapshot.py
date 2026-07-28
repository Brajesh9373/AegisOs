"""Repository for atomic knowledge-graph snapshot activation."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ecms.persistence.models.knowledge_graph_snapshot import KnowledgeGraphSnapshot
from ecms.shared.time import utcnow

__all__ = ["KnowledgeGraphSnapshotRepository"]


class KnowledgeGraphSnapshotRepository:
    """Manage build state while retaining the last known-good current snapshot."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind the repository to one transactional session."""
        self._session = session

    async def create_build(
        self,
        *,
        snapshot_id: str,
        organization_id: str,
        version: str,
        source_watermark: str | None = None,
        now: datetime | None = None,
    ) -> KnowledgeGraphSnapshot:
        """Create a non-current build record."""
        snapshot = KnowledgeGraphSnapshot(
            id=snapshot_id,
            organization_id=organization_id,
            version=version,
            state="building",
            is_current=False,
            source_watermark=source_watermark,
            started_at=now or utcnow(),
        )
        self._session.add(snapshot)
        await self._session.flush()
        return snapshot

    async def get(self, snapshot_id: str) -> KnowledgeGraphSnapshot | None:
        """Return a snapshot by identifier."""
        return await self._session.get(KnowledgeGraphSnapshot, snapshot_id)

    async def get_version(
        self,
        organization_id: str,
        version: str,
    ) -> KnowledgeGraphSnapshot | None:
        """Return one immutable ready version within an organization."""
        result = await self._session.execute(
            select(KnowledgeGraphSnapshot).where(
                KnowledgeGraphSnapshot.organization_id == organization_id,
                KnowledgeGraphSnapshot.version == version,
                KnowledgeGraphSnapshot.state == "ready",
            )
        )
        return result.scalar_one_or_none()

    async def get_current(self, organization_id: str) -> KnowledgeGraphSnapshot | None:
        """Return the last ready snapshot atomically marked current."""
        result = await self._session.execute(
            select(KnowledgeGraphSnapshot).where(
                KnowledgeGraphSnapshot.organization_id == organization_id,
                KnowledgeGraphSnapshot.is_current.is_(True),
                KnowledgeGraphSnapshot.state == "ready",
            )
        )
        return result.scalar_one_or_none()

    async def get_latest(self, organization_id: str) -> KnowledgeGraphSnapshot | None:
        """Return the newest build regardless of state."""
        result = await self._session.execute(
            select(KnowledgeGraphSnapshot)
            .where(KnowledgeGraphSnapshot.organization_id == organization_id)
            .order_by(KnowledgeGraphSnapshot.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def retention_candidates(
        self,
        organization_id: str,
        *,
        keep_non_current: int = 3,
    ) -> list[KnowledgeGraphSnapshot]:
        """Return old non-current snapshots, never including the active version."""
        result = await self._session.execute(
            select(KnowledgeGraphSnapshot)
            .where(
                KnowledgeGraphSnapshot.organization_id == organization_id,
                KnowledgeGraphSnapshot.is_current.is_(False),
            )
            .order_by(KnowledgeGraphSnapshot.created_at.desc())
            .offset(max(keep_non_current, 0))
        )
        return list(result.scalars())

    async def delete_non_current(self, snapshot_id: str) -> None:
        """Delete metadata only when the target is still non-current."""
        await self._session.execute(
            delete(KnowledgeGraphSnapshot).where(
                KnowledgeGraphSnapshot.id == snapshot_id,
                KnowledgeGraphSnapshot.is_current.is_(False),
            )
        )

    async def activate(
        self,
        snapshot: KnowledgeGraphSnapshot,
        *,
        points_object_key: str,
        links_object_key: str,
        points_checksum: str,
        links_checksum: str,
        point_count: int,
        link_count: int,
        points_bytes: int,
        links_bytes: int,
        completed_at: datetime | None = None,
    ) -> KnowledgeGraphSnapshot:
        """Make a fully verified build current and retire its predecessor."""
        if snapshot.state != "building":
            raise ValueError("only a building snapshot can be activated")
        await self._session.execute(
            update(KnowledgeGraphSnapshot)
            .where(
                KnowledgeGraphSnapshot.organization_id == snapshot.organization_id,
                KnowledgeGraphSnapshot.is_current.is_(True),
            )
            .values(is_current=False)
        )
        snapshot.points_object_key = points_object_key
        snapshot.links_object_key = links_object_key
        snapshot.points_checksum = points_checksum
        snapshot.links_checksum = links_checksum
        snapshot.point_count = point_count
        snapshot.link_count = link_count
        snapshot.points_bytes = points_bytes
        snapshot.links_bytes = links_bytes
        snapshot.state = "ready"
        snapshot.is_current = True
        snapshot.completed_at = completed_at or utcnow()
        snapshot.error_summary = None
        await self._session.flush()
        return snapshot

    async def fail(
        self,
        snapshot: KnowledgeGraphSnapshot,
        *,
        error_summary: str,
        completed_at: datetime | None = None,
    ) -> None:
        """Record a failed build without changing the current snapshot."""
        snapshot.state = "failed"
        snapshot.is_current = False
        snapshot.error_summary = error_summary[:4_000]
        snapshot.completed_at = completed_at or utcnow()
        await self._session.flush()
