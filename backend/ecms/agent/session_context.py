"""Session context — cross-request memory with dual-write persistence.

Wraps Redis for fast reads + PostgreSQL for permanent storage.
All methods are async to share the agent's event loop.
"""

from __future__ import annotations

import logging
from typing import Any

from legacy_ecms.config import get_settings
from legacy_ecms.memory.session_redis import RedisSessionMemory

logger = logging.getLogger(__name__)

_SESSION_MEMORY: RedisSessionMemory | None = None


def _get_session_memory() -> RedisSessionMemory:
    global _SESSION_MEMORY
    if _SESSION_MEMORY is None:
        settings = get_settings()
        _SESSION_MEMORY = RedisSessionMemory(
            redis_url=settings.redis_url,
            default_ttl_seconds=86400,
            workspace_id="default",
        )
    return _SESSION_MEMORY


async def _pg_set(session_id: str, key: str, value: Any) -> None:
    try:
        from sqlalchemy import select

        from ecms.persistence.database.rest_session import db_session
        from ecms.persistence.models.session_context import SessionContextKV

        async with db_session() as s:
            stmt = select(SessionContextKV).where(
                SessionContextKV.session_id == session_id,
                SessionContextKV.key == key,
            )
            result = await s.execute(stmt)
            existing = result.scalar_one_or_none()
            if existing:
                existing.value = {"v": value}
            else:
                s.add(SessionContextKV(session_id=session_id, key=key, value={"v": value}))
    except Exception as e:
        logger.debug("PG session set failed: %s", e)


async def _pg_get(session_id: str, key: str) -> Any:
    try:
        from sqlalchemy import select

        from ecms.persistence.database.rest_session import db_session
        from ecms.persistence.models.session_context import SessionContextKV

        async with db_session() as s:
            stmt = select(SessionContextKV).where(
                SessionContextKV.session_id == session_id,
                SessionContextKV.key == key,
            )
            result = await s.execute(stmt)
            row = result.scalar_one_or_none()
            if row and row.value:
                return row.value.get("v")
    except Exception as e:
        logger.debug("PG session get failed: %s", e)
    return None


async def _pg_snapshot(session_id: str) -> dict[str, Any]:
    try:
        from sqlalchemy import select

        from ecms.persistence.database.rest_session import db_session
        from ecms.persistence.models.session_context import SessionContextKV

        async with db_session() as s:
            stmt = select(SessionContextKV).where(
                SessionContextKV.session_id == session_id,
            )
            result = await s.execute(stmt)
            rows = result.scalars().all()
            return {row.key: row.value.get("v") for row in rows if row.value and "v" in row.value}
    except Exception as e:
        logger.debug("PG snapshot failed: %s", e)
        return {}


class SessionContext:
    """Per-session memory bridge with dual-write persistence.

    All methods are async. Redis for sub-ms reads, PostgreSQL for permanence.
    """

    def __init__(self, session_id: str) -> None:
        self._session_id = session_id
        self._sm = _get_session_memory()
        self._snapshot_cache: dict[str, Any] | None = None

    async def set(self, key: str, value: Any) -> None:
        # Redis (fast, sync-safe via thread)
        self._sm.set(self._session_id, key, value)
        # PostgreSQL (permanent, on the same event loop)
        await _pg_set(self._session_id, key, value)
        # Invalidate cache
        self._snapshot_cache = None

    async def get(self, key: str, default: Any = None) -> Any:
        # Redis first
        val = self._sm.get(self._session_id, key)
        if val is not None:
            return val
        # PostgreSQL fallback
        val = await _pg_get(self._session_id, key)
        if val is not None:
            self._sm.set(self._session_id, key, val)
            return val
        return default

    async def snapshot(self) -> dict[str, Any]:
        if self._snapshot_cache is not None:
            return self._snapshot_cache
        # Redis first
        snap = self._sm.snapshot(self._session_id)
        if snap:
            self._snapshot_cache = snap
            return snap
        # PostgreSQL fallback
        snap = await _pg_snapshot(self._session_id)
        self._snapshot_cache = snap
        return snap
