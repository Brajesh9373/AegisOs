from pathlib import Path

from fastapi import APIRouter, Query
from pydantic import BaseModel

from legacy_ecms.config import get_settings
from legacy_ecms.memory.brain import GBrain
from legacy_ecms.memory.mem0_layer import get_mem0

router = APIRouter(prefix="/memory", tags=["memory"])


# ── Existing GBrain endpoints (unchanged) ──────────────────────────

class MemoryWriteRequest(BaseModel):
    topic: str
    content: str


class MemoryWriteResponse(BaseModel):
    episode_count: int


class MemorySearchResponse(BaseModel):
    matches: list[dict[str, str]]


@router.post("/notes", response_model=MemoryWriteResponse)
async def write_note(request: MemoryWriteRequest) -> MemoryWriteResponse:
    episodes = await GBrain(Path("memory")).write(request.topic, request.content)
    return MemoryWriteResponse(episode_count=len(episodes))


@router.get("/notes", response_model=MemorySearchResponse)
async def search_notes(q: str) -> MemorySearchResponse:
    matches = await GBrain(Path("memory")).read(q)
    return MemorySearchResponse(matches=matches)


# ── New mem0 endpoints (uses singleton for connection pooling) ──────

class Mem0AddRequest(BaseModel):
    content: str
    user_id: str = "default"
    metadata: dict | None = None
    workspace_id: str = "default"


class Mem0AddResponse(BaseModel):
    results: list[dict]


class Mem0SearchResponse(BaseModel):
    results: list[dict]


@router.post("/remember", response_model=Mem0AddResponse)
async def mem0_add(request: Mem0AddRequest) -> Mem0AddResponse:
    settings = get_settings()
    mem0 = get_mem0(settings, request.workspace_id)
    result = await mem0.add(request.content, request.user_id, request.metadata)
    results_list = result.get("results", []) if isinstance(result, dict) else []

    # Auto-promote high-confidence memories to graph
    for entry in results_list:
        if entry.get("score", 0) >= getattr(settings, "mem0_promotion_threshold", 0.70):
            try:
                from legacy_ecms.api.graph_context import create_graph_client
                graph = create_graph_client()
                await graph.initialize()
                await mem0.promote_to_graph(entry, graph)
                await graph.close()
            except Exception:
                pass

    return Mem0AddResponse(results=results_list)


@router.get("/remember", response_model=Mem0SearchResponse)
async def mem0_search(
    q: str,
    user_id: str = "default",
    workspace_id: str = "default",
    limit: int = 5,
) -> Mem0SearchResponse:
    settings = get_settings()
    mem0 = get_mem0(settings, workspace_id)
    results = await mem0.search(q, user_id, limit)
    return Mem0SearchResponse(results=results)


@router.get("/remember/all")
async def mem0_get_all(user_id: str = "default", workspace_id: str = "default") -> list[dict]:
    settings = get_settings()
    mem0 = get_mem0(settings, workspace_id)
    return await mem0.get_all(user_id)


@router.delete("/remember/{memory_id}")
async def mem0_delete(memory_id: str, workspace_id: str = "default") -> dict:
    settings = get_settings()
    mem0 = get_mem0(settings, workspace_id)
    return await mem0.delete(memory_id)


# ── Cognitive loop endpoints ───────────────────────────────────────

@router.post("/consolidate")
async def trigger_consolidation(
    user_id: str = "default",
    workspace_id: str = "default",
) -> dict:
    """Trigger GBrain consolidation from clustered mem0 memories."""
    from legacy_ecms.memory.cognitive_orchestrator import CognitiveOrchestrator
    settings = get_settings()
    orch = CognitiveOrchestrator(settings, workspace_id=workspace_id)
    consolidated = await orch.consolidate(user_id)
    return {"consolidated_topics": consolidated, "count": len(consolidated)}


@router.post("/validate")
async def trigger_validation(
    user_id: str = "default",
    workspace_id: str = "default",
) -> dict:
    """Trigger contradiction detection between mem0 and graph."""
    from legacy_ecms.memory.cognitive_orchestrator import CognitiveOrchestrator
    settings = get_settings()
    orch = CognitiveOrchestrator(settings, workspace_id=workspace_id)
    result = await orch.validate(user_id)
    return result


@router.post("/decay")
async def trigger_decay(
    user_id: str = "default",
    workspace_id: str = "default",
) -> dict:
    """Trigger confidence decay on old memories."""
    from legacy_ecms.memory.cognitive_orchestrator import CognitiveOrchestrator
    settings = get_settings()
    orch = CognitiveOrchestrator(settings, workspace_id=workspace_id)
    decayed = await orch.decay(user_id)
    return {"decayed_memories": decayed}
