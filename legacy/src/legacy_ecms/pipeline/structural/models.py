from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class StructuralArtifactType(str, Enum):
    FUNCTION = "function"
    CLASS = "class"
    IMPORT = "import"
    HEADING = "heading"
    JSON_KEY = "json_key"
    TABLE = "table"
    COLUMN = "column"


class StructuralRelationship(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_name: str
    relationship: str
    target_name: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class StructuralArtifact(BaseModel):
    model_config = ConfigDict(frozen=True)

    type: StructuralArtifactType
    name: str
    start_line: int | None = None
    end_line: int | None = None
    signature: str | None = None
    docstring: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class StructuralExtractionResult(BaseModel):
    model_config = ConfigDict(frozen=True)

    artifacts: list[StructuralArtifact] = Field(default_factory=list)
    relationships: list[StructuralRelationship] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
