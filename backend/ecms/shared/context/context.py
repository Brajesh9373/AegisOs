"""Request, correlation and tracing context primitives (SECTION 85/96).

Context values are stored in :class:`contextvars.ContextVar` objects so they propagate
correctly across ``asyncio`` tasks without leaking between concurrent requests.
"""

from __future__ import annotations

from contextvars import ContextVar

from pydantic import BaseModel, ConfigDict

from ecms.shared.ids import new_correlation_id

__all__ = [
    "RequestContext",
    "bind_context",
    "clear_context",
    "current_context",
    "get_correlation_id",
]

_correlation_id: ContextVar[str | None] = ContextVar("ecms_correlation_id", default=None)
_request_id: ContextVar[str | None] = ContextVar("ecms_request_id", default=None)
_session_id: ContextVar[str | None] = ContextVar("ecms_session_id", default=None)
_task_id: ContextVar[str | None] = ContextVar("ecms_task_id", default=None)
_user_id: ContextVar[str | None] = ContextVar("ecms_user_id", default=None)
_trace_id: ContextVar[str | None] = ContextVar("ecms_trace_id", default=None)
_span_id: ContextVar[str | None] = ContextVar("ecms_span_id", default=None)


class RequestContext(BaseModel):
    """Immutable snapshot of the ambient request, correlation and tracing context."""

    model_config = ConfigDict(frozen=True)

    correlation_id: str | None = None
    request_id: str | None = None
    session_id: str | None = None
    task_id: str | None = None
    user_id: str | None = None
    trace_id: str | None = None
    span_id: str | None = None


def current_context() -> RequestContext:
    """Return an immutable snapshot of the current ambient context."""
    return RequestContext(
        correlation_id=_correlation_id.get(),
        request_id=_request_id.get(),
        session_id=_session_id.get(),
        task_id=_task_id.get(),
        user_id=_user_id.get(),
        trace_id=_trace_id.get(),
        span_id=_span_id.get(),
    )


def bind_context(
    *,
    correlation_id: str | None = None,
    request_id: str | None = None,
    session_id: str | None = None,
    task_id: str | None = None,
    user_id: str | None = None,
    trace_id: str | None = None,
    span_id: str | None = None,
) -> RequestContext:
    """Bind the supplied identifiers to the current execution context.

    A correlation id is generated when neither supplied nor already bound. Only
    explicitly-supplied identifiers overwrite existing values.

    Returns:
        An immutable snapshot of the resulting context.
    """
    _correlation_id.set(correlation_id or _correlation_id.get() or new_correlation_id())
    if request_id is not None:
        _request_id.set(request_id)
    if session_id is not None:
        _session_id.set(session_id)
    if task_id is not None:
        _task_id.set(task_id)
    if user_id is not None:
        _user_id.set(user_id)
    if trace_id is not None:
        _trace_id.set(trace_id)
    if span_id is not None:
        _span_id.set(span_id)
    return current_context()


def get_correlation_id() -> str:
    """Return the current correlation id, generating and binding one when absent."""
    existing = _correlation_id.get()
    if existing is None:
        existing = new_correlation_id()
        _correlation_id.set(existing)
    return existing


def clear_context() -> None:
    """Reset all context variables to their defaults."""
    for var in (
        _correlation_id,
        _request_id,
        _session_id,
        _task_id,
        _user_id,
        _trace_id,
        _span_id,
    ):
        var.set(None)
