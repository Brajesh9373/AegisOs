"""SQLAlchemy declarative base (SECTION 81)."""

from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase

__all__ = ["Base"]


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""
