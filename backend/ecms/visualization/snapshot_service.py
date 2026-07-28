"""End-to-end immutable graph snapshot construction."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from ecms.configuration.schemas.settings import get_settings
from ecms.infrastructure.storage.object_store import ObjectStore
from ecms.persistence.models.knowledge_graph_snapshot import KnowledgeGraphSnapshot
from ecms.persistence.repositories.knowledge_graph_snapshot import (
    KnowledgeGraphSnapshotRepository,
)
from ecms.shared.time import utcnow
from ecms.visualization.knowledge_graph_snapshot import build_arrow_artifacts

__all__ = ["GraphSnapshotService", "GraphSource", "LegacyFalkorGraphSource"]

ARROW_CONTENT_TYPE = "application/vnd.apache.arrow.file"


class GraphSource(Protocol):
    """Source contract used by the dedicated snapshot worker."""

    async def load(self) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
        """Return the complete organization graph projection."""
        ...


class LegacyFalkorGraphSource:
    """Read the current universal graph using the established FalkorDB projection."""

    async def load(self) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
        """Load nodes and edges off the API event loop."""
        from legacy_ecms.api.routes.graph import load_graph_data_sync

        response = await asyncio.to_thread(load_graph_data_sync)
        return (
            [node.model_dump() for node in response.nodes],
            [edge.model_dump() for edge in response.edges],
        )


class GraphSnapshotService:
    """Build, verify, upload, and atomically activate one organization snapshot."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        object_store: ObjectStore,
        graph_source: GraphSource,
    ) -> None:
        """Bind transactional and infrastructure dependencies."""
        self._session = session
        self._store = object_store
        self._source = graph_source
        self._repository = KnowledgeGraphSnapshotRepository(session)

    async def build(
        self,
        *,
        organization_id: str,
        source_watermark: str | None = None,
    ) -> KnowledgeGraphSnapshot:
        """Build a new immutable version while retaining the previous current version."""
        snapshot_id = f"kgs-{uuid4().hex}"
        version = uuid4().hex
        snapshot = await self._repository.create_build(
            snapshot_id=snapshot_id,
            organization_id=organization_id,
            version=version,
            source_watermark=source_watermark,
        )
        uploaded_keys: list[str] = []
        try:
            qualification_delay = (
                get_settings().knowledge_graph_build_start_delay_seconds
            )
            if qualification_delay:
                await asyncio.sleep(qualification_delay)
            nodes, edges = await self._source.load()
            artifacts = await asyncio.to_thread(build_arrow_artifacts, nodes, edges)
            prefix = f"knowledge-graph/{organization_id}/{version}"
            points_key = f"{prefix}/points.arrow"
            links_key = f"{prefix}/links.arrow"

            with tempfile.TemporaryDirectory(prefix="ecms-kgraph-") as directory:
                points_path = Path(directory) / "points.arrow"
                links_path = Path(directory) / "links.arrow"
                await asyncio.to_thread(points_path.write_bytes, artifacts.points.data)
                await asyncio.to_thread(links_path.write_bytes, artifacts.links.data)
                await self._store.put_file(
                    points_key,
                    points_path,
                    content_type=ARROW_CONTENT_TYPE,
                )
                uploaded_keys.append(points_key)
                await self._store.put_file(
                    links_key,
                    links_path,
                    content_type=ARROW_CONTENT_TYPE,
                )
                uploaded_keys.append(links_key)

            points_info, links_info = await asyncio.gather(
                self._store.stat_object(points_key),
                self._store.stat_object(links_key),
            )
            if points_info.size != len(artifacts.points.data):
                raise ValueError("uploaded points object size mismatch")
            if links_info.size != len(artifacts.links.data):
                raise ValueError("uploaded links object size mismatch")

            await self._repository.activate(
                snapshot,
                points_object_key=points_key,
                links_object_key=links_key,
                points_checksum=artifacts.points.checksum,
                links_checksum=artifacts.links.checksum,
                point_count=artifacts.points.row_count,
                link_count=artifacts.links.row_count,
                points_bytes=points_info.size,
                links_bytes=links_info.size,
                completed_at=utcnow(),
            )
            return snapshot
        except Exception as exc:
            for key in uploaded_keys:
                await self._store.delete_object(key)
            await self._repository.fail(snapshot, error_summary=str(exc))
            raise

    async def apply_retention(
        self,
        *,
        organization_id: str,
        keep_non_current: int = 3,
    ) -> int:
        """Remove only old non-current objects and metadata."""
        candidates = await self._repository.retention_candidates(
            organization_id,
            keep_non_current=keep_non_current,
        )
        removed = 0
        for snapshot in candidates:
            for key in (snapshot.points_object_key, snapshot.links_object_key):
                if key:
                    await self._store.delete_object(key)
            await self._repository.delete_non_current(snapshot.id)
            removed += 1
        return removed
