"""Generic aggregate-record ORM model (SECTION 244/251/254/259).

Every aggregate is persisted as a versioned, tenant-scoped JSON document. This
keeps storage hidden behind repositories, supports soft-delete and versioning
uniformly, and scales without a bespoke table per aggregate type. The columns
used for querying (type, tenant, lifecycle) are promoted to indexed columns.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from ecms.persistence.models.base import Base
from ecms.shared.time import utcnow

__all__ = ["AggregateRecord"]


class AggregateRecord(Base):
    """A versioned, tenant-scoped persisted aggregate document (SECTION 251)."""

    __tablename__ = "aggregates"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    aggregate_type: Mapped[str] = mapped_column(String(128), index=True)
    organization_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    workspace_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    project_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    lifecycle_state: Mapped[str] = mapped_column(String(32), default="active", index=True)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow
    )
