"""Organizational layer: validated patterns shared across all agents."""

from __future__ import annotations

import logging
import os
import uuid
from typing import Any, cast

from sqlalchemy import Table, select
from sqlalchemy.ext.asyncio import create_async_engine

from ecms.memory.keywords import rank_by_overlap
from ecms.persistence.database.rest_session import db_session

logger = logging.getLogger("ecms.memory.organization")

PATTERN_TYPES = frozenset({"best_practice", "known_bug", "optimization", "convention"})


class PatternStore:
    """Durable store for org patterns with keyword search."""

    async def ensure_table(self) -> None:
        """Create org_patterns when missing (migrations are canonical)."""
        from ecms.persistence.models.agent_memory_layers import OrgPattern

        url = os.environ.get("ECMS_DATABASE_URL", "sqlite+aiosqlite:///./ecms.db")
        engine = create_async_engine(url)
        try:
            async with engine.begin() as connection:
                table = cast(Table, OrgPattern.__table__)
                await connection.run_sync(table.create, checkfirst=True)
        finally:
            await engine.dispose()

    async def publish(
        self, pattern_type: str, description: str, published_by: str
    ) -> dict[str, Any]:
        """Publish a pattern; returns its record."""
        from ecms.persistence.models.agent_memory_layers import OrgPattern

        if pattern_type not in PATTERN_TYPES:
            raise ValueError(f"pattern_type must be one of {sorted(PATTERN_TYPES)}")
        await self.ensure_table()
        record = OrgPattern(
            id=f"pat-{uuid.uuid4().hex[:12]}",
            pattern_type=pattern_type,
            description=description.strip(),
            published_by=published_by,
        )
        async with db_session() as session:
            session.add(record)
        logger.info("Published %s pattern from %s", pattern_type, published_by)
        return record.to_dict()

    async def search(self, query: str, limit: int = 3) -> list[dict[str, Any]]:
        """Return patterns matching the query, best overlap first."""
        from ecms.persistence.models.agent_memory_layers import OrgPattern

        try:
            async with db_session() as session:
                rows = (await session.execute(select(OrgPattern))).scalars().all()
        except Exception as e:
            logger.warning("Pattern search failed: %s", e)
            return []
        candidates = [(f"{row.pattern_type} {row.description}", row) for row in rows]
        return [
            row.to_dict()
            for row in rank_by_overlap(query, candidates, limit=limit)
        ]
