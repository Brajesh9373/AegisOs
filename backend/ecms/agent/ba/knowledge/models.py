"""Pydantic models for the knowledge base."""

from __future__ import annotations

from pydantic import BaseModel, Field

# ── Knowledge categories ────────────────────────────────────────────────────

CATEGORIES = (
    "universal_pattern",  # BA methodology, how to think
    "domain_pattern",  # Industry/domain knowledge
    "anti_pattern",  # Red flags, common mistakes
    "compliance",  # Regulatory frameworks
    "correction",  # Fix a BA mistake
    "project_context",  # Specific project intel
    "architecture_pattern",  # Technical patterns
    "success_pattern",  # What worked well
)


# ── Request/response models ─────────────────────────────────────────────────


class KnowledgeEntry(BaseModel):
    """A single knowledge entry as stored in the DB."""

    id: str
    category: str
    domain: str = ""
    tags: list[str] = Field(default_factory=list)
    content: str
    embedding: list[float] | None = None
    source: str = "telegram"
    contributor: str = ""
    project_id: str | None = None
    chunk_index: int = 0
    parent_id: str | None = None


class KnowledgeIngestRequest(BaseModel):
    """Input for ingesting knowledge."""

    text: str
    source: str = "telegram"
    contributor: str = ""
    project_id: str | None = None


class KnowledgeClassifyResult(BaseModel):
    """LLM classification output for a piece of knowledge."""

    category: str
    domain: str = ""
    tags: list[str] = Field(default_factory=list)
    summary: str = ""


class KnowledgeSearchResult(BaseModel):
    """A knowledge entry with its relevance score."""

    entry: KnowledgeEntry
    score: float  # cosine similarity or text rank
    match_type: str = "hybrid"  # "text", "semantic", "hybrid"
