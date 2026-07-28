"""Tests for ``ecms.shared.security``."""

from __future__ import annotations

from ecms.shared.security import REDACTED, constant_time_compare, redact, redact_mapping


def test_redact_returns_marker() -> None:
    assert redact("supersecret") == REDACTED


def test_redact_mapping_redacts_sensitive_keys() -> None:
    data = {
        "username": "alice",
        "password": "p",
        "nested": {"api_key": "k", "keep": "v"},
    }
    result = redact_mapping(data)
    assert result["username"] == "alice"
    assert result["password"] == REDACTED
    assert result["nested"]["api_key"] == REDACTED
    assert result["nested"]["keep"] == "v"


def test_constant_time_compare() -> None:
    assert constant_time_compare("abc", "abc")
    assert not constant_time_compare("abc", "abd")
