"""Generic Agent OS run and step persistence models.

These provide organization-scoped run tracking independent of any profile-specific
outcome tables. They complement the existing BA-specific outcome tables.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, CheckConstraint, DateTime, ForeignKey, ForeignKeyConstraint, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ecms.persistence.models.base import Base
from ecms.shared.time import utcnow

__all__ = ["AgentRun", "AgentRunStep", "RunState", "StepState"]


class RunState(StrEnum):
    """Possible states for an AgentRun."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepState(StrEnum):
    """Possible states for an AgentRunStep."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class AgentRun(Base):
    """Organization-scoped execution of an Agent OS profile.

    This provides the generic durable run tracking that all profiles use.
    Profile-specific outcomes (like BA receipts) reference this run.
    """

    __tablename__ = "agent_runs"
    __table_args__ = (
        Index("ix_agent_runs_org_created", "organization_id", "created_at"),
        Index("ix_agent_runs_org_profile", "organization_id", "profile_id"),
        Index("ix_agent_runs_correlation", "correlation_id"),
        CheckConstraint(
            "state IN ('pending','running','completed','failed','cancelled')",
            name="ck_agent_run_state",
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    profile_id: Mapped[str] = mapped_column(String(64), nullable=False)
    profile_version: Mapped[str] = mapped_column(String(64), nullable=False)
    correlation_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    idempotency_key: Mapped[str] = mapped_column(String(64), nullable=False)

    # Request context (limited, non-secret metadata)
    request_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    # State tracking
    state: Mapped[str] = mapped_column(
        String(32), nullable=False, default=RunState.PENDING.value
    )

    # Profile fingerprint at execution time
    profile_fingerprint: Mapped[str] = mapped_column(String(255), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Execution metrics (non-secret)
    execution_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    total_steps: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_error: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Relationship to steps
    steps: Mapped[list[AgentRunStep]] = relationship(
        "AgentRunStep", back_populates="run", cascade="all, delete-orphan"
    )


class AgentRunStep(Base):
    """Monotonic step record within an AgentRun.

    Steps are immutable once recorded - they only transition forward.
    """

    __tablename__ = "agent_run_steps"
    __table_args__ = (
        Index("ix_agent_run_steps_run_index", "run_id", "step_index"),
        Index("ix_agent_run_steps_org_created", "organization_id", "created_at"),
        ForeignKeyConstraint(
            ["run_id", "organization_id"],
            ["agent_runs.id", "agent_runs.organization_id"],
            ondelete="CASCADE",
            name="fk_agent_run_step_run",
        ),
        CheckConstraint(
            "state IN ('pending','running','completed','failed')",
            name="ck_agent_run_step_state",
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)

    # Step sequencing
    step_index: Mapped[int] = mapped_column(Integer, nullable=False)
    stage_id: Mapped[str] = mapped_column(String(64), nullable=False)

    # State
    state: Mapped[str] = mapped_column(
        String(32), nullable=False, default=StepState.PENDING.value
    )

    # Receipt data (checksum, not full content)
    receipt_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)
    output_checksum: Mapped[str] = mapped_column(String(64), nullable=False)

    # Timing
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Execution metrics
    execution_duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    repair_attempts: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Error tracking
    last_error: Mapped[str | None] = mapped_column(String(512), nullable=True)

    # Relationship to run
    run: Mapped[AgentRun] = relationship("AgentRun", back_populates="steps")