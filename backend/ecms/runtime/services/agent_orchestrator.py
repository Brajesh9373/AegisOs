"""Agent orchestrator: agent lifecycle and assignment (SECTION 22/74).

The Runtime owns agents; agents never own knowledge. The orchestrator creates
agents, assigns them to tasks, and tracks their status.
"""

from __future__ import annotations

from ecms.events import EventBus
from ecms.runtime.events.runtime_events import agent_assigned, agent_created
from ecms.shared.enums import AgentRole, AgentStatus
from ecms.shared.events import BaseEvent
from ecms.shared.exceptions import NotFoundError
from ecms.shared.models import Agent

__all__ = ["AgentOrchestrator"]


class AgentOrchestrator:
    """Creates, assigns and tracks runtime agents (SECTION 74)."""

    def __init__(self, *, event_bus: EventBus | None = None) -> None:
        """Initialize an empty agent registry."""
        self._agents: dict[str, Agent] = {}
        self._event_bus = event_bus

    async def create(
        self,
        role: AgentRole,
        *,
        reasoning_model: str = "deterministic",
        permissions: list[str] | None = None,
        tool_access: list[str] | None = None,
    ) -> Agent:
        """Create an agent with a role and scoped permissions."""
        agent = Agent(
            role=role,
            reasoning_model=reasoning_model,
            permissions=permissions or [],
            tool_access=tool_access or [],
        )
        self._agents[agent.agent_id] = agent
        await self._emit(agent_created(agent.agent_id))
        return agent

    async def assign(self, agent_id: str, task_id: str) -> Agent:
        """Assign an agent to a task and mark it executing."""
        agent = self._require(agent_id)
        agent.current_task = task_id
        agent.status = AgentStatus.EXECUTING
        await self._emit(agent_assigned(agent_id, task_id))
        return agent

    async def stop(self, agent_id: str) -> Agent:
        """Stop an agent."""
        agent = self._require(agent_id)
        agent.status = AgentStatus.STOPPED
        agent.current_task = None
        return agent

    def get(self, agent_id: str) -> Agent | None:
        """Return an agent by id, or ``None``."""
        return self._agents.get(agent_id)

    def _require(self, agent_id: str) -> Agent:
        agent = self._agents.get(agent_id)
        if agent is None:
            raise NotFoundError(f"agent {agent_id!r} not found")
        return agent

    async def _emit(self, event: BaseEvent) -> None:
        if self._event_bus is not None:
            await self._event_bus.publish(event)
