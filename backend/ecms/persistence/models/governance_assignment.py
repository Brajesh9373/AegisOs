"""Governance assignment ORM model.

Links permanent organization members to project-scoped runtime agents
with a defined responsibility (primary_owner, monitor, approver).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ecms.persistence.models.base import Base
from ecms.persistence.models.agent import Agent  # noqa: F401  (required for relationship resolution)
from ecms.shared.time import utcnow

__all__ = ["ProjectAgentGovernanceAssignment"]


class ProjectAgentGovernanceAssignment(Base):
    __tablename__ = "project_agent_governance_assignments"
    __table_args__ = (
        UniqueConstraint(
            "organization_member_id", "project_agent_id", "responsibility",
            name="uq_member_agent_responsibility",
        ),
    )

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    organization_member_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("organization_members.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    project_agent_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("agents.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    responsibility: Mapped[str] = mapped_column(
        String(32), nullable=False, index=True,
    )  # primary_owner | monitor | approver
    status: Mapped[str] = mapped_column(
        String(32), nullable=False, default="active", index=True,
    )  # active | needs_review | revoked
    assigned_by_user_id: Mapped[str] = mapped_column(String(128), nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow,
    )
    review_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Relationships
    member: Mapped["OrganizationMember"] = relationship(
        "OrganizationMember", foreign_keys=[organization_member_id],
        passive_deletes=True,
    )
    agent: Mapped["Agent"] = relationship(
        "Agent", foreign_keys=[project_agent_id],
        primaryjoin="ProjectAgentGovernanceAssignment.project_agent_id == foreign(Agent.id)",
        passive_deletes=True,
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "organization_member_id": self.organization_member_id,
            "project_agent_id": self.project_agent_id,
            "project_id": self.project_id,
            "responsibility": self.responsibility,
            "status": self.status,
            "assigned_by_user_id": self.assigned_by_user_id,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else "",
            "updated_at": self.updated_at.isoformat() if self.updated_at else "",
            "review_reason": self.review_reason,
        }
