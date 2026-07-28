"""Audit repository (SECTION 65/81)."""

from __future__ import annotations

from collections.abc import Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from ecms.persistence.models.audit import AuditRecord

__all__ = ["AuditRepository"]


class AuditRepository:
    """Persists and queries immutable audit records (SECTION 65)."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize the repository with an async session."""
        self._session = session

    async def add(self, record: AuditRecord) -> AuditRecord:
        """Persist an audit record and flush it to obtain generated values."""
        self._session.add(record)
        await self._session.flush()
        return record

    async def list_by_actor(self, actor: str) -> Sequence[AuditRecord]:
        """Return audit records for an actor, most recent first."""
        result = await self._session.execute(
            select(AuditRecord)
            .where(AuditRecord.actor == actor)
            .order_by(AuditRecord.created_at.desc()),
        )
        return result.scalars().all()

    async def count(self) -> int:
        """Return the total number of audit records."""
        result = await self._session.execute(select(func.count()).select_from(AuditRecord))
        return int(result.scalar_one())
