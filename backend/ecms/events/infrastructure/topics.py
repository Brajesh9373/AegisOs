"""Kafka topic taxonomy for enterprise events (SECTION 249).

Every event category maps to one Kafka topic. Centralizing the naming keeps
producers and consumers consistent and lets the topic set be provisioned from a
single source of truth.
"""

from __future__ import annotations

from ecms.shared.enums import EventCategory

__all__ = ["all_topics", "event_topic"]


def event_topic(category: EventCategory, *, prefix: str = "ecms") -> str:
    """Return the Kafka topic name for an event category (for example ``ecms.task``)."""
    return f"{prefix}.{category.value}"


def all_topics(*, prefix: str = "ecms") -> list[str]:
    """Return the Kafka topic names for every event category."""
    return [event_topic(category, prefix=prefix) for category in EventCategory]
