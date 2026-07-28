from datetime import datetime, timezone

from pydantic import BaseModel, ConfigDict, Field

from legacy_ecms.core.uko import (
    ExtractionProvenance,
    UKOMetadata,
    UKORelationship,
    UKOType,
    UniversalKnowledgeObject,
)


class TemporalEvent(BaseModel):
    model_config = ConfigDict(frozen=True)

    name: str
    occurred_at: datetime
    actor: str | None = None
    details: dict = Field(default_factory=dict)


class ChangeTracker:
    """Extracts temporal events from provider raw data when present."""

    def extract(self, uko: UniversalKnowledgeObject) -> list[UniversalKnowledgeObject]:
        events: list[UniversalKnowledgeObject] = []
        for item in uko.raw_data.get("events", []):
            occurred_at = item.get("occurred_at", uko.metadata.modified_at)
            if isinstance(occurred_at, str):
                occurred_at = datetime.fromisoformat(occurred_at.replace("Z", "+00:00"))
            event = TemporalEvent(
                name=item.get("name", "Change Event"),
                occurred_at=occurred_at,
                actor=item.get("actor"),
                details=item,
            )
            timestamp = datetime.now(timezone.utc)
            events.append(
                UniversalKnowledgeObject(
                    id=f"{uko.id}:event:{len(events)}",
                    type=UKOType.EVENT,
                    name=event.name,
                    content=str(event.details),
                    metadata=UKOMetadata(
                        source="temporal",
                        source_id=f"{uko.evidence_key}#event-{len(events)}",
                        source_url=uko.metadata.source_url,
                        created_at=event.occurred_at,
                        modified_at=event.occurred_at,
                        authors=[event.actor] if event.actor else [],
                        tags=["event"],
                        tenant_id=uko.metadata.tenant_id,
                    ),
                    relationships=[
                        UKORelationship(
                            target_id=uko.id,
                            relationship="changed",
                            target_type=uko.type,
                            provenance=ExtractionProvenance(
                                extraction_method="provider_changelog",
                                extraction_timestamp=timestamp,
                                confidence=1.0,
                                evidence_snippet=f"changelog event: {event.name}",
                                model_version="",
                                pipeline_stage="temporal",
                            ),
                        )
                    ],
                    raw_data=event.model_dump(),
                    provenance=ExtractionProvenance(
                        extraction_method="provider_changelog",
                        extraction_timestamp=timestamp,
                        confidence=1.0,
                        evidence_snippet=f"temporal event from provider: {event.name}",
                        model_version="",
                        pipeline_stage="temporal",
                    ),
                )
            )
        return events
