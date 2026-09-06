"""Agent Hierarchy Manager — orchestrates profile-based team initialization.

Manages the full agent hierarchy for a project:
1. Loading AgentProfiles from the database
2. Spawning designated (profile-initialized) agents with persistent sessions
3. Handling delegation with dynamic child spawning (shared session)
4. Tracking parent→child relationships for multi-level delegation

Architecture:
    AgentProfile (DB)
        ↓ load via AgentFactory
    AgentInstance
        ↓ spawn via DSHSDKSessionManager
    SDKAgentSession (persistent DSH subprocess)
        ↓ delegate_task(to_agent=None)
    DynamicChildAgent (general, task-specific, shared session)
        ↓ subagent.started/finished
    TaskResult → returned to parent
"""

from __future__ import annotations

import logging
from typing import Any

from ecms.agent_os.runtime.agent_factory import AgentFactory
from ecms.agent_os.runtime.dsh_sdk_manager import (
    DSHSDKSessionManager,
    SDKAgentSession,
    get_session_manager,
)

logger = logging.getLogger("ecms.agent_os.hierarchy_manager")


class AgentHierarchyManager:
    """Manages the full agent hierarchy for a project.

    Coordinates:
    - Loading profiles from DB
    - Spawning designated agents from profiles
    - Handling delegation with dynamic child spawning
    - Tracking parent→child relationships
    """

    def __init__(
        self,
        session_manager: DSHSDKSessionManager | None = None,
        factory: AgentFactory | None = None,
    ) -> None:
        self.factory = factory or AgentFactory()
        self.session_manager = session_manager or get_session_manager()

    async def initialize_project_team(
        self,
        project_id: str,
        api_key: str,
    ) -> dict[str, SDKAgentSession]:
        """Initialize all designated agents for a project.

        1. Load project positions from DB (via ProjectAgentPositionRepository)
        2. For each position, load the assigned AgentProfile
        3. Spawn a persistent agent from that profile
        4. Return map of position_id → session

        Args:
            project_id: The project to initialize the team for
            api_key: LLM API key for all agents

        Returns:
            Dict mapping position_id → SDKAgentSession
        """
        positions = await self._load_project_positions(project_id)
        sessions: dict[str, SDKAgentSession] = {}

        for position in positions:
            profile_id = position.get("profile_id")
            if not profile_id:
                logger.warning(
                    "Position %s has no profile_id, skipping",
                    position.get("id"),
                )
                continue

            agent_id = f"{project_id}-{position.position_key}"
            try:
                session = await self.session_manager.spawn_agent_from_profile(
                    profile_id=profile_id,
                    agent_id=agent_id,
                    api_key=api_key,
                    extra_system_prompt=position.get("system_prompt_addon"),
                )
                sessions[position.id] = session
                logger.info(
                    "Initialized agent %s for position %s (profile=%s)",
                    agent_id, position.id, profile_id,
                )
            except Exception as e:
                logger.error(
                    "Failed to spawn agent for position %s (profile=%s): %s",
                    position.id, profile_id, e,
                )

        logger.info(
            "Initialized %d/%d agents for project %s",
            len(sessions), len(positions), project_id,
        )
        return sessions

    async def delegate_to_named_agent(
        self,
        from_agent: str,
        to_agent: str,
        task: str,
        timeout: float = 600.0,
    ) -> str | None:
        """Delegate a task to a specific named agent (designated profile-initialized agent).

        Use this when you want to delegate to a specific team member (e.g., senior-eng-1).

        Args:
            from_agent: Parent agent ID
            to_agent: Specific child agent ID (must be running)
            task: Task description
            timeout: Max seconds to wait for response

        Returns:
            Child agent's response text, or None if failed
        """
        return await self.session_manager.delegate_task(
            from_agent=from_agent,
            to_agent=to_agent,
            task=task,
            spawn_dynamic=False,
            timeout=timeout,
        )

    async def delegate_with_dynamic_child(
        self,
        parent_agent_id: str,
        task: str,
        task_type: str = "general",
        timeout: float = 600.0,
    ) -> str:
        """Delegate a task by spawning a dynamic child in the parent's session.

        The child is a general-purpose subagent with no designation.
        It shares the parent's session context and can itself spawn children
        (up to the configured max depth).

        Args:
            parent_agent_id: Parent agent ID
            task: Task description
            task_type: Type of task (for logging/context)
            timeout: Max seconds to wait for child completion

        Returns:
            Child agent's response text
        """
        parent_session = self.session_manager.sessions.get(parent_agent_id)
        if not parent_session:
            logger.warning("Parent agent %s not running", parent_agent_id)
            return "Parent agent not running"

        # Determine current depth from parent
        parent_depth = parent_session.subagent_depth
        child_depth = parent_depth + 1

        logger.info(
            "Delegating from %s to dynamic child (type=%s, depth=%d)",
            parent_agent_id, task_type, child_depth,
        )

        return await self.session_manager.spawn_child_in_parent_session(
            parent_agent_id=parent_agent_id,
            child_task=task,
            child_depth=child_depth,
            timeout=timeout,
        )

    async def delegate_to_team(
        self,
        from_agent: str,
        team: dict[str, str],
        task: str,
        timeout: float = 600.0,
    ) -> dict[str, str | None]:
        """Delegate a task to multiple agents in parallel.

        Args:
            from_agent: Parent agent ID
            team: Dict mapping agent_id → task_specific_context
            task: Base task description
            timeout: Max seconds to wait per agent

        Returns:
            Dict mapping agent_id → response (or None if failed)
        """
        import asyncio

        tasks = {
            agent_id: self.session_manager.delegate_task(
                from_agent=from_agent,
                to_agent=agent_id,
                task=f"{task}\n\nContext: {context}",
                spawn_dynamic=False,
                timeout=timeout,
            )
            for agent_id, context in team.items()
        }

        results: dict[str, str | None] = {}
        for agent_id, coro in tasks.items():
            try:
                results[agent_id] = await coro
            except Exception as e:
                logger.error("Delegation to %s failed: %s", agent_id, e)
                results[agent_id] = None

        return results

    async def get_team_status(
        self, agent_ids: list[str]
    ) -> dict[str, dict[str, Any]]:
        """Get status for a list of agents.

        Args:
            agent_ids: List of agent IDs to check

        Returns:
            Dict mapping agent_id → status dict
        """
        statuses: dict[str, dict[str, Any]] = {}
        for agent_id in agent_ids:
            status = await self.session_manager.get_delegation_status(agent_id)
            statuses[agent_id] = status
        return statuses

    async def shutdown_team(self, agent_ids: list[str]) -> None:
        """Gracefully shutdown a list of agents.

        Args:
            agent_ids: List of agent IDs to stop
        """
        for agent_id in agent_ids:
            try:
                await self.session_manager.stop_agent(agent_id)
                logger.info("Stopped agent %s", agent_id)
            except Exception as e:
                logger.error("Failed to stop agent %s: %s", agent_id, e)

    async def _load_project_positions(
        self, project_id: str
    ) -> list[dict[str, Any]]:
        """Load project positions from database.

        Each position dict contains:
        - id: position ID
        - position_key: short identifier
        - profile_id: AgentProfile to use
        - designation: role title
        - reports_to: parent position ID
        - system_prompt_addon: extra context
        """
        try:
            from ecms.persistence.database.rest_session import db_session
            from ecms.persistence.repositories.project_agent_position import (
                ProjectAgentPositionRepository,
            )

            async with db_session() as session:
                repo = ProjectAgentPositionRepository(session)
                positions = await repo.list_by_project(project_id)
                return [
                    {
                        "id": p.id,
                        "position_key": p.position_key,
                        "profile_id": p.designation or p.role,  # Use designation as profile_id fallback
                        "designation": p.designation,
                        "role": p.role,
                        "reports_to": p.reports_to,
                        "system_prompt_addon": p.system_prompt_addon,
                    }
                    for p in positions
                ]
        except Exception as e:
            logger.error("Failed to load project positions: %s", e)
            return []


# ── Module-level singleton ──────────────────────────────────────────────

_hierarchy_manager: AgentHierarchyManager | None = None


def get_hierarchy_manager() -> AgentHierarchyManager:
    """Get the global AgentHierarchyManager singleton."""
    global _hierarchy_manager
    if _hierarchy_manager is None:
        _hierarchy_manager = AgentHierarchyManager()
    return _hierarchy_manager
