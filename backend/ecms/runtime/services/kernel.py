"""The ECMS runtime kernel: the deterministic execution pipeline (SECTION 71/92).

Every request flows through one pipeline: create session and task, assign an
agent, plan, activate memory and retrieve knowledge, execute tools, reflect,
promote candidates, update the graph, release working memory, and complete the
task. Steps whose engines are not wired (planner, tools, reflection, promotion)
are skipped; the kernel runs the steps it has and emits an event at each stage.
"""

from __future__ import annotations

from ecms.events import EventBus
from ecms.graph import GraphEngine
from ecms.knowledge.interfaces.engine import KnowledgeRepository
from ecms.memory.interfaces.memory import MemoryEngine
from ecms.runtime.domain.execution import ExecutionResult
from ecms.runtime.events.runtime_events import prompt_received
from ecms.runtime.interfaces.pipeline import Planner, Promoter, Reflector, ToolRunner
from ecms.runtime.services.agent_orchestrator import AgentOrchestrator
from ecms.runtime.services.session_manager import SessionManager
from ecms.runtime.services.task_manager import TaskManager
from ecms.shared.enums import AgentRole
from ecms.shared.events import BaseEvent
from ecms.shared.models import UniversalCognitiveObject

__all__ = ["RuntimeKernel"]


class RuntimeKernel:
    """Orchestrates every execution through one deterministic pipeline (SECTION 71/92)."""

    def __init__(
        self,
        *,
        knowledge: KnowledgeRepository,
        memory: MemoryEngine,
        graph: GraphEngine | None = None,
        event_bus: EventBus | None = None,
        session_manager: SessionManager | None = None,
        task_manager: TaskManager | None = None,
        agent_orchestrator: AgentOrchestrator | None = None,
        planner: Planner | None = None,
        tool_runner: ToolRunner | None = None,
        reflector: Reflector | None = None,
        promoter: Promoter | None = None,
    ) -> None:
        """Wire the kernel with engines, managers and optional pipeline collaborators."""
        self._knowledge = knowledge
        self._memory = memory
        self._graph = graph
        self._event_bus = event_bus
        self._sessions = session_manager or SessionManager(event_bus=event_bus)
        self._tasks = task_manager or TaskManager(event_bus=event_bus)
        self._agents = agent_orchestrator or AgentOrchestrator(event_bus=event_bus)
        self._planner = planner
        self._tool_runner = tool_runner
        self._reflector = reflector
        self._promoter = promoter

    @property
    def tasks(self) -> TaskManager:
        """Return the task manager."""
        return self._tasks

    @property
    def sessions(self) -> SessionManager:
        """Return the session manager."""
        return self._sessions

    async def execute(
        self,
        prompt: str,
        *,
        organization_id: str,
        user_id: str,
        session_id: str | None = None,
    ) -> ExecutionResult:
        """Run the full cognitive pipeline for a prompt and return the result (SECTION 92)."""
        session = self._sessions.get(session_id) if session_id else None
        if session is None:
            session = await self._sessions.create(organization_id=organization_id, user_id=user_id)
        task = await self._tasks.create(
            session_id=session.session_id,
            organization_id=organization_id,
            user_id=user_id,
            goal=prompt,
        )
        await self._sessions.add_task(session.session_id, task.task_id)
        await self._emit(prompt_received(task.task_id, prompt))
        await self._tasks.start(task.task_id)
        result = ExecutionResult(session_id=session.session_id, task_id=task.task_id)
        try:
            agent = await self._agents.create(AgentRole.PLANNER)
            await self._agents.assign(agent.agent_id, task.task_id)
            result.agent_id = agent.agent_id

            if self._planner is not None:
                plan = await self._planner.plan(task, prompt)
                result.plan_id = plan.plan_id
                task.planner_output = {
                    "plan_id": plan.plan_id,
                    "strategy": plan.strategy.value,
                }

            working = await self._memory.activate(prompt, task_id=task.task_id)
            task.working_memory_id = working.working_memory_id
            result.activated_uco_ids = working.active_uco_references
            activated = await self._resolve(working.active_uco_references)

            if self._tool_runner is not None:
                executions = await self._tool_runner.run(task, working)
                result.tool_executions = [item.execution_id for item in executions]

            if self._reflector is not None:
                reflection = await self._reflector.reflect(task, activated)
                result.reflection_id = reflection.reflection_id
                task.reflection_id = reflection.reflection_id
                candidates = await self._reflector.generate_candidates(task, reflection, activated)
                result.knowledge_candidates = [candidate.candidate_id for candidate in candidates]
                if self._promoter is not None:
                    await self._promoter.promote(candidates)

            if self._graph is not None:
                graph_nodes: list[str] = []
                for uco in activated:
                    node = await self._graph.upsert_uco(uco)
                    graph_nodes.append(node.node_id)
                result.graph_nodes = graph_nodes

            await self._memory.release(working)
            summary = f"activated {len(activated)} cognitive objects"
            await self._tasks.complete(task.task_id, summary=summary)
            await self._sessions.complete_task(session.session_id, task.task_id)
            result.summary = summary
        except Exception as exc:
            await self._tasks.fail(task.task_id, str(exc))
            result.status = "failed"
            raise
        return result

    async def _resolve(self, references: list[str]) -> list[UniversalCognitiveObject]:
        resolved = [await self._knowledge.get(reference) for reference in references]
        return [uco for uco in resolved if uco is not None]

    async def _emit(self, event: BaseEvent) -> None:
        if self._event_bus is not None:
            await self._event_bus.publish(event)
