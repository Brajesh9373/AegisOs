"""Live catalogs the BA draws from when designing a team.

The design must be directly instantiable, so the BA may only choose:
  - a `model` that exists as an ai_models row (its model_id);
  - `tools` that exist in the agent tool registry.

Both are resolved at call time, never hardcoded, so the catalogs always reflect
what is actually installed.
"""

from __future__ import annotations

import logging

from ecms.persistence.database.rest_session import db_session

logger = logging.getLogger("ecms.ba.catalog")


async def get_model_ids() -> list[str]:
    """Return the model_ids of every configured ai_models row."""
    try:
        async with db_session() as session:
            from sqlalchemy import text
            rows = (await session.execute(text(
                "SELECT model_id FROM ai_models ORDER BY is_default DESC, created_at DESC"
            ))).fetchall()
        ids = [r[0] for r in rows if r[0]]
        # de-duplicate, preserve order
        seen: set[str] = set()
        out: list[str] = []
        for m in ids:
            if m not in seen:
                seen.add(m)
                out.append(m)
        return out
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("[ba.catalog] model lookup failed: %s", exc)
        return []


def get_tool_names() -> list[str]:
    """Return every tool name an agent could be granted."""
    from ecms.agent.tools import TOOL_DEFINITIONS
    from ecms.agent.org_tools import ORG_TOOL_DEFINITIONS

    names: list[str] = []
    seen: set[str] = set()
    for defn in list(TOOL_DEFINITIONS) + list(ORG_TOOL_DEFINITIONS):
        name = defn.get("function", {}).get("name")
        if name and name not in seen:
            seen.add(name)
            names.append(name)
    return names
