"""Tests for ``ecms.shared.ids``."""

from __future__ import annotations

import pytest

from ecms.shared.exceptions import ValidationError
from ecms.shared.ids import new_correlation_id, new_id, new_uuid


def test_new_uuid_has_canonical_length() -> None:
    assert len(new_uuid()) == 36


def test_new_uuid_is_unique() -> None:
    assert new_uuid() != new_uuid()


def test_new_id_has_prefix() -> None:
    assert new_id("task").startswith("task-")


def test_new_id_rejects_empty_prefix() -> None:
    with pytest.raises(ValidationError):
        new_id("")


def test_new_id_rejects_whitespace_prefix() -> None:
    with pytest.raises(ValidationError):
        new_id("bad prefix")


def test_correlation_id_is_prefixed() -> None:
    assert new_correlation_id().startswith("corr-")
