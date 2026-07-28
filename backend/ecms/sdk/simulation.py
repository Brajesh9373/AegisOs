"""Enterprise Simulation Environment (SECTION 339/343).

Exercises the whole cognitive system with synthetic data before production:
ingests generated source artifacts, executes prompts through the runtime kernel
(planning, memory activation, reflection, promotion, graph update), and reports
what the system produced. Everything runs offline via the deterministic providers.
"""

from __future__ import annotations

from dataclasses import dataclass

from ecms.sdk.cognitive import CognitiveSystem, create_cognitive_system
from ecms.shared.models import UniversalKnowledgeObject

__all__ = ["SimulationEnvironment", "SimulationReport"]


@dataclass(frozen=True, slots=True)
class SimulationReport:
    """A summary of one simulation run (SECTION 339)."""

    ukos_ingested: int
    ucos_generated: int
    tasks_executed: int
    graph_nodes: int
    knowledge_candidates: int


class SimulationEnvironment:
    """Runs full-system simulations with synthetic data (SECTION 339)."""

    def __init__(self, system: CognitiveSystem | None = None) -> None:
        """Initialize with a cognitive system, creating one when none is given."""
        self._system = system or create_cognitive_system()

    async def run(
        self,
        *,
        files: int = 10,
        prompts: int = 3,
        organization_id: str = "sim-org",
    ) -> SimulationReport:
        """Ingest synthetic artifacts, execute prompts, and return a report."""
        ucos_generated = 0
        for index in range(files):
            ucos = await self._system.knowledge.ingest(self._synthetic_uko(index, organization_id))
            ucos_generated += len(ucos)

        candidates = 0
        for index in range(prompts):
            result = await self._system.kernel.execute(
                f"Service{index}",
                organization_id=organization_id,
                user_id="simulator",
            )
            candidates += len(result.knowledge_candidates)

        stats = await self._system.graph.statistics()
        return SimulationReport(
            ukos_ingested=files,
            ucos_generated=ucos_generated,
            tasks_executed=prompts,
            graph_nodes=int(stats["node_count"]),
            knowledge_candidates=candidates,
        )

    @staticmethod
    def _synthetic_uko(index: int, organization_id: str) -> UniversalKnowledgeObject:
        content = (
            f"class Service{index}(BaseService):\n"
            f'    """Synthetic service {index}."""\n\n'
            f"    def handle(self, request: str) -> bool:\n"
            f"        return True\n"
        )
        return UniversalKnowledgeObject(
            provider="simulation",
            provider_object_type="file",
            provider_object_id=f"service_{index}.py",
            organization_id=organization_id,
            title=f"service_{index}",
            raw_content=content,
            language="python",
        )
