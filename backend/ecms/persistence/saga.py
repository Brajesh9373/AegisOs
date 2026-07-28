"""Saga orchestration for cross-service transactions (SECTION 253).

A saga runs an ordered list of steps. If a step fails, the compensations of the
previously completed steps run in reverse order, providing eventual consistency
across resources (Postgres, the graph, the event bus) that a single ACID
transaction cannot span.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any, Self

from ecms.shared.exceptions import EcmsError

__all__ = ["Saga", "SagaError", "SagaStep"]


class SagaError(EcmsError):
    """Raised when a saga fails after attempting to compensate completed steps."""

    default_message = "Saga execution failed."
    default_code = "saga_error"


@dataclass(slots=True)
class SagaStep:
    """A single saga step: an action and an optional compensating action."""

    name: str
    action: Callable[[], Awaitable[Any]]
    compensation: Callable[[], Awaitable[None]] | None = None


class Saga:
    """Executes steps with reverse-order compensation on failure (SECTION 253)."""

    def __init__(self, name: str) -> None:
        """Initialize an empty saga with a name used in error messages."""
        self._name = name
        self._steps: list[SagaStep] = []

    def add_step(
        self,
        name: str,
        action: Callable[[], Awaitable[Any]],
        compensation: Callable[[], Awaitable[None]] | None = None,
    ) -> Self:
        """Append a step and return the saga for fluent chaining."""
        self._steps.append(SagaStep(name=name, action=action, compensation=compensation))
        return self

    async def execute(self) -> list[Any]:
        """Run every step in order, compensating completed steps if one fails.

        Returns:
            The list of results from each step's action, in order.

        Raises:
            SagaError: If any step fails; completed steps are compensated first.
        """
        completed: list[SagaStep] = []
        results: list[Any] = []
        for step in self._steps:
            try:
                results.append(await step.action())
            except Exception as exc:
                await self._compensate(completed)
                raise SagaError(f"saga {self._name!r} failed at step {step.name!r}: {exc}") from exc
            completed.append(step)
        return results

    async def _compensate(self, completed: list[SagaStep]) -> None:
        """Run the compensations of completed steps in reverse order."""
        for step in reversed(completed):
            if step.compensation is not None:
                await step.compensation()
