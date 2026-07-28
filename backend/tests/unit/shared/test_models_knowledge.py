"""Tests for the knowledge domain models."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ecms.shared.enums import (
    LifecycleState,
    ProcessingStatus,
    RelationshipDirection,
    SecurityClassification,
    ValidationStatus,
)
from ecms.shared.models import (
    Episode,
    Relationship,
    UniversalCognitiveObject,
    UniversalKnowledgeObject,
)


def _uko() -> UniversalKnowledgeObject:
    return UniversalKnowledgeObject(
        provider="github",
        provider_object_type="commit",
        provider_object_id="abc123",
        organization_id="org-1",
        title="Initial commit",
    )


def test_uko_defaults_and_id_prefix() -> None:
    uko = _uko()
    assert uko.uko_id.startswith("uko-")
    assert uko.version == 1
    assert uko.processing_status is ProcessingStatus.PENDING
    assert uko.validation_status is ValidationStatus.NEEDS_REVIEW
    assert uko.security_classification is SecurityClassification.INTERNAL


def test_uko_rejects_unknown_field() -> None:
    with pytest.raises(ValidationError):
        UniversalKnowledgeObject(
            provider="x",
            provider_object_type="y",
            provider_object_id="z",
            organization_id="o",
            title="t",
            bogus=1,
        )


def test_uko_records_and_clears_domain_events() -> None:
    uko = _uko()
    uko.register_event({"type": "created"})
    assert uko.collect_events() == [{"type": "created"}]
    assert uko.collect_events() == []


def test_uco_is_immutable_and_validates_scores() -> None:
    uco = UniversalCognitiveObject(
        canonical_name="Auth Service",
        display_name="Authentication Service",
        ontology_type="Service",
        description="Handles authentication",
    )
    assert uco.uco_id.startswith("uco-")
    assert uco.lifecycle_state is LifecycleState.DRAFT
    assert uco.security_policy.classification is SecurityClassification.INTERNAL
    with pytest.raises(ValidationError):
        uco.confidence = 50
    with pytest.raises(ValidationError):
        UniversalCognitiveObject(
            canonical_name="x",
            display_name="x",
            ontology_type="Service",
            description="d",
            confidence=150,
        )


def test_relationship_defaults() -> None:
    rel = Relationship(source_uco="uco-a", target_uco="uco-b", relationship_type="implements")
    assert rel.relationship_id.startswith("rel-")
    assert rel.direction is RelationshipDirection.DIRECTED
    assert rel.status is LifecycleState.ACTIVE


def test_episode_is_immutable() -> None:
    episode = Episode(episode_type="knowledge_created", description="created auth service")
    assert episode.episode_id.startswith("ep-")
    with pytest.raises(ValidationError):
        episode.description = "changed"
