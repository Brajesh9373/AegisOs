from pydantic import BaseModel, ConfigDict, Field

from legacy_ecms.config import get_settings
from legacy_ecms.memory.brain import GBrain
from legacy_ecms.memory.long_term import LongTermMemory
from legacy_ecms.memory.mem0_layer import Mem0Memory
from legacy_ecms.memory.session import SessionMemory
from legacy_ecms.memory.working import WorkingMemory


def create_session_memory(workspace_id: str = "default") -> "SessionMemory":
    """Create session memory — auto-detects Redis availability.

    If Redis is reachable at the configured URL, uses RedisSessionMemory
    (shared across CLI agents). Otherwise falls back to in-process dict
    (single-node only).
    """
    try:
        settings = get_settings()
    except Exception:
        return _create_inprocess_session()

    if getattr(settings, "session_backend", "memory") == "redis":
        try:
            from legacy_ecms.memory.session_redis import RedisSessionMemory
            rsm = RedisSessionMemory(
                redis_url=settings.redis_url,
                workspace_id=workspace_id,
            )
            if rsm._available:
                return rsm  # type: ignore[return-value]
        except Exception:
            pass
    return _create_inprocess_session()


def _create_inprocess_session() -> SessionMemory:
    return SessionMemory()


class AssembledContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    query: str
    working: dict = Field(default_factory=dict)
    session: dict = Field(default_factory=dict)
    memory_notes: list[dict] = Field(default_factory=list)
    mem0_results: list[dict] = Field(default_factory=list)
    graph_results: list = Field(default_factory=list)


class ContextAssembler:
    def __init__(
        self,
        working_memory: WorkingMemory | None = None,
        session_memory: SessionMemory | None = None,
        long_term_memory: LongTermMemory | None = None,
        brain: GBrain | None = None,
        mem0: Mem0Memory | None = None,
    ) -> None:
        self.working_memory = working_memory or WorkingMemory()
        self.session_memory = session_memory or create_session_memory()
        self.long_term_memory = long_term_memory or LongTermMemory()
        self.brain = brain
        self.mem0 = mem0

    async def assemble(self, query: str, session_id: str | None = None) -> AssembledContext:
        memory_notes = await self.brain.read(query) if self.brain else []
        graph_results = await self.long_term_memory.search(query)
        mem0_results = (
            await self.mem0.search(query, user_id=session_id or "default")
            if self.mem0
            else []
        )
        return AssembledContext(
            query=query,
            working=self.working_memory.snapshot(),
            session=self.session_memory.snapshot(session_id) if session_id else {},
            memory_notes=memory_notes,
            mem0_results=mem0_results,
            graph_results=list(graph_results) if graph_results else [],
        )
