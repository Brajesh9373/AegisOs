"""Universal knowledge and cognitive object models (SECTION 22/23/29/30).

Separates raw information (:class:`UniversalKnowledgeObject`) from enterprise understanding
(:class:`UniversalCognitiveObject`). A UKO never contains reasoning; a UCO never contains
raw source data. UCOs are the source of truth; the graph is an index.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from ecms.shared.enums import (
    LifecycleState,
    ProcessingStatus,
    RelationshipDirection,
    SecurityClassification,
    ValidationStatus,
)
from ecms.shared.ids import new_id
from ecms.shared.models.base import (
    AggregateRoot,
    Attachment,
    DomainModel,
    ImmutableModel,
    SecurityPolicy,
)
from ecms.shared.time import utcnow

__all__ = [
    "Episode",
    "Evidence",
    "ProviderRelationship",
    "Relationship",
    "UniversalCognitiveObject",
    "UniversalKnowledgeObject",
]


def _uko_id() -> str:
    return new_id("uko")


def _uco_id() -> str:
    return new_id("uco")


def _relationship_id() -> str:
    return new_id("rel")


def _episode_id() -> str:
    return new_id("ep")


class ProviderRelationship(DomainModel):
    """A relationship between raw objects as discovered by a provider (SECTION 22)."""

    target_object_id: str
    relationship_type: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class Evidence(DomainModel):
    """A traceable reference supporting a cognitive object (SECTION 139).

    Evidence links understanding back to the raw information that justifies it, and
    remains traceable to its source, origin and checksum.
    """

    uko_id: str
    description: str | None = None
    confidence: int = Field(default=0, ge=0, le=100)
    source: str | None = None
    origin: str | None = None
    checksum: str | None = None
    reference: str | None = None
    timestamp: datetime = Field(default_factory=utcnow)


class UniversalKnowledgeObject(AggregateRoot):
    """Normalized snapshot of raw information from an external platform (SECTION 22).

    A UKO captures raw content and provider metadata exactly as collected and forms the
    evidence layer of the Global Cognitive Graph. It never contains reasoning.
    """

    uko_id: str = Field(default_factory=_uko_id)
    provider: str
    provider_object_type: str
    provider_object_id: str
    organization_id: str
    workspace_id: str | None = None
    project_id: str | None = None
    repository_id: str | None = None
    parent_id: str | None = None
    collected_at: datetime = Field(default_factory=utcnow)
    version: int = Field(default=1, ge=1)
    checksum: str | None = None
    title: str
    description: str | None = None
    raw_content: str = ""
    attachments: list[Attachment] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)
    labels: list[str] = Field(default_factory=list)
    language: str | None = None
    mime_type: str | None = None
    status: str | None = None
    author: str | None = None
    contributors: list[str] = Field(default_factory=list)
    permissions: dict[str, Any] = Field(default_factory=dict)
    relationships: list[ProviderRelationship] = Field(default_factory=list)
    references: list[str] = Field(default_factory=list)
    embedding: list[float] | None = None
    processing_status: ProcessingStatus = ProcessingStatus.PENDING
    validation_status: ValidationStatus = ValidationStatus.NEEDS_REVIEW
    security_classification: SecurityClassification = SecurityClassification.INTERNAL


class UniversalCognitiveObject(ImmutableModel):
    """Immutable snapshot of enterprise understanding derived from UKOs (SECTION 23).

    UCOs are the source of truth; the graph is an index. Updates create new versions
    rather than mutating an existing object.
    """

    uco_id: str = Field(default_factory=_uco_id)
    canonical_name: str
    display_name: str
    ontology_type: str
    description: str
    summary: str | None = None
    aliases: list[str] = Field(default_factory=list)
    confidence: int = Field(default=0, ge=0, le=100)
    importance: int = Field(default=0, ge=0, le=100)
    business_value: int = Field(default=0, ge=0, le=100)
    reusability: int = Field(default=0, ge=0, le=100)
    stability: int = Field(default=0, ge=0, le=100)
    lifecycle_state: LifecycleState = LifecycleState.DRAFT
    created_at: datetime = Field(default_factory=utcnow)
    updated_at: datetime = Field(default_factory=utcnow)
    created_by: str | None = None
    last_modified_by: str | None = None
    episodes: list[str] = Field(default_factory=list)
    evidence: list[Evidence] = Field(default_factory=list)
    relationships: list[str] = Field(default_factory=list)
    knowledge_sources: list[str] = Field(default_factory=list)
    graph_node_id: str | None = None
    security_policy: SecurityPolicy = Field(default_factory=SecurityPolicy)
    activation_statistics: dict[str, Any] = Field(default_factory=dict)
    usage_statistics: dict[str, Any] = Field(default_factory=dict)
    history: list[dict[str, Any]] = Field(default_factory=list)
    custom_attributes: dict[str, Any] = Field(default_factory=dict)


class Relationship(DomainModel):
    """A first-class semantic relationship between two cognitive objects (SECTION 30)."""

    relationship_id: str = Field(default_factory=_relationship_id)
    source_uco: str
    target_uco: str
    relationship_type: str
    confidence: int = Field(default=0, ge=0, le=100)
    importance: int = Field(default=0, ge=0, le=100)
    weight: float = Field(default=1.0, ge=0.0)
    direction: RelationshipDirection = RelationshipDirection.DIRECTED
    created_at: datetime = Field(default_factory=utcnow)
    created_by: str | None = None
    evidence: list[str] = Field(default_factory=list)
    episodes: list[str] = Field(default_factory=list)
    status: LifecycleState = LifecycleState.ACTIVE
    version: int = Field(default=1, ge=1)
    history: list[dict[str, Any]] = Field(default_factory=list)


class Episode(ImmutableModel):
    """An immutable record of how knowledge evolved over time (SECTION 29)."""

    episode_id: str = Field(default_factory=_episode_id)
    episode_type: str
    timestamp: datetime = Field(default_factory=utcnow)
    description: str
    trigger: str | None = None
    source_uko: str | None = None
    affected_uco: str | None = None
    graph_changes: list[dict[str, Any]] = Field(default_factory=list)
    evidence: list[str] = Field(default_factory=list)
    participants: list[str] = Field(default_factory=list)
    affected_relationships: list[str] = Field(default_factory=list)
    artifacts: list[str] = Field(default_factory=list)
