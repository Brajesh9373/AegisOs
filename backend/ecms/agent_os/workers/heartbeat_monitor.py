"""Heartbeat Monitor — watches agent health and respawns dead agents.

Monitors all active DSH agent sessions. If an agent's DSH subprocess dies
or becomes unresponsive (no heartbeat within timeout), it automatically
respawns the agent, preserving session memory.

Heartbeat signals come from DSH's session.status notifications:
- "running" = agent is processing a message
- "idle" = agent is waiting for work

If no status is received within HEARTBEAT_TIMEOUT seconds, the agent is
considered dead and is respawned.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from ecms.agent_os.runtime.dsh_sdk_manager import (
    DSHSDKSessionManager,
    get_session_manager,
)

logger = logging.getLogger("ecms.agent_os.heartbeat_monitor")


class HeartbeatMonitor:
    """Monitors agent health and triggers respawns when needed.

    The monitor runs as a background task that periodically checks each
    agent's heartbeat. An agent is considered dead if:

    1. The DSH subprocess has exited (returncode is not None)
    2. No session.status notification received within HEARTBEAT_TIMEOUT seconds

    On death detection, the agent is respawned with the same session_id,
    preserving its durable memory.
    """

    # Heartbeat configuration
    HEARTBEAT_INTERVAL = 300   # How often to check (5 minutes)
    HEARTBEAT_TIMEOUT = 600    # Dead threshold (10 minutes with no heartbeat)

    def __init__(
        self,
        session_manager: DSHSDKSessionManager | None = None,
        *,
        check_interval: float | None = None,
        timeout: float | None = None,
        on_agent_dead: Any | None = None,  # Callback when agent dies
        on_agent_respawned: Any | None = None,  # Callback after respawn
    ) -> None:
        """Initialize the heartbeat monitor.

        Args:
            session_manager: DSHSDKSessionManager instance (default: global)
            check_interval: Seconds between health checks (default: 300)
            timeout: Seconds without heartbeat before dead (default: 600)
            on_agent_dead: Callback(agent_id, reason) when agent detected dead
            on_agent_respawned: Callback(agent_id, new_session) after respawn
        """
        self.session_manager = session_manager or get_session_manager()
        self.check_interval = check_interval or self.HEARTBEAT_INTERVAL
        self.timeout = timeout or self.HEARTBEAT_TIMEOUT
        self.on_agent_dead = on_agent_dead
        self.on_agent_respawned = on_agent_respawned

        self._running = False
        self._monitor_task: asyncio.Task | None = None

        # Track death/respawn statistics
        self._stats: dict[str, dict[str, Any]] = {}

    @property
    def stats(self) -> dict[str, dict[str, Any]]:
        """Get monitor statistics."""
        return dict(self._stats)

    async def start(self) -> None:
        """Start the heartbeat monitor background task."""
        if self._running:
            logger.warning("Heartbeat monitor already running")
            return

        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(
            "Heartbeat monitor started (interval=%ds, timeout=%ds)",
            self.check_interval, self.timeout,
        )

    async def stop(self) -> None:
        """Stop the heartbeat monitor."""
        self._running = False

        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
            self._monitor_task = None

        logger.info("Heartbeat monitor stopped")

    async def check_now(self) -> dict[str, str]:
        """Immediately check all agents and return status.

        Returns:
            Dict mapping agent_id -> status ("alive", "dead", "unresponsive")
        """
        results: dict[str, str] = {}
        now = time.time()

        for agent_id, session in self.session_manager.sessions.items():
            if session.status == "dead":
                results[agent_id] = "dead"
                continue

            # Check if process is alive
            process_alive = (
                session.process is not None
                and session.process.returncode is None
            )

            if not process_alive:
                results[agent_id] = "dead"
                continue

            # Check heartbeat freshness
            elapsed = now - session.last_heartbeat
            if elapsed > self.timeout:
                results[agent_id] = "unresponsive"
            else:
                results[agent_id] = "alive"

        return results

    async def _monitor_loop(self) -> None:
        """Main monitor loop — periodically checks agent health."""
        while self._running:
            try:
                await asyncio.sleep(self.check_interval)
                await self._check_all_agents()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error("Heartbeat monitor error: %s", e, exc_info=True)

    async def _check_all_agents(self) -> None:
        """Check each agent and respawn dead ones."""
        now = time.time()

        for agent_id, session in list(self.session_manager.sessions.items()):
            if session.status == "dead":
                continue

            # Check if process is still alive
            process_alive = (
                session.process is not None
                and session.process.returncode is None
            )

            if not process_alive:
                returncode = session.process.returncode if session.process else None
                logger.warning(
                    "Agent %s process died (returncode=%s)",
                    agent_id, returncode,
                )
                await self._handle_dead_agent(agent_id, f"process_exit_{returncode}")
                continue

            # Check heartbeat freshness
            elapsed = now - session.last_heartbeat
            if elapsed > self.timeout:
                logger.warning(
                    "Agent %s unresponsive for %ds (threshold %ds)",
                    agent_id, elapsed, self.timeout,
                )
                await self._handle_dead_agent(agent_id, f"timeout_{elapsed:.0f}s")

    async def _handle_dead_agent(self, agent_id: str, reason: str) -> None:
        """Handle a dead agent — log, notify, and respawn."""
        # Update stats
        if agent_id not in self._stats:
            self._stats[agent_id] = {"deaths": 0, "respawns": 0}
        self._stats[agent_id]["deaths"] += 1
        self._stats[agent_id]["last_death_reason"] = reason
        self._stats[agent_id]["last_death_time"] = time.time()

        # Notify callback
        if self.on_agent_dead:
            try:
                if asyncio.iscoroutinefunction(self.on_agent_dead):
                    await self.on_agent_dead(agent_id, reason)
                else:
                    self.on_agent_dead(agent_id, reason)
            except Exception as e:
                logger.error("on_agent_dead callback error: %s", e)

        # Respawn
        logger.info("Respawning agent %s (reason: %s)", agent_id, reason)
        new_session = await self.session_manager.respawn_agent(agent_id)

        if new_session:
            self._stats[agent_id]["respawns"] += 1

            if self.on_agent_respawned:
                try:
                    if asyncio.iscoroutinefunction(self.on_agent_respawned):
                        await self.on_agent_respawned(agent_id, new_session)
                    else:
                        self.on_agent_respawned(agent_id, new_session)
                except Exception as e:
                    logger.error("on_agent_respawned callback error: %s", e)


# ── Module-level singleton ──────────────────────────────────────────────

_heartbeat_monitor: HeartbeatMonitor | None = None


def get_heartbeat_monitor(
    session_manager: DSHSDKSessionManager | None = None,
) -> HeartbeatMonitor:
    """Get the global HeartbeatMonitor singleton."""
    global _heartbeat_monitor
    if _heartbeat_monitor is None:
        _heartbeat_monitor = HeartbeatMonitor(session_manager)
    return _heartbeat_monitor


async def shutdown_heartbeat_monitor() -> None:
    """Shutdown the global heartbeat monitor."""
    global _heartbeat_monitor
    if _heartbeat_monitor:
        await _heartbeat_monitor.stop()
        _heartbeat_monitor = None
