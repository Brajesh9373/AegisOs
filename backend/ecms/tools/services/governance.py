"""Tool permission and policy engines (SECTION 175/176).

The permission engine decides whether a caller may use a tool at all; the policy
engine constrains how a tool may be used (allowed and denied commands, execution
timeout). Both are configurable per deployment.
"""

from __future__ import annotations

from collections.abc import Iterable

__all__ = ["ToolPermissionEngine", "ToolPolicyEngine"]


class ToolPermissionEngine:
    """Decides whether a caller may execute a tool (SECTION 175)."""

    def __init__(
        self,
        *,
        default_allow: bool = True,
        denied_tools: Iterable[str] | None = None,
    ) -> None:
        """Initialize with a default policy and an optional deny list."""
        self._default_allow = default_allow
        self._denied = set(denied_tools or ())

    def check(self, tool_name: str, *, agent_permissions: Iterable[str] | None = None) -> bool:
        """Return whether ``tool_name`` may be executed by a caller.

        A tool is permitted when it is not denied and either the default is allow
        or the caller's permissions explicitly grant it.
        """
        if tool_name in self._denied:
            return False
        if self._default_allow:
            return True
        return agent_permissions is not None and tool_name in set(agent_permissions)


class ToolPolicyEngine:
    """Constrains how tools may be used (SECTION 176)."""

    def __init__(
        self,
        *,
        allowed_commands: Iterable[str] | None = None,
        denied_commands: Iterable[str] | None = None,
        timeout_seconds: float = 30.0,
    ) -> None:
        """Initialize command allow/deny lists and an execution timeout."""
        self._allowed = set(allowed_commands) if allowed_commands is not None else None
        self._denied = set(denied_commands or ())
        self._timeout = timeout_seconds

    @property
    def timeout_seconds(self) -> float:
        """Return the maximum execution time policy."""
        return self._timeout

    def allows_command(self, command: str) -> bool:
        """Return whether a command is permitted by policy."""
        if command in self._denied:
            return False
        return self._allowed is None or command in self._allowed
