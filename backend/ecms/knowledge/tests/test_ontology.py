"""Tests for the ontology mapping engine (SECTION 128)."""

from __future__ import annotations

from ecms.knowledge import OntologyMapper
from ecms.knowledge.domain.analysis import CodeEntity
from ecms.shared.enums import OntologyCategory


def _entity(kind: str, name: str, bases: list[str] | None = None) -> CodeEntity:
    return CodeEntity(kind=kind, name=name, qualified_name=f"m.{name}", bases=bases or [])


def test_maps_by_keyword() -> None:
    mapper = OntologyMapper()
    assert mapper.map_entity(_entity("class", "AuthMiddleware")) == "security_component"
    assert mapper.map_entity(_entity("class", "UserRepository")) == "data_access"
    assert mapper.map_entity(_entity("class", "OrderModel")) == "database_entity"


def test_maps_by_kind_when_no_keyword() -> None:
    mapper = OntologyMapper()
    assert mapper.map_entity(_entity("api", "health")) == "api"
    assert mapper.map_entity(_entity("class", "Widget")) == "component"
    assert mapper.map_entity(_entity("function", "helper")) == "function"


def test_category_lookup() -> None:
    mapper = OntologyMapper()
    assert mapper.category_for("security_component") is OntologyCategory.SECURITY
    assert mapper.category_for("api") is OntologyCategory.ARCHITECTURE
    assert mapper.category_for("unknown") is OntologyCategory.TECHNOLOGY


def test_custom_rules_override_defaults() -> None:
    mapper = OntologyMapper(type_rules=[("widget", "ui_component")])
    assert mapper.map_entity(_entity("class", "Widget")) == "ui_component"
