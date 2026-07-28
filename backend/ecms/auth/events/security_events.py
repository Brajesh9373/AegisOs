"""Security event factories (SECTION 222).

Security-relevant actions publish immutable events in the SECURITY category so
they can be audited and fed to security analytics.
"""

from __future__ import annotations

from typing import Any

from ecms.shared.enums import EventCategory
from ecms.shared.events import BaseEvent, make_event

__all__ = [
    "authentication_failed",
    "authorization_denied",
    "knowledge_access_denied",
    "secret_rotated",
    "security_violation_detected",
    "tool_execution_denied",
]

_PRODUCER = "security-runtime"


def _event(event_type: str, payload: dict[str, Any]) -> BaseEvent:
    return make_event(event_type, EventCategory.SECURITY, _PRODUCER, payload=payload)


def authentication_failed(principal: str) -> BaseEvent:
    """Emitted when authentication fails (SECTION 222)."""
    return _event("AuthenticationFailed", {"principal": principal})


def authorization_denied(principal: str, resource: str) -> BaseEvent:
    """Emitted when authorization is denied (SECTION 222)."""
    return _event("AuthorizationDenied", {"principal": principal, "resource": resource})


def secret_rotated(key: str) -> BaseEvent:
    """Emitted when a secret or key is rotated (SECTION 222)."""
    return _event("SecretRotated", {"key": key})


def security_violation_detected(detail: str) -> BaseEvent:
    """Emitted when a security violation is detected (SECTION 222)."""
    return _event("SecurityViolationDetected", {"detail": detail})


def knowledge_access_denied(principal: str, uco_id: str) -> BaseEvent:
    """Emitted when access to knowledge is denied (SECTION 222)."""
    return _event("KnowledgeAccessDenied", {"principal": principal, "uco_id": uco_id})


def tool_execution_denied(tool: str) -> BaseEvent:
    """Emitted when a tool execution is denied (SECTION 222)."""
    return _event("ToolExecutionDenied", {"tool": tool})
