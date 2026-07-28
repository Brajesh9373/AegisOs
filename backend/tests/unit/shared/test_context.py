"""Tests for ``ecms.shared.context``."""

from __future__ import annotations

from ecms.shared.context import (
    bind_context,
    clear_context,
    current_context,
    get_correlation_id,
)


def test_bind_and_current_context() -> None:
    clear_context()
    ctx = bind_context(user_id="u1", session_id="s1")
    assert ctx.user_id == "u1"
    assert ctx.session_id == "s1"
    assert ctx.correlation_id
    assert current_context().user_id == "u1"


def test_get_correlation_id_is_stable() -> None:
    clear_context()
    first = get_correlation_id()
    assert first == get_correlation_id()


def test_clear_context_resets() -> None:
    bind_context(user_id="u2")
    clear_context()
    assert current_context().user_id is None


def test_bind_all_identifier_fields() -> None:
    clear_context()
    ctx = bind_context(
        correlation_id="corr-x",
        request_id="req-1",
        session_id="s",
        task_id="t",
        user_id="u",
        trace_id="tr",
        span_id="sp",
    )
    assert ctx.correlation_id == "corr-x"
    assert ctx.request_id == "req-1"
    assert ctx.task_id == "t"
    assert ctx.trace_id == "tr"
    assert ctx.span_id == "sp"
