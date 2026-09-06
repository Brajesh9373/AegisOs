"""Agent Profile Factory - instantiates runtime agents from profiles.

This module provides:
- ProfileLoader: Loads profiles from DB or plugins
- AgentFactory: Creates agent sessions from profiles with scope enforcement
- ScopeEnforcer: Validates agent actions against profile scopes
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import select

from ecms.agent_os.profiles.plugin import AgentProfileCatalog, AgentProfilePlugin
from ecms.persistence.database.rest_session import db_session
from ecms.persistence.models.agent_profile import AgentProfile

logger = logging.getLogger(__name__)


@dataclass
class LoadedProfile:
    """A profile ready for agent instantiation."""

    profile_id: str
    name: str
    description: str | None
    version: str
    role: str | None
    system_prompt: str | None
    user_prompt_template: str | None
    stages: list[dict[str, Any]]
    memory_scope: dict[str, Any]
    knowledge_scope: dict[str, Any]
    tool_scope: dict[str, Any]
    model_provider: str | None
    model_name: str | None
    temperature: float | None
    max_tokens: int | None
    execution_budget: dict[str, Any]
    parent_profile_id: str | None = None
    source: str = "db"  # "db" or "plugin"


class ProfileLoader:
    """Loads agent profiles from database or plugins."""

    def __init__(self) -> None:
        self._plugin_catalogs: dict[str, ProfileCatalog] = {}

    async def load(self, profile_id: str) -> LoadedProfile | None:
        """Load a profile by ID, checking plugins first, then database."""
        # Try plugin profiles first
        plugin_profile = await self._load_plugin_profile(profile_id)
        if plugin_profile:
            return plugin_profile

        # Try database profiles (with error handling)
        try:
            db_profile = await self._load_db_profile(profile_id)
            if db_profile:
                return db_profile
        except Exception as e:
            logger.warning("Failed to load DB profile %s: %s", profile_id, e)

        return None

    async def _load_plugin_profile(self, profile_id: str) -> LoadedProfile | None:
        """Load a built-in plugin profile."""
        # Check Business Analyst
        try:
            from ecms.agent.ba.plugin import get_ba_profile_catalog

            catalog = get_ba_profile_catalog()
            plugin = catalog.resolve(profile_id)
            logger.info("Loaded plugin profile %s from BA", profile_id)
            return self._plugin_to_loaded_profile(plugin, "plugin")
        except Exception as e:
            logger.warning("BA plugin load failed for %s: %s - %s", profile_id, type(e).__name__, e)

        # Check Compliance Officer
        try:
            from ecms.agent.compliance_officer import get_compliance_officer_profile_catalog

            catalog = get_compliance_officer_profile_catalog()
            plugin = catalog.resolve(profile_id)
            logger.info("Loaded plugin profile %s from Compliance Officer", profile_id)
            return self._plugin_to_loaded_profile(plugin, "plugin")
        except Exception as e:
            logger.warning("Compliance Officer plugin load failed for %s: %s - %s", profile_id, type(e).__name__, e)

        return None

    def _plugin_to_loaded_profile(self, plugin: AgentProfilePlugin, source: str) -> LoadedProfile:
        """Convert an AgentProfilePlugin to LoadedProfile."""
        spec = plugin.profile_spec
        # DSHProfileSpec has profile_id, version, stages but no name/description/role
        # Get them from the plugin's manifest or compute defaults
        profile_id = spec.profile_id
        name = profile_id.replace("-", " ").title()
        description = f"AI agent profile: {profile_id}"

        return LoadedProfile(
            profile_id=profile_id,
            name=name,
            description=description,
            version=spec.version,
            role=None,
            system_prompt=None,
            user_prompt_template=None,
            stages=[{"stage_id": s.stage_id} for s in spec.stages],
            memory_scope={
                "read": True,
                "write": False,
                "categories": [],
                "retention_days": 30,
            },
            knowledge_scope={
                "graphs": ["default"],
                "read": True,
                "write": False,
                "node_types": [],
            },
            tool_scope={
                "allowed_tools": [],
                "rate_limit": 60,
                "restrictions": {},
            },
            model_provider=None,
            model_name=None,
            temperature=None,
            max_tokens=None,
            execution_budget=spec.execution_budget.model_dump() if spec.execution_budget else {},
            source=source,
        )

    async def _load_db_profile(self, profile_id: str) -> LoadedProfile | None:
        """Load a database-stored profile."""
        async with db_session() as session:
            result = await session.execute(
                select(AgentProfile).where(AgentProfile.profile_id == profile_id)
            )
            profile = result.scalar_one_or_none()
            if not profile:
                return None

            # Handle parent profile inheritance
            memory_scope = profile.memory_scope or {}
            knowledge_scope = profile.knowledge_scope or {}
            tool_scope = profile.tool_scope or {}

            if profile.parent_profile_id:
                parent = await self._load_db_profile(profile.parent_profile_id)
                if parent:
                    # Merge with parent scopes (child overrides parent)
                    memory_scope = {**parent.memory_scope, **memory_scope}
                    knowledge_scope = {**parent.knowledge_scope, **knowledge_scope}
                    tool_scope = self._merge_tool_scopes(parent.tool_scope, tool_scope)

            return LoadedProfile(
                profile_id=profile.profile_id,
                name=profile.name,
                description=profile.description,
                version=profile.version,
                role=profile.role,
                system_prompt=profile.system_prompt,
                user_prompt_template=profile.user_prompt_template,
                stages=profile.stages or [],
                memory_scope=memory_scope,
                knowledge_scope=knowledge_scope,
                tool_scope=tool_scope,
                model_provider=profile.model_provider,
                model_name=profile.model_name,
                temperature=profile.temperature,
                max_tokens=profile.max_tokens,
                execution_budget=profile.execution_budget or {},
                parent_profile_id=profile.parent_profile_id,
                source="db",
            )

    def _merge_tool_scopes(
        self, parent: dict[str, Any], child: dict[str, Any]
    ) -> dict[str, Any]:
        """Merge child tool scope with parent (child takes precedence)."""
        parent_tools = set(parent.get("allowed_tools", []))
        child_tools = set(child.get("allowed_tools", []))

        # Child can only add tools, not remove parent tools
        combined_tools = list(parent_tools | child_tools)

        return {
            "allowed_tools": combined_tools,
            "rate_limit": child.get("rate_limit", parent.get("rate_limit", 60)),
            "restrictions": {**parent.get("restrictions", {}), **child.get("restrictions", {})},
        }


@dataclass
class AgentInstance:
    """A runtime agent instance created from a profile."""

    instance_id: str
    profile_id: str
    name: str
    role: str | None
    system_prompt: str
    stages: list[dict[str, Any]]
    memory_scope: dict[str, Any]
    knowledge_scope: dict[str, Any]
    tool_scope: dict[str, Any]
    model_config: dict[str, Any]
    execution_budget: dict[str, Any]
    created_at: Any = field(default_factory=lambda: None)  # Will be set to datetime


class AgentFactory:
    """Creates runtime agent instances from profiles."""

    def __init__(self, profile_loader: ProfileLoader | None = None) -> None:
        self.profile_loader = profile_loader or ProfileLoader()
        self._instances: dict[str, AgentInstance] = {}
        self._active_enforcer: ScopeEnforcer | None = None

    async def create_execution_context(
        self, profile_id: str, **overrides: Any
    ) -> AgentInstance:
        """Create an agent instance and set up scope enforcement context.

        This method creates an agent instance and configures the global
        scope enforcer so that all tool invocations are checked against
        the profile's scopes.

        Args:
            profile_id: The profile to instantiate
            **overrides: Optional overrides for profile settings

        Returns:
            AgentInstance ready for execution with scope enforcement active

        Raises:
            ValueError: If profile not found
        """
        # Import here to avoid circular imports
        from ecms.agent.tools import set_scope_enforcer

        # Create the instance
        instance = await self.create_from_profile(profile_id, **overrides)

        # Set up scope enforcement
        enforcer = ScopeEnforcer(instance)
        self._active_enforcer = enforcer
        set_scope_enforcer(enforcer)

        logger.info(
            "Created execution context for agent %s with scope enforcement",
            instance.instance_id,
        )

        return instance

    def clear_execution_context(self) -> None:
        """Clear the current execution context and scope enforcement."""
        from ecms.agent.tools import set_scope_enforcer

        if self._active_enforcer:
            set_scope_enforcer(None)
            self._active_enforcer = None
            logger.info("Cleared execution context and scope enforcement")

    async def create_from_profile(self, profile_id: str, **overrides: Any) -> AgentInstance:
        """Create an agent instance from a profile.

        Args:
            profile_id: The profile to instantiate
            **overrides: Optional overrides for profile settings

        Returns:
            AgentInstance ready for execution

        Raises:
            ValueError: If profile not found
        """
        profile = await self.profile_loader.load(profile_id)
        if not profile:
            raise ValueError(f"Profile '{profile_id}' not found")

        # Apply overrides
        system_prompt = overrides.get("system_prompt", profile.system_prompt) or ""
        if profile.role:
            system_prompt = f"[Role: {profile.role}]\n{system_prompt}"

        # Build model config
        model_config = {
            "provider": overrides.get("model_provider", profile.model_provider),
            "model_name": overrides.get("model_name", profile.model_name),
            "temperature": overrides.get("temperature", profile.temperature),
            "max_tokens": overrides.get("max_tokens", profile.max_tokens),
        }

        # Merge execution budget with overrides
        execution_budget = {**profile.execution_budget}
        if "execution_budget" in overrides:
            execution_budget = {**execution_budget, **overrides["execution_budget"]}

        instance = AgentInstance(
            instance_id=f"agent-{uuid.uuid4().hex[:12]}",
            profile_id=profile.profile_id,
            name=profile.name,
            role=profile.role,
            system_prompt=system_prompt,
            stages=overrides.get("stages", profile.stages),
            memory_scope=overrides.get("memory_scope", profile.memory_scope),
            knowledge_scope=overrides.get("knowledge_scope", profile.knowledge_scope),
            tool_scope=overrides.get("tool_scope", profile.tool_scope),
            model_config=model_config,
            execution_budget=execution_budget,
        )

        self._instances[instance.instance_id] = instance
        logger.info(
            "Created agent instance %s from profile %s",
            instance.instance_id,
            profile_id,
        )

        return instance

    def get(self, instance_id: str) -> AgentInstance | None:
        """Get an agent instance by ID."""
        return self._instances.get(instance_id)

    def get_by_profile_id(self, profile_id: str) -> AgentInstance | None:
        """Get an active agent instance by profile ID."""
        for instance in self._instances.values():
            if instance.profile_id == profile_id:
                return instance
        return None

    def list_instances(self) -> list[AgentInstance]:
        """List all active agent instances."""
        return list(self._instances.values())

    def remove(self, instance_id: str) -> bool:
        """Remove an agent instance."""
        if instance_id in self._instances:
            del self._instances[instance_id]
            return True
        return False


class ScopeEnforcer:
    """Enforces profile scopes on agent actions."""

    def __init__(self, agent_instance: AgentInstance) -> None:
        self.agent = agent_instance
        self.tool_scope = agent_instance.tool_scope
        self.memory_scope = agent_instance.memory_scope
        self.knowledge_scope = agent_instance.knowledge_scope

    def can_use_tool(self, tool_name: str) -> tuple[bool, str | None]:
        """Check if the agent can use a specific tool.

        Returns:
            (allowed, reason_if_not)
        """
        allowed_tools = self.tool_scope.get("allowed_tools", [])
        if not allowed_tools:
            return True, None

        # Wildcard allows all tools
        if "*" in allowed_tools or "all" in allowed_tools:
            return True, None

        if tool_name in allowed_tools:
            return True, None

        return False, f"Tool '{tool_name}' not in allowed tools: {allowed_tools}"

    def can_read_memory(self, category: str) -> bool:
        """Check if the agent can read from a memory category."""
        if not self.memory_scope.get("read", True):
            return False

        allowed_categories = self.memory_scope.get("categories", [])
        if not allowed_categories:
            return True  # No restrictions

        return category in allowed_categories

    def can_write_memory(self, category: str) -> bool:
        """Check if the agent can write to a memory category."""
        if not self.memory_scope.get("write", False):
            return False

        allowed_categories = self.memory_scope.get("categories", [])
        if not allowed_categories:
            return True

        return category in allowed_categories

    def can_read_knowledge(self, graph: str) -> bool:
        """Check if the agent can read from a knowledge graph."""
        if not self.knowledge_scope.get("read", True):
            return False

        allowed_graphs = self.knowledge_scope.get("graphs", [])
        if not allowed_graphs:
            return True

        return graph in allowed_graphs

    def can_write_knowledge(self, graph: str) -> bool:
        """Check if the agent can write to a knowledge graph."""
        if not self.knowledge_scope.get("write", False):
            return False

        allowed_graphs = self.knowledge_scope.get("graphs", [])
        if not allowed_graphs:
            return True

        return graph in allowed_graphs

    def check_rate_limit(self, tool_name: str) -> tuple[bool, str | None]:
        """Check if the tool call is within rate limits."""
        # Simple rate limiting - in production, track actual usage
        rate_limit = self.tool_scope.get("rate_limit", 60)
        restrictions = self.tool_scope.get("restrictions", {})

        # Check for tool-specific restrictions
        tool_restrictions = restrictions.get(tool_name, {})
        if tool_restrictions.get("blocked", False):
            return False, f"Tool '{tool_name}' is blocked by profile restrictions"

        # Check for approval requirements
        if tool_restrictions.get("require_approval", False):
            return False, f"Tool '{tool_name}' requires approval before use"

        # Rate limit info (actual enforcement would need tracking)
        return True, None

    def enforce(self, action: str, target: str | None = None) -> tuple[bool, str | None]:
        """Enforce all scopes on an action.

        Args:
            action: The action type (e.g., "tool", "memory_read", "memory_write", "knowledge_read", "knowledge_write")
            target: The target of the action (e.g., tool name, memory category, graph name)

        Returns:
            (allowed, reason_if_not)
        """
        if action == "tool":
            if not target:
                return False, "Tool name required"
            return self.can_use_tool(target)

        if action == "memory_read":
            return (self.can_read_memory(target or ""), None)

        if action == "memory_write":
            return (self.can_write_memory(target or ""), None)

        if action == "knowledge_read":
            return (self.can_read_knowledge(target or ""), None)

        if action == "knowledge_write":
            return (self.can_write_knowledge(target or ""), None)

        # Unknown action - allow but log
        logger.warning("Unknown action type: %s", action)
        return True, None