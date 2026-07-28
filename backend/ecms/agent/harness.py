"""Agent Harness — observability layer for specialized agents.

Updates agent KPIs (execution_count, last_active_at, error_count_30d)
after every AgentLoop run. Connects the runtime to the CollaborationPanel UI.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("ecms.harness")


class AgentHarness:
    """Wraps an AgentLoop, tracking execution metrics per agent."""

    def __init__(self, agent_id: str | None = None) -> None:
        self._agent_id = agent_id

    async def track_run(
        self,
        answer: str | None,
        trace: dict[str, Any] | None = None,
        error: str | None = None,
    ) -> None:
        """Update agent KPIs after each run."""
        if not self._agent_id:
            return

        try:
            from ecms.persistence.database.rest_session import db_session
            from sqlalchemy import text

            now = datetime.now(timezone.utc).isoformat()
            async with db_session() as session:
                if error:
                    await session.execute(text(
                        "UPDATE agents SET execution_count = COALESCE(execution_count, 0) + 1, "
                        "last_active_at = :t, error_count_30d = COALESCE(error_count_30d, 0) + 1 "
                        "WHERE id = :aid"
                    ), {"aid": self._agent_id, "t": now})
                else:
                    await session.execute(text(
                        "UPDATE agents SET execution_count = COALESCE(execution_count, 0) + 1, "
                        "last_active_at = :t WHERE id = :aid"
                    ), {"aid": self._agent_id, "t": now})

            logger.info("[HARNESS-%s] Tracked run | success=%s", self._agent_id[:8], error is None)
        except Exception as e:
            logger.warning("[HARNESS-%s] Failed to update KPIs: %s", self._agent_id[:8], e)

    @staticmethod
    async def get_agent_kpis(agent_id: str) -> dict[str, Any]:
        """Fetch live KPIs for an agent."""
        try:
            from ecms.persistence.database.rest_session import db_session
            from sqlalchemy import text

            async with db_session() as session:
                row = (await session.execute(text(
                    "SELECT execution_count, last_active_at, error_count_30d, active_workspaces "
                    "FROM agents WHERE id = :aid"
                ), {"aid": agent_id})).first()

                if row:
                    return {
                        "execution_count": row[0] or 0,
                        "last_active_at": row[1] or "never",
                        "error_count_30d": row[2] or 0,
                        "active_workspaces": row[3] or 0,
                    }
        except Exception:
            pass

        return {
            "execution_count": 0,
            "last_active_at": "never",
            "error_count_30d": 0,
            "active_workspaces": 0,
        }
