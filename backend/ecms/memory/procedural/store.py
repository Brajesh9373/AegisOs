"""Procedural layer: named multi-step workflows agents can learn and reuse."""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any, cast

from sqlalchemy import Table, select
from sqlalchemy.ext.asyncio import create_async_engine

from ecms.memory.keywords import rank_by_overlap
from ecms.persistence.database.rest_session import db_session

logger = logging.getLogger("ecms.memory.procedural")


class ProceduralStore:
    """Durable store for learned procedures with keyword search."""

    async def ensure_table(self) -> None:
        """Create agent_procedures when missing (migrations are canonical)."""
        from ecms.persistence.models.agent_memory_layers import AgentProcedure

        url = os.environ.get("ECMS_DATABASE_URL", "sqlite+aiosqlite:///./ecms.db")
        engine = create_async_engine(url)
        try:
            async with engine.begin() as connection:
                table = cast(Table, AgentProcedure.__table__)
                await connection.run_sync(table.create, checkfirst=True)
        finally:
            await engine.dispose()

    async def learn(
        self, name: str, description: str, steps: list[str], learned_by: str
    ) -> dict[str, Any]:
        """Store a procedure; returns its record."""
        from ecms.persistence.models.agent_memory_layers import AgentProcedure

        await self.ensure_table()
        record = AgentProcedure(
            id=f"proc-{uuid.uuid4().hex[:12]}",
            name=name.strip(),
            description=description.strip(),
            steps=[s.strip() for s in steps if s.strip()],
            learned_by=learned_by,
        )
        async with db_session() as session:
            session.add(record)
        logger.info("Learned procedure %r from %s", name, learned_by)
        return record.to_dict()

    async def search(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        """Return procedures matching the query, best overlap first."""
        from ecms.persistence.models.agent_memory_layers import AgentProcedure

        try:
            async with db_session() as session:
                rows = (await session.execute(select(AgentProcedure))).scalars().all()
        except Exception as e:
            logger.warning("Procedure search failed: %s", e)
            return []
        candidates = [(f"{row.name} {row.description}", row) for row in rows]
        return [
            row.to_dict()
            for row in rank_by_overlap(query, candidates, limit=limit)
        ]
