from pathlib import Path

import pytest

from ecms.agents.base_agent import BaseAgent
from ecms.agents.context_assembler import ContextAssembler
from ecms.memory.brain import GBrain
from ecms.memory.session import SessionMemory
from ecms.memory.working import WorkingMemory


def test_working_and_session_memory_store_context() -> None:
    working = WorkingMemory()
    working.set("objective", "understand authentication")
    session = SessionMemory()
    session.set("s1", "project", "payments")

    assert working.snapshot()["objective"] == "understand authentication"
    assert session.snapshot("s1")["project"] == "payments"


@pytest.mark.asyncio
async def test_gbrain_writes_and_reads_markdown_memory(tmp_path: Path) -> None:
    brain = GBrain(tmp_path)

    episodes = await brain.write("Authentication", "JWT token login belongs to the payment service.")
    matches = await brain.read("JWT payment")

    assert episodes
    assert (tmp_path / "authentication.md").exists()
    assert len(matches) == 1


@pytest.mark.asyncio
async def test_agent_assembles_memory_context(tmp_path: Path) -> None:
    brain = GBrain(tmp_path)
    await brain.write("Authentication", "JWT token login belongs to the payment service.")

    agent = BaseAgent(context_assembler=ContextAssembler(brain=brain))
    answer = await agent.ask("How does authentication work?")

    assert "memory note" in answer
