"""Structured logging configuration (SECTION 76/102).

Configures structlog with UTC timestamps, log level, ambient request context (correlation,
session, task and user ids), and automatic redaction of sensitive fields. Logs render as
JSON in production and human-readable output in development.
"""

from __future__ import annotations

import logging
from collections.abc import MutableMapping
from typing import Any, cast

import structlog

from ecms.shared.context import current_context
from ecms.shared.security import REDACTED, SENSITIVE_KEYS

__all__ = ["add_context", "configure_logging", "get_logger", "scrub_secrets"]

EventDict = MutableMapping[str, Any]


def add_context(_logger: Any, _method: str, event_dict: EventDict) -> EventDict:
    """Inject ambient correlation/session/task/user ids into the log event."""
    context = current_context()
    if context.correlation_id:
        event_dict.setdefault("correlation_id", context.correlation_id)
    if context.session_id:
        event_dict.setdefault("session_id", context.session_id)
    if context.task_id:
        event_dict.setdefault("task_id", context.task_id)
    if context.user_id:
        event_dict.setdefault("user_id", context.user_id)
    return event_dict


def scrub_secrets(_logger: Any, _method: str, event_dict: EventDict) -> EventDict:
    """Redact values whose keys look sensitive (SECTION 76)."""
    for key in list(event_dict):
        if any(marker in key.lower() for marker in SENSITIVE_KEYS):
            event_dict[key] = REDACTED
    return event_dict


def configure_logging(*, level: str = "INFO", json_logs: bool = True) -> None:
    """Configure structlog processors and level filtering (SECTION 76/102)."""
    level_number = logging.getLevelNamesMapping().get(level.upper(), logging.INFO)
    renderer: Any = (
        structlog.processors.JSONRenderer() if json_logs else structlog.dev.ConsoleRenderer()
    )
    processors: list[Any] = [
        structlog.contextvars.merge_contextvars,
        add_context,
        scrub_secrets,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        renderer,
    ]
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level_number),
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.typing.FilteringBoundLogger:
    """Return a bound structured logger for a named component."""
    return cast(
        "structlog.typing.FilteringBoundLogger",
        structlog.get_logger(name, component=name),
    )
