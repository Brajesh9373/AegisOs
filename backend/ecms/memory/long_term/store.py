"""Long-term layer: key/value preferences per agent or team-shared."""

from __future__ import annotations

import logging
import os
from typing import Any, cast

from sqlalchemy import Table, select
from sqlalchemy.ext.asyncio import create_async_engine

from ecms.persistence.database.rest_session import db_session

logger = logging.getLogger("ecms.memory.long_term")

SHARED_SCOPE = "team:shared"


def agent_scope(agent_id: str) -> str:
    """Return the preference scope for one agent (empty id = shared only)."""
    return f"agent:{agent_id}" if agent_id else SHARED_SCOPE


class PreferenceStore:
    """Durable store for long-term preferences with shared/agent overlay."""

    async def ensure_table(self) -> None:
        """Create agent_preferences when missing (migrations are canonical)."""
        from ecms.persistence.models.agent_memory_layers import AgentPreference

        url = os.environ.get("ECMS_DATABASE_URL", "sqlite+aiosqlite:///./ecms.db")
        engine = create_async_engine(url)
        try:
            async with engine.begin() as connection:
                table = cast(Table, AgentPreference.__table__)
                await connection.run_sync(table.create, checkfirst=True)
        finally:
            await engine.dispose()

    async def remember(
        self, key: str, value: str, agent_id: str, *, shared: bool = False
    ) -> None:
        """Upsert a preference (team-shared, or scoped to one agent)."""
        from ecms.persistence.models.agent_memory_layers import AgentPreference

        await self.ensure_table()
        scope = SHARED_SCOPE if shared else agent_scope(agent_id)
        async with db_session() as session:
            existing = (
                await session.execute(
                    select(AgentPreference).where(
                        AgentPreference.scope == scope, AgentPreference.key == key
                    )
                )
            ).scalar_one_or_none()
            if existing is None:
                session.add(
                    AgentPreference(
                        scope=scope, key=key, value=value, updated_by=agent_id
                    )
                )
            else:
                existing.value = value
                existing.updated_by = agent_id

    async def recall(self, agent_id: str) -> dict[str, str]:
        """Return shared prefs overlaid with the agent's own (agent wins)."""
        from ecms.persistence.models.agent_memory_layers import AgentPreference

        scopes = [SHARED_SCOPE] if not agent_id else [SHARED_SCOPE, agent_scope(agent_id)]
        try:
            async with db_session() as session:
                rows = (
                    await session.execute(
                        select(AgentPreference).where(AgentPreference.scope.in_(scopes))
                    )
                ).scalars().all()
        except Exception as e:
            logger.warning("Preference recall failed: %s", e)
            return {}
        prefs: dict[str, str] = {}
        # Shared first so the agent's own values win on key conflicts.
        for row in sorted(rows, key=lambda r: 0 if r.scope == SHARED_SCOPE else 1):
            prefs[row.key] = row.value
        return prefs
