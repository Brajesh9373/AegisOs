"""Durable metadata for immutable organization knowledge-graph snapshots."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column

from ecms.persistence.models.base import Base
from ecms.shared.time import utcnow

__all__ = ["KnowledgeGraphSnapshot"]


class KnowledgeGraphSnapshot(Base):
    """Build lifecycle and active pointer for one immutable graph version."""

    __tablename__ = "knowledge_graph_snapshots"
    __table_args__ = (
        Index(
            "uq_knowledge_graph_snapshot_current_org",
            "organization_id",
            unique=True,
            postgresql_where=text("is_current"),
            sqlite_where=text("is_current"),
        ),
        Index(
            "ix_knowledge_graph_snapshot_org_created",
            "organization_id",
            "created_at",
        ),
        UniqueConstraint(
            "organization_id",
            "version",
            name="uq_knowledge_graph_snapshot_org_version",
        ),
    )

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    organization_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    version: Mapped[str] = mapped_column(String(64), nullable=False)
    schema_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    state: Mapped[str] = mapped_column(String(24), nullable=False, index=True)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    points_object_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    links_object_key: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    points_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    links_checksum: Mapped[str | None] = mapped_column(String(64), nullable=True)
    point_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    link_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    points_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    links_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    source_watermark: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
