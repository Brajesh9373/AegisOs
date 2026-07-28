"""Tests for ``ecms.shared.events``."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ecms.shared.context import bind_context, clear_context
from ecms.shared.enums import EventCategory, SecurityClassification
from ecms.shared.events import BaseEvent, make_event


def test_base_event_defaults() -> None:
    event = BaseEvent(
        event_type="ServiceStarted",
        event_category=EventCategory.SYSTEM,
        producer="api",
    )
    assert event.event_id.startswith("evt-")
    assert event.event_version == 1
    assert event.security_classification is SecurityClassification.INTERNAL
    assert event.producer_version


def test_base_event_is_immutable() -> None:
    event = BaseEvent(event_type="X", event_category=EventCategory.SYSTEM, producer="api")
    with pytest.raises(ValidationError):
        event.event_type = "Y"


def test_make_event_uses_context() -> None:
    clear_context()
    bind_context(correlation_id="corr-1", session_id="s1", task_id="t1", trace_id="tr1")
    event = make_event(
        "KnowledgeCreated",
        EventCategory.KNOWLEDGE,
        "knowledge",
        payload={"uco_id": "uco-1"},
    )
    assert event.correlation_id == "corr-1"
    assert event.session_id == "s1"
    assert event.task_id == "t1"
    assert event.trace_context == {"trace_id": "tr1"}
    assert event.payload == {"uco_id": "uco-1"}
    clear_context()
