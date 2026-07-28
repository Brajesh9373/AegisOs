"""Tests for event serialization and the topic registry."""

from __future__ import annotations

import pytest

from ecms.events import TopicRegistry, deserialize_event, serialize_event
from ecms.shared.enums import EventCategory
from ecms.shared.events import BaseEvent
from ecms.shared.exceptions import SerializationError


def test_serialization_round_trip() -> None:
    event = BaseEvent(event_type="X", event_category=EventCategory.SYSTEM, producer="t")
    restored = deserialize_event(serialize_event(event))
    assert restored.event_id == event.event_id
    assert restored.event_type == "X"


def test_deserialize_invalid_raises() -> None:
    with pytest.raises(SerializationError):
        deserialize_event("{}")


def test_topic_for_category() -> None:
    assert TopicRegistry().topic_for(EventCategory.KNOWLEDGE) == "ecms.events.knowledge"


def test_all_topics_cover_every_category() -> None:
    assert len(TopicRegistry().all_topics()) == len(EventCategory)
