from datetime import datetime, timezone

from legacy_ecms.core.uko import (
    ExtractionProvenance,
    UKOMetadata,
    UKORelationship,
    UKOType,
    UniversalKnowledgeObject,
)
from legacy_ecms.pipeline.semantic.models import SemanticConcept


class ConceptMapper:
    """Maps semantic concepts into knowledge-layer UKOs."""

    def map_concepts(
        self,
        source_uko: UniversalKnowledgeObject,
        concepts: list[SemanticConcept],
    ) -> list[UniversalKnowledgeObject]:
        mapped: list[UniversalKnowledgeObject] = []
        for concept in concepts:
            concept_id = concept.name.lower().replace(" ", "-")
            evidence_text = ", ".join(concept.evidence)
            timestamp = datetime.now(timezone.utc)
            mapped.append(
                UniversalKnowledgeObject(
                    id=f"concept:{concept_id}",
                    type=UKOType.CONCEPT,
                    name=concept.name,
                    content=f"{concept.name} concept extracted from {source_uko.name}",
                    metadata=UKOMetadata(
                        source="semantic",
                        source_id=f"{source_uko.evidence_key}#{concept_id}",
                        source_url=source_uko.metadata.source_url,
                        created_at=source_uko.metadata.modified_at,
                        modified_at=source_uko.metadata.modified_at,
                        authors=source_uko.metadata.authors,
                        tags=[concept.category, *concept.evidence],
                        tenant_id=source_uko.metadata.tenant_id,
                    ),
                    relationships=[
                        UKORelationship(
                            target_id=source_uko.id,
                            relationship="extracted_from",
                            target_type=source_uko.type,
                            confidence=concept.confidence,
                            metadata={"evidence": concept.evidence},
                            provenance=ExtractionProvenance(
                                extraction_method="keyword_match",
                                extraction_timestamp=timestamp,
                                confidence=concept.confidence,
                                evidence_snippet=evidence_text,
                                model_version="",
                                pipeline_stage="semantic",
                            ),
                        )
                    ],
                    raw_data=concept.model_dump(),
                    provenance=ExtractionProvenance(
                        extraction_method="keyword_match",
                        extraction_timestamp=timestamp,
                        confidence=concept.confidence,
                        evidence_snippet=f"concept {concept.name} from {source_uko.name} via terms: {evidence_text}",
                        model_version="",
                        pipeline_stage="semantic",
                    ),
                )
            )
        return mapped
