"""Unit tests for score and budget value objects (SECTION 50)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError as PydanticValidationError

from ecms.shared.exceptions import ValidationError
from ecms.shared.value_objects import (
    ConfidenceScore,
    ExecutionBudget,
    ImportanceScore,
    Score,
    TokenBudget,
)


def test_score_fraction_and_from_fraction_round_trip() -> None:
    assert ConfidenceScore(value=50).fraction == 0.5
    assert Score.from_fraction(0.25).value == 25
    assert isinstance(ConfidenceScore.from_fraction(0.5), ConfidenceScore)


def test_score_from_fraction_clamps_out_of_range() -> None:
    assert Score.from_fraction(2.0).value == 100
    assert Score.from_fraction(-1.0).value == 0


def test_score_rejects_out_of_range_value() -> None:
    with pytest.raises(PydanticValidationError):
        ConfidenceScore(value=101)


def test_scores_of_different_types_are_not_equal() -> None:
    assert ConfidenceScore(value=50) != ImportanceScore(value=50)


def test_budget_consume_is_immutable() -> None:
    budget = TokenBudget(limit=100)
    used = budget.consume(30)
    assert used.consumed == 30
    assert used.remaining == 70
    assert budget.consumed == 0


def test_unbounded_budget_has_no_limit() -> None:
    budget = ExecutionBudget()
    assert budget.remaining is None
    assert budget.can_afford(10_000)
    assert not budget.exhausted


def test_budget_rejects_overspend() -> None:
    budget = TokenBudget(limit=10)
    with pytest.raises(ValidationError):
        budget.consume(11)


def test_budget_rejects_negative_consumption() -> None:
    with pytest.raises(ValidationError):
        TokenBudget(limit=10).consume(-1)


def test_budget_exhaustion() -> None:
    assert TokenBudget(limit=10).consume(10).exhausted


def test_budget_rejects_invalid_construction() -> None:
    with pytest.raises((ValidationError, PydanticValidationError)):
        TokenBudget(limit=5, consumed=10)
