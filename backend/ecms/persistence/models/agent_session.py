"""Agent Session ORM model.

Tracks DSH SDK sessions for AegisOS agents. Each agent can have one active
session at a time, with durable memory stored in DSH_HOME/sessions/.

The session_id is the DSH session identifier, which persists across agent
respawns — so even if the DSH subprocess dies and is restarted, the agent
retains its memory.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ecms.persistence.models.base import Base
from ecms.shared.time import utcnow

__all__ = ["AgentSession"]


class AgentSession(Base):
    __tablename__ = "agent_sessions"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)

    # Link to the agent this session belongs to
    agent_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("agents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # DSH session configuration
    dsh_session_id: Mapped[str] = mapped_column(String(255), nullable=False)
    dsh_home: Mapped[str] = mapped_column(String(512), nullable=False)
    profile: Mapped[str] = mapped_column(String(64), nullable=False, default="sdk")

    # Session state
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
        index=True,
    )  # "active" | "paused" | "dead"

    # Heartbeat tracking
    last_heartbeat: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_status: Mapped[str | None] = mapped_column(String(32), nullable=True)

    # Session metadata
    message_count: Mapped[int] = mapped_column(default=0)
    error_count: Mapped[int] = mapped_column(default=0)
    metadata_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "agent_id": self.agent_id,
            "dsh_session_id": self.dsh_session_id,
            "dsh_home": self.dsh_home,
            "profile": self.profile,
            "status": self.status,
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "last_status": self.last_status,
            "message_count": self.message_count,
            "error_count": self.error_count,
            "metadata": self.metadata_json or {},
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "updated_at": self.updated_at.isoformat() if self.updated_at else "",
        }
