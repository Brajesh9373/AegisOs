"""Session persistence repository.

CRUD for sessions and messages in PostgreSQL. Workspace-scoped.
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ecms.persistence.models.session import Session, SessionMessage
from ecms.shared.time import utcnow


class SessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(
        self,
        *,
        session_id: str,
        workspace_id: str,
        title: str | None = None,
        project_id: str | None = None,
    ) -> Session:
        s = Session(
            id=session_id,
            workspace_id=workspace_id,
            project_id=project_id,
            title=title,
        )
        self._session.add(s)
        return s

    async def get(self, session_id: str) -> Session | None:
        stmt = select(Session).where(Session.id == session_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_workspace(self, workspace_id: str, limit: int = 50) -> list[Session]:
        stmt = (
            select(Session)
            .where(Session.workspace_id == workspace_id)
            .options(selectinload(Session.messages))
            .order_by(Session.updated_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def add_message(
        self,
        session_id: str,
        *,
        role: str,
        content: str | None = None,
        tool_calls: dict[str, Any] | None = None,
        tool_call_id: str | None = None,
        name: str | None = None,
    ) -> None:
        msg = SessionMessage(
            session_id=session_id,
            role=role,
            content=content,
            tool_calls=tool_calls,
            tool_call_id=tool_call_id,
            name=name,
        )
        self._session.add(msg)

        stmt = select(Session).where(Session.id == session_id)
        result = await self._session.execute(stmt)
        s = result.scalar_one_or_none()
        if s:
            s.updated_at = utcnow()

    async def get_messages(self, session_id: str) -> list[dict[str, Any]]:
        stmt = (
            select(SessionMessage)
            .where(SessionMessage.session_id == session_id)
            .order_by(SessionMessage.created_at)
        )
        result = await self._session.execute(stmt)
        msgs = result.scalars().all()
        return [
            {
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "tool_calls": m.tool_calls,
                "tool_call_id": m.tool_call_id,
                "name": m.name,
                "created_at": m.created_at.isoformat() if m.created_at else "",
            }
            for m in msgs
        ]

    async def delete(self, session_id: str) -> bool:
        """Delete a single session (messages cascade via FK). Returns True if deleted."""
        stmt = select(Session).where(Session.id == session_id)
        result = await self._session.execute(stmt)
        sess = result.scalar_one_or_none()
        if not sess:
            return False
        await self._session.delete(sess)
        await self._session.flush()
        return True

    async def delete_by_workspace(self, workspace_id: str) -> int:
        stmt = select(Session.id).where(Session.workspace_id == workspace_id)
        result = await self._session.execute(stmt)
        session_ids = [row[0] for row in result.all()]

        if session_ids:
            await self._session.execute(
                delete(Session).where(Session.workspace_id == workspace_id),
            )
            await self._session.flush()
        return len(session_ids)
