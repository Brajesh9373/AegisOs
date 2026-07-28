from datetime import datetime, timezone
from pathlib import Path

from legacy_ecms.config import get_settings
from legacy_ecms.core.episode import EpisodePayload, uko_to_episode
from legacy_ecms.core.graph import BatchWriteResult, GraphClient
from legacy_ecms.core.uko import (
    ExtractionProvenance,
    UKOMetadata,
    UKORelationship,
    UKOType,
    UniversalKnowledgeObject,
)
from legacy_ecms.pipeline.structural.json_parser import JsonStructuralExtractor
from legacy_ecms.pipeline.structural.markdown_parser import MarkdownStructuralExtractor
from legacy_ecms.pipeline.structural.models import StructuralArtifactType, StructuralExtractionResult
from legacy_ecms.pipeline.structural.python_parser import PythonStructuralExtractor
from legacy_ecms.pipeline.structural.sql_parser import SqlStructuralExtractor
from legacy_ecms.pipeline.semantic.concept_mapper import ConceptMapper
from legacy_ecms.pipeline.semantic.llm_extractor import KeywordSemanticExtractor
from legacy_ecms.pipeline.temporal.change_tracker import ChangeTracker


def _structural_provenance(
    method: str = "ast_parser",
    confidence: float = 1.0,
    evidence_snippet: str = "",
) -> ExtractionProvenance:
    return ExtractionProvenance(
        extraction_method=method,
        extraction_timestamp=datetime.now(timezone.utc),
        confidence=confidence,
        evidence_snippet=evidence_snippet,
        pipeline_stage="structural",
    )


def _semantic_provenance(
    confidence: float = 0.0,
    evidence_snippet: str = "",
) -> ExtractionProvenance:
    return ExtractionProvenance(
        extraction_method="keyword_match",
        extraction_timestamp=datetime.now(timezone.utc),
        confidence=confidence,
        evidence_snippet=evidence_snippet,
        pipeline_stage="semantic",
    )


class PipelineOrchestrator:
    """Runs deterministic extraction and optional graph ingestion."""

    def __init__(self, graph: GraphClient | None = None) -> None:
        self.graph = graph
        self.settings = get_settings()
        self.python_extractor = PythonStructuralExtractor()
        self.markdown_extractor = MarkdownStructuralExtractor()
        self.json_extractor = JsonStructuralExtractor(
            max_artifacts=self.settings.structural_max_artifacts_per_file,
            max_depth=self.settings.structural_json_max_depth,
            max_array_items=self.settings.structural_json_max_array_items,
        )
        self.sql_extractor = SqlStructuralExtractor()
        self.semantic_extractor = KeywordSemanticExtractor()
        self.concept_mapper = ConceptMapper()
        self.change_tracker = ChangeTracker()
        self.last_write_result: BatchWriteResult | None = None

    async def process_uko(self, uko: UniversalKnowledgeObject) -> tuple[list[EpisodePayload], BatchWriteResult]:
        derived_ukos = await self.derive_ukos(uko)
        episodes = [uko_to_episode(item) for item in [uko, *derived_ukos]]
        write_result = BatchWriteResult()
        if self.graph is not None:
            if self.settings.semantic_mode == "llm":
                result = await self.graph.add_episodes_bulk([uko_to_episode(uko)])
                write_result = self._aggregate(write_result, result)
                if derived_ukos:
                    result = await self.graph.add_episodes_raw_batch([uko_to_episode(item) for item in derived_ukos])
                    write_result = self._aggregate(write_result, result)
            else:
                result = await self.graph.add_episodes_raw_batch(episodes)
                write_result = self._aggregate(write_result, result)
        self.last_write_result = write_result
        return episodes, write_result

    async def process_batch(
        self, ukos: list[UniversalKnowledgeObject]
    ) -> tuple[list[EpisodePayload], BatchWriteResult]:
        all_episodes: list[EpisodePayload] = []
        source_episodes: list[EpisodePayload] = []
        derived_episodes: list[EpisodePayload] = []

        for uko in ukos:
            source_episode = uko_to_episode(uko)
            derived = [uko_to_episode(item) for item in await self.derive_ukos(uko)]
            source_episodes.append(source_episode)
            derived_episodes.extend(derived)
            all_episodes.extend([source_episode, *derived])

        write_result = BatchWriteResult()
        if self.graph is None:
            self.last_write_result = write_result
            return all_episodes, write_result

        if self.settings.semantic_mode == "llm":
            result = await self.graph.add_episodes_bulk(source_episodes)
            write_result = self._aggregate(write_result, result)
            if derived_episodes:
                result = await self.graph.add_episodes_raw_batch(derived_episodes)
                write_result = self._aggregate(write_result, result)
        else:
            result = await self.graph.add_episodes_raw_batch(all_episodes)
            write_result = self._aggregate(write_result, result)

        self.last_write_result = write_result
        return all_episodes, write_result

    @staticmethod
    def _aggregate(a: BatchWriteResult, b: BatchWriteResult) -> BatchWriteResult:
        return BatchWriteResult(
            success_count=a.success_count + b.success_count,
            failure_count=a.failure_count + b.failure_count,
            failures=a.failures + b.failures,
            orphan_stubs_created=a.orphan_stubs_created + b.orphan_stubs_created,
        )

    async def derive_ukos(self, uko: UniversalKnowledgeObject) -> list[UniversalKnowledgeObject]:
        derived_ukos = self.extract_structural_ukos(uko)
        semantic_result = await self.semantic_extractor.extract(uko)
        concepts = [
            concept
            for concept in semantic_result.concepts
            if concept.confidence >= self.settings.semantic_min_confidence
        ]
        concept_ukos = self._link_concepts_to_evidence(
            self.concept_mapper.map_concepts(uko, concepts),
            derived_ukos,
        )
        temporal_ukos = self.change_tracker.extract(uko)
        return [*derived_ukos, *concept_ukos, *temporal_ukos]

    def extract_structural_ukos(self, uko: UniversalKnowledgeObject) -> list[UniversalKnowledgeObject]:
        result = self.extract_structure(uko)
        if result.errors:
            return []

        ukos: list[UniversalKnowledgeObject] = []
        artifact_ids_by_name: dict[str, str] = {}
        artifact_types_by_name: dict[str, UKOType] = {}
        for artifact in result.artifacts:
            artifact_type = self._uko_type_for_artifact(artifact.type)
            if artifact_type is None:
                continue
            artifact_ids_by_name.setdefault(artifact.name, self._artifact_id_for(uko, artifact))
            artifact_types_by_name.setdefault(artifact.name, artifact_type)

        relationships_by_source: dict[str, list] = {}
        for relationship in result.relationships:
            relationships_by_source.setdefault(relationship.source_name, []).append(relationship)

        for artifact in result.artifacts:
            artifact_type = self._uko_type_for_artifact(artifact.type)
            if artifact_type is None:
                continue

            relationships = [
                UKORelationship(
                    target_id=uko.id,
                    relationship="contained_in",
                    target_type=uko.type,
                    confidence=1.0,
                    provenance=_structural_provenance(
                        evidence_snippet=f"{artifact.name} in {uko.name}",
                    ),
                )
            ]
            table_name = artifact.metadata.get("table")
            if artifact.type == StructuralArtifactType.COLUMN and table_name:
                relationships.append(
                    UKORelationship(
                        target_id=artifact_ids_by_name.get(table_name, table_name),
                        relationship="belongs_to",
                        target_type=artifact_types_by_name.get(table_name, UKOType.TABLE),
                        confidence=1.0,
                        provenance=_structural_provenance(
                            evidence_snippet=f"column {artifact.name} in table {table_name}",
                        ),
                    )
                )
            parent_class = artifact.metadata.get("parent_class")
            if artifact.type == StructuralArtifactType.FUNCTION and parent_class:
                relationships.append(
                    UKORelationship(
                        target_id=artifact_ids_by_name.get(parent_class, parent_class),
                        relationship="defined_in",
                        target_type=artifact_types_by_name.get(parent_class, UKOType.CLASS),
                        confidence=1.0,
                        provenance=_structural_provenance(
                            evidence_snippet=f"function {artifact.name} in class {parent_class}",
                        ),
                    )
                )
            for relationship in relationships_by_source.get(artifact.name, []):
                target_id = artifact_ids_by_name.get(relationship.target_name, relationship.target_name)
                target_type = artifact_types_by_name.get(
                    relationship.target_name,
                    self._target_type_for_relationship(relationship.relationship),
                )
                relationships.append(
                    UKORelationship(
                        target_id=target_id,
                        relationship=relationship.relationship,
                        target_type=target_type,
                        confidence=1.0,
                        metadata=relationship.metadata,
                        provenance=_structural_provenance(
                            evidence_snippet=f"{artifact.name} {relationship.relationship} {relationship.target_name}",
                        ),
                    )
                )

            ukos.append(
                UniversalKnowledgeObject(
                    id=self._artifact_id_for(uko, artifact),
                    type=artifact_type,
                    name=artifact.name,
                    content=artifact.docstring or artifact.signature or "",
                    metadata=UKOMetadata(
                        source=uko.metadata.source,
                        source_id=self._source_id_for_artifact(uko, artifact.name, artifact.start_line),
                        source_url=uko.metadata.source_url,
                        created_at=uko.metadata.created_at,
                        modified_at=uko.metadata.modified_at,
                        authors=uko.metadata.authors,
                        tags=[*uko.metadata.tags, artifact.type.value],
                        tenant_id=uko.metadata.tenant_id,
                    ),
                    relationships=relationships,
                    raw_data=artifact.model_dump(),
                    provenance=_structural_provenance(
                        method="ast_parser",
                        evidence_snippet=f"extracted {artifact.type.value} from {uko.name}",
                    ),
                )
            )

        return ukos

    def _link_concepts_to_evidence(
        self,
        concept_ukos: list[UniversalKnowledgeObject],
        evidence_ukos: list[UniversalKnowledgeObject],
    ) -> list[UniversalKnowledgeObject]:
        linked: list[UniversalKnowledgeObject] = []
        for concept in concept_ukos:
            evidence_terms = [str(term).lower() for term in concept.raw_data.get("evidence", [])]
            relationships = list(concept.relationships)
            for evidence in evidence_ukos:
                haystack = " ".join([evidence.name, evidence.content, " ".join(evidence.metadata.tags)]).lower()
                matched_terms = [term for term in evidence_terms if term and term in haystack]
                if matched_terms:
                    base_confidence = (
                        concept.relationships[0].confidence if concept.relationships else None
                    )
                    relationships.append(
                        UKORelationship(
                            target_id=evidence.id,
                            relationship="supported_by",
                            target_type=evidence.type,
                            confidence=base_confidence,
                            metadata={"evidence": evidence_terms},
                            provenance=_semantic_provenance(
                                confidence=base_confidence or 0.5,
                                evidence_snippet=f"concept {concept.name} supported by {evidence.name} (terms: {', '.join(matched_terms)})",
                            ),
                        )
                    )
            linked.append(concept.model_copy(update={"relationships": relationships}))
        return linked

    def _artifact_id_for(
        self,
        uko: UniversalKnowledgeObject,
        artifact,
    ) -> str:
        return f"{uko.id}:{artifact.type.value}:{artifact.name}:{artifact.start_line or 0}"

    def _target_type_for_relationship(self, relationship: str) -> UKOType:
        if relationship in {"calls", "extends"}:
            return UKOType.API
        if relationship == "uses_import":
            return UKOType.IMPORT
        if relationship in {"defines_method", "defined_in"}:
            return UKOType.FUNCTION
        if relationship in {"belongs_to", "references"}:
            return UKOType.TABLE
        return UKOType.CONCEPT

    def extract_structure(self, uko: UniversalKnowledgeObject) -> StructuralExtractionResult:
        path = Path(uko.metadata.source_id)
        suffix = path.suffix.lower()
        if suffix == ".py":
            return self.python_extractor.extract(uko.content)
        if suffix in {".md", ".markdown"}:
            return self.markdown_extractor.extract(uko.content)
        if suffix == ".json":
            return self.json_extractor.extract(uko.content)
        if suffix == ".sql" or uko.type == UKOType.TABLE:
            return self.sql_extractor.extract(uko.content)
        return StructuralExtractionResult()

    def _uko_type_for_artifact(self, artifact_type: StructuralArtifactType) -> UKOType | None:
        mapping = {
            StructuralArtifactType.FUNCTION: UKOType.FUNCTION,
            StructuralArtifactType.CLASS: UKOType.CLASS,
            StructuralArtifactType.IMPORT: UKOType.IMPORT,
            StructuralArtifactType.HEADING: UKOType.DOCUMENT,
            StructuralArtifactType.JSON_KEY: UKOType.API,
            StructuralArtifactType.TABLE: UKOType.TABLE,
            StructuralArtifactType.COLUMN: UKOType.COLUMN,
        }
        return mapping.get(artifact_type)

    def _source_id_for_artifact(
        self,
        uko: UniversalKnowledgeObject,
        artifact_name: str,
        start_line: int | None,
    ) -> str:
        suffix = f":{start_line}" if start_line else ""
        return f"{uko.metadata.source_id}#{artifact_name}{suffix}"
