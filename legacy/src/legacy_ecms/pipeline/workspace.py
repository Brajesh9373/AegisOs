"""Workspace node creation — explicit central node linking all providers under one project."""
from datetime import datetime, timezone
from typing import Any

from legacy_ecms.core.episode import uko_to_episode
from legacy_ecms.core.uko import (
    ExtractionProvenance,
    UKOMetadata,
    UKORelationship,
    UKOType,
    UniversalKnowledgeObject,
)


def create_workspace_uko(workspace_id: str, workspace_name: str | None = None) -> UniversalKnowledgeObject:
    """Create a WORKSPACE UKO that acts as the central hub for all provider data."""
    name = workspace_name or workspace_id
    timestamp = datetime.now(timezone.utc)
    return UniversalKnowledgeObject(
        id=f"workspace:{workspace_id}",
        type=UKOType.WORKSPACE,
        name=name,
        content=f"Workspace '{name}' — unified knowledge hub for all connected platforms.",
        metadata=UKOMetadata(
            source="workspace",
            source_id=workspace_id,
            created_at=timestamp,
            modified_at=timestamp,
            tags=["workspace"],
            tenant_id=workspace_id,
        ),
        provenance=ExtractionProvenance(
            extraction_method="workspace_init",
            extraction_timestamp=timestamp,
            confidence=1.0,
            evidence_snippet=f"workspace created: {workspace_id}",
            pipeline_stage="provider",
        ),
        status="active",
        version=1,
    )


def attach_ukos_to_workspace(
    ukos: list[UniversalKnowledgeObject],
    workspace_id: str,
    workspace_name: str | None = None,
) -> list[UniversalKnowledgeObject]:
    """Thread workspace_id as tenant_id and add a 'part_of_workspace' relationship."""
    workspace_uko = create_workspace_uko(workspace_id, workspace_name)
    tagged: list[UniversalKnowledgeObject] = [workspace_uko]
    for uko in ukos:
        tagged.append(
            uko.model_copy(
                update={
                    "metadata": uko.metadata.model_copy(update={"tenant_id": workspace_id}),
                    "relationships": [
                        *uko.relationships,
                        UKORelationship(
                            target_id=f"workspace:{workspace_id}",
                            relationship="part_of_workspace",
                            target_type=UKOType.WORKSPACE,
                            confidence=1.0,
                            provenance=ExtractionProvenance(
                                extraction_method="workspace_link",
                                extraction_timestamp=datetime.now(timezone.utc),
                                confidence=1.0,
                                evidence_snippet=f"{uko.id} belongs to workspace {workspace_id}",
                                pipeline_stage="provider",
                            ),
                        ),
                    ],
                    "ingestion_batch_id": workspace_id,
                }
            )
        )
    return tagged


async def persist_workspace_node(graph: Any, workspace_id: str, workspace_name: str | None = None) -> None:
    """Ensure workspace UKO exists in FalkorDB. Idempotent — uses MERGE."""
    ws_uko = create_workspace_uko(workspace_id, workspace_name)
    ep = uko_to_episode(ws_uko)
    if getattr(graph, "raw_mode", True):
        await graph.add_episodes_raw_batch([ep])
    else:
        await graph.add_episode(ep)
