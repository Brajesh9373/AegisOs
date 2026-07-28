"""Resource budget value objects (SECTION 41/50/145).

Budgets bound the resources an execution may consume (tokens, memory,
activations, wall-clock work units). They are immutable: consuming resources
yields a new budget rather than mutating in place, keeping working memory and
execution context side-effect free and replayable.
"""

from __future__ import annotations

from typing import Self

from pydantic import Field, model_validator

from ecms.shared.exceptions import ValidationError
from ecms.shared.value_objects.base import ValueObject

__all__ = [
    "ActivationBudget",
    "Budget",
    "ExecutionBudget",
    "MemoryBudget",
    "TokenBudget",
]


class Budget(ValueObject):
    """Immutable resource budget with an optional limit and a consumed amount.

    A ``limit`` of ``None`` denotes an unbounded budget. Consumption never
    mutates the instance; :meth:`consume` returns a new budget.
    """

    limit: int | None = Field(default=None, ge=0)
    consumed: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def _check_within_limit(self) -> Self:
        """Ensure the consumed amount never exceeds a bounded limit."""
        if self.limit is not None and self.consumed > self.limit:
            raise ValidationError(f"budget consumed {self.consumed} exceeds limit {self.limit}")
        return self

    @property
    def remaining(self) -> int | None:
        """Return the remaining amount, or ``None`` when the budget is unbounded."""
        return None if self.limit is None else self.limit - self.consumed

    @property
    def exhausted(self) -> bool:
        """Return ``True`` when a bounded budget has no remaining amount."""
        remaining = self.remaining
        return remaining is not None and remaining <= 0

    def can_afford(self, amount: int) -> bool:
        """Return ``True`` when ``amount`` fits within the remaining budget."""
        return self.limit is None or self.consumed + amount <= self.limit

    def consume(self, amount: int) -> Self:
        """Return a new budget with ``amount`` added to the consumed total.

        Args:
            amount: A non-negative amount to consume.

        Returns:
            A new budget of the same concrete type with the updated total.

        Raises:
            ValidationError: If ``amount`` is negative or exceeds the remaining budget.
        """
        if amount < 0:
            raise ValidationError(f"cannot consume a negative amount: {amount}")
        if not self.can_afford(amount):
            raise ValidationError(f"amount {amount} exceeds remaining budget {self.remaining}")
        return self.model_copy(update={"consumed": self.consumed + amount})


class TokenBudget(Budget):
    """Budget bounding the number of reasoning tokens an execution may use."""


class MemoryBudget(Budget):
    """Budget bounding the working-memory footprint of an execution (SECTION 41)."""


class ActivationBudget(Budget):
    """Budget bounding how many knowledge objects may be activated (SECTION 145)."""


class ExecutionBudget(Budget):
    """Budget bounding the work units an execution may perform (SECTION 40)."""
