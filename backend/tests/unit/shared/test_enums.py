"""Tests for ``ecms.shared.enums``."""

from __future__ import annotations

from ecms.shared.enums import (
    EventCategory,
    LifecycleState,
    ProcessingStatus,
    SecurityClassification,
    ValidationStatus,
)


def test_security_classification_values() -> None:
    assert SecurityClassification.PUBLIC.value == "public"
    assert len(SecurityClassification) == 5


def test_lifecycle_state_values() -> None:
    assert LifecycleState.ACTIVE.value == "active"
    assert len(LifecycleState) == 5


def test_processing_status_values() -> None:
    assert ProcessingStatus.PENDING.value == "pending"
    assert len(ProcessingStatus) == 4


def test_validation_status_values() -> None:
    assert ValidationStatus.NEEDS_REVIEW.value == "needs_review"


def test_event_category_contains_core_members() -> None:
    values = {category.value for category in EventCategory}
    assert {"knowledge", "memory", "runtime", "provider", "graph"} <= values
