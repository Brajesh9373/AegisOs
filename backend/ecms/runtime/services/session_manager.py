"""Session manager: session lifecycle and timeline (SECTION 21/73).

A session is a collaborative execution context that contains many tasks. When it
closes, its accumulated understanding is handed to reflection and promotion (a
step orchestrated by the runtime kernel).
"""

from __future__ import annotations

from ecms.events import EventBus
from ecms.runtime.events.runtime_events import (
    session_completed,
    session_created,
    session_started,
)
from ecms.shared.enums import SessionStatus
from ecms.shared.events import BaseEvent
from ecms.shared.exceptions import NotFoundError
from ecms.shared.models import Session
from ecms.shared.time import utcnow

__all__ = ["SessionManager"]


class SessionManager:
    """Owns session lifecycle and timeline (SECTION 73)."""

    def __init__(self, *, event_bus: EventBus | None = None) -> None:
        """Initialize an empty session registry."""
        self._sessions: dict[str, Session] = {}
        self._event_bus = event_bus

    async def create(
        self,
        *,
        organization_id: str,
        user_id: str,
        workspace_id: str | None = None,
        project_id: str | None = None,
    ) -> Session:
        """Create and start a new session."""
        session = Session(
            organization_id=organization_id,
            user_id=user_id,
            workspace_id=workspace_id,
            project_id=project_id,
        )
        self._sessions[session.session_id] = session
        await self._emit(session_created(session.session_id))
        await self._emit(session_started(session.session_id))
        return session

    async def add_task(self, session_id: str, task_id: str) -> Session:
        """Record an active task on a session."""
        session = self._require(session_id)
        session.active_tasks = [*session.active_tasks, task_id]
        return session

    async def complete_task(self, session_id: str, task_id: str) -> Session:
        """Move a task from active to completed on a session."""
        session = self._require(session_id)
        session.active_tasks = [t for t in session.active_tasks if t != task_id]
        session.completed_tasks = [*session.completed_tasks, task_id]
        return session

    async def close(self, session_id: str, *, summary: str | None = None) -> Session:
        """Close a session, marking it completed."""
        session = self._require(session_id)
        session.status = SessionStatus.COMPLETED
        session.ended_at = utcnow()
        if summary is not None:
            session.session_summary = summary
        await self._emit(session_completed(session_id))
        return session

    def get(self, session_id: str) -> Session | None:
        """Return a session by id, or ``None``."""
        return self._sessions.get(session_id)

    def _require(self, session_id: str) -> Session:
        session = self._sessions.get(session_id)
        if session is None:
            raise NotFoundError(f"session {session_id!r} not found")
        return session

    async def _emit(self, event: BaseEvent) -> None:
        if self._event_bus is not None:
            await self._event_bus.publish(event)
