"""Tests for ``ecms.shared.utils``."""

from __future__ import annotations

import pytest

from ecms.shared.exceptions import ValidationError
from ecms.shared.utils import chunked, deep_merge


def test_chunked_splits_evenly_and_remainder() -> None:
    assert list(chunked([1, 2, 3, 4, 5], 2)) == [[1, 2], [3, 4], [5]]


def test_chunked_rejects_non_positive_size() -> None:
    with pytest.raises(ValidationError):
        list(chunked([1], 0))


def test_deep_merge_recurses() -> None:
    base = {"a": 1, "nested": {"x": 1, "y": 2}}
    override = {"nested": {"y": 3, "z": 4}, "b": 5}
    assert deep_merge(base, override) == {
        "a": 1,
        "b": 5,
        "nested": {"x": 1, "y": 3, "z": 4},
    }
