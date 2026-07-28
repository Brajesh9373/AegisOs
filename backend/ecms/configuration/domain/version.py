"""Configuration version model (SECTION 97)."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from ecms.shared.models.base import ImmutableModel
from ecms.shared.time import utcnow

__all__ = ["ConfigVersion"]


class ConfigVersion(ImmutableModel):
    """An immutable, versioned snapshot of resolved configuration values (SECTION 97)."""

    version: int = Field(ge=1)
    values: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
