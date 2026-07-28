from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class UKOType(str, Enum):
    FILE = "file"
    FUNCTION = "function"
    CLASS = "class"
    IMPORT = "import"
    API = "api"
    TABLE = "table"
    COLUMN = "column"
    DOCUMENT = "document"
    MESSAGE = "message"
    TICKET = "ticket"
    PERSON = "person"
    NAME = "name"
    COMMIT = "commit"
    CONCEPT = "concept"
    EVENT = "event"
    WORKSPACE = "workspace"


class ExtractionProvenance(BaseModel):
    """Captures how and when a fact was extracted, so downstream agents can
    evaluate trustworthiness at query time."""

    model_config = ConfigDict(frozen=True)

    extraction_method: str = Field(min_length=1)
    extraction_timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_snippet: str = ""
    model_version: str = ""
    pipeline_stage: str = ""


class UKORelationship(BaseModel):
    model_config = ConfigDict(frozen=True)

    target_id: str = Field(min_length=1)
    relationship: str = Field(min_length=1)
    target_type: UKOType
    confidence: float | None = Field(default=None, ge=0.0, le=1.0)
    metadata: dict[str, Any] = Field(default_factory=dict)
    provenance: ExtractionProvenance | None = None


class UKOMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    source: str = Field(min_length=1)
    source_id: str = Field(min_length=1)
    source_url: str | None = None
    created_at: datetime
    modified_at: datetime
    authors: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)
    tenant_id: str | None = None

    @model_validator(mode="after")
    def modified_at_must_not_precede_created_at(self) -> "UKOMetadata":
        if self.modified_at < self.created_at:
            raise ValueError("modified_at cannot be earlier than created_at")
        return self


class UniversalKnowledgeObject(BaseModel):
    """Provider-neutral artifact emitted before graph ingestion."""

    model_config = ConfigDict(frozen=True)

    id: str = Field(default_factory=lambda: f"uko-{uuid4()}", min_length=1)
    type: UKOType
    name: str = Field(min_length=1)
    content: str = ""
    metadata: UKOMetadata
    relationships: list[UKORelationship] = Field(default_factory=list)
    raw_data: dict[str, Any] = Field(default_factory=dict)
    schema_version: str = "1.0"
    provenance: ExtractionProvenance | None = None
    status: str = "active"
    version: int = 1
    previous_version_id: str | None = None
    ingestion_batch_id: str | None = None

    @property
    def evidence_key(self) -> str:
        return f"{self.metadata.source}:{self.metadata.source_id}"
