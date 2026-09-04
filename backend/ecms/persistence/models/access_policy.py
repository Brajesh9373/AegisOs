"""Access policy and recommendation ORM models.

Policies are separate database rows evaluated at query time — resources carry
only intrinsic attributes. Root agents (reports_to IS NULL) bypass all checks.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ecms.persistence.models.base import Base
from ecms.shared.time import utcnow

__all__ = ["AccessPolicy", "PolicyRecommendation"]


class AccessPolicy(Base):
    __tablename__ = "access_policies"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    effect: Mapped[str] = mapped_column(String(16), nullable=False)  # 'allow' | 'deny'

    # Subject matching
    agent_id: Mapped[str | None] = mapped_column(
        String(128), ForeignKey("agents.id", ondelete="CASCADE"), nullable=True, index=True
    )
    department: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    role_level_min: Mapped[int | None] = mapped_column(Integer, nullable=True, default=1)

    # Resource matching
    resource_type: Mapped[str | None] = mapped_column(
        String(32), nullable=True
    )  # 'memory_atom' | 'graph_node' | 'file' | None = all
    path_pattern: Mapped[str | None] = mapped_column(String(512), nullable=True)
    source_type: Mapped[str | None] = mapped_column(
        String(64), nullable=True
    )  # 'git' | 'mysql' | 'jira' | None = all
    resource_attrs: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)

    # Actions
    action: Mapped[str] = mapped_column(
        String(16), nullable=False
    )  # 'read' | 'write' | 'delete' | '*'

    # Metadata
    priority: Mapped[int] = mapped_column(Integer, default=100)
    created_by: Mapped[str | None] = mapped_column(
        String(128), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "effect": self.effect,
            "agent_id": self.agent_id,
            "department": self.department,
            "role_level_min": self.role_level_min,
            "resource_type": self.resource_type,
            "path_pattern": self.path_pattern,
            "source_type": self.source_type,
            "resource_attrs": self.resource_attrs,
            "action": self.action,
            "priority": self.priority,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "updated_at": self.updated_at.isoformat() if self.updated_at else "",
        }


class PolicyRecommendation(Base):
    __tablename__ = "policy_recommendations"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    project_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    policies_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    org_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(32), default="pending", index=True
    )  # pending|approved|rejected|modified
    reviewed_by: Mapped[str | None] = mapped_column(
        String(128), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[str | None] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "project_id": self.project_id,
            "policies_json": self.policies_json,
            "status": self.status,
            "reviewed_by": self.reviewed_by,
            "reviewed_at": self.reviewed_at.isoformat() if self.reviewed_at else "",
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat() if self.created_at else "",
        }
