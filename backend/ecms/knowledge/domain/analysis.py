"""Code-analysis domain models (SECTION 109/126).

These immutable-by-convention models capture the *meaning* extracted from source
code: the entities it defines (modules, classes, functions, APIs) and the
relationships between them. They are derived from semantic analysis (an AST),
never from file names.
"""

from __future__ import annotations

from pydantic import Field

from ecms.shared.enums import RelationshipType
from ecms.shared.models.base import DomainModel

__all__ = ["CodeAnalysis", "CodeEntity", "CodeRelationship"]


class CodeEntity(DomainModel):
    """A single entity discovered in source code (SECTION 126)."""

    kind: str
    name: str
    qualified_name: str
    signature: str | None = None
    docstring: str | None = None
    bases: list[str] = Field(default_factory=list)
    decorators: list[str] = Field(default_factory=list)
    lineno: int = Field(default=0, ge=0)


class CodeRelationship(DomainModel):
    """A directed relationship discovered between two code symbols (SECTION 126)."""

    source: str
    target: str
    relationship_type: RelationshipType


class CodeAnalysis(DomainModel):
    """The structured result of analyzing one source artifact (SECTION 126)."""

    language: str
    imports: list[str] = Field(default_factory=list)
    entities: list[CodeEntity] = Field(default_factory=list)
    relationships: list[CodeRelationship] = Field(default_factory=list)
