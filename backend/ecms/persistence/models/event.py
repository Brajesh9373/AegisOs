"""Append-only event-store ORM model (SECTION 65/67).

Events are never updated or deleted. The monotonic ``sequence`` column preserves
global insertion order so the platform can be rebuilt by replaying the store.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ecms.persistence.models.base import Base
from ecms.shared.time import utcnow

__all__ = ["EventRecord"]


class EventRecord(Base):
    """A single durably-stored event; the store is append-only (SECTION 67)."""

    __tablename__ = "event_store"

    sequence: Mapped[int] = mapped_column(
        BigInteger().with_variant(Integer, "sqlite"),
        primary_key=True,
        autoincrement=True,
    )
    event_id: Mapped[str] = mapped_column(String(128), index=True)
    event_type: Mapped[str] = mapped_column(String(128), index=True)
    event_category: Mapped[str] = mapped_column(String(32), index=True)
    correlation_id: Mapped[str | None] = mapped_column(String(128), index=True, nullable=True)
    payload: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, index=True
    )
