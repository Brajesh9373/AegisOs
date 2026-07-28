import re
from collections import defaultdict
from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

from legacy_ecms.core.uko import (
    ExtractionProvenance,
    UKOMetadata,
    UKORelationship,
    UKOType,
    UniversalKnowledgeObject,
)


class IdentityCluster(BaseModel):
    model_config = ConfigDict(frozen=True)

    canonical_id: str
    display_name: str
    confidence: float = Field(ge=0.0, le=1.0)
    evidence_ids: list[str]


class IdentityResolver:
    """Rule-based resolver for person-like UKOs and relationship targets."""

    async def resolve(self, ukos: list[UniversalKnowledgeObject]) -> list[UniversalKnowledgeObject]:
        clusters = self.cluster(ukos)
        resolved: list[UniversalKnowledgeObject] = []
        timestamp = datetime.now(timezone.utc)
        for cluster in clusters:
            source = self._first_evidence_uko(ukos, cluster.evidence_ids)
            if source is None:
                continue
            resolved.append(
                UniversalKnowledgeObject(
                    id=cluster.canonical_id,
                    type=UKOType.PERSON,
                    name=cluster.display_name,
                    content=f"Unified person identity for {cluster.display_name}",
                    metadata=UKOMetadata(
                        source="identity",
                        source_id=cluster.canonical_id,
                        created_at=source.metadata.created_at,
                        modified_at=max(uko.metadata.modified_at for uko in ukos if uko.id in cluster.evidence_ids),
                        tags=["resolved-person"],
                        tenant_id=source.metadata.tenant_id,
                    ),
                    relationships=[
                        UKORelationship(
                            target_id=evidence_id,
                            relationship="same_as",
                            target_type=UKOType.PERSON,
                            confidence=cluster.confidence,
                            provenance=ExtractionProvenance(
                                extraction_method="rule_based_resolver",
                                extraction_timestamp=timestamp,
                                confidence=cluster.confidence,
                                evidence_snippet=f"identity resolution: {cluster.display_name} resolves {evidence_id}",
                                model_version="",
                                pipeline_stage="identity",
                            ),
                        )
                        for evidence_id in cluster.evidence_ids
                    ],
                    raw_data=cluster.model_dump(),
                    provenance=ExtractionProvenance(
                        extraction_method="rule_based_resolver",
                        extraction_timestamp=timestamp,
                        confidence=cluster.confidence,
                        evidence_snippet=f"resolved person identity: {cluster.display_name} from {len(cluster.evidence_ids)} evidence IDs",
                        model_version="",
                        pipeline_stage="identity",
                    ),
                )
            )
        return resolved

    def cluster(self, ukos: list[UniversalKnowledgeObject]) -> list[IdentityCluster]:
        names_by_key: dict[str, list[tuple[str, str]]] = defaultdict(list)

        for uko in ukos:
            if uko.type == UKOType.PERSON:
                self._add_name(names_by_key, uko.name, uko.id)
            for author in uko.metadata.authors:
                self._add_name(names_by_key, author, uko.id)
            for relationship in uko.relationships:
                if relationship.target_type == UKOType.PERSON:
                    self._add_name(names_by_key, relationship.target_id, uko.id)

        clusters: list[IdentityCluster] = []
        for key, values in names_by_key.items():
            evidence_ids = sorted({item[1] for item in values})
            if len(evidence_ids) < 2:
                continue
            display_name = self._best_display_name([item[0] for item in values])
            clusters.append(
                IdentityCluster(
                    canonical_id=f"person:{key}",
                    display_name=display_name,
                    confidence=0.85,
                    evidence_ids=evidence_ids,
                )
            )
        return clusters

    def _add_name(self, names_by_key: dict[str, list[tuple[str, str]]], name: str | None, evidence_id: str) -> None:
        if not name:
            return
        key = self._identity_key(name)
        if key:
            names_by_key[key].append((name, evidence_id))
        alternate_key = self._initial_last_key(name)
        if alternate_key and alternate_key != key:
            names_by_key[alternate_key].append((name, evidence_id))

    def _identity_key(self, name: str) -> str:
        value = name.strip().lower()
        if "@" in value and "." in value:
            return re.sub(r"[^a-z0-9]+", "-", value.split("@", 1)[0]).strip("-")
        value = value.removeprefix("@")
        parts = re.findall(r"[a-z0-9]+", value)
        if not parts:
            return ""
        if len(parts) >= 2:
            return f"{parts[0]}-{parts[-1]}"
        return parts[0]

    def _initial_last_key(self, name: str) -> str:
        value = name.strip().lower().removeprefix("@")
        parts = re.findall(r"[a-z0-9]+", value)
        if len(parts) < 2:
            return ""
        return f"{parts[0][0]}-{parts[-1]}"

    def _best_display_name(self, names: list[str]) -> str:
        return max(names, key=lambda item: (len(item.split()), len(item)))

    def _first_evidence_uko(
        self,
        ukos: list[UniversalKnowledgeObject],
        evidence_ids: list[str],
    ) -> UniversalKnowledgeObject | None:
        evidence = set(evidence_ids)
        return next((uko for uko in ukos if uko.id in evidence), None)
