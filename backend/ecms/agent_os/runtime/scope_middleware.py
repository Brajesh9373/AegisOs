"""Scope Enforcement Middleware for Agent Runtime.

This module provides middleware that enforces profile scopes on agent actions,
intercepting tool calls, memory operations, and knowledge graph access.
"""

from __future__ import annotations

import logging
from typing import Any, Callable

from ecms.agent_os.runtime.agent_factory import AgentInstance, ScopeEnforcer

logger = logging.getLogger(__name__)


class ScopeEnforcementMiddleware:
    """Middleware that enforces scope restrictions on agent actions.

    Intercepts tool calls, memory operations, and knowledge access to validate
    against the agent profile's defined scopes.
    """

    def __init__(self, agent_instance: AgentInstance) -> None:
        self._enforcer = ScopeEnforcer(agent_instance)
        self._instance = agent_instance

    def can_invoke_tool(self, tool_name: str) -> tuple[bool, str | None]:
        """Check if a tool can be invoked.

        Returns:
            (allowed, reason_if_blocked)
        """
        # First check rate limits and restrictions
        rate_ok, rate_reason = self._enforcer.check_rate_limit(tool_name)
        if not rate_ok:
            return False, rate_reason

        # Then check allowed tools list
        return self._enforcer.can_use_tool(tool_name)

    def wrap_tool_invocation(
        self, original_invoke: Callable[..., Any]
    ) -> Callable[..., Any]:
        """Create a wrapped version of tool invocation with scope enforcement.

        Args:
            original_invoke: The original tool invocation function

        Returns:
            Wrapped function that enforces scopes
        """

        async def wrapped_invoke(name: str, arguments: dict[str, Any]) -> str:
            # Check tool scope
            allowed, reason = self.can_invoke_tool(name)
            if not allowed:
                logger.warning(
                    "[%s] Tool '%s' blocked by scope policy: %s",
                    self._instance.instance_id,
                    name,
                    reason,
                )
                return f"Tool '{name}' is not allowed: {reason}"

            # Tool is allowed - proceed with original invocation
            return await original_invoke(name, arguments)

        return wrapped_invoke

    def get_enforcer(self) -> ScopeEnforcer:
        """Get the underlying scope enforcer."""
        return self._enforcer


class ScopedAgentContext:
    """Context manager for scoped agent operations.

    Provides a convenient interface for checking scope permissions
    before performing operations.
    """

    def __init__(self, agent_instance: AgentInstance) -> None:
        self._enforcer = ScopeEnforcer(agent_instance)
        self._instance = agent_instance

    # Tool permissions
    def check_tool(self, tool_name: str) -> tuple[bool, str | None]:
        """Check if tool can be used."""
        rate_ok, rate_reason = self._enforcer.check_rate_limit(tool_name)
        if not rate_ok:
            return False, rate_reason
        return self._enforcer.can_use_tool(tool_name)

    # Memory permissions
    def can_read_memory(self, category: str = "") -> bool:
        """Check if memory read is allowed."""
        return self._enforcer.can_read_memory(category)

    def can_write_memory(self, category: str = "") -> bool:
        """Check if memory write is allowed."""
        return self._enforcer.can_write_memory(category)

    # Knowledge permissions
    def can_read_knowledge(self, graph: str = "default") -> bool:
        """Check if knowledge read is allowed."""
        return self._enforcer.can_read_knowledge(graph)

    def can_write_knowledge(self, graph: str = "default") -> bool:
        """Check if knowledge write is allowed."""
        return self._enforcer.can_write_knowledge(graph)

    # Get scopes for inspection
    def get_scopes(self) -> dict[str, Any]:
        """Get current scope configuration."""
        return {
            "tool_scope": self._instance.tool_scope,
            "memory_scope": self._instance.memory_scope,
            "knowledge_scope": self._instance.knowledge_scope,
        }

    def get_instance_id(self) -> str:
        """Get the agent instance ID."""
        return self._instance.instance_id

    def get_profile_id(self) -> str:
        """Get the profile ID."""
        return self._instance.profile_id