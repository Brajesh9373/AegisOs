"""Event bus domain models (SECTION 68/99)."""

from __future__ import annotations

from datetime import datetime

from pydantic import Field

from ecms.shared.events import BaseEvent
from ecms.shared.models.base import DomainModel
from ecms.shared.time import utcnow

__all__ = ["BusMetrics", "DeadLetter"]


class DeadLetter(DomainModel):
    """An event whose delivery failed after exhausting retries (SECTION 99)."""

    event: BaseEvent
    error: str
    attempts: int = Field(ge=1)
    failed_at: datetime = Field(default_factory=utcnow)


class BusMetrics(DomainModel):
    """Counters describing event-bus activity (SECTION 99)."""

    published: int = 0
    delivered: int = 0
    failed: int = 0
    dead_lettered: int = 0
    retried: int = 0
