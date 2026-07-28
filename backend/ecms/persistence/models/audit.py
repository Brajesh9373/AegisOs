"""Audit record ORM model (SECTION 65/81)."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from ecms.persistence.models.base import Base
from ecms.shared.ids import new_id
from ecms.shared.time import utcnow

__all__ = ["AuditRecord"]


def _audit_id() -> str:
    return new_id("audit")


class AuditRecord(Base):
    """An immutable audit-log entry (SECTION 65)."""

    __tablename__ = "audit_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True, default=_audit_id)
    actor: Mapped[str] = mapped_column(String(255), index=True)
    action: Mapped[str] = mapped_column(String(255), index=True)
    resource: Mapped[str] = mapped_column(String(255))
    outcome: Mapped[str] = mapped_column(String(32))
    details: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=utcnow,
        index=True,
    )
