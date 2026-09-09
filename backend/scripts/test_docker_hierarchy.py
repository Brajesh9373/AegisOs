"""Test agent hierarchy inside Docker backend container.

Run from host: uv run python scripts/test_docker_hierarchy.py
Script copies itself into the container and runs the test.
"""

import asyncio
import os
import sys
import json
from pathlib import Path

# Test script that runs inside the container
TEST_SCRIPT = '''
import asyncio
import os
import sys
import json
from pathlib import Path

sys.path.insert(0, "/app")

# Set env for DSH
os.environ["DSH_HOME"] = "/home/ecms/.dsh"
os.environ["DSH_REPO"] = "/app/DSH"

from ecms.agent_os.runtime.dsh_sdk_manager import DSHSDKSessionManager, AgentMessage

async def wait_for_response(manager, agent_id: str, timeout: int = 120) -> dict:
    """Wait for agent process to complete and capture output."""
    session = manager.sessions.get(agent_id)
    if not session:
        return {"error": "Session not found"}

    # Wait for process to complete
    for i in range(timeout):
        await asyncio.sleep(1)
        if session.process and session.process.returncode is not None:
            return {
                "status": "completed",
                "returncode": session.process.returncode,
                "seconds": i + 1,
            }

    return {"status": "timeout", "seconds": timeout}

async def test():
    print("=" * 60)
    print("  DOCKER HIERARCHY HELLO TEST")
    print("=" * 60)

    manager = DSHSDKSessionManager(
        base_dsh_home="/tmp/aegisos-dsh-homes",
        base_workspace="/tmp/aegisos-workspaces",
    )

    results = {}

    # Spawn HOE
    print("\\n[1] Spawning HOE from profile...")
    hoe_session = await manager.spawn_agent_from_profile(
        profile_id="head-of-engineering",
        agent_id="hoe-1",
        api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
    )
    print(f"    HOE spawned: {hoe_session.agent_id} (PID: {hoe_session.process.pid})")

    # Spawn Frontend Engineer
    print("\\n[2] Spawning Frontend Engineer from profile...")
    fe_session = await manager.spawn_agent_from_profile(
        profile_id="senior-frontend-engineer",
        agent_id="frontend-1",
        api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
    )
    print(f"    Frontend spawned: {fe_session.agent_id} (PID: {fe_session.process.pid})")

    # Spawn Backend Engineer
    print("\\n[3] Spawning Backend Engineer from profile...")
    be_session = await manager.spawn_agent_from_profile(
        profile_id="senior-backend-engineer",
        agent_id="backend-1",
        api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
    )
    print(f"    Backend spawned: {be_session.agent_id} (PID: {be_session.process.pid})")

    # Test 1: Frontend hello
    print("\\n[4] Sending 'say hello + designation' to Frontend Engineer...")
    fe_msg = AgentMessage(
        source="test",
        sender_id="test",
        sender_name="Test",
        content="Please say hello and state your designation/role in one sentence.",
        channel_id="test",
    )
    await manager.ingest_message("frontend-1", fe_msg)
    fe_result = await wait_for_response(manager, "frontend-1")
    print(f"    Frontend result: {json.dumps(fe_result)}")
    results["frontend"] = fe_result

    # Test 2: Backend hello
    print("\\n[5] Sending 'say hello + designation' to Backend Engineer...")
    be_msg = AgentMessage(
        source="test",
        sender_id="test",
        sender_name="Test",
        content="Please say hello and state your designation/role in one sentence.",
        channel_id="test",
    )
    await manager.ingest_message("backend-1", be_msg)
    be_result = await wait_for_response(manager, "backend-1")
    print(f"    Backend result: {json.dumps(be_result)}")
    results["backend"] = be_result

    # Test 3: HOE coordination
    print("\\n[6] Sending coordination task to HOE...")
    hoe_msg = AgentMessage(
        source="test",
        sender_id="test",
        sender_name="Test",
        content="Say 'Hello Done from all' to confirm you have coordinated with your team.",
        channel_id="test",
    )
    await manager.ingest_message("hoe-1", hoe_msg)
    hoe_result = await wait_for_response(manager, "hoe-1")
    print(f"    HOE result: {json.dumps(hoe_result)}")
    results["hoe"] = hoe_result

    # Cleanup
    print("\\n[7] Cleaning up...")
    for agent_id in ["hoe-1", "frontend-1", "backend-1"]:
        try:
            await manager.stop_agent(agent_id)
            print(f"    Stopped {agent_id}")
        except Exception as e:
            print(f"    Error stopping {agent_id}: {e}")

    # Summary
    print("\\n" + "=" * 60)
    print("  RESULTS SUMMARY")
    print("=" * 60)
    for agent, result in results.items():
        status = result.get("status", "unknown")
        rc = result.get("returncode", "?")
        secs = result.get("seconds", "?")
        print(f"  {agent}: {status} (code={rc}, time={secs}s)")

    print("\\n" + "=" * 60)
    print("  TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(test())
'''

if __name__ == "__main__":
    # Write test script to container
    import subprocess

    print("Copying test script to container...")
    subprocess.run(
        ["docker", "exec", "ecms-backend", "bash", "-c", f"cat > /tmp/test_hierarchy.py << 'HEREDOC'\n{TEST_SCRIPT}\nHEREDOC"],
        check=True,
    )

    print("Running test in container...")
    result = subprocess.run(
        ["docker", "exec", "-e", f"ANTHROPIC_API_KEY={os.environ.get('ANTHROPIC_API_KEY', 'user_59UthjyP4Vt2CxcqErU3gGvGxgiQiao2m8xVCDYYfomxaevK46w45khorDQjT29tHwpz9MCet3Qzx5cL34XhF74R')}",
         "ecms-backend", "bash", "-c", "cd /app && python /tmp/test_hierarchy.py"],
        capture_output=True,
        text=True,
        timeout=300,
    )

    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr[:2000])

    sys.exit(result.returncode)
