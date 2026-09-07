"""Agent procedural memory, long-term preferences, and organizational patterns.

Three durable stores that complete the memory layers alongside episodic
exchanges (agent_episodes):

- AgentProcedure: a named multi-step workflow an agent learned
  (learn_procedure / recall_procedure).
- AgentPreference: a long-term key/value preference, optionally scoped to one
  agent or shared across the team (remember / recall).
- OrgPattern: a validated best practice / known bug / convention published
  for all agents (publish_pattern / search_patterns).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ecms.persistence.models.base import Base
from ecms.shared.time import utcnow

__all__ = ["AgentProcedure", "AgentPreference", "OrgPattern"]


class AgentProcedure(Base):
    __tablename__ = "agent_procedures"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False, default="")
    steps: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    learned_by: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    use_count: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "steps": self.steps,
            "learned_by": self.learned_by,
            "use_count": self.use_count,
        }


class AgentPreference(Base):
    __tablename__ = "agent_preferences"

    # Composite identity: one key per scope ("agent:<id>" or "team:shared").
    scope: Mapped[str] = mapped_column(String(128), nullable=False, primary_key=True)
    key: Mapped[str] = mapped_column(String(255), nullable=False, primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False, default="")
    updated_by: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    def to_dict(self) -> dict[str, Any]:
        return {"scope": self.scope, "key": self.key, "value": self.value}


class OrgPattern(Base):
    __tablename__ = "org_patterns"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    pattern_type: Mapped[str] = mapped_column(String(32), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    published_by: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "pattern_type": self.pattern_type,
            "description": self.description,
            "published_by": self.published_by,
        }
