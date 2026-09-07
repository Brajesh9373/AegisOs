"""Episodic layer: durable prompt/response exchanges per agent.

Episodes are written twice: into the embedding index (fast semantic recall
within the process) and into the `agent_episodes` table (survives restarts;
reloaded by :meth:`EpisodicStore.backfill`). The in-memory repository stays
the single search path; this store owns durability.
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any, Protocol, cast

from sqlalchemy import Table, select
from sqlalchemy.ext.asyncio import create_async_engine

from ecms.persistence.database.rest_session import db_session

logger = logging.getLogger("ecms.memory.episodic")


class EpisodicRepositoryLike(Protocol):
    """Structural slice of the embedding index used for episodic search."""

    async def add(self, uco: Any) -> None: ...


class EpisodicStore:
    """Durable episodic memory with startup backfill."""

    def __init__(
        self,
        repository: EpisodicRepositoryLike,
        uco_factory: Any | None = None,
    ) -> None:
        self._repository = repository
        self._uco_factory = uco_factory

    def _factory(self) -> Any | None:
        if self._uco_factory is None:
            try:
                from ecms.shared.models import UniversalCognitiveObject
            except ImportError:
                return None
            self._uco_factory = UniversalCognitiveObject
        return self._uco_factory

    async def ensure_table(self) -> None:
        """Create agent_episodes when missing (migrations are canonical)."""
        from ecms.persistence.models.agent_episode import AgentEpisode

        url = os.environ.get("ECMS_DATABASE_URL", "sqlite+aiosqlite:///./ecms.db")
        engine = create_async_engine(url)
        try:
            async with engine.begin() as connection:
                table = cast(Table, AgentEpisode.__table__)
                await connection.run_sync(table.create, checkfirst=True)
        finally:
            await engine.dispose()

    async def save(
        self, agent_id: str, prompt: str, response: str
    ) -> str | None:
        """Index one exchange and persist it; returns the episode id (None on skip)."""
        factory = self._factory()
        if factory is None:
            logger.warning("Episodic save skipped (no UCO model)")
            return None
        await self.ensure_table()
        summary = response.strip().split("\n")[0][:280] if response.strip() else "(no response)"
        uco = factory(
            canonical_name=f"agent-episode-{agent_id}-{int(time.time() * 1000)}",
            display_name=f"Agent episode ({agent_id})",
            ontology_type="agent_episode",
            description=f"Q: {prompt.strip()[:500]}\nA: {response.strip()[:500]}",
            summary=summary,
            created_by=agent_id,
            custom_attributes={
                "agent_id": agent_id,
                "category": "agent_episode",
                "prompt": prompt.strip()[:2000],
                "response": response.strip()[:2000],
            },
        )
        await self._repository.add(uco)
        await self._persist(agent_id, uco)
        uco_id: str = uco.uco_id
        return uco_id

    async def backfill(self) -> int:
        """Reload persisted episodes into the index; returns rows restored."""
        from ecms.persistence.models.agent_episode import AgentEpisode

        try:
            await self.ensure_table()
            async with db_session() as session:
                rows = (
                    await session.execute(
                        select(AgentEpisode).order_by(AgentEpisode.created_at)
                    )
                ).scalars().all()
        except Exception as e:
            logger.warning("Episodic backfill failed: %s", e)
            return 0
        restored = 0
        for row in rows:
            uco = self._from_row(row)
            if uco is None:
                continue
            try:
                await self._repository.add(uco)
                restored += 1
            except Exception as e:
                logger.warning("Skipping episode %s on backfill: %s", row.uco_id, e)
        if restored:
            logger.info("Backfilled %d agent episodes into memory", restored)
        return restored

    async def _persist(self, agent_id: str, uco: Any) -> None:
        from ecms.persistence.models.agent_episode import AgentEpisode

        try:
            dump = uco.model_dump(mode="json") if hasattr(uco, "model_dump") else {}
            async with db_session() as session:
                session.add(
                    AgentEpisode(
                        uco_id=uco.uco_id,
                        agent_id=agent_id,
                        display_name=uco.display_name,
                        description=uco.description,
                        summary=uco.summary or "",
                        ontology_type=uco.ontology_type,
                        uco_json=dump,
                    )
                )
        except Exception as e:
            logger.warning("Episode persistence failed for agent %s: %s", agent_id, e)

    def _from_row(self, row: Any) -> Any | None:
        factory = self._factory()
        if factory is None:
            return None
        try:
            return factory.model_validate(row.uco_json or {})
        except Exception:
            try:
                return factory(
                    canonical_name=f"agent-episode-{row.agent_id}-{row.uco_id}",
                    display_name=row.display_name,
                    ontology_type=row.ontology_type,
                    description=row.description,
                    summary=row.summary,
                    created_by=row.agent_id,
                    custom_attributes={"agent_id": row.agent_id},
                )
            except Exception:
                return None
