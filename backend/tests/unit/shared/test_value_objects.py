"""Tests for ``ecms.shared.value_objects``."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from ecms.shared.value_objects import ValueObject


class _Point(ValueObject):
    x: int
    y: int


def test_value_object_is_frozen() -> None:
    point = _Point(x=1, y=2)
    with pytest.raises(ValidationError):
        point.x = 5


def test_value_object_equality_by_value() -> None:
    assert _Point(x=1, y=2) == _Point(x=1, y=2)
    assert _Point(x=1, y=2) != _Point(x=1, y=3)
