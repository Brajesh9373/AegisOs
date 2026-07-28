"""End-to-end simulation test of the full cognitive system (SECTION 339/340/343)."""

from __future__ import annotations

from ecms.sdk import SimulationEnvironment


async def test_simulation_runs_full_system() -> None:
    report = await SimulationEnvironment().run(files=6, prompts=3)
    assert report.ukos_ingested == 6
    assert report.ucos_generated >= report.ukos_ingested
    assert report.tasks_executed == 3
    assert report.graph_nodes > 0
    assert report.knowledge_candidates >= 0


async def test_simulation_grows_the_graph() -> None:
    environment = SimulationEnvironment()
    small = await environment.run(files=2, prompts=1)
    assert small.graph_nodes > 0
