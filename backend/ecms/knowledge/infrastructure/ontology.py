"""Ontology mapping engine (SECTION 128/141).

Maps extracted entities into the enterprise ontology. Mapping is configurable:
callers may supply their own keyword-to-type and type-to-category rules; the
defaults cover common technical concepts (services, APIs, security components,
database entities, configuration, tests).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from ecms.knowledge.domain.analysis import CodeEntity
from ecms.shared.enums import OntologyCategory

__all__ = ["OntologyMapper"]

_DEFAULT_TYPE_RULES: tuple[tuple[str, str], ...] = (
    ("middleware", "security_component"),
    ("auth", "security_component"),
    ("security", "security_component"),
    ("crypto", "security_component"),
    ("service", "service"),
    ("controller", "api"),
    ("router", "api"),
    ("endpoint", "api"),
    ("gateway", "api"),
    ("repository", "data_access"),
    ("dao", "data_access"),
    ("model", "database_entity"),
    ("entity", "database_entity"),
    ("table", "database_entity"),
    ("schema", "database_entity"),
    ("config", "configuration"),
    ("settings", "configuration"),
    ("client", "integration"),
    ("connector", "integration"),
    ("adapter", "integration"),
)

_DEFAULT_CATEGORY_RULES: dict[str, OntologyCategory] = {
    "security_component": OntologyCategory.SECURITY,
    "service": OntologyCategory.TECHNOLOGY,
    "api": OntologyCategory.ARCHITECTURE,
    "data_access": OntologyCategory.TECHNOLOGY,
    "database_entity": OntologyCategory.INFRASTRUCTURE,
    "configuration": OntologyCategory.INFRASTRUCTURE,
    "integration": OntologyCategory.TECHNOLOGY,
    "component": OntologyCategory.TECHNOLOGY,
    "module": OntologyCategory.DEVELOPMENT,
    "function": OntologyCategory.DEVELOPMENT,
}


class OntologyMapper:
    """Maps code entities into configurable enterprise ontology types (SECTION 128)."""

    def __init__(
        self,
        type_rules: Sequence[tuple[str, str]] | None = None,
        category_rules: Mapping[str, OntologyCategory] | None = None,
    ) -> None:
        """Initialize with optional custom mapping rules, falling back to defaults."""
        self._type_rules = tuple(type_rules) if type_rules is not None else _DEFAULT_TYPE_RULES
        self._category_rules = (
            dict(category_rules) if category_rules is not None else dict(_DEFAULT_CATEGORY_RULES)
        )

    def map_entity(self, entity: CodeEntity) -> str:
        """Return the ontology type for an entity based on its kind, name and bases."""
        if entity.kind == "api":
            return "api"
        haystack = " ".join([entity.name, *entity.bases, *entity.decorators]).lower()
        for keyword, ontology_type in self._type_rules:
            if keyword in haystack:
                return ontology_type
        if entity.kind == "class":
            return "component"
        return entity.kind

    def category_for(self, ontology_type: str) -> OntologyCategory:
        """Return the ontology category for an ontology type."""
        return self._category_rules.get(ontology_type, OntologyCategory.TECHNOLOGY)
