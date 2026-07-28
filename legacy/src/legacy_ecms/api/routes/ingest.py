from fastapi import APIRouter
from pydantic import BaseModel

from legacy_ecms.api.graph_context import orchestrator_context
from legacy_ecms.core.uko import UniversalKnowledgeObject
from legacy_ecms.pipeline.workspace import attach_ukos_to_workspace
from ecms.visualization.graph_changed import snapshot_after_graph_write

router = APIRouter(prefix="/ingest", tags=["ingest"])


class IngestUKORequest(BaseModel):
    uko: UniversalKnowledgeObject
    persist: bool = False
    workspace_id: str | None = None
    workspace_name: str | None = None


class IngestResponse(BaseModel):
    episode_count: int
    episode_names: list[str]
    persisted: bool
    write_success_count: int = 0
    write_failure_count: int = 0


@router.post("/uko", response_model=IngestResponse)
async def ingest_uko(request: IngestUKORequest) -> IngestResponse:
    ukos_to_process = [request.uko]
    if request.workspace_id:
        ukos_to_process = attach_ukos_to_workspace(ukos_to_process, request.workspace_id, request.workspace_name)
    async with orchestrator_context(request.persist) as orchestrator:
        all_episodes, write_result = await orchestrator.process_batch(ukos_to_process)
    await snapshot_after_graph_write(
        persisted=request.persist,
        success_count=write_result.success_count,
        source="uko",
        revision=request.uko.id,
    )
    return IngestResponse(
        episode_count=len(all_episodes),
        episode_names=[episode.name for episode in all_episodes],
        persisted=request.persist,
        write_success_count=write_result.success_count,
        write_failure_count=write_result.failure_count,
    )
