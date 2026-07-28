from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from legacy_ecms.agents.base_agent import BaseAgent
from legacy_ecms.agents.context_assembler import ContextAssembler, create_session_memory
from legacy_ecms.config import get_settings
from legacy_ecms.memory.brain import GBrain
from legacy_ecms.memory.cognitive_orchestrator import CognitiveOrchestrator
from legacy_ecms.memory.mem0_layer import Mem0Memory

router = APIRouter(prefix="/query", tags=["query"])


class QueryRequest(BaseModel):
    question: str
    session_id: str | None = None


class QueryResponse(BaseModel):
    answer: str


@router.post("", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    settings = get_settings()
    brain = GBrain(Path("memory"))
    mem0 = Mem0Memory(settings) if getattr(settings, "mem0_enabled", False) else None
    assembler = ContextAssembler(brain=brain, mem0=mem0)
    agent = BaseAgent(context_assembler=assembler)

    answer = await agent.ask(request.question, session_id=request.session_id)

    # Write context back to shared session for cross-agent visibility
    if request.session_id:
        sm = create_session_memory()
        sm.set(request.session_id, "last_question", request.question)
        sm.set(request.session_id, "last_answer", answer)

    # Fire-and-forget cognitive capture
    if mem0 and mem0.enabled:
        import asyncio
        user_id = request.session_id or "default"

        async def capture():
            try:
                orch = CognitiveOrchestrator(settings, brain=brain, mem0=mem0)
                await orch.process_turn(request.question, answer, user_id, request.session_id)
            except Exception:
                pass

        asyncio.create_task(capture())

    return QueryResponse(answer=answer)
