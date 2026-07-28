"""Default knowledge engine (SECTION 29/75/125).

Implements the cognitive pipeline that turns a UKO (raw information) into UCOs
(understanding): normalize, analyze the source semantically, extract entities and
relationships, map them into the ontology, generate cognitive objects, validate
them, and publish them (index + emit events). Reasoning and embedding are
supplied by replaceable providers; the deterministic defaults keep the pipeline
runnable offline.
"""

from __future__ import annotations

from ecms.events import EventBus
from ecms.infrastructure.reasoning import (
    DeterministicEmbeddingProvider,
    DeterministicReasoningProvider,
)
from ecms.knowledge.domain.analysis import CodeAnalysis, CodeEntity, CodeRelationship
from ecms.knowledge.events.knowledge_events import (
    knowledge_discovered,
    knowledge_merged,
    knowledge_normalized,
    knowledge_validated,
    knowledge_version_created,
)
from ecms.knowledge.infrastructure.code_analysis import analyze_code
from ecms.knowledge.infrastructure.ontology import OntologyMapper
from ecms.knowledge.infrastructure.repository import InMemoryKnowledgeRepository
from ecms.knowledge.interfaces.engine import KnowledgeRepository
from ecms.shared.enums import ValidationStatus
from ecms.shared.events import BaseEvent
from ecms.shared.exceptions import ValidationError
from ecms.shared.interfaces import EmbeddingProvider, ReasoningProvider, ReasoningRequest
from ecms.shared.models import (
    Evidence,
    UniversalCognitiveObject,
    UniversalKnowledgeObject,
)

__all__ = ["DefaultKnowledgeEngine"]

_IMPORTANCE_BY_KIND = {"api": 80, "class": 60, "function": 40, "module": 50}


class DefaultKnowledgeEngine:
    """Transforms UKOs into validated, indexed cognitive objects (SECTION 29/75)."""

    def __init__(
        self,
        *,
        embedder: EmbeddingProvider | None = None,
        reasoner: ReasoningProvider | None = None,
        ontology: OntologyMapper | None = None,
        repository: KnowledgeRepository | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize the engine with replaceable providers and collaborators."""
        self._embedder = embedder or DeterministicEmbeddingProvider()
        self._reasoner = reasoner or DeterministicReasoningProvider()
        self._ontology = ontology or OntologyMapper()
        self._repository = repository or InMemoryKnowledgeRepository(self._embedder)
        self._event_bus = event_bus

    async def ingest(self, uko: UniversalKnowledgeObject) -> list[UniversalCognitiveObject]:
        """Run the full pipeline for a UKO and return the validated UCOs it yields."""
        await self._emit(knowledge_discovered(uko.uko_id))
        analysis = self.analyze(uko)
        await self._emit(knowledge_normalized(uko.uko_id))
        generated: list[UniversalCognitiveObject] = []
        for entity in analysis.entities:
            uco = await self.generate_uco(uko, entity, analysis)
            if self.validate(uco) is ValidationStatus.VALIDATED:
                generated.append(uco)
        await self.publish(generated)
        return generated

    def analyze(self, uko: UniversalKnowledgeObject) -> CodeAnalysis:
        """Analyze a UKO's content semantically (SECTION 126)."""
        return analyze_code(
            uko.raw_content,
            language=uko.language,
            module_name=uko.title or "module",
        )

    def extract_entities(self, uko: UniversalKnowledgeObject) -> list[CodeEntity]:
        """Return the entities discovered in a UKO's content (SECTION 75)."""
        return self.analyze(uko).entities

    def extract_relationships(self, uko: UniversalKnowledgeObject) -> list[CodeRelationship]:
        """Return the relationships discovered in a UKO's content (SECTION 75)."""
        return self.analyze(uko).relationships

    async def generate_uco(
        self,
        uko: UniversalKnowledgeObject,
        entity: CodeEntity,
        analysis: CodeAnalysis,
    ) -> UniversalCognitiveObject:
        """Build one cognitive object from a UKO and an extracted entity (SECTION 75)."""
        ontology_type = self._ontology.map_entity(entity)
        category = self._ontology.category_for(ontology_type)
        description = self._describe(entity)
        confidence = self._confidence(entity)
        summary = await self._summarize(entity, description)
        related = [
            relationship.target
            for relationship in analysis.relationships
            if relationship.source in {entity.name, entity.qualified_name}
        ]
        return UniversalCognitiveObject(
            canonical_name=entity.qualified_name,
            display_name=entity.name,
            ontology_type=ontology_type,
            description=description,
            summary=summary,
            confidence=confidence,
            importance=_IMPORTANCE_BY_KIND.get(entity.kind, 50),
            evidence=[
                Evidence(
                    uko_id=uko.uko_id,
                    source=uko.provider,
                    origin=uko.provider_object_id,
                    reference=entity.qualified_name,
                    confidence=confidence,
                )
            ],
            knowledge_sources=[uko.uko_id],
            custom_attributes={
                "category": category.value,
                "language": analysis.language,
                "related": related,
            },
        )

    def validate(self, uco: UniversalCognitiveObject) -> ValidationStatus:
        """Return the validation status of a cognitive object (SECTION 75)."""
        if uco.canonical_name and uco.evidence:
            return ValidationStatus.VALIDATED
        return ValidationStatus.NEEDS_REVIEW

    async def publish(self, ucos: list[UniversalCognitiveObject]) -> None:
        """Index cognitive objects and emit validation and version events (SECTION 75)."""
        for uco in ucos:
            await self._repository.add(uco)
            await self._emit(knowledge_validated(uco.uco_id))
            await self._emit(knowledge_version_created(uco.uco_id, version=1))

    async def search(self, query: str, *, limit: int = 10) -> list[UniversalCognitiveObject]:
        """Return cognitive objects most relevant to a query (SECTION 75)."""
        return await self._repository.search(query, limit=limit)

    async def merge(self, ucos: list[UniversalCognitiveObject]) -> UniversalCognitiveObject:
        """Merge duplicate cognitive objects into one, preserving evidence (SECTION 75).

        Raises:
            ValidationError: If ``ucos`` is empty.
        """
        if not ucos:
            raise ValidationError("cannot merge an empty set of cognitive objects")
        primary = max(ucos, key=lambda candidate: candidate.confidence)
        evidence = [item for candidate in ucos for item in candidate.evidence]
        aliases = sorted({candidate.display_name for candidate in ucos} | set(primary.aliases))
        sources = sorted({source for candidate in ucos for source in candidate.knowledge_sources})
        merged = primary.model_copy(
            update={
                "evidence": evidence,
                "aliases": aliases,
                "knowledge_sources": sources,
                "confidence": max(candidate.confidence for candidate in ucos),
                "importance": max(candidate.importance for candidate in ucos),
            }
        )
        await self._repository.add(merged)
        await self._emit(knowledge_merged(merged.uco_id, sources))
        return merged

    async def reindex(self) -> int:
        """Rebuild the search index; return the number of objects indexed (SECTION 75)."""
        result: int = await self._repository.reindex()
        return result

    async def _summarize(self, entity: CodeEntity, description: str) -> str:
        response = await self._reasoner.reason(
            ReasoningRequest(
                instruction=f"summarize {entity.kind} {entity.name}",
                context=entity.docstring or description,
            )
        )
        return response.content

    async def _emit(self, event: BaseEvent) -> None:
        if self._event_bus is not None:
            await self._event_bus.publish(event)

    def _describe(self, entity: CodeEntity) -> str:
        parts = [f"{entity.kind} '{entity.name}'"]
        if entity.bases:
            parts.append(f"extending {', '.join(entity.bases)}")
        if entity.signature:
            parts.append(f"with signature {entity.signature}")
        text = " ".join(parts)
        docstring_lines = (entity.docstring or "").strip().splitlines()
        if docstring_lines:
            text = f"{text}: {docstring_lines[0].strip()}"
        return text

    @staticmethod
    def _confidence(entity: CodeEntity) -> int:
        confidence = 60
        if entity.docstring:
            confidence += 20
        if entity.bases:
            confidence += 10
        return min(confidence, 100)
