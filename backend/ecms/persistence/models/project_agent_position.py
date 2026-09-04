"""Project agent staffing models.

ProjectAgentPosition is the role the BA says a workspace needs.
ProjectAgentAssignment links that position to a reusable permanent Agent.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ecms.persistence.models.agent import Agent
from ecms.persistence.models.base import Base
from ecms.shared.time import utcnow

__all__ = ["ProjectAgentAssignment", "ProjectAgentPosition", "ProjectHumanAssignment"]


class ProjectAgentPosition(Base):
    __tablename__ = "project_agent_positions"
    __table_args__ = (
        UniqueConstraint("project_id", "position_key", name="uq_project_agent_position_key"),
    )

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    position_key: Mapped[str] = mapped_column(String(128), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    designation: Mapped[str] = mapped_column(String(255), nullable=False, default="", index=True)
    role_description: Mapped[str | None] = mapped_column(Text, nullable=True)
    skills: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    department: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    reports_to: Mapped[str | None] = mapped_column(
        String(128),
        ForeignKey("project_agent_positions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    model: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tool_policy: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    system_prompt_addon: Mapped[str | None] = mapped_column(Text, nullable=True)
    automation: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    features: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    manager: Mapped[ProjectAgentPosition | None] = relationship(
        "ProjectAgentPosition",
        remote_side="ProjectAgentPosition.id",
        back_populates="reports",
        foreign_keys=[reports_to],
    )
    reports: Mapped[list[ProjectAgentPosition]] = relationship(
        "ProjectAgentPosition",
        back_populates="manager",
        foreign_keys=[reports_to],
    )
    assignment: Mapped[ProjectAgentAssignment | None] = relationship(
        "ProjectAgentAssignment",
        back_populates="position",
        cascade="all, delete-orphan",
        uselist=False,
    )

    def to_dict(self, assigned_agent: Agent | None = None) -> dict[str, Any]:
        return {
            "id": self.id,
            "project_id": self.project_id,
            "position_key": self.position_key,
            "name": self.name,
            "role": self.role,
            "designation": self.designation,
            "role_description": self.role_description,
            "skills": self.skills or [],
            "department": self.department,
            "reports_to": self.reports_to,
            "model": self.model,
            "tool_policy": self.tool_policy or {},
            "system_prompt_addon": self.system_prompt_addon,
            "automation": self.automation or {},
            "features": self.features or {},
            "status": self.status,
            "filled": assigned_agent is not None,
            "assigned_agent": assigned_agent.to_dict() if assigned_agent else None,
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "updated_at": self.updated_at.isoformat() if self.updated_at else "",
        }


class ProjectAgentAssignment(Base):
    __tablename__ = "project_agent_assignments"

    position_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("project_agent_positions.id", ondelete="CASCADE"),
        primary_key=True,
    )
    agent_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("agents.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    assigned_by_user_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    assigned_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    position: Mapped[ProjectAgentPosition] = relationship(
        "ProjectAgentPosition",
        back_populates="assignment",
        foreign_keys=[position_id],
    )
    agent: Mapped[Agent] = relationship("Agent", foreign_keys=[agent_id])

    def to_dict(self) -> dict[str, Any]:
        return {
            "position_id": self.position_id,
            "agent_id": self.agent_id,
            "assigned_by_user_id": self.assigned_by_user_id,
            "assigned_at": self.assigned_at.isoformat() if self.assigned_at else "",
        }


class ProjectHumanAssignment(Base):
    __tablename__ = "project_human_assignments"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "scope",
            "position_id",
            "organization_member_id",
            name="uq_project_human_assignment",
        ),
    )

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    organization_member_id: Mapped[str] = mapped_column(
        String(128),
        ForeignKey("organization_members.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    position_id: Mapped[str | None] = mapped_column(
        String(128),
        ForeignKey("project_agent_positions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    scope: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    responsibility: Mapped[str] = mapped_column(
        String(64), nullable=False, default="workspace_owner"
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active", index=True)
    assigned_by_user_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    source: Mapped[str] = mapped_column(String(64), nullable=False, default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    def to_dict(self, organization_member: Any | None = None) -> dict[str, Any]:
        member_dict = organization_member.to_dict() if organization_member else None
        return {
            "id": self.id,
            "project_id": self.project_id,
            "organization_member_id": self.organization_member_id,
            "organization_member": member_dict,
            "position_id": self.position_id,
            "scope": self.scope,
            "responsibility": self.responsibility,
            "status": self.status,
            "assigned_by_user_id": self.assigned_by_user_id,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "updated_at": self.updated_at.isoformat() if self.updated_at else "",
        }
