"""Message Router — channel-agnostic message ingestion for agent sessions.

Routes messages from Slack, AegisOS REST API, and system triggers into the
same agent session. This ensures that an agent has unified memory regardless
of where messages originate.

Supported channels:
- Slack: @agent mentions, DMs
- AegisOS: Direct chat, New Project flow, task assignments
- System: Scheduled tasks, delegation results, internal events
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

from ecms.agent_os.runtime.dsh_sdk_manager import (
    AgentMessage,
    DSHSDKSessionManager,
    get_session_manager,
)

logger = logging.getLogger("ecms.agent_os.message_router")

# Pattern to extract @agent mentions from Slack messages
_AGENT_MENTION_RE = re.compile(r"@([a-z][a-z0-9-]*)")

# Map Slack user IDs to agent IDs (configured at runtime)
_SLACK_AGENT_MAP: dict[str, str] = {}


# ── Channel Handlers ────────────────────────────────────────────────────

class SlackChannelHandler:
    """Handles messages from Slack."""

    def __init__(self, router: "MessageRouter") -> None:
        self.router = router

    async def handle_message(self, event: dict[str, Any]) -> bool:
        """Process a Slack message event.

        Args:
            event: Slack event payload

        Returns:
            True if message was routed to an agent
        """
        text = event.get("text", "")
        if not text:
            return False

        # Extract agent mention
        agent_id = self._extract_agent_id(text)
        if not agent_id:
            return False

        # Clean message (remove @mention)
        clean_text = self._clean_mention(text)

        message = AgentMessage(
            source="slack",
            sender_id=event.get("user", "unknown"),
            sender_name=self._get_user_name(event),
            content=clean_text,
            channel_id=event.get("channel", ""),
            metadata={
                "ts": event.get("ts", ""),
                "thread_ts": event.get("thread_ts"),
                "channel_type": event.get("channel_type", ""),
            },
        )

        return await self.router.route_message(agent_id, message)

    async def handle_app_mention(self, event: dict[str, Any]) -> bool:
        """Process an app_mention event (bot was @mentioned)."""
        text = event.get("text", "")
        if not text:
            return False

        # Extract which agent was mentioned
        agent_id = self._extract_agent_id(text)
        if not agent_id:
            return False

        clean_text = self._clean_mention(text)

        message = AgentMessage(
            source="slack",
            sender_id=event.get("user", "unknown"),
            sender_name=self._get_user_name(event),
            content=clean_text,
            channel_id=event.get("channel", ""),
            metadata={
                "ts": event.get("ts", ""),
                "event_type": "app_mention",
            },
        )

        return await self.router.route_message(agent_id, message)

    def _extract_agent_id(self, text: str) -> str | None:
        """Extract agent ID from @mention in message text."""
        match = _AGENT_MENTION_RE.search(text)
        if match:
            return match.group(1)
        return None

    def _clean_mention(self, text: str) -> str:
        """Remove @mention from message text."""
        return _AGENT_MENTION_RE.sub("", text).strip()

    def _get_user_name(self, event: dict[str, Any]) -> str:
        """Get display name for Slack user."""
        # In production, this would look up the user profile
        return event.get("user_name", event.get("user", "Unknown"))


class AegisOSChannelHandler:
    """Handles messages from AegisOS direct channels."""

    def __init__(self, router: "MessageRouter") -> None:
        self.router = router

    async def handle_direct_message(
        self,
        agent_id: str,
        content: str,
        sender_id: str,
        sender_name: str,
        metadata: dict[str, Any] | None = None,
    ) -> bool:
        """Process a direct message from AegisOS UI.

        Args:
            agent_id: Target agent ID
            content: Message content
            sender_id: User ID who sent the message
            sender_name: User display name
            metadata: Additional context

        Returns:
            True if message was routed
        """
        message = AgentMessage(
            source="aegisos",
            sender_id=sender_id,
            sender_name=sender_name,
            content=content,
            channel_id=metadata.get("endpoint", "direct") if metadata else "direct",
            metadata=metadata or {},
        )

        return await self.router.route_message(agent_id, message)

    async def handle_new_project(
        self,
        project: dict[str, Any],
        user: dict[str, Any],
        target_agent: str = "business-analyst",
    ) -> bool:
        """Process a new project creation — routes to BA agent.

        Args:
            project: Project data (id, title, requirements, etc.)
            user: User who created the project
            target_agent: Agent to notify (default: business-analyst)

        Returns:
            True if message was routed
        """
        content = (
            f"New project created: {project.get('title', 'Untitled')}\n\n"
            f"Requirements:\n{project.get('requirements', 'No requirements provided')}\n\n"
            f"Please analyze these requirements and create a detailed specification."
        )

        message = AgentMessage(
            source="aegisos",
            sender_id=user.get("id", "system"),
            sender_name=user.get("name", "AegisOS"),
            content=content,
            channel_id=f"project-{project.get('id', 'unknown')}",
            metadata={
                "type": "new_project",
                "project_id": project.get("id"),
                "project_title": project.get("title"),
            },
        )

        return await self.router.route_message(target_agent, message)

    async def handle_task_assignment(
        self,
        agent_id: str,
        task: dict[str, Any],
        assigned_by: dict[str, Any],
    ) -> bool:
        """Process a task assignment — routes to the assigned agent.

        Args:
            agent_id: Target agent ID
            task: Task data (id, title, description, etc.)
            assigned_by: User/system who assigned the task

        Returns:
            True if message was routed
        """
        content = (
            f"New task assigned: {task.get('title', 'Untitled')}\n\n"
            f"Description:\n{task.get('description', 'No description')}\n\n"
            f"Priority: {task.get('priority', 'normal')}\n"
            f"Due: {task.get('due_date', 'No deadline')}"
        )

        message = AgentMessage(
            source="aegisos",
            sender_id=assigned_by.get("id", "system"),
            sender_name=assigned_by.get("name", "System"),
            content=content,
            channel_id=f"task-{task.get('id', 'unknown')}",
            metadata={
                "type": "task_assignment",
                "task_id": task.get("id"),
                "project_id": task.get("project_id"),
            },
        )

        return await self.router.route_message(agent_id, message)


class SystemChannelHandler:
    """Handles system-triggered messages (delegation, scheduled tasks, etc.)."""

    def __init__(self, router: "MessageRouter") -> None:
        self.router = router

    async def handle_delegation(
        self,
        from_agent: str,
        to_agent: str,
        task: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Process a task delegation from one agent to another.

        Args:
            from_agent: Parent agent ID
            to_agent: Child agent ID
            task: Task description
            context: Additional delegation context

        Returns:
            True if message was routed
        """
        content = (
            f"Task delegated from {from_agent}:\n\n"
            f"{task}\n\n"
            f"Complete this task and report your findings."
        )

        message = AgentMessage(
            source="system",
            sender_id=from_agent,
            sender_name=f"Agent {from_agent}",
            content=content,
            channel_id=f"delegation-{from_agent}-{to_agent}",
            metadata={
                "type": "delegation",
                "from_agent": from_agent,
                "to_agent": to_agent,
                **(context or {}),
            },
        )

        return await self.router.route_message(to_agent, message)

    async def handle_scheduled_task(
        self,
        agent_id: str,
        task: dict[str, Any],
    ) -> bool:
        """Process a scheduled/recurring task.

        Args:
            agent_id: Target agent ID
            task: Scheduled task data

        Returns:
            True if message was routed
        """
        message = AgentMessage(
            source="system",
            sender_id="scheduler",
            sender_name="Task Scheduler",
            content=task.get("description", "Scheduled task"),
            channel_id=f"scheduled-{task.get('id', 'unknown')}",
            metadata={
                "type": "scheduled_task",
                "task_id": task.get("id"),
                "schedule": task.get("schedule"),
            },
        )

        return await self.router.route_message(agent_id, message)


# ── Message Router ──────────────────────────────────────────────────────

class MessageRouter:
    """Routes messages from any channel to the appropriate agent session.

    This is the central hub that connects Slack, AegisOS, and system triggers
    to the DSH SDK Session Manager. All messages flow through here.
    """

    def __init__(
        self,
        session_manager: DSHSDKSessionManager | None = None,
    ) -> None:
        self.session_manager = session_manager or get_session_manager()

        # Channel handlers
        self.slack = SlackChannelHandler(self)
        self.aegisos = AegisOSChannelHandler(self)
        self.system = SystemChannelHandler(self)

        # Response callbacks (channel-specific response routing)
        self._response_callbacks: dict[
            str, Callable[[str, AgentMessage, str], Awaitable[None]]
        ] = {}

    def register_response_callback(
        self,
        channel: str,
        callback: Callable[[str, AgentMessage, str], Awaitable[None]],
    ) -> None:
        """Register a callback for routing responses back to a channel.

        Args:
            channel: Channel identifier ("slack", "aegisos", "system")
            callback: Called with (agent_id, original_message, response)
        """
        self._response_callbacks[channel] = callback

    async def route_message(self, agent_id: str, message: AgentMessage) -> bool:
        """Route a message to an agent session.

        Args:
            agent_id: Target agent ID
            message: The message to deliver

        Returns:
            True if message was queued for delivery
        """
        # Register response routing callback for this message's source
        self.session_manager.sessions.get(agent_id) if agent_id in self.session_manager.sessions else None

        success = await self.session_manager.ingest_message(agent_id, message)

        if success:
            logger.info(
                "Routed %s message to agent %s (queue depth: %d)",
                message.source,
                agent_id,
                self.session_manager.sessions[agent_id].message_queue.qsize(),
            )
        else:
            logger.warning(
                "Failed to route %s message to agent %s (agent not running)",
                message.source,
                agent_id,
            )

        return success

    async def send_response(
        self,
        agent_id: str,
        original_message: AgentMessage,
        response: str,
    ) -> None:
        """Send an agent's response back to the originating channel.

        Args:
            agent_id: Agent that generated the response
            original_message: The message that triggered the response
            response: The agent's response text
        """
        callback = self._response_callbacks.get(original_message.source)
        if callback:
            try:
                await callback(agent_id, original_message, response)
            except Exception as e:
                logger.error(
                    "Error routing response for agent %s to %s: %s",
                    agent_id, original_message.source, e,
                )
        else:
            logger.warning(
                "No response callback registered for channel %s",
                original_message.source,
            )


# ── Module-level singleton ──────────────────────────────────────────────

_message_router: MessageRouter | None = None


def get_router(
    session_manager: DSHSDKSessionManager | None = None,
) -> MessageRouter:
    """Get the global MessageRouter singleton."""
    global _message_router
    if _message_router is None:
        _message_router = MessageRouter(session_manager)
    return _message_router
