"""Run the full agent hierarchy demo: HOE delegates web site creation.

This script:
1. Loads AgentProfiles from DB
2. Spawns HOE, Frontend, Backend agents from profiles
3. Assigns the web site creation task to HOE
4. HOE delegates to Frontend and Backend engineers
5. Results aggregate back to HOE

Environment variables required:
- ANTHROPIC_BASE_URL: http://127.0.0.1:3457/v1
- ANTHROPIC_API_KEY: your API key
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


async def main():
    print("=" * 60)
    print("  AGENT HIERARCHY DEMO: Web Site Creation")
    print("=" * 60)

    # Check environment
    base_url = os.environ.get("ANTHROPIC_BASE_URL", "http://127.0.0.1:3457/v1")
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        print("\n⚠️  ANTHROPIC_API_KEY not set!")
        print("Set it with: export ANTHROPIC_API_KEY=your_key")
        print("\nContinuing in dry-run mode (no DSH subprocesses)...")
        dry_run = True
    else:
        dry_run = False
        print(f"\n✓ API configured: {base_url}")

    # Import modules
    from ecms.agent_os.runtime.dsh_sdk_manager import DSHSDKSessionManager
    from ecms.agent_os.runtime.hierarchy_manager import AgentHierarchyManager

    # Initialize managers
    manager = DSHSDKSessionManager(
        base_dsh_home="/tmp/aegisos-dsh-homes",
        base_workspace="/tmp/aegisos-workspaces",
    )
    hierarchy = AgentHierarchyManager(session_manager=manager)

    print("\n--- Step 1: Load AgentProfiles ---")
    from sqlalchemy import select
    from ecms.persistence.database.rest_session import db_session
    from ecms.persistence.models.agent_profile import AgentProfile

    async with db_session() as session:
        result = await session.execute(select(AgentProfile))
        profiles = {p.profile_id: p for p in result.scalars().all()}

    print(f"Loaded {len(profiles)} profiles:")
    for pid, p in profiles.items():
        print(f"  - {pid}: {p.name} (role={p.role})")

    print("\n--- Step 2: Spawn Agents from Profiles ---")

    sessions = {}

    # Spawn HOE
    try:
        hoe_session = await manager.spawn_agent_from_profile(
            profile_id="head-of-engineering",
            agent_id="hoe-1",
            api_key=api_key or "dry-run-key",
        )
        sessions["hoe-1"] = hoe_session
        print(f"✓ HOE spawned: {hoe_session.agent_id} (session={hoe_session.session_id})")
    except Exception as e:
        print(f"✗ HOE spawn failed: {e}")
        if not dry_run:
            return

    # Spawn Frontend Engineer
    try:
        fe_session = await manager.spawn_agent_from_profile(
            profile_id="senior-frontend-engineer",
            agent_id="frontend-1",
            api_key=api_key or "dry-run-key",
        )
        sessions["frontend-1"] = fe_session
        print(f"✓ Frontend Engineer spawned: {fe_session.agent_id} (session={fe_session.session_id})")
    except Exception as e:
        print(f"✗ Frontend spawn failed: {e}")

    # Spawn Backend Engineer
    try:
        be_session = await manager.spawn_agent_from_profile(
            profile_id="senior-backend-engineer",
            agent_id="backend-1",
            api_key=api_key or "dry-run-key",
        )
        sessions["backend-1"] = be_session
        print(f"✓ Backend Engineer spawned: {be_session.agent_id} (session={be_session.session_id})")
    except Exception as e:
        print(f"✗ Backend spawn failed: {e}")

    if dry_run:
        print("\n--- Dry Run: Simulated Task Assignment ---")
        print("""
    Task assigned to HOE:
    "Create a modern portfolio website with:
    - Responsive landing page
    - Project showcase with filtering
    - Contact form with validation
    - Blog section with markdown rendering
    - API backend for form submission"

    HOE would:
    1. Analyze requirements
    2. Delegate frontend tasks to frontend-1
    3. Delegate backend tasks to backend-1
    4. Review their work
    5. Report final status
        """)
    else:
        print("\n--- Step 3: Assign Task to HOE ---")

        task = """Create a modern portfolio website with the following features:

FRONTEND:
- Responsive landing page with hero section
- Project showcase grid with category filtering
- Contact form with client-side validation
- Blog section with markdown rendering
- Smooth animations and transitions

BACKEND:
- REST API for project CRUD operations
- Contact form submission endpoint with email notification
- Blog content management API
- PostgreSQL database schema
- Input validation and error handling

Please coordinate between frontend and backend teams. Ensure the API contract
is agreed upon before implementation begins."""

        # Send task to HOE
        from ecms.agent_os.runtime.dsh_sdk_manager import AgentMessage

        hoe_message = AgentMessage(
            source="aegisos",
            sender_id="user-1",
            sender_name="User",
            content=task,
            channel_id="project-website-1",
            metadata={"type": "new_project", "project_id": "website-1"},
        )

        await manager.ingest_message("hoe-1", hoe_message)
        print(f"✓ Task assigned to HOE (queue depth: {sessions['hoe-1'].message_queue.qsize()})")

        print("\n--- Step 4: HOE Processing ---")
        print("HOE is analyzing the task and will delegate to team members...")
        print("(Processing happens asynchronously in the message loop)")

        # Wait for HOE to process (in real usage, this would be event-driven)
        await asyncio.sleep(5)

        # Check status
        status = await manager.get_delegation_status("hoe-1")
        print(f"\nHOE status: {status}")

    print("\n--- Cleanup ---")
    # Stop all sessions
    for agent_id in list(sessions.keys()):
        await manager.stop_agent(agent_id)
        print(f"  Stopped {agent_id}")

    print("\n" + "=" * 60)
    print("  DEMO COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
