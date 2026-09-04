"""AgentProfile ORM model for storing configurable agent profiles."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import JSON, DateTime, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ecms.persistence.models.base import Base


def utcnow() -> datetime:
    """Return current UTC time."""
    return datetime.now(timezone.utc)


class AgentProfile(Base):
    """Storable agent profile with configurable scopes.

    This model allows creating agent profiles dynamically without Python plugins.
    Each profile defines its identity, system prompt, hierarchy, and permission scopes.
    """

    __tablename__ = "agent_profiles"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4()),
    )
    profile_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
        doc="Unique profile identifier (e.g., 'business-analyst', 'data-engineer')",
    )
    name: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        doc="Human-readable profile name",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        doc="Profile purpose and responsibilities",
    )
    version: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="1.0.0",
        doc="Profile version for tracking changes",
    )
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default="active",
        doc="Profile status: active, deprecated, draft",
    )

    # Identity and hierarchy
    role: Mapped[str] = mapped_column(
        String(64),
        nullable=True,
        doc="Agent role designation (e.g., 'senior_dev', 'data_engineer')",
    )
    parent_profile_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        doc="Parent profile this agent reports to",
    )

    # Core agent configuration
    system_prompt: Mapped[str] = mapped_column(
        Text,
        nullable=True,
        doc="System prompt defining agent behavior and instructions",
    )
    user_prompt_template: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Template for user prompts with variable substitution",
    )

    # Stage definitions (for DSH profiles)
    stages: Mapped[list[dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        doc="List of stage definitions: [{stage_id, description, max_capability_requests}]",
    )

    # Scope configurations
    memory_scope: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        doc="Memory access config: {read: bool, write: bool, categories: [], retention_days: int}",
    )
    knowledge_scope: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        doc="Knowledge graph access: {graphs: [], read: bool, write: bool, node_types: []}",
    )
    tool_scope: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
        doc="Tool permissions: {allowed_tools: [], rate_limit: int, restrictions: {}}",
    )

    # AI-generated scope recommendations
    scope_recommendations: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        doc="AI-suggested scopes based on role analysis",
    )

    # LLM configuration
    model_provider: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        doc="LLM provider: openai, anthropic, deepseek",
    )
    model_name: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        doc="Model identifier (e.g., gpt-4o, claude-3-5-sonnet)",
    )
    temperature: Mapped[float | None] = mapped_column(
        nullable=True,
        doc="Sampling temperature for LLM",
    )
    max_tokens: Mapped[int | None] = mapped_column(
        nullable=True,
        doc="Max tokens for LLM response",
    )

    # Execution budget
    execution_budget: Mapped[dict[str, Any] | None] = mapped_column(
        JSON,
        nullable=True,
        doc="DSH execution limits: {timeout_seconds, max_task_bytes, max_stdout_bytes}",
    )

    # Metadata
    created_by: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        doc="User who created the profile",
    )
    createdat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updatedat: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Note: Self-referential relationship not implemented
    # parent_profile_id is a simple string reference, not a foreign key
    # If needed, can be queried via explicit joins

    __table_args__ = (
        Index("ix_agent_profiles_status", "status"),
        Index("ix_agent_profiles_parent", "parent_profile_id"),
    )

    def __repr__(self) -> str:
        return f"<AgentProfile {self.profile_id} v{self.version}>"