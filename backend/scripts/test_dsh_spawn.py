"""Test DSH process spawning with real API credentials."""

import asyncio
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ecms.agent_os.runtime.dsh_sdk_manager import DSHSDKSessionManager, AgentMessage


async def test():
    manager = DSHSDKSessionManager(
        base_dsh_home="/tmp/aegisos-dsh-homes",
        base_workspace="/tmp/aegisos-workspaces",
    )

    # Spawn HOE
    session = await manager.spawn_agent_from_profile(
        profile_id="head-of-engineering",
        agent_id="hoe-test",
        api_key=os.environ.get("ANTHROPIC_API_KEY", "test"),
    )

    print(f"Session spawned: {session.agent_id}")
    print(f"Process PID: {session.process.pid if session.process else None}")
    print(f"Process alive: {session.process.returncode is None if session.process else False}")
    print(f"cordis.patch: {session.cordis_patch_path}")

    # Send a simple test message
    msg = AgentMessage(
        source="test",
        sender_id="test",
        sender_name="Test",
        content="Say hello and confirm you are the Head of Engineering.",
        channel_id="test",
    )

    await manager.ingest_message("hoe-test", msg)
    print("Message queued, waiting for processing...")

    # Wait for processing (DSH SDK processes one message then stays alive)
    # The process will exit after completing the task
    for i in range(30):
        await asyncio.sleep(1)
        if session.process and session.process.returncode is not None:
            print(f"Process completed after {i+1}s with returncode: {session.process.returncode}")
            break
    else:
        print("Process still running after 30s")

    print(f"\nStatus: {session.status}")
    print(f"Last heartbeat: {session.last_heartbeat}")
    print(f"Pending requests: {len(session.pending_requests)}")

    # Check if process is still alive
    if session.process:
        print(f"Process returncode: {session.process.returncode}")

    # Cleanup (process may already be done)
    if session.process and session.process.returncode is None:
        await manager.stop_agent("hoe-test")
    print("\nStopped")


if __name__ == "__main__":
    asyncio.run(test())
