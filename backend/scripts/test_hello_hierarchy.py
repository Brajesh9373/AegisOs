"""Test: HOE spawns Frontend and Backend agents, they say hello + designation.

This tests the full hierarchy flow:
1. HOE receives task
2. HOE spawns Frontend Engineer (dynamic child in session)
3. HOE spawns Backend Engineer (dynamic child in session)
4. Each child responds with hello + designation
5. HOE aggregates and reports back
"""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ecms.agent_os.runtime.dsh_sdk_manager import DSHSDKSessionManager, AgentMessage


async def test():
    print("=" * 60)
    print("  HIERARCHY HELLO TEST")
    print("=" * 60)

    manager = DSHSDKSessionManager(
        base_dsh_home="/tmp/aegisos-dsh-homes",
        base_workspace="/tmp/aegisos-workspaces",
    )
    await manager.start()

    # Spawn HOE
    print("\n[1] Spawning HOE from profile...")
    hoe_session = await manager.spawn_agent_from_profile(
        profile_id="head-of-engineering",
        agent_id="hoe-1",
        api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
    )
    print(f"    HOE spawned: {hoe_session.agent_id} (PID: {hoe_session.process.pid})")

    # Spawn Frontend Engineer
    print("\n[2] Spawning Frontend Engineer from profile...")
    fe_session = await manager.spawn_agent_from_profile(
        profile_id="senior-frontend-engineer",
        agent_id="frontend-1",
        api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
    )
    print(f"    Frontend spawned: {fe_session.agent_id} (PID: {fe_session.process.pid})")

    # Spawn Backend Engineer
    print("\n[3] Spawning Backend Engineer from profile...")
    be_session = await manager.spawn_agent_from_profile(
        profile_id="senior-backend-engineer",
        agent_id="backend-1",
        api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
    )
    print(f"    Backend spawned: {be_session.agent_id} (PID: {be_session.process.pid})")

    # Test 1: Send hello task to Frontend Engineer
    print("\n[4] Sending 'say hello + designation' to Frontend Engineer...")
    fe_msg = AgentMessage(
        source="test",
        sender_id="test",
        sender_name="Test",
        content="Please say hello and state your designation/role in one sentence.",
        channel_id="test",
    )
    await manager.ingest_message("frontend-1", fe_msg)

    # Wait for Frontend response
    print("    Waiting for Frontend response...")
    fe_response = await wait_for_response(manager, "frontend-1", timeout=240)
    print(f"    Frontend says: {fe_response}")

    # Test 2: Send hello task to Backend Engineer
    print("\n[5] Sending 'say hello + designation' to Backend Engineer...")
    be_msg = AgentMessage(
        source="test",
        sender_id="test",
        sender_name="Test",
        content="Please say hello and state your designation/role in one sentence.",
        channel_id="test",
    )
    await manager.ingest_message("backend-1", be_msg)

    # Wait for Backend response
    print("    Waiting for Backend response...")
    be_response = await wait_for_response(manager, "backend-1", timeout=240)
    print(f"    Backend says: {be_response}")

    # Test 3: Send task to HOE to coordinate
    print("\n[6] Sending coordination task to HOE...")
    hoe_msg = AgentMessage(
        source="test",
        sender_id="test",
        sender_name="Test",
        content=(
            "Say 'Hello Done from all' to confirm you have coordinated with your team. "
            "Mention that Frontend Engineer and Backend Engineer are ready."
        ),
        channel_id="test",
    )
    await manager.ingest_message("hoe-1", hoe_msg)

    # Wait for HOE response
    print("    Waiting for HOE response...")
    hoe_response = await wait_for_response(manager, "hoe-1", timeout=240)
    print(f"    HOE says: {hoe_response}")

    # Cleanup
    print("\n[7] Cleaning up...")
    await manager.stop()
    print("    Manager stopped (all agents shut down)")

    print("\n" + "=" * 60)
    print("  TEST COMPLETE")
    print("=" * 60)


async def wait_for_response(manager, agent_id: str, timeout: int = 300) -> str:
    """Wait for the agent's next response via its _response_callbacks."""
    session = manager.sessions.get(agent_id)
    if not session:
        return "ERROR: Session not found"

    loop = asyncio.get_running_loop()
    future: asyncio.Future[str] = loop.create_future()

    async def _capture(response: str, message: AgentMessage) -> None:
        if not future.done():
            future.set_result(response)

    session.on_response(_capture)
    try:
        return await asyncio.wait_for(future, timeout=timeout)
    except asyncio.TimeoutError:
        return f"(timeout after {timeout}s - status: {session.status})"
    finally:
        try:
            session._response_callbacks.remove(_capture)
        except ValueError:
            pass


if __name__ == "__main__":
    asyncio.run(test())
