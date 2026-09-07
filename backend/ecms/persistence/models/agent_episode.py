"""Agent Episode ORM model.

Durable platform memory for DSH-backed agents. Each prompt/response exchange
an agent completes is stored as one row (plus its embedding vector), so episode
recall survives backend restarts — unlike the in-memory knowledge index, which
is rebuilt from this table on startup (see AgentMemoryBridge backfill).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Float, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ecms.persistence.models.base import Base
from ecms.shared.time import utcnow

__all__ = ["AgentEpisode"]


class AgentEpisode(Base):
    __tablename__ = "agent_episodes"

    # UCO identity (matches UniversalCognitiveObject.uco_id)
    uco_id: Mapped[str] = mapped_column(String(128), primary_key=True)

    agent_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    summary: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    ontology_type: Mapped[str] = mapped_column(String(64), nullable=False, default="agent_episode")

    # Full UCO snapshot for faithful backfill into the in-memory index
    # (vectors are recomputed deterministically on load)
    uco_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "uco_id": self.uco_id,
            "agent_id": self.agent_id,
            "display_name": self.display_name,
            "description": self.description,
            "summary": self.summary,
            "ontology_type": self.ontology_type,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
