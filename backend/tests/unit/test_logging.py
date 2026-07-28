"""Tests for structured logging."""

from __future__ import annotations

from ecms.infrastructure.telemetry import (
    add_context,
    configure_logging,
    get_logger,
    scrub_secrets,
)
from ecms.shared.context import bind_context, clear_context
from ecms.shared.security import REDACTED


def test_scrub_secrets_redacts_sensitive_keys() -> None:
    result = scrub_secrets(None, "info", {"password": "x", "user": "a"})
    assert result["password"] == REDACTED
    assert result["user"] == "a"


def test_add_context_injects_ids() -> None:
    clear_context()
    bind_context(correlation_id="c1", session_id="s1", task_id="t1", user_id="u1")
    result = add_context(None, "info", {})
    assert result["correlation_id"] == "c1"
    assert result["session_id"] == "s1"
    assert result["task_id"] == "t1"
    assert result["user_id"] == "u1"
    clear_context()


def test_configure_json_logging_and_log() -> None:
    configure_logging(json_logs=True, level="INFO")
    get_logger("svc").info("ready", outcome="success")


def test_configure_console_logging() -> None:
    configure_logging(json_logs=False, level="DEBUG")
    get_logger("svc").debug("debugging")
