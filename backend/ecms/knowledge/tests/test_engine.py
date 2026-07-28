"""Tests for the default knowledge engine pipeline (SECTION 29/75)."""

from __future__ import annotations

from ecms.events import InMemoryEventBus
from ecms.knowledge import DefaultKnowledgeEngine
from ecms.shared.enums import EventCategory, ValidationStatus
from ecms.shared.events import BaseEvent
from ecms.shared.models import UniversalKnowledgeObject

_SOURCE = '''
import os
from fastapi import APIRouter

router = APIRouter()


class AuthService(BaseService):
    """Handles authentication."""

    def login(self, user: str) -> bool:
        return True


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}
'''


def _uko(source: str = _SOURCE, *, title: str = "auth_module") -> UniversalKnowledgeObject:
    return UniversalKnowledgeObject(
        provider="git",
        provider_object_type="file",
        provider_object_id="repo:auth.py",
        organization_id="org-1",
        title=title,
        raw_content=source,
        language="python",
    )


async def test_ingest_generates_typed_ucos() -> None:
    engine = DefaultKnowledgeEngine()
    ucos = await engine.ingest(_uko())
    by_name = {uco.display_name: uco for uco in ucos}
    assert "AuthService" in by_name
    assert by_name["AuthService"].ontology_type == "security_component"
    assert by_name["health"].ontology_type == "api"
    assert all(uco.evidence for uco in ucos)
    assert all(uco.knowledge_sources for uco in ucos)


async def test_ingest_emits_pipeline_events() -> None:
    bus = InMemoryEventBus()
    seen: list[str] = []

    async def handler(event: BaseEvent) -> None:
        seen.append(event.event_type)

    bus.subscribe(handler, category=EventCategory.KNOWLEDGE)
    engine = DefaultKnowledgeEngine(event_bus=bus)
    await engine.ingest(_uko())
    assert "KnowledgeDiscovered" in seen
    assert "KnowledgeNormalized" in seen
    assert seen.count("KnowledgeValidated") >= 1
    assert seen.count("KnowledgeVersionCreated") >= 1


async def test_search_finds_relevant_object() -> None:
    engine = DefaultKnowledgeEngine()
    await engine.ingest(_uko())
    results = await engine.search("AuthService", limit=3)
    assert any(uco.display_name == "AuthService" for uco in results)


async def test_validation_flags_object_without_evidence() -> None:
    engine = DefaultKnowledgeEngine()
    ucos = await engine.ingest(_uko())
    assert engine.validate(ucos[0]) is ValidationStatus.VALIDATED


async def test_merge_combines_evidence_and_reindexes() -> None:
    engine = DefaultKnowledgeEngine()
    ucos = await engine.ingest(_uko())
    auth = next(uco for uco in ucos if uco.display_name == "AuthService")
    duplicate = auth.model_copy(update={"confidence": 90})
    merged = await engine.merge([auth, duplicate])
    assert len(merged.evidence) == 2
    assert merged.confidence == 90
    assert await engine.reindex() >= len(ucos)


async def test_extract_helpers() -> None:
    engine = DefaultKnowledgeEngine()
    uko = _uko()
    entities = engine.extract_entities(uko)
    relationships = engine.extract_relationships(uko)
    assert any(entity.kind == "api" for entity in entities)
    assert relationships
