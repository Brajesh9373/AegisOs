"""Memory domain models — atoms, relationships, evidence, and types.

Storage-agnostic. All models are pure Pydantic — no I/O, no DB assumptions.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


# ── Memory Types ────────────────────────────────────────────────────

class MemoryType(str, Enum):
    """Knowledge category for an atom. Extensible — add new values freely."""

    FACT = "fact"
    ARCHITECTURE = "architecture"
    DECISION = "decision"
    CONVENTION = "convention"
    OBSERVATION = "observation"
    BUG = "bug"
    LIMITATION = "limitation"
    INVESTIGATION = "investigation"
    HYPOTHESIS = "hypothesis"
    RESOLUTION = "resolution"
    MIGRATION = "migration"
    TRADE_OFF = "trade_off"
    PERFORMANCE = "performance"
    BEST_PRACTICE = "best_practice"
    SECURITY = "security"
    DESIGN_RATIONALE = "design_rationale"
    KNOWN_RISK = "known_risk"


class MemoryStatus(str, Enum):
    DRAFT = "draft"
    VERIFIED = "verified"
    SUPERSEDED = "superseded"


class MemoryScope(str, Enum):
    WORKSPACE = "workspace"
    PROJECT = "project"
    ORGANIZATION = "organization"
    GLOBAL = "global"


# ── Relationship Types ──────────────────────────────────────────────

class RelationshipType(str, Enum):
    """Directed relationship between two memory atoms."""

    PART_OF = "part_of"
    IMPLEMENTS = "implements"
    DEPENDS_ON = "depends_on"
    RELATED_TO = "related_to"
    REFERENCES = "references"
    DERIVED_FROM = "derived_from"
    SUPERSEDES = "supersedes"
    CONTRADICTS = "contradicts"
    AFFECTS = "affects"
    RESOLVES = "resolves"
    REPLACES = "replaces"


class MemoryRelationship(BaseModel):
    """A directed relationship between two memory atoms."""

    id: str = Field(description="Unique relationship ID, e.g. REL-001")
    source_id: str = Field(description="Source atom ID")
    target_id: str = Field(description="Target atom ID")
    type: RelationshipType = Field(description="Relationship type")
    confidence: float = Field(default=0.80, ge=0.0, le=1.0)
    evidence: list[str] = Field(default_factory=list, description="Supporting evidence for this relationship")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def generate_id(cls) -> str:
        import uuid
        return f"REL-{uuid.uuid4().hex[:8].upper()}"


# ── Related Atom Reference (embedded in MemoryAtom) ─────────────────

class RelatedAtom(BaseModel):
    """Lightweight reference to a related atom, embedded in MemoryAtom."""

    atom_id: str = Field(description="Target atom ID")
    type: RelationshipType = Field(description="Relationship type")
    confidence: float = Field(default=0.80, ge=0.0, le=1.0)


# ── Evidence ────────────────────────────────────────────────────────

class EvidenceSource(str, Enum):
    """Evidence source type — determines default weight."""

    SOURCE_CODE = "source_code"
    DOCUMENTATION = "documentation"
    ADR = "adr"
    VERIFIED_MEMORY = "verified_memory"
    CONVERSATION = "conversation"
    TEST = "test"
    COMMIT = "commit"


# Default evidence weights — configurable, not hardcoded
DEFAULT_EVIDENCE_WEIGHTS: dict[EvidenceSource, float] = {
    EvidenceSource.SOURCE_CODE: 1.0,
    EvidenceSource.DOCUMENTATION: 0.95,
    EvidenceSource.ADR: 0.90,
    EvidenceSource.VERIFIED_MEMORY: 0.85,
    EvidenceSource.CONVERSATION: 0.70,
    EvidenceSource.TEST: 0.80,
    EvidenceSource.COMMIT: 0.65,
}


class Evidence(BaseModel):
    """Weighted evidence supporting a memory atom."""

    source: str = Field(description="File path, session ID, commit hash, or URL")
    source_type: EvidenceSource = Field(description="Evidence source category")
    weight: float | None = Field(default=None, ge=0.0, le=1.0, description="Override weight; auto-computed from source_type if None")
    description: str | None = Field(default=None, description="Human-readable context")

    @property
    def effective_weight(self) -> float:
        if self.weight is not None:
            return self.weight
        return DEFAULT_EVIDENCE_WEIGHTS.get(self.source_type, 0.50)


# ── Memory Atom ─────────────────────────────────────────────────────

class MemoryAtom(BaseModel):
    """A single atomic unit of structured, typed, evidence-backed knowledge."""

    id: str = Field(description="Stable identifier, e.g. AUTH-001")
    type: MemoryType = Field(description="Knowledge category")
    topic: str = Field(description="High-level topic")
    summary: str = Field(description="Concise natural-language description, max 500 chars")
    confidence: float = Field(default=0.80, ge=0.0, le=1.0)
    status: MemoryStatus = Field(default=MemoryStatus.DRAFT)
    scope: MemoryScope = Field(default=MemoryScope.WORKSPACE)
    evidence: list[Evidence] = Field(default_factory=list, description="Weighted evidence sources")
    related_atoms: list[RelatedAtom] = Field(default_factory=list, description="Related atom references")
    tags: list[str] = Field(default_factory=list, description="Searchable keywords")
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    validated_at: str | None = Field(default=None, description="Last verification timestamp")
    superseded_by: str | None = Field(default=None, description="Atom ID that replaces this one")
    version: int = Field(default=1, description="Version number, incremented on update")
    version_history: list[dict[str, Any]] = Field(default_factory=list, description="Previous versions for audit trail")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @classmethod
    def generate_id(cls, topic: str, index: int) -> str:
        prefix = topic.upper().replace(" ", "-")[:8]
        return f"{prefix}-{index:03d}"

    def evidence_quality(self) -> float:
        """Compute aggregate evidence quality score."""
        if not self.evidence:
            return 0.50
        weights = [e.effective_weight for e in self.evidence]
        return sum(weights) / len(weights)

    def computed_confidence(self) -> float:
        """Confidence adjusted by evidence quality."""
        eq = self.evidence_quality()
        return round(self.confidence * (0.7 + 0.3 * eq), 2)


# ── Retrieval Result ────────────────────────────────────────────────

class ScoredAtom(BaseModel):
    """A memory atom with a retrieval score for ranking."""

    atom: MemoryAtom
    score: float = Field(default=0.0, description="Combined retrieval score (0-1)")
    score_breakdown: dict[str, float] = Field(default_factory=dict, description="Per-strategy score breakdown")

    model_config = {"arbitrary_types_allowed": True}


class RetrievalResult(BaseModel):
    """Result of a memory retrieval operation."""

    query: str
    atoms: list[ScoredAtom]
    total_candidates: int = Field(default=0)
    strategies_used: list[str] = Field(default_factory=list)
    execution_ms: float = Field(default=0.0)


# ── Provenance ──────────────────────────────────────────────────────

class ProvenanceEntry(BaseModel):
    """Maps a statement in a response back to source memory atoms."""

    statement: str = Field(description="Claim or statement from the response")
    atom_ids: list[str] = Field(default_factory=list, description="Supporting atom IDs")
    confidence: float = Field(default=0.0, description="Aggregate confidence of supporting atoms")
