"""Task ORM model.

Tasks are assigned by one agent (assigner) to another (assignee) through
the delegation hierarchy. Tasks track status, inputs, expected outputs,
review feedback, and produced artifacts.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ecms.persistence.models.base import Base
from ecms.shared.time import utcnow

__all__ = ["CrossTeamRequest", "Task", "TaskDependency"]


class Task(Base):
    __tablename__ = "tasks"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    assigner_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    assignee_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(32), default="pending", index=True
    )  # pending | in_progress | submitted | approved | rejected
    priority: Mapped[str] = mapped_column(
        String(32), default="normal"
    )  # low | normal | high | blocking
    inputs: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    expected_output: Mapped[str | None] = mapped_column(Text, nullable=True)
    output_files: Mapped[list[Any] | None] = mapped_column(JSON, nullable=True)
    output_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    review_feedback: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_task_id: Mapped[str | None] = mapped_column(
        String(128), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )

    assigner: Mapped[Agent] = relationship("Agent", foreign_keys=[assigner_id])
    assignee: Mapped[Agent] = relationship("Agent", foreign_keys=[assignee_id])

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "assigner_id": self.assigner_id,
            "assignee_id": self.assignee_id,
            "status": self.status,
            "priority": self.priority,
            "inputs": self.inputs,
            "expected_output": self.expected_output,
            "output_files": self.output_files,
            "output_summary": self.output_summary,
            "review_feedback": self.review_feedback,
            "parent_task_id": self.parent_task_id,
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "updated_at": self.updated_at.isoformat() if self.updated_at else "",
        }


class TaskDependency(Base):
    __tablename__ = "task_dependencies"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    blocked_task_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    blocker_task_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    dependency_type: Mapped[str] = mapped_column(
        String(32), default="same_team"
    )  # same_team | cross_team
    cross_team_request_id: Mapped[str | None] = mapped_column(
        String(128), ForeignKey("cross_team_requests.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class CrossTeamRequest(Base):
    __tablename__ = "cross_team_requests"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    title: Mapped[str] = mapped_column(String(512), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    requester_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_dept: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    target_senior_id: Mapped[str | None] = mapped_column(
        String(128), ForeignKey("agents.id", ondelete="SET NULL"), nullable=True
    )
    spawned_task_id: Mapped[str | None] = mapped_column(
        String(128), ForeignKey("tasks.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        String(32), default="pending", index=True
    )  # pending | accepted | in_progress | fulfilled | declined
    priority: Mapped[str] = mapped_column(String(32), default="normal")
    inputs: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    output: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "requester_id": self.requester_id,
            "target_dept": self.target_dept,
            "target_senior_id": self.target_senior_id,
            "spawned_task_id": self.spawned_task_id,
            "status": self.status,
            "priority": self.priority,
            "inputs": self.inputs,
            "output": self.output,
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else "",
        }
