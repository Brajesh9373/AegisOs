"""Topic registry mapping event categories to bus topics (SECTION 99)."""

from __future__ import annotations

from ecms.shared.enums import EventCategory

__all__ = ["TopicRegistry"]


class TopicRegistry:
    """Maps event categories to durable topic names for transport routing."""

    def __init__(self, prefix: str = "ecms.events") -> None:
        """Initialize the registry with a topic-name prefix."""
        self._prefix = prefix

    def topic_for(self, category: EventCategory) -> str:
        """Return the topic name for an event category."""
        return f"{self._prefix}.{category.value}"

    def all_topics(self) -> list[str]:
        """Return the topic name for every known event category."""
        return [self.topic_for(category) for category in EventCategory]
