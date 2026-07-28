"""Tests for ``ecms.shared.config`` helpers."""

from __future__ import annotations

import pytest

from ecms.shared.config import get_env, parse_bool
from ecms.shared.exceptions import ConfigurationError


def test_parse_bool_true() -> None:
    assert parse_bool("Yes") is True


def test_parse_bool_false() -> None:
    assert parse_bool("off") is False


def test_parse_bool_invalid_raises() -> None:
    with pytest.raises(ConfigurationError):
        parse_bool("maybe")


def test_get_env_returns_default() -> None:
    assert get_env("ECMS_NONEXISTENT_XYZ_KEY", "fallback") == "fallback"
