"""Organization member ORM model.

Represents permanent AegisOS company hierarchy members.
Distinct from project-generated runtime agents (which live in the `agents` table).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ecms.persistence.models.base import Base
from ecms.shared.time import utcnow

__all__ = ["OrganizationMember"]


class OrganizationMember(Base):
    __tablename__ = "organization_members"

    id: Mapped[str] = mapped_column(String(128), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    designation: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    role: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    department: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    role_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    skills: Mapped[Optional[list[Any]]] = mapped_column(JSON, nullable=True)
    reports_to: Mapped[Optional[str]] = mapped_column(
        String(128),
        ForeignKey("organization_members.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=utcnow, onupdate=utcnow,
    )

    # Self-referential hierarchy
    manager: Mapped[Optional["OrganizationMember"]] = relationship(
        "OrganizationMember",
        remote_side="OrganizationMember.id",
        back_populates="reports",
        foreign_keys=[reports_to],
    )
    reports: Mapped[list["OrganizationMember"]] = relationship(
        "OrganizationMember",
        back_populates="manager",
        foreign_keys=[reports_to],
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "designation": self.designation,
            "role": self.role,
            "department": self.department,
            "role_description": self.role_description,
            "skills": self.skills or [],
            "reports_to": self.reports_to,
            "status": self.status,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat() if self.created_at else "",
            "updated_at": self.updated_at.isoformat() if self.updated_at else "",
        }
