"""Default planner: converts intent into an execution plan (SECTION 283/285).

The planner decomposes the prompt into goals, selects a strategy, records the
choice as an explainable decision, and compiles a versioned execution plan. It
plans only; it never executes tools or writes the graph.
"""

from __future__ import annotations

from typing import Any

from ecms.events import EventBus
from ecms.intelligence.events.intelligence_events import (
    planner_completed,
    planner_started,
)
from ecms.intelligence.services.decision_engine import DecisionEngine
from ecms.intelligence.services.goal_engine import GoalEngine
from ecms.intelligence.services.strategy_engine import StrategyEngine
from ecms.shared.enums import StrategyType
from ecms.shared.events import BaseEvent
from ecms.shared.models import Decision, ExecutionPlan, Task

__all__ = ["DefaultPlanner"]


class DefaultPlanner:
    """Converts a prompt and task into a versioned execution plan (SECTION 283)."""

    def __init__(
        self,
        *,
        goals: GoalEngine | None = None,
        strategy: StrategyEngine | None = None,
        decisions: DecisionEngine | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize with goal, strategy and decision engines."""
        self._goals = goals or GoalEngine()
        self._strategy = strategy or StrategyEngine()
        self._decisions = decisions or DecisionEngine()
        self._event_bus = event_bus
        self._last_decision: Decision | None = None

    @property
    def last_decision(self) -> Decision | None:
        """Return the most recent strategy decision, for explainability."""
        return self._last_decision

    async def plan(self, task: Task, context: str) -> ExecutionPlan:
        """Decompose intent, choose a strategy and compile an execution plan."""
        await self._emit(planner_started(task.task_id))
        goals = self._goals.decompose(context)
        strategy = self._strategy.select(context, goals)
        self._last_decision = self._decisions.decide(
            question="Which execution strategy?",
            chosen=strategy.value,
            rationale=f"selected {strategy.value} for {len(goals)} goal(s)",
            task_id=task.task_id,
            considered=[option.value for option in StrategyType],
            strategy=strategy,
        )
        steps: list[dict[str, Any]] = [
            {"order": index, "goal_id": goal.goal_id, "description": goal.description}
            for index, goal in enumerate(goals)
        ]
        plan = ExecutionPlan(
            task_id=task.task_id,
            strategy=strategy,
            steps=steps,
            validation_points=[goals[-1].goal_id],
            reflection_points=[goals[-1].goal_id],
        )
        await self._emit(planner_completed(task.task_id, plan.plan_id))
        return plan

    async def _emit(self, event: BaseEvent) -> None:
        if self._event_bus is not None:
            await self._event_bus.publish(event)
