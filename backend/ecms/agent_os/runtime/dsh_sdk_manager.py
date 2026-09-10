"""DSH SDK Session Manager — one persistent DSH subprocess per agent.

Manages persistent DSH SDK sessions for AegisOS agents. Each agent gets:
- One long-running `dsh --profile sdk` subprocess
- One durable session ID (memory persists across messages)
- One message queue (processes messages one at a time)
- Heartbeat monitoring (auto-respawn on failure)

Messages can come from Slack, AegisOS direct, or system triggers — all feed
the same agent session for shared memory.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import shutil
import signal
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Awaitable, Callable

import yaml

from ecms.agent_os.runtime.agent_factory import AgentInstance

logger = logging.getLogger("ecms.agent_os.dsh_sdk_manager")


# ── Agent personas by role ──────────────────────────────────────────────

# Roles that can delegate to subagents (parent roles)
PARENT_ROLES: frozenset[str] = frozenset({
    "head-of-engineering",
    "senior-engineer",
})

# Default subagent depth per role
DEFAULT_MAX_DEPTH: dict[str, int] = {
    "head-of-engineering": 3,
    "senior-engineer": 2,
    "junior-engineer": 0,
    "business-analyst": 1,
    "code-reviewer": 0,
    "qa-engineer": 0,
    "devops-engineer": 1,
}

AGENT_PERSONAS: dict[str, str] = {
    "head-of-engineering": (
        "You are the Head of Engineering. Your working directory is {{cwd}}.\n\n"
        "Your responsibilities:\n"
        "- Break down projects into clear, actionable tasks\n"
        "- Delegate tasks to senior engineers with clear requirements\n"
        "- Review completed work and provide feedback\n"
        "- Report progress to stakeholders\n"
        "- Make architectural decisions and set technical direction\n\n"
        "You have access to junior and senior engineers. Delegate complex work "
        "to senior engineers and simpler tasks to junior engineers."
    ),
    "senior-engineer": (
        "You are a Senior Software Engineer. Your working directory is {{cwd}}.\n\n"
        "Your responsibilities:\n"
        "- Design system architecture for features\n"
        "- Write complex, production-quality code\n"
        "- Review code from junior engineers and provide mentorship\n"
        "- Make technical decisions within your domain\n"
        "- Break down complex tasks into implementable steps\n\n"
        "You may delegate simpler implementation tasks to junior engineers."
    ),
    "junior-engineer": (
        "You are a Junior Software Engineer. Your working directory is {{cwd}}.\n\n"
        "Your responsibilities:\n"
        "- Write clean, well-tested code\n"
        "- Fix bugs and implement well-defined features\n"
        "- Write unit tests for your code\n"
        "- Ask senior engineers for guidance when requirements are unclear\n"
        "- Follow the coding standards and patterns established in the codebase\n\n"
        "When you encounter blockers beyond your scope, ask your senior engineer."
    ),
    "business-analyst": (
        "You are a Senior Business Analyst. Your working directory is {{cwd}}.\n\n"
        "Your responsibilities:\n"
        "- Analyze project requirements and identify gaps\n"
        "- Write detailed specifications and user stories\n"
        "- Create acceptance criteria for features\n"
        "- Validate requirements with stakeholders\n"
        "- Translate business needs into technical requirements\n\n"
        "When you complete your analysis, produce a structured specification document."
    ),
    "code-reviewer": (
        "You are a Senior Code Reviewer. Your working directory is {{cwd}}.\n\n"
        "Your responsibilities:\n"
        "- Review code for correctness, security, and maintainability\n"
        "- Check adherence to coding standards and best practices\n"
        "- Identify potential bugs, edge cases, and performance issues\n"
        "- Provide constructive, actionable feedback\n"
        "- Approve code that meets quality standards\n\n"
        "Be thorough but fair. Explain why changes are needed."
    ),
}


# ── Message model ───────────────────────────────────────────────────────

@dataclass
class AgentMessage:
    """A message from any channel, destined for an agent session."""

    source: str                    # "slack" | "aegisos" | "system"
    sender_id: str                 # who sent it
    sender_name: str               # display name
    content: str                   # the actual message text
    channel_id: str = ""           # slack channel or AegisOS endpoint
    metadata: dict[str, Any] = field(default_factory=dict)

    def format_for_agent(self, agent_id: str) -> str:
        """Format message with source context for the agent."""
        source_labels = {
            "slack": f"Message from Slack (from {self.sender_name}):",
            "aegisos": f"Message from AegisOS (from {self.sender_name}):",
            "system": "System-triggered task:",
        }
        source_label = source_labels.get(self.source, "Message:")

        return f"""{source_label}
{self.content}

---
Your agent_id: {agent_id}
Timestamp: {self.metadata.get("timestamp", "now")}"""


# ── SDK Agent Session ───────────────────────────────────────────────────

@dataclass
class PendingRequest:
    """Tracks an in-flight JSON-RPC request waiting for a response."""
    request_id: str
    method: str
    sent_at: float
    future: asyncio.Future = field(default_factory=asyncio.Future)
    events: list[dict[str, Any]] = field(default_factory=list)  # session.event notifications


@dataclass
class SDKAgentSession:
    """One persistent DSH session for one agent."""

    agent_id: str
    instance_id: str
    session_id: str                # DSH session ID (durable memory)
    dsh_home: Path                 # Isolated DSH home per agent
    workspace: Path                # Agent's working directory
    profile: str                   # "sdk" or "sdk-minimal"
    role: str                      # Agent role (persona key)
    model_provider: str            # LLM provider
    model_name: str                # LLM model
    api_key: str                   # API key (for env setup)

    # Runtime state
    message_queue: asyncio.Queue[AgentMessage] = field(default_factory=asyncio.Queue)
    status: str = "idle"           # "idle" | "working" | "dead"
    last_heartbeat: float = 0.0
    process: asyncio.subprocess.Process | None = None
    cordis_patch_path: Path | None = None

    # JSON-RPC request tracking (request_id → PendingRequest)
    pending_requests: dict[str, PendingRequest] = field(default_factory=dict)

    # Run-completion tracking for session/prompt: the prompt response only
    # carries {messageId}; the agent's text arrives later via session.event
    # notifications, and run end is signaled by session.status → idle.
    # _process_message arms these before sending; the status/event handlers
    # resolve via _check_run_done. Idle alone is not enough: tool-heavy runs
    # can report idle mid-run, so completion also requires an assistant
    # message or a turn/end event.
    _awaiting_run: bool = False
    _saw_running: bool = False
    _saw_idle: bool = False
    _saw_assistant: bool = False
    _saw_turn_end: bool = False
    _run_idle: asyncio.Event | None = None

    # Delegation tracking (for multi-level delegation)
    subagent_depth: int = 0         # 0 = top-level, 1 = child, 2 = grandchild, etc.
    max_subagent_depth: int = 3     # Configurable per agent
    parent_agent_id: str | None = None  # If this session is a child, the parent's ID

    # ECMS memory scope from the AgentProfile (read/write/categories)
    memory_scope: dict[str, Any] = field(default_factory=dict)

    # Callbacks
    _response_callbacks: list[Callable[[str, AgentMessage], Awaitable[None]]] = field(
        default_factory=list
    )

    # Last stderr lines from the DSH process (diagnostics on failure)
    _stderr_tail: list[str] = field(default_factory=list)

    def on_response(self, callback: Callable[[str, AgentMessage], Awaitable[None]]) -> None:
        """Register a callback for when agent responds."""
        self._response_callbacks.append(callback)

    def arm_run_completion(self) -> None:
        """Arm run-completion tracking before sending a session/prompt."""
        self._awaiting_run = True
        self._saw_running = False
        self._saw_idle = False
        self._saw_assistant = False
        self._saw_turn_end = False
        if self._run_idle is None:
            self._run_idle = asyncio.Event()
        else:
            self._run_idle.clear()

    def disarm_run_completion(self) -> None:
        """Disarm run-completion tracking after a run settles."""
        self._awaiting_run = False


# ── DSH SDK Session Manager ─────────────────────────────────────────────

class DSHSDKSessionManager:
    """Manages persistent DSH SDK sessions for all agents.

    Each agent gets one persistent `dsh --profile sdk` subprocess that stays
    alive across multiple messages. Memory is maintained via DSH's durable
    session log (JSONL), so the agent remembers prior conversations.

    Messages from Slack, AegisOS, or system triggers all feed into the same
    agent session, so the agent has unified memory regardless of source.
    """

    # Heartbeat config
    HEARTBEAT_INTERVAL = 300       # Check every 5 minutes
    HEARTBEAT_TIMEOUT = 600        # Dead after 10 minutes with no heartbeat

    # SDK server config
    SDK_PORT_BASE = 9500           # Base port for SDK JSON-RPC (agent gets port + index)

    # DSH SDK must be launched from a repo checkout, not the global binary.
    # The global `dsh` (0.1.1-rc.2) doesn't ship dsh-sdk-app and has version mismatches.
    # Override with DSH_REPO in containers (default: this dev checkout).
    # Use: node --import tsx/esm apps/cli/src/bin.ts --profile sdk
    DEFAULT_DSH_REPO = os.environ.get(
        "DSH_REPO", "/home/brajesh_kurkure/Projects/AegisOs/DSH"
    )
    DEFAULT_DSH_LAUNCHER = "node --import tsx/esm apps/cli/src/bin.ts"

    # AegisOS memory tools (DSH plugin): symlinked into each agent home so the
    # loader resolves it without touching the shipped bundles. The tools call
    # back to the ECMS backend over HTTP (AEGISOS_API_URL).
    MEMORY_TOOL_PACKAGE = "packages/experimental/tool-agent-memory"
    MEMORY_TOOL_NAME = "@deepseek-ai/dsh-tool-agent-memory"
    MEMORY_TOOL_NAMES = [
        "memory_search_episodes",
        "memory_search_procedures",
        "memory_learn_procedure",
        "memory_get_preferences",
        "memory_set_preference",
        "memory_search_patterns",
        "memory_publish_pattern",
    ]

    def __init__(
        self,
        dsh_executable: str | Path | None = None,
        base_dsh_home: str | Path = "/tmp/dsh-homes",
        base_workspace: str | Path = "/tmp/agent-workspaces",
        memory_bridge: Any | None = None,
    ) -> None:
        # Default to repo launcher if dsh_executable not specified
        if dsh_executable is None:
            self._dsh_executable = self.DEFAULT_DSH_LAUNCHER
        else:
            self._dsh_executable = str(dsh_executable)
        self._base_dsh_home = Path(base_dsh_home)
        self._base_workspace = Path(base_workspace)
        # Optional ECMS memory bridge (recall before prompt, record after).
        # None keeps the manager on DSH session memory only.
        self.memory_bridge = memory_bridge
        self._sessions: dict[str, SDKAgentSession] = {}
        self._session_tasks: dict[str, asyncio.Task] = {}
        self._monitor_task: asyncio.Task | None = None
        self._running = False

    @property
    def sessions(self) -> dict[str, SDKAgentSession]:
        """Get all active sessions."""
        return dict(self._sessions)

    async def ensure_started(self) -> None:
        """Start the manager if it is not running yet (idempotent)."""
        if not self._running:
            await self.start()

    async def start(self) -> None:
        """Start the session manager and heartbeat monitor."""
        self._running = True
        self._base_dsh_home.mkdir(parents=True, exist_ok=True)
        self._base_workspace.mkdir(parents=True, exist_ok=True)
        self._monitor_task = asyncio.create_task(self._heartbeat_monitor())
        logger.info("DSH SDK Session Manager started")

    async def stop(self) -> None:
        """Stop all sessions and cleanup."""
        self._running = False

        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        # Stop all sessions
        for agent_id in list(self._sessions.keys()):
            await self.stop_agent(agent_id)

        logger.info("DSH SDK Session Manager stopped")

    async def spawn_agent(
        self,
        agent_id: str,
        instance: AgentInstance,
        role: str,
        api_key: str,
        model_provider: str = "deepseek-official",
        model_name: str = "deepseek-v4-flash",
        profile: str = "sdk",
        workspace: str | Path | None = None,
        extra_system_prompt: str | None = None,
        response_callback: Callable[[str, AgentMessage], Awaitable[None]] | None = None,
    ) -> SDKAgentSession:
        """Launch persistent DSH subprocess for an agent.

        Args:
            agent_id: Unique agent identifier
            instance: The AgentInstance from AgentFactory
            role: Agent role (maps to persona)
            api_key: LLM API key
            model_provider: LLM provider name
            model_name: LLM model name
            profile: DSH profile ("sdk" or "sdk-minimal")
            workspace: Working directory (defaults to base_workspace/agent_id)
            extra_system_prompt: Additional system prompt text
            response_callback: Called when agent responds to a message

        Returns:
            SDKAgentSession ready to receive messages
        """
        if agent_id in self._sessions:
            logger.warning("Agent %s already running, stopping first", agent_id)
            await self.stop_agent(agent_id)

        # Create isolated directories
        agent_dsh_home = self._base_dsh_home / agent_id
        agent_workspace = Path(workspace) if workspace else self._base_workspace / agent_id
        agent_dsh_home.mkdir(parents=True, exist_ok=True)
        agent_workspace.mkdir(parents=True, exist_ok=True)

        # Generate session ID. Must be unique per spawn: the SDK server can
        # only create sessions, not reopen persisted ones, so reusing an ID
        # from a previous process lifetime fails with "already exists".
        # Within one process lifetime the durable log gives cross-message memory.
        session_id = f"{agent_id}-session-{uuid.uuid4().hex[:8]}"

        # Generate per-agent cordis.patch.yml
        cordis_patch_path = self._generate_cordis_patch(
            agent_dsh_home=agent_dsh_home,
            role=role,
            extra_system_prompt=extra_system_prompt,
        )

        # Create session object
        session = SDKAgentSession(
            agent_id=agent_id,
            instance_id=instance.instance_id,
            session_id=session_id,
            dsh_home=agent_dsh_home,
            workspace=agent_workspace,
            profile=profile,
            role=role,
            model_provider=model_provider,
            model_name=model_name,
            api_key=api_key,
            cordis_patch_path=cordis_patch_path,
            last_heartbeat=time.time(),
            memory_scope=dict(instance.memory_scope or {}),
        )

        if response_callback:
            session.on_response(response_callback)

        self._sessions[agent_id] = session

        # Declare the LLM route before boot (settings are read at startup),
        # launch, then handshake before accepting messages
        self._write_settings_yaml(session)
        await self._launch_dsh_process(session)
        await self._initialize_session(session)

        # Start the message loop
        self._session_tasks[agent_id] = asyncio.create_task(
            self._message_loop(session)
        )

        logger.info("Spawned agent %s (role=%s, session=%s)", agent_id, role, session_id)
        return session

    async def stop_agent(self, agent_id: str) -> None:
        """Gracefully stop an agent's DSH subprocess."""
        session = self._sessions.get(agent_id)
        if not session:
            return

        session.status = "dead"

        # Cancel message loop
        task = self._session_tasks.pop(agent_id, None)
        if task:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Kill DSH process
        await self._kill_dsh_process(session)

        del self._sessions[agent_id]
        logger.info("Stopped agent %s", agent_id)

    async def ingest_message(self, agent_id: str, message: AgentMessage) -> bool:
        """Accept a message from any channel for an agent.

        Args:
            agent_id: Target agent
            message: The message to deliver

        Returns:
            True if message was queued, False if agent not found
        """
        session = self._sessions.get(agent_id)
        if not session or session.status == "dead":
            logger.warning("Agent %s not running, cannot deliver message", agent_id)
            return False

        await session.message_queue.put(message)
        logger.info(
            "Queued message for agent %s from %s (queue depth: %d)",
            agent_id, message.source, session.message_queue.qsize()
        )
        return True

    async def spawn_agent_from_profile(
        self,
        profile_id: str,
        agent_id: str,
        api_key: str,
        *,
        extra_system_prompt: str | None = None,
        response_callback: Callable[[str, AgentMessage], Awaitable[None]] | None = None,
    ) -> SDKAgentSession:
        """Spawn a persistent agent from an AgentProfile.

        This is the primary way to initialize designated agents (HOE, Senior, Junior).
        The profile provides:
        - System prompt / persona
        - Role and designation
        - Tool scope restrictions
        - Memory/knowledge scope
        - Model configuration

        Args:
            profile_id: The AgentProfile.profile_id to load
            agent_id: Unique agent identifier
            api_key: LLM API key
            extra_system_prompt: Additional context appended to profile's prompt
            response_callback: Called when agent responds

        Returns:
            SDKAgentSession ready to receive messages

        Raises:
            ValueError: If profile not found
        """
        from ecms.agent_os.runtime.agent_factory import AgentFactory

        # Load profile via AgentFactory
        factory = AgentFactory()
        instance = await factory.create_from_profile(profile_id)

        # Extract configuration from profile
        role = instance.role or "general"
        model_provider = instance.model_config.get("provider", "deepseek-official")
        model_name = instance.model_config.get("model_name", "deepseek-v4-flash")

        # Generate cordis.patch.yml from profile
        agent_dsh_home = self._base_dsh_home / agent_id
        cordis_patch_path = self._generate_cordis_patch_from_profile(
            agent_dsh_home=agent_dsh_home,
            instance=instance,
            extra_system_prompt=extra_system_prompt,
        )

        # Create session (fresh session ID per spawn; see spawn_agent)
        session = SDKAgentSession(
            agent_id=agent_id,
            instance_id=instance.instance_id,
            session_id=f"{agent_id}-session-{uuid.uuid4().hex[:8]}",
            dsh_home=agent_dsh_home,
            workspace=self._base_workspace / agent_id,
            profile="sdk",
            role=role,
            model_provider=model_provider,
            model_name=model_name,
            api_key=api_key,
            cordis_patch_path=cordis_patch_path,
            last_heartbeat=time.time(),
            max_subagent_depth=DEFAULT_MAX_DEPTH.get(role, 2),
            memory_scope=dict(instance.memory_scope or {}),
        )

        if response_callback:
            session.on_response(response_callback)

        self._sessions[agent_id] = session

        # Create directories
        agent_dsh_home.mkdir(parents=True, exist_ok=True)
        session.workspace.mkdir(parents=True, exist_ok=True)

        # Declare the LLM route before boot (settings are read at startup),
        # launch, then handshake before accepting messages
        self._write_settings_yaml(session)
        await self._launch_dsh_process(session)
        await self._initialize_session(session)

        # Start the message loop
        self._session_tasks[agent_id] = asyncio.create_task(
            self._message_loop(session)
        )

        logger.info(
            "Spawned profile-based agent %s (profile=%s, role=%s, session=%s)",
            agent_id, profile_id, role, session.session_id,
        )
        return session

    async def spawn_team_from_profiles(
        self,
        specs: list[tuple[str, str]],
        api_key: str,
        *,
        extra_system_prompt: str | None = None,
    ) -> dict[str, SDKAgentSession]:
        """Spawn several profile-based agents concurrently.

        Launches all DSH subprocesses in parallel (each boot is ~1-2s warm)
        instead of sequentially. Returns agent_id → session in spec order.

        Args:
            specs: (profile_id, agent_id) pairs, e.g. HOE + engineers.
            api_key: LLM API key shared by the team.
            extra_system_prompt: Optional context appended to every profile.

        Raises:
            RuntimeError: If any member fails to spawn (already-running
                members are left up; callers should stop the team).
        """
        await self.ensure_started()
        sessions = await asyncio.gather(*[            self.spawn_agent_from_profile(
                profile_id=profile_id,
                agent_id=agent_id,
                api_key=api_key,
                extra_system_prompt=extra_system_prompt,
            )
            for profile_id, agent_id in specs
        ])
        return dict(zip([agent_id for _, agent_id in specs], sessions))

    async def stop_team(self, agent_ids: list[str]) -> None:
        """Stop several agents concurrently (best-effort per member)."""
        await asyncio.gather(*[
            self.stop_agent(agent_id) for agent_id in agent_ids
        ], return_exceptions=True)

    def rotate_session(self, agent_id: str) -> str:
        """Start a fresh DSH session for an agent in the same live process.

        The next prompt creates a new server-side session with a clean event
        log, which recovers from poisoned history (e.g. a malformed tool call
        the model emitted that breaks every later turn's replay). Platform
        memory still injects past episodes, so cross-message knowledge is
        preserved. Returns the new session id.
        """
        session = self._sessions.get(agent_id)
        if not session:
            raise ValueError(f"Agent {agent_id} not running")
        session.session_id = f"{agent_id}-session-{uuid.uuid4().hex[:8]}"
        logger.info("Rotated session for agent %s -> %s", agent_id, session.session_id)
        return session.session_id

    async def spawn_child_in_parent_session(
        self,
        parent_agent_id: str,
        child_task: str,
        child_depth: int = 1,
        timeout: float = 600.0,
    ) -> str:
        """Spawn a child agent within the parent's DSH session (shared memory).

        Uses DSH's native subagent system. The child shares the parent's:
        - DSH_HOME (file access)
        - Session context (memory)
        - Tool scope

        The child gets a task-specific context injection and can itself spawn
        children up to the configured max depth.

        Args:
            parent_agent_id: The parent agent that owns this child
            child_task: Task description for the child
            child_depth: Current delegation depth (1 = direct child)
            timeout: Max seconds to wait for child completion

        Returns:
            Child agent's response text

        Raises:
            ValueError: If parent agent not running
        """
        parent_session = self._sessions.get(parent_agent_id)
        if not parent_session:
            raise ValueError(f"Parent agent {parent_agent_id} not running")

        # Check depth limit
        if child_depth > parent_session.max_subagent_depth:
            raise ValueError(
                f"Child depth {child_depth} exceeds max {parent_session.max_subagent_depth}"
            )

        child_id = f"child-{parent_agent_id}-{uuid.uuid4().hex[:8]}"

        # Build the child context prompt
        child_context = f"""[SUBAGENT CONTEXT - Depth {child_depth}]
You are a subagent spawned by {parent_agent_id} to complete a specific task.

Task: {child_task}

You share the parent's working directory and have access to the same files.
Complete this task and report your findings back to the parent.

If you need to spawn your own subagents, you may do so (max depth: {child_depth + 1}).
"""

        # Send subagent start command via JSON-RPC
        request_id = f"sub_{uuid.uuid4().hex[:12]}"
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "subagent.start",
            "params": {
                "childId": child_id,
                "parentSessionId": parent_session.session_id,
                "task": child_context,
                "depth": child_depth,
                "maxDepth": child_depth + 1,  # Allow further delegation
            },
        }

        # Track the subagent
        pending = PendingRequest(
            request_id=request_id,
            method="subagent.start",
            sent_at=time.time(),
        )
        parent_session.pending_requests[request_id] = pending

        # Send to parent's DSH session
        process = parent_session.process
        if not process or process.returncode is not None:
            raise RuntimeError(f"Parent DSH process is dead")

        request_line = (json.dumps(request) + "\n").encode("utf-8")
        process.stdin.write(request_line)
        await process.stdin.drain()

        logger.info(
            "Spawned child %s in parent %s session (depth=%d)",
            child_id, parent_agent_id, child_depth,
        )

        # Wait for child to complete
        try:
            result = await asyncio.wait_for(pending.future, timeout=timeout)
            response_text = self._extract_response_text(result, pending)
            logger.info(
                "Child %s completed (response length: %d)",
                child_id, len(response_text),
            )
            return response_text
        except asyncio.TimeoutError:
            logger.warning("Child %s timed out after %ds", child_id, timeout)
            return "Child agent timed out"
        finally:
            parent_session.pending_requests.pop(request_id, None)

    async def respawn_agent(self, agent_id: str) -> SDKAgentSession | None:
        """Kill and restart an agent's DSH subprocess, preserving session memory.

        Args:
            agent_id: Agent to respawn

        Returns:
            New SDKAgentSession or None if agent not found
        """
        session = self._sessions.get(agent_id)
        if not session:
            return None

        role = session.role
        instance_id = session.instance_id
        api_key = session.api_key
        model_provider = session.model_provider
        model_name = session.model_name
        profile = session.profile

        logger.warning("Respawning agent %s", agent_id)

        # Stop existing
        await self.stop_agent(agent_id)

        # Create a lightweight AgentInstance for respawn
        from ecms.agent_os.runtime.agent_factory import AgentInstance
        instance = AgentInstance(
            instance_id=instance_id,
            profile_id=role,
            name=agent_id,
            role=role,
            system_prompt="",
            stages=[],
            memory_scope={},
            knowledge_scope={},
            tool_scope={},
            model_config={"provider": model_provider, "model_name": model_name},
            execution_budget={},
        )

        # Respawn (the SDK server cannot reopen a persisted session, so a
        # respawn starts a fresh session; message history stays in the old log)
        return await self.spawn_agent(
            agent_id=agent_id,
            instance=instance,
            role=role,
            api_key=api_key,
            model_provider=model_provider,
            model_name=model_name,
            profile=profile,
        )

    async def delegate_task(
        self,
        from_agent: str,
        to_agent: str,
        task: str,
        timeout: float = 600.0,
    ) -> str | None:
        """Parent agent delegates a task to a child agent and waits for the result.

        This is the core of the agent hierarchy: a parent (HOE or Senior Engineer)
        breaks down a task and delegates it to a child agent. The child processes
        the task in its own session and returns the result.

        Args:
            from_agent: Parent agent ID
            to_agent: Child agent ID
            task: Task description (what the child should do)
            timeout: Max seconds to wait for child's response (default: 10 min)

        Returns:
            Child agent's response text, or None if child not running / timed out

        Example:
            # HOE delegates architecture design to a senior engineer
            result = await manager.delegate_task(
                from_agent="hoe-1",
                to_agent="senior-eng-1",
                task="Design the authentication system for the new project. "
                     "Include JWT flow, refresh tokens, and session management.",
            )
        """
        if to_agent not in self._sessions:
            logger.warning("Target agent %s not running", to_agent)
            return None

        child_session = self._sessions[to_agent]

        # Build a delegation message with full context
        delegation_content = (
            f"Task delegated from {from_agent}:\n\n"
            f"{task}\n\n"
            f"---\n"
            f"Instructions:\n"
            f"1. Complete this task using your expertise\n"
            f"2. If you need to delegate sub-tasks, use the delegate tool\n"
            f"3. Report your findings, decisions, and any code/artifacts produced\n"
            f"4. If requirements are unclear, state your assumptions"
        )

        message = AgentMessage(
            source="system",
            sender_id=from_agent,
            sender_name=f"Agent {from_agent}",
            content=delegation_content,
            channel_id=f"delegation-{from_agent}-{to_agent}",
            metadata={
                "type": "delegation",
                "from_agent": from_agent,
                "to_agent": to_agent,
                "delegated_at": time.time(),
            },
        )

        # Create a future that will be resolved when the child responds
        delegation_id = f"deleg_{uuid.uuid4().hex[:12]}"
        future: asyncio.Future[str] = asyncio.Future()

        # Register a one-shot callback that resolves the future on child's response
        async def _delegation_callback(response: str, original_msg: AgentMessage) -> None:
            if not future.done():
                future.set_result(response)

        # Temporarily wrap the callback to only fire for our delegation
        original_callbacks = list(child_session._response_callbacks)

        async def _filtered_callback(response: str, msg: AgentMessage) -> None:
            # Only resolve if this is a response to our delegation
            if msg.metadata.get("type") == "delegation" and msg.metadata.get("from_agent") == from_agent:
                if not future.done():
                    future.set_result(response)
            # Also call original callbacks
            for cb in original_callbacks:
                try:
                    await cb(response, msg)
                except Exception as e:
                    logger.error("Original callback error during delegation: %s", e)

        child_session._response_callbacks = [_filtered_callback]

        # Queue the delegation message
        await self.ingest_message(to_agent, message)

        logger.info(
            "Agent %s delegated task to %s (delegation_id=%s)",
            from_agent, to_agent, delegation_id,
        )

        try:
            # Wait for the child to complete the task
            result = await asyncio.wait_for(future, timeout=timeout)
            logger.info(
                "Delegation %s completed by agent %s (response length: %d)",
                delegation_id, to_agent, len(result),
            )
            return result
        except asyncio.TimeoutError:
            logger.warning(
                "Delegation %s timed out after %ds (parent=%s, child=%s)",
                delegation_id, timeout, from_agent, to_agent,
            )
            return None
        finally:
            # Restore original callbacks
            child_session._response_callbacks = original_callbacks

    async def review_delegated_work(
        self,
        reviewer_agent: str,
        worker_agent: str,
        work_product: str,
        review_criteria: str | None = None,
        timeout: float = 300.0,
    ) -> str | None:
        """Have one agent review another agent's work product.

        Used by senior engineers to review junior engineer code, or by HOE
        to review senior engineer architecture.

        Args:
            reviewer_agent: Agent ID doing the review
            worker_agent: Agent ID who did the original work
            work_product: The output/code/spec to review
            review_criteria: Specific criteria to check (optional)
            timeout: Max seconds to wait for review

        Returns:
            Review feedback, or None if reviewer not running / timed out
        """
        criteria = review_criteria or (
            "Check for: correctness, completeness, security, maintainability, "
            "and adherence to project standards."
        )

        review_task = (
            f"Review the following work product from {worker_agent}:\n\n"
            f"{work_product}\n\n"
            f"Review criteria:\n{criteria}\n\n"
            f"Provide:\n"
            f"1. Overall assessment (approved / needs changes / rejected)\n"
            f"2. Specific issues found (if any)\n"
            f"3. Suggested improvements"
        )

        return await self.delegate_task(
            from_agent=reviewer_agent,
            to_agent=worker_agent,
            task=review_task,
            timeout=timeout,
        )

    # ── Delegation Helpers ───────────────────────────────────────────────

    async def get_delegation_status(
        self, agent_id: str
    ) -> dict[str, Any]:
        """Get the current delegation status for an agent.

        Shows what tasks are pending, what's being processed, and
        recent delegation history.

        Args:
            agent_id: Agent to check

        Returns:
            Dict with delegation status information
        """
        session = self._sessions.get(agent_id)
        if not session:
            return {"error": "Agent not running"}

        pending_count = session.message_queue.qsize()
        active_requests = len(session.pending_requests)

        return {
            "agent_id": agent_id,
            "status": session.status,
            "pending_messages": pending_count,
            "active_requests": active_requests,
            "last_heartbeat": session.last_heartbeat,
            "session_id": session.session_id,
        }

    async def broadcast_to_team(
        self,
        from_agent: str,
        team: list[str],
        message: str,
        gather_responses: bool = True,
        timeout: float = 600.0,
    ) -> dict[str, str | None]:
        """Broadcast a message to multiple agents (parallel delegation).

        Used when a parent agent needs input from multiple team members
        simultaneously (e.g., HOE asks both senior engineers for estimates).

        Args:
            from_agent: Parent agent broadcasting
            team: List of child agent IDs
            message: Message to send to all
            gather_responses: If True, wait for all responses
            timeout: Max seconds to wait per agent

        Returns:
            Dict mapping agent_id → response (or None if failed)
        """
        if not gather_responses:
            # Fire-and-forget: send to all, don't wait
            for agent_id in team:
                msg = AgentMessage(
                    source="system",
                    sender_id=from_agent,
                    sender_name=f"Agent {from_agent}",
                    content=message,
                    metadata={"type": "broadcast", "from_agent": from_agent},
                )
                await self.ingest_message(agent_id, msg)
            return {agent_id: None for agent_id in team}

        # Parallel delegation: send to all, gather responses
        tasks = [
            self.delegate_task(from_agent, agent_id, message, timeout=timeout)
            for agent_id in team
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        responses: dict[str, str | None] = {}
        for agent_id, result in zip(team, results):
            if isinstance(result, Exception):
                logger.error(
                    "Broadcast to %s failed: %s", agent_id, result
                )
                responses[agent_id] = None
            else:
                responses[agent_id] = result

        return responses

    # ── Internal: cordis.patch.yml Generation ────────────────────────────

    def _link_memory_tool(self, agent_dsh_home: Path) -> None:
        """Symlink the memory tool package into an agent home's node_modules.

        Lets the profile loader resolve `@deepseek-ai/dsh-tool-agent-memory`
        from the DSH workspace (with its pnpm-linked peers) without modifying
        shipped bundles. No-ops when the workspace package is absent.
        """
        source = Path(self.DEFAULT_DSH_REPO) / self.MEMORY_TOOL_PACKAGE
        if not (source / "package.json").exists():
            logger.warning("Memory tool package missing at %s; agents run without memory tools", source)
            return
        target_dir = agent_dsh_home / "node_modules" / "@deepseek-ai"
        target_dir.mkdir(parents=True, exist_ok=True)
        link = target_dir / "dsh-tool-agent-memory"
        try:
            if link.is_symlink() or link.exists():
                link.unlink()
            link.symlink_to(source)
        except OSError as e:
            logger.warning("Could not link memory tools for %s: %s", agent_dsh_home, e)

    def _memory_tool_patch(self) -> dict[str, Any]:
        """Cordis insert entry mounting the memory tools (base URL from env).

        Returned as a separate overlay file (see `_write_tools_patch`): the
        manager passes cordis.patch.yml both as the profile user layer and as
        a --patch overlay, so an insert living in cordis.patch.yml would apply
        twice and fail with a duplicate entry id. Id-targeted rows are
        idempotent and stay in cordis.patch.yml.
        """
        return {
            "insert": [
                {
                    "id": "tool-agent-memory",
                    "name": self.MEMORY_TOOL_NAME,
                    "config": {
                        "baseUrl": os.environ.get("AEGISOS_API_URL", "http://127.0.0.1:8000"),
                    },
                }
            ]
        }

    def _write_tools_patch(self, agent_dsh_home: Path) -> Path:
        """Write the insert-only overlay (tool rows) next to cordis.patch.yml."""
        tools_path = agent_dsh_home / "tools.patch.yml"
        tools_path.parent.mkdir(parents=True, exist_ok=True)
        with open(tools_path, "w") as f:
            yaml.dump([self._memory_tool_patch()], f, default_flow_style=False, sort_keys=False)
        return tools_path

    def _with_memory_tools(self, allowed_tools: list[str]) -> list[str]:
        """Append memory tool names to a tool allow-list (unless wildcarded)."""
        if "*" in allowed_tools or "all" in allowed_tools:
            return allowed_tools
        return [*allowed_tools, *[t for t in self.MEMORY_TOOL_NAMES if t not in allowed_tools]]

    def _generate_cordis_patch_from_profile(
        self,
        agent_dsh_home: Path,
        instance: AgentInstance,
        extra_system_prompt: str | None = None,
    ) -> Path:
        """Generate cordis.patch.yml from a full AgentProfile/Instance.

        This uses the profile's:
        - system prompt (with role prefix)
        - tool_scope for tool restrictions
        - role for subagent enablement (parent roles can delegate)
        """
        persona = instance.system_prompt
        if extra_system_prompt:
            persona = f"{persona}\n\n{extra_system_prompt}"

        patch: list[dict[str, Any]] = [
            {"id": "system-prompt", "config": {"persona": persona}},
            {"id": "approval", "name": "@deepseek-ai/dsh-user-approval", "config": {"policy": "never"}},
            {"id": "sandbox-policy", "name": "@deepseek-ai/dsh-sandbox-policy", "config": {"mode": "danger-full-access"}},
            # The native Anthropic adapter declares the same `anthropic`
            # provider route our llm-pi-ai settings route needs; two
            # declarants race at boot and one always loses. The pi-ai route
            # carries our custom model + base URL, so the native one stays off.
            {"id": "llm-anthropic", "disabled": True},
        ]

        # Enable subagents for parent roles
        if instance.role in PARENT_ROLES:
            patch.append({
                "id": "subagent",
                "name": "@deepseek-ai/dsh-subagent",
                "config": {"maxDepth": DEFAULT_MAX_DEPTH.get(instance.role, 2)},
            })

        # Apply tool restrictions from profile (+ memory tools, unless wildcarded)
        allowed_tools = instance.tool_scope.get("allowed_tools", [])
        if allowed_tools:
            patch.append({
                "id": "tools",
                "name": "@deepseek-ai/dsh-tools",
                "config": {"mode": "native", "allowedTools": self._with_memory_tools(list(allowed_tools))},
            })

        # AegisOS memory tools live in a separate overlay file (inserts must
        # not sit in cordis.patch.yml: it applies twice — user layer plus
        # --patch — and a doubled insert fails as a duplicate entry id).
        patch_path = agent_dsh_home / "cordis.patch.yml"
        patch_path.parent.mkdir(parents=True, exist_ok=True)
        with open(patch_path, "w") as f:
            yaml.dump(patch, f, default_flow_style=False, sort_keys=False)

        self._link_memory_tool(agent_dsh_home)
        self._write_tools_patch(agent_dsh_home)
        return patch_path

    # ── Internal: Process Launch ─────────────────────────────────────────

    def _write_settings_yaml(self, session: SDKAgentSession) -> Path:
        """Write $DSH_HOME/settings.yaml declaring the LLM provider route.

        The sdk profile mounts llm-pi-ai dormant with zero routes; routes come
        from the `llm-pi-ai:` settings section. Without this file, `initialize`
        fails with "no adapter registered" for any non-DeepSeek provider.

        Reads ANTHROPIC_BASE_URL / ANTHROPIC_API_KEY from the environment so a
        local Anthropic-compatible proxy (e.g. Claude Code Proxy) can serve
        custom models like meituan/LongCat-2.0:free.
        """
        base_url = os.environ.get("ANTHROPIC_BASE_URL", "").strip().rstrip("/")
        # pi-ai's anthropic-messages protocol appends /v1/messages to the
        # route baseURL itself, so strip a /v1 suffix from the env value
        # (which follows the Anthropic SDK convention of including /v1).
        if base_url.endswith("/v1"):
            base_url = base_url[: -len("/v1")]
        providers: dict[str, Any] = {
            session.model_provider: {
                "apiKeyEnv": "ANTHROPIC_API_KEY",
                "models": [
                    {
                        "id": session.model_name,
                        "contextWindow": 200000,
                        "maxTokens": 4096,
                    }
                ],
            }
        }
        if base_url:
            providers[session.model_provider]["baseURL"] = base_url

        settings_path = session.dsh_home / "settings.yaml"
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        with open(settings_path, "w") as f:
            yaml.dump({"llm-pi-ai": {"providers": providers}}, f, default_flow_style=False, sort_keys=False)

        logger.info(
            "Wrote settings.yaml for agent %s (provider=%s, model=%s, base_url=%s)",
            session.agent_id, session.model_provider, session.model_name,
            base_url or "(catalog default)",
        )
        return settings_path

    async def _initialize_session(
        self, session: SDKAgentSession, timeout: float = 120.0
    ) -> None:
        """Send the SDK `initialize` handshake and wait for the result.

        Must complete before any session/prompt; the server rejects prompts
        while uninitialized. Raises on failure so spawn fails loud.
        """
        process = session.process
        if not process or process.returncode is not None:
            tail = "\n".join(session._stderr_tail[-10:])
            raise RuntimeError(
                f"DSH process for {session.agent_id} died before initialize "
                f"(returncode={process.returncode if process else None}). "
                f"Stderr tail:\n{tail}"
            )

        request_id = f"init_{uuid.uuid4().hex[:12]}"
        pending = PendingRequest(
            request_id=request_id,
            method="initialize",
            sent_at=time.time(),
        )
        session.pending_requests[request_id] = pending
        try:
            request = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": "initialize",
                "params": {
                    "cwd": str(session.workspace),
                    "provider": session.model_provider,
                    "model": session.model_name,
                },
            }
            if process.stdin is None:
                raise RuntimeError(f"DSH stdin for {session.agent_id} is closed")
            try:
                process.stdin.write((json.dumps(request) + "\n").encode("utf-8"))
                await process.stdin.drain()
            except (BrokenPipeError, ConnectionResetError) as e:
                # Give the stderr reader a moment to collect the boot failure
                await asyncio.sleep(1.0)
                tail = "\n".join(session._stderr_tail[-15:])
                raise RuntimeError(
                    f"DSH process for {session.agent_id} died on boot. "
                    f"Stderr tail:\n{tail}"
                ) from e
            result = await asyncio.wait_for(pending.future, timeout=timeout)
            logger.info(
                "Agent %s initialized: %s", session.agent_id, result,
            )
        except asyncio.TimeoutError:
            tail = "\n".join(session._stderr_tail[-10:])
            logger.error(
                "Initialize timed out for agent %s (process alive: %s). Stderr tail:\n%s",
                session.agent_id,
                process.returncode is None,
                tail,
            )
            raise
        finally:
            session.pending_requests.pop(request_id, None)

    def _generate_cordis_patch(
        self,
        agent_dsh_home: Path,
        role: str,
        extra_system_prompt: str | None = None,
    ) -> Path:
        """Generate per-agent cordis.patch.yml.

        Args:
            agent_dsh_home: Agent's isolated DSH home
            role: Agent role (maps to persona)
            extra_system_prompt: Additional system prompt

        Returns:
            Path to generated patch file
        """
        persona = AGENT_PERSONAS.get(role, AGENT_PERSONAS.get("junior-engineer", ""))

        if extra_system_prompt:
            persona = f"{persona}\n\n{extra_system_prompt}"

        patch = [
            # Agent-specific system prompt
            {
                "id": "system-prompt",
                "config": {"persona": persona},
            },
            # Full autonomy: no human approval
            {
                "id": "approval",
                "name": "@deepseek-ai/dsh-user-approval",
                "config": {"policy": "never"},
            },
            # No sandbox confinement
            {
                "id": "sandbox-policy",
                "name": "@deepseek-ai/dsh-sandbox-policy",
                "config": {"mode": "danger-full-access"},
            },
            # The native Anthropic adapter declares the same `anthropic`
            # provider route our llm-pi-ai settings route needs; two
            # declarants race at boot and one always loses. The pi-ai route
            # carries our custom model + base URL, so the native one stays off.
            {"id": "llm-anthropic", "disabled": True},
        ]

        # Only enable subagents for parent roles (HOE, Senior Engineer)
        if role in ("head-of-engineering", "senior-engineer"):
            patch.append({
                "id": "subagent",
                "name": "@deepseek-ai/dsh-subagent",
                "config": {"maxDepth": 3},
            })

        # AegisOS memory tools live in a separate overlay file (see above).
        patch_path = agent_dsh_home / "cordis.patch.yml"
        with open(patch_path, "w") as f:
            yaml.dump(patch, f, default_flow_style=False, sort_keys=False)

        self._link_memory_tool(agent_dsh_home)
        self._write_tools_patch(agent_dsh_home)
        return patch_path

    async def _launch_dsh_process(self, session: SDKAgentSession) -> None:
        """Launch the DSH SDK subprocess for an agent."""
        env = os.environ.copy()

        # Required environment
        env["DSH_HOME"] = str(session.dsh_home)
        env["HOME"] = str(session.dsh_home)
        env["DEEPSEEK_API_KEY"] = session.api_key
        env["DSH_PERMISSION_MODE"] = "danger-full-access"
        env["DSH_MAX_TOKENS_AS_SUCCESS"] = "true"
        env["DSH_TELEMETRY_MODE"] = "DISABLED"

        # Agent identity available to DSH
        env["AGENT_ID"] = session.agent_id
        env["AGENT_ROLE"] = session.role

        # Build command - detect repo launcher vs global binary
        if "tsx/esm" in self._dsh_executable or "apps/cli" in self._dsh_executable:
            # Repo launcher: split into tokens and run from DSH repo
            launcher_parts = self._dsh_executable.split()
            cmd = [
                *launcher_parts,
                "--profile", session.profile,
                "--patch", str(session.cordis_patch_path),
            ]
            cwd = self.DEFAULT_DSH_REPO
        elif self._dsh_executable == "dsh" or str(self._dsh_executable).endswith("/dsh"):
            # Global dsh binary
            cmd = [
                self._dsh_executable,
                "--profile", session.profile,
                "--patch", str(session.cordis_patch_path),
            ]
            cwd = str(session.workspace)
        else:
            # Custom launcher - assume it's a full command
            launcher_parts = self._dsh_executable.split()
            cmd = [
                *launcher_parts,
                "--profile", session.profile,
                "--patch", str(session.cordis_patch_path),
            ]
            cwd = self.DEFAULT_DSH_REPO

        # Insert-only overlay (memory tool row): applies once, after the user
        # layer, so inserts never double-apply.
        if session.cordis_patch_path is not None:
            tools_patch = Path(session.cordis_patch_path).parent / "tools.patch.yml"
            if tools_patch.exists():
                cmd += ["--patch", str(tools_patch)]

        logger.info("Launching DSH for agent %s: %s", agent_id := session.agent_id, " ".join(cmd))

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
                cwd=cwd,
                start_new_session=os.name == "posix",
            )
            session.process = process
            session.status = "idle"
            session.last_heartbeat = time.time()

            # Start background log readers
            asyncio.create_task(self._read_stdout(session))
            asyncio.create_task(self._read_stderr(session))

        except Exception as e:
            logger.error("Failed to launch DSH for agent %s: %s", session.agent_id, e)
            session.status = "dead"
            raise

    async def _kill_dsh_process(self, session: SDKAgentSession) -> None:
        """Kill the DSH subprocess for an agent."""
        process = session.process
        if not process or process.returncode is not None:
            return

        try:
            # Graceful: SIGTERM first
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGTERM)
            else:
                process.terminate()

            # Wait for graceful exit
            try:
                await asyncio.wait_for(process.wait(), timeout=5.0)
            except asyncio.TimeoutError:
                # Force kill
                if os.name == "posix":
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
                await process.wait()
        except (ProcessLookupError, OSError):
            pass

    def _check_run_done(self, session: SDKAgentSession) -> None:
        """Resolve run completion when the run provably finished.

        Requires the running → idle transition AND run output (an assistant
        message or a turn/end marker). Idle alone is not completion: tool-heavy
        runs can report idle between tool calls, which previously resolved
        early with just the prompt ack ({messageId}) as the "response".
        """
        if not session._awaiting_run:
            return
        if not (session._saw_running and session._saw_idle):
            return
        if not (session._saw_assistant or session._saw_turn_end):
            # Mid-run idle (e.g. between tool calls): wait for the next cycle.
            session._saw_running = False
            session._saw_idle = False
            return
        session._awaiting_run = False
        if session._run_idle is not None:
            session._run_idle.set()

    async def _read_stdout(self, session: SDKAgentSession) -> None:
        """Read DSH stdout (JSON-RPC notifications)."""
        process = session.process
        if not process or not process.stdout:
            return

        try:
            while True:
                line = await process.stdout.readline()
                if not line:
                    break

                line_str = line.decode("utf-8", errors="replace").strip()
                if not line_str:
                    continue

                try:
                    msg = json.loads(line_str)
                    await self._handle_jsonrpc_message(session, msg)
                except json.JSONDecodeError:
                    # Non-JSON line from DSH (diagnostic output)
                    logger.debug("[DSH:%s stdout] %s", session.agent_id, line_str)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning("Error reading stdout for %s: %s", session.agent_id, e)

    async def _read_stderr(self, session: SDKAgentSession) -> None:
        """Read DSH stderr (diagnostics)."""
        process = session.process
        if not process or not process.stderr:
            return

        try:
            while True:
                line = await process.stderr.readline()
                if not line:
                    break

                line_str = line.decode("utf-8", errors="replace").strip()
                if line_str:
                    session._stderr_tail.append(line_str)
                    del session._stderr_tail[:-20]
                    logger.debug("[DSH:%s stderr] %s", session.agent_id, line_str)

        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.warning("Error reading stderr for %s: %s", session.agent_id, e)

    async def _handle_jsonrpc_message(
        self, session: SDKAgentSession, msg: dict[str, Any]
    ) -> None:
        """Handle an incoming JSON-RPC notification/response from DSH.

        Handles three types of messages:
        1. Notifications (no "id", have "method") — async events from DSH
        2. Responses (have "id", no "method") — responses to our requests
        3. Error responses (have "id" and "error") — failed requests
        """
        # ── Response to one of our requests ──
        if "id" in msg and "method" not in msg:
            request_id = msg["id"]
            pending = session.pending_requests.get(request_id)
            if pending:
                if "error" in msg:
                    # Request failed
                    error = msg["error"]
                    logger.warning(
                        "[DSH:%s] Request %s failed: %s",
                        session.agent_id, request_id, error,
                    )
                    if not pending.future.done():
                        pending.future.set_exception(
                            RuntimeError(f"DSH error: {error}")
                        )
                elif "result" in msg:
                    # Request succeeded
                    logger.debug(
                        "[DSH:%s] Request %s completed",
                        session.agent_id, request_id,
                    )
                    if not pending.future.done():
                        pending.future.set_result(msg["result"])
                else:
                    # Unknown response format
                    logger.warning(
                        "[DSH:%s] Response %s has no result/error",
                        session.agent_id, request_id,
                    )
                    if not pending.future.done():
                        pending.future.set_result(msg)
            else:
                logger.debug(
                    "[DSH:%s] Response for unknown request_id=%s",
                    session.agent_id, request_id,
                )
            return

        # ── Notification from DSH ──
        method = msg.get("method")
        params = msg.get("params", {})

        if method == "session.status":
            status = params.get("status")
            session.last_heartbeat = time.time()
            if status == "idle":
                session.status = "idle"
            elif status == "running":
                session.status = "working"
            # Resolve run completion: a prompt's ack only carries {messageId},
            # so _process_message waits for running → idle after its send.
            if session._awaiting_run:
                if status == "running":
                    session._saw_running = True
                elif status == "idle":
                    session._saw_idle = True
                self._check_run_done(session)

        elif method == "session.event":
            # Durable session event — correlate with pending requests
            event = params.get("event", {})
            event_type = event.get("type", "unknown")

            # Store events in pending requests for response assembly
            for pending in session.pending_requests.values():
                pending.events.append(event)

            if session._awaiting_run:
                if event_type == "assistant/message":
                    session._saw_assistant = True
                elif event_type == "turn/end":
                    session._saw_turn_end = True
                self._check_run_done(session)

            logger.debug(
                "[DSH:%s event] %s",
                session.agent_id,
                event_type,
            )

        elif method == "subagent.started":
            logger.info(
                "[DSH:%s] Subagent started: %s -> %s",
                session.agent_id,
                params.get("parentSessionId"),
                params.get("childSessionId"),
            )

        elif method == "subagent.finished":
            logger.info(
                "[DSH:%s] Subagent finished: %s (status=%s)",
                session.agent_id,
                params.get("childSessionId"),
                params.get("status"),
            )

        elif method == "session/prompt.accepted":
            logger.debug(
                "[DSH:%s] Prompt accepted for session %s",
                session.agent_id,
                params.get("sessionId"),
            )

    # ── Internal: Message Loop ───────────────────────────────────────────

    async def _message_loop(self, session: SDKAgentSession) -> None:
        """Process messages one at a time for an agent."""
        while self._running and session.status != "dead":
            try:
                message = await asyncio.wait_for(
                    session.message_queue.get(),
                    timeout=1.0,
                )
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break

            try:
                session.status = "working"
                response = await self._process_message(session, message)

                # ECMS memory write: store the exchange as an episodic UCO
                # (scope-gated; skipped for error fallbacks and when no
                # bridge is attached).
                if (
                    self.memory_bridge is not None
                    and not response.startswith("ERROR:")
                    and response != "Agent did not respond within timeout period"
                ):
                    try:
                        await self.memory_bridge.record_exchange(
                            session.agent_id,
                            message.content,
                            response,
                            session.memory_scope or None,
                        )
                    except Exception as e:
                        logger.warning(
                            "Memory write failed for %s: %s", session.agent_id, e
                        )

                # Notify callbacks
                for callback in session._response_callbacks:
                    try:
                        await callback(response, message)
                    except Exception as e:
                        logger.error("Response callback error: %s", e)

            except Exception as e:
                logger.error(
                    "Error processing message for agent %s: %s",
                    session.agent_id, e,
                )
                # Unblock callback waiters (delegate_task, tests) on failure
                response = f"ERROR: {e}"
                for callback in session._response_callbacks:
                    try:
                        await callback(response, message)
                    except Exception as cb_e:
                        logger.error("Response callback error: %s", cb_e)
                return
            finally:
                if session.status != "dead":
                    session.status = "idle"

    async def _process_message(
        self, session: SDKAgentSession, message: AgentMessage
    ) -> str:
        """Process a single message through DSH.

        Sends the message to the DSH subprocess via JSON-RPC session/prompt
        and waits for the correlated response. Uses request ID tracking to
        match responses to requests.
        """
        prompt = message.format_for_agent(session.agent_id)

        # ECMS memory recall: prepend relevant past knowledge (scope-gated).
        # Empty when no bridge is attached, scope denies reading, or the
        # index has nothing relevant — the prompt is then sent unchanged.
        if self.memory_bridge is not None:
            try:
                context = await self.memory_bridge.recall(
                    message.content,
                    session.memory_scope or None,
                    agent_id=session.agent_id,
                )
            except Exception as e:
                logger.warning("Memory recall failed for %s: %s", session.agent_id, e)
                context = ""
            if context:
                prompt = (
                    "[AegisOS memory — relevant past knowledge]\n"
                    f"{context}\n\n---\n{prompt}"
                )

        process = session.process
        if not process or process.returncode is not None:
            tail = "\n".join(session._stderr_tail[-10:])
            raise RuntimeError(
                f"DSH process for {session.agent_id} is dead "
                f"(returncode={process.returncode if process else None}). "
                f"Stderr tail:\n{tail}"
            )

        # Generate unique request ID for correlation
        request_id = f"req_{uuid.uuid4().hex[:12]}"

        # Create a pending request to track the response
        pending = PendingRequest(
            request_id=request_id,
            method="session/prompt",
            sent_at=time.time(),
        )
        session.pending_requests[request_id] = pending

        # Send the prompt as a JSON-RPC session/prompt request
        request = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": "session/prompt",
            "params": {
                "sessionId": session.session_id,
                "contentBlocks": [{"type": "text", "text": prompt}],
            },
        }

        request_line = (json.dumps(request) + "\n").encode("utf-8")
        session.arm_run_completion()
        process.stdin.write(request_line)
        await process.stdin.drain()

        logger.debug(
            "[DSH:%s] Sent request %s (prompt length: %d)",
            session.agent_id, request_id, len(prompt),
        )

        try:
            # The prompt ack only carries {messageId}; the agent runs async.
            # Wait for the ack (proves the prompt was accepted), then for the
            # running → idle transition (proves the run finished).
            ack = await asyncio.wait_for(pending.future, timeout=120.0)
            logger.debug(
                "[DSH:%s] Prompt %s accepted: %s",
                session.agent_id, request_id, ack,
            )

            if session._run_idle is None:
                session.arm_run_completion()
            await asyncio.wait_for(session._run_idle.wait(), timeout=600.0)

            # Extract the response text from collected session events
            response_text = self._extract_response_text(ack, pending)

            logger.info(
                "[DSH:%s] Got response for %s (length: %d, events: %d)",
                session.agent_id, request_id,
                len(response_text), len(pending.events),
            )

            return response_text

        except asyncio.TimeoutError:
            logger.warning(
                "[DSH:%s] Request %s timed out",
                session.agent_id, request_id,
            )
            return "Agent did not respond within timeout period"

        finally:
            # Clean up pending request
            session.disarm_run_completion()
            session.pending_requests.pop(request_id, None)

    def _extract_response_text(
        self, result: Any, pending: PendingRequest
    ) -> str:
        """Extract the agent's response text from a JSON-RPC result + events.

        The session/prompt ack only carries {messageId}; the text arrives via
        session.event notifications. On the wire an assistant event is
        {seq, type: "assistant/message", data: {message: {content: [...]}}}.
        Falls back to older/flatter shapes, then the raw ack.
        """
        # Strategy 1: prompt ack with inline text (not currently sent, but cheap)
        if isinstance(result, dict):
            if "text" in result:
                return str(result["text"])
            if "contentBlocks" in result:
                texts = [
                    block.get("text", "")
                    for block in result["contentBlocks"]
                    if isinstance(block, dict) and block.get("type") == "text"
                ]
                if texts:
                    return "\n\n".join(texts)

        # Strategy 2: last assistant/message event from session.event notifications
        for event in reversed(pending.events):
            if not isinstance(event, dict):
                continue
            if event.get("type") not in ("assistant/message", "assistant"):
                continue
            text = self._event_text(event)
            if text:
                return text

        # Strategy 3: the run ended without assistant text. Surface the
        # turn failure loudly instead of the ack: returning {messageId} here
        # once caused downstream broadcasts of garbage response IDs.
        reason = self._turn_error(pending)
        if reason:
            return f"ERROR: agent run produced no text ({reason})"
        if result is not None:
            return str(result)

        return "Agent returned no response"

    @staticmethod
    def _turn_error(pending: PendingRequest) -> str:
        """Extract the last turn/end error reason from collected events."""
        for event in reversed(pending.events):
            if not isinstance(event, dict) or event.get("type") != "turn/end":
                continue
            reason = event.get("data", {}).get("reason", {})
            if isinstance(reason, dict) and reason.get("kind") == "error":
                error = reason.get("error", {})
                if isinstance(error, dict):
                    return str(error.get("message", "unknown turn error"))[:200]
                return str(reason)[:200]
        return ""

    @staticmethod
    def _event_text(event: dict[str, Any]) -> str:
        """Extract text from one assistant event in any known shape."""
        candidates: list[Any] = [
            event.get("content"),
            event.get("data", {}).get("message", {}).get("content")
            if isinstance(event.get("data"), dict) else None,
            event.get("data", {}).get("content")
            if isinstance(event.get("data"), dict) else None,
        ]
        for content in candidates:
            if isinstance(content, str) and content:
                return content
            if isinstance(content, list):
                texts = [
                    b.get("text", "")
                    for b in content
                    if isinstance(b, dict) and b.get("type") == "text"
                    and isinstance(b.get("text"), str) and b.get("text")
                ]
                if texts:
                    return "\n\n".join(texts)
        message = event.get("data", {}).get("message") if isinstance(event.get("data"), dict) else None
        if isinstance(message, str) and message:
            return message
        return ""

    # ── Internal: Heartbeat Monitor ──────────────────────────────────────

    async def _heartbeat_monitor(self) -> None:
        """Periodically check agent health and respawn dead agents."""
        while self._running:
            try:
                await asyncio.sleep(self.HEARTBEAT_INTERVAL)
                await self._check_all_agents()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Heartbeat monitor error: %s", e)

    async def _check_all_agents(self) -> None:
        """Check each agent's heartbeat and respawn if dead."""
        now = time.time()

        for agent_id, session in list(self._sessions.items()):
            if session.status == "dead":
                continue

            elapsed = now - session.last_heartbeat

            # Check if process is still alive
            process_alive = (
                session.process is not None
                and session.process.returncode is None
            )

            if not process_alive:
                logger.warning(
                    "Agent %s process died (returncode=%s)",
                    agent_id,
                    session.process.returncode if session.process else None,
                )
                await self.respawn_agent(agent_id)
            elif elapsed > self.HEARTBEAT_TIMEOUT:
                logger.warning(
                    "Agent %s unresponsive for %ds (threshold %ds)",
                    agent_id, elapsed, self.HEARTBEAT_TIMEOUT,
                )
                await self.respawn_agent(agent_id)


# ── Module-level singleton ──────────────────────────────────────────────

_session_manager: DSHSDKSessionManager | None = None


def get_session_manager() -> DSHSDKSessionManager:
    """Get the global DSH SDK Session Manager singleton."""
    global _session_manager
    if _session_manager is None:
        _session_manager = DSHSDKSessionManager()
    return _session_manager


async def shutdown_session_manager() -> None:
    """Shutdown the global session manager."""
    global _session_manager
    if _session_manager:
        await _session_manager.stop()
        _session_manager = None
