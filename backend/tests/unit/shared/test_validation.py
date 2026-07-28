"""Tests for ``ecms.shared.validation``."""

from __future__ import annotations

import pytest

from ecms.shared.exceptions import ValidationError
from ecms.shared.validation import ensure_in_range, ensure_non_empty, ensure_one_of


def test_ensure_non_empty_strips() -> None:
    assert ensure_non_empty("  hi ") == "hi"


def test_ensure_non_empty_raises() -> None:
    with pytest.raises(ValidationError):
        ensure_non_empty("   ")


def test_ensure_in_range_ok() -> None:
    assert ensure_in_range(5, minimum=0, maximum=10) == 5


def test_ensure_in_range_raises() -> None:
    with pytest.raises(ValidationError):
        ensure_in_range(11, minimum=0, maximum=10)


def test_ensure_one_of_ok() -> None:
    assert ensure_one_of("a", {"a", "b"}) == "a"


def test_ensure_one_of_raises() -> None:
    with pytest.raises(ValidationError):
        ensure_one_of("z", {"a", "b"})
