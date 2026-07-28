from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

from legacy_ecms.core.uko import UniversalKnowledgeObject


class EpisodePayloadType(str, Enum):
    TEXT = "text"
    JSON = "json"


class EpisodePayload(BaseModel):
    model_config = ConfigDict(frozen=True)

    uko: UniversalKnowledgeObject
    name: str
    episode_body: str
    episode_type: EpisodePayloadType = EpisodePayloadType.TEXT
    reference_time: datetime
    source_description: str
    group_id: str | None = None


def uko_to_episode(uko: UniversalKnowledgeObject) -> EpisodePayload:
    """Convert a UKO into a Graphiti-ready episode payload."""

    relationship_lines = [
        f"- {rel.relationship} -> {rel.target_type.value}:{rel.target_id}"
        for rel in uko.relationships
    ]
    relationships = "\n".join(relationship_lines) if relationship_lines else "- none"
    authors = ", ".join(uko.metadata.authors) if uko.metadata.authors else "unknown"
    tags = ", ".join(uko.metadata.tags) if uko.metadata.tags else "none"

    body = "\n".join(
        [
            f"Artifact: {uko.name}",
            f"Type: {uko.type.value}",
            f"Source: {uko.metadata.source}",
            f"Source ID: {uko.metadata.source_id}",
            f"Authors: {authors}",
            f"Tags: {tags}",
            "Content:",
            uko.content,
            "Relationships:",
            relationships,
        ]
    )

    return EpisodePayload(
        uko=uko,
        name=f"{uko.metadata.source}:{uko.type.value}:{uko.name}",
        episode_body=body,
        reference_time=uko.metadata.modified_at,
        source_description=f"{uko.metadata.source} artifact {uko.metadata.source_id}",
        group_id=uko.metadata.tenant_id,
    )
