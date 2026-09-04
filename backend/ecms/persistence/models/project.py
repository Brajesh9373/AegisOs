"""Project + connector ORM models (SECTION 301).

Each workspace project owns many connectors. Connectors store non-secret
configuration (URL, host, database name, etc.) — tokens/passwords are never
persisted. Cascade delete is handled at the application level.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ecms.persistence.models.base import Base
from ecms.shared.time import utcnow

__all__ = ["Project", "ProjectConnector"]


class Project(Base):
    """A workspace project — source-of-truth for project metadata."""

    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    workspace_id: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    group_id: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        onupdate=utcnow,
    )

    connectors: Mapped[list[ProjectConnector]] = relationship(
        "ProjectConnector",
        back_populates="project",
        cascade="all, delete-orphan",
    )


class ProjectConnector(Base):
    """Non-secret connector configuration for a project.

    Stores type, URL/host/branch/database name, and any additional metadata.
    Tokens, passwords, and API keys are excluded.
    """

    __tablename__ = "project_connectors"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True
    )
    connector_type: Mapped[str] = mapped_column(String(64), nullable=False)
    config: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    persist_path: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    project: Mapped[Project] = relationship("Project", back_populates="connectors")
