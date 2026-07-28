"""Planning and decision domain models (SECTION 284/285/288).

The Intelligence Layer converts intent into :class:`Goal` objects, compiles them
into a versioned :class:`ExecutionPlan`, and records every choice as an
explainable :class:`Decision`. None of these execute anything; they describe work.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from ecms.shared.enums import GoalStatus, StrategyType
from ecms.shared.ids import new_id
from ecms.shared.models.base import DomainModel, ImmutableModel
from ecms.shared.time import utcnow

__all__ = ["Decision", "ExecutionPlan", "Goal"]


def _goal_id() -> str:
    return new_id("goal")


def _plan_id() -> str:
    return new_id("plan")


def _decision_id() -> str:
    return new_id("dec")


class Goal(DomainModel):
    """A goal derived from user intent (SECTION 284).

    A goal's definition (description, constraints, success criteria) is immutable
    during execution; only its status advances.
    """

    goal_id: str = Field(default_factory=_goal_id)
    description: str
    parent_goal: str | None = None
    sub_goals: list[str] = Field(default_factory=list)
    dependencies: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    expected_outputs: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    status: GoalStatus = GoalStatus.PENDING


class ExecutionPlan(DomainModel):
    """A versioned execution plan converting tasks into an ordered graph (SECTION 285)."""

    plan_id: str = Field(default_factory=_plan_id)
    task_id: str
    strategy: StrategyType = StrategyType.SEQUENTIAL
    steps: list[dict[str, Any]] = Field(default_factory=list)
    synchronization_points: list[str] = Field(default_factory=list)
    validation_points: list[str] = Field(default_factory=list)
    reflection_points: list[str] = Field(default_factory=list)
    version: int = Field(default=1, ge=1)
    created_at: datetime = Field(default_factory=utcnow)


class Decision(ImmutableModel):
    """An explainable, traceable decision made during reasoning (SECTION 288/297).

    Every decision answers why it was made: which knowledge and memory it used,
    which options it considered, and why the alternatives were rejected.
    """

    decision_id: str = Field(default_factory=_decision_id)
    task_id: str | None = None
    agent_id: str | None = None
    question: str
    chosen: str
    rationale: str
    considered_options: list[str] = Field(default_factory=list)
    rejected_options: list[dict[str, Any]] = Field(default_factory=list)
    knowledge_used: list[str] = Field(default_factory=list)
    memory_activated: list[str] = Field(default_factory=list)
    tools_considered: list[str] = Field(default_factory=list)
    strategy: StrategyType | None = None
    confidence: int = Field(default=0, ge=0, le=100)
    created_at: datetime = Field(default_factory=utcnow)
