"""Agent identity ORM model.

Self-referential hierarchy: each agent reports to a parent agent.
CTO is the root (reports_to = NULL). Tool permissions and workspace
scope are stored as JSON policies.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ecms.persistence.models.base import Base
from ecms.shared.time import utcnow

__all__ = ["Agent"]


class Agent(Base):
    __tablename__ = "agents"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    designation: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    role_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    skills: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True)
    department: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    project_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True, index=True)
    model: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reports_to: Mapped[Optional[str]] = mapped_column(
        String(128), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True, index=True
    )
    tool_policy: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    workspace_scope: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    system_prompt_addon: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    automation: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    features: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    certificates: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    # Self-referential relationship
    manager: Mapped[Optional["Agent"]] = relationship(
        "Agent", remote_side="Agent.id", back_populates="reports", foreign_keys=[reports_to]
    )
    reports: Mapped[list["Agent"]] = relationship(
        "Agent", back_populates="manager", foreign_keys=[reports_to]
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "designation": self.designation,
            "role_description": self.role_description,
            "skills": self.skills or [],
            "department": self.department,
            "project_id": self.project_id,
            "model": self.model,
            "reports_to": self.reports_to,
            "tool_policy": self.tool_policy,
            "workspace_scope": self.workspace_scope,
            "system_prompt_addon": self.system_prompt_addon,
            "status": self.status,
            "automation": self.automation if hasattr(self, 'automation') else {},
            "features": self.features if hasattr(self, 'features') else {},
            "certificates": self.certificates or [],
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "updated_at": self.updated_at.isoformat() if self.updated_at else "",
        }
