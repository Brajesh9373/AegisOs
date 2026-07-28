"""Default reflection engine (SECTION 33/78/101).

Executes after a task completes: summarizes the work, records successes and
mistakes, distills reusable patterns from the activated knowledge, and proposes
knowledge candidates. Candidates remain isolated from enterprise knowledge until
the Promotion pipeline validates them. Reflection never writes the graph.
"""

from __future__ import annotations

from ecms.events import EventBus
from ecms.infrastructure.reasoning import DeterministicReasoningProvider
from ecms.reflection.events.reflection_events import (
    candidate_generated,
    improvement_suggested,
    pattern_discovered,
    reflection_completed,
    reflection_started,
)
from ecms.shared.enums import TaskStatus
from ecms.shared.events import BaseEvent
from ecms.shared.interfaces import ReasoningProvider, ReasoningRequest
from ecms.shared.models import (
    KnowledgeCandidate,
    Reflection,
    Task,
    UniversalCognitiveObject,
)

__all__ = ["DefaultReflectionEngine"]


class DefaultReflectionEngine:
    """Learns from completed tasks and proposes knowledge candidates (SECTION 78)."""

    def __init__(
        self,
        *,
        reasoner: ReasoningProvider | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        """Initialize with a reasoning provider and optional event bus."""
        self._reasoner = reasoner or DeterministicReasoningProvider()
        self._event_bus = event_bus

    async def reflect(self, task: Task, activated: list[UniversalCognitiveObject]) -> Reflection:
        """Analyze a completed task and return a reflection (SECTION 101)."""
        await self._emit(reflection_started(task.task_id))
        successful = task.status is not TaskStatus.FAILED
        patterns = self._patterns(activated)
        improvements = self._improvements(task, activated)
        reflection = Reflection(
            task_id=task.task_id,
            summary=await self._summarize(task),
            successes=[f"completed goal: {task.goal}"] if successful else [],
            mistakes=list(task.errors),
            patterns=patterns,
            improvements=improvements,
            confidence=90 if successful and not task.errors else 40,
        )
        for pattern in patterns:
            await self._emit(pattern_discovered(reflection.reflection_id, pattern))
        for improvement in improvements:
            await self._emit(improvement_suggested(reflection.reflection_id, improvement))
        await self._emit(reflection_completed(reflection.reflection_id))
        return reflection

    async def generate_candidates(
        self,
        task: Task,
        reflection: Reflection,
        activated: list[UniversalCognitiveObject],
    ) -> list[KnowledgeCandidate]:
        """Turn a reflection's patterns into isolated knowledge candidates (SECTION 102)."""
        evidence = [uco.uco_id for uco in activated]
        candidates: list[KnowledgeCandidate] = []
        for pattern in reflection.patterns:
            candidate = KnowledgeCandidate(
                source_task=task.task_id,
                reflection_id=reflection.reflection_id,
                confidence=reflection.confidence,
                importance=60,
                proposed_uco={
                    "canonical_name": pattern,
                    "ontology_type": "pattern",
                    "description": f"Reusable pattern observed while: {task.goal}",
                },
                supporting_evidence=evidence,
            )
            candidates.append(candidate)
            await self._emit(candidate_generated(candidate.candidate_id))
        reflection.knowledge_candidates = [candidate.candidate_id for candidate in candidates]
        return candidates

    async def _summarize(self, task: Task) -> str:
        response = await self._reasoner.reason(
            ReasoningRequest(
                instruction="summarize the outcome of this task",
                context=f"{task.goal} (status: {task.status.value})",
            )
        )
        return response.content

    @staticmethod
    def _patterns(activated: list[UniversalCognitiveObject]) -> list[str]:
        ontology_types = sorted({uco.ontology_type for uco in activated})
        return [f"reuse of {ontology_type} knowledge" for ontology_type in ontology_types]

    @staticmethod
    def _improvements(task: Task, activated: list[UniversalCognitiveObject]) -> list[str]:
        improvements: list[str] = []
        if task.errors:
            improvements.append("add validation to prevent the observed errors")
        if not activated:
            improvements.append("capture knowledge for this task domain")
        return improvements

    async def _emit(self, event: BaseEvent) -> None:
        if self._event_bus is not None:
            await self._event_bus.publish(event)
