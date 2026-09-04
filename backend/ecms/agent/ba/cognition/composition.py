"""Fail-closed composition and readiness for DSH-only BA execution.

The module keeps composition explicit: production callers receive no native-model
or global-memory fallback. It only wires host-owned prompt construction to the
pinned DSH subprocess boundary; canonical retrieval adapters must be supplied by
the persistence layer and enforce their own query-bound authorization rules.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from ecms.agent.ba.cognition.contracts import PromptBudget
from ecms.agent.ba.cognition.executor import DSHBAStageExecutor
from ecms.agent.ba.cognition.provider import (
    ScopedCognitionContextProvider,
    ScopedGraphEvidenceRetriever,
    ScopedKnowledgeEvidenceRetriever,
)
from ecms.agent.ba.cognition.service import BACognitionService
from ecms.agent.ba.dsh_profile import business_analyst_dsh_profile_spec
from ecms.agent.dsh_runtime import DSHRuntime
from ecms.configuration.schemas.settings import AppSettings, Profile

__all__ = [
    "BAExecutionUnavailable",
    "BAReadiness",
    "BAReadinessProbe",
    "build_ba_cognition_service",
]


class BAExecutionUnavailable(RuntimeError):  # noqa: N818
    """Raised when the required production BA execution path is unavailable."""


class BAReadinessProbe(Protocol):
    """Expose a non-invasive readiness check for the DSH BA service."""

    def readiness(self) -> BAReadiness:
        """Return non-secret readiness details without invoking a model."""

    def require_ready(self) -> None:
        """Raise when a request must fail closed instead of executing BA work."""


@dataclass(frozen=True, slots=True)
class BAReadiness:
    """Non-secret health of the composed DSH-only BA execution route."""

    ready: bool
    reason_code: str | None = None
    profile_fingerprint: str | None = None

    def __post_init__(self) -> None:
        """Validate that readiness status carries a consistent reason code."""
        if self.ready and self.reason_code is not None:
            raise ValueError("ready BA status cannot carry a reason code")
        if not self.ready and not self.reason_code:
            raise ValueError("unready BA status requires a reason code")


class _ReadinessAwareBACognitionService(BACognitionService):
    """BACognitionService whose dependency checks occur before any stage runs."""

    def __init__(
        self,
        *,
        readiness: Callable[[], BAReadiness],
        provider: ScopedCognitionContextProvider,
        executor: DSHBAStageExecutor,
        budget: PromptBudget,
    ) -> None:
        super().__init__(provider=provider, executor=executor, budget=budget)
        self._readiness = readiness

    def readiness(self) -> BAReadiness:
        """Return current executable/profile/gateway configuration readiness."""
        return self._readiness()

    def require_ready(self) -> None:
        """Fail closed before prompt retrieval or DSH invocation."""
        status = self.readiness()
        if not status.ready:
            raise BAExecutionUnavailable(
                f"DSH business-analyst execution is unavailable: {status.reason_code}"
            )

    async def execute(self, **kwargs: Any) -> Any:
        """Reject unavailable configurations before inherited execution orchestration."""
        self.require_ready()
        return await super().execute(**kwargs)


def build_ba_cognition_service(
    *,
    settings: AppSettings,
    knowledge: ScopedKnowledgeEvidenceRetriever,
    graph: ScopedGraphEvidenceRetriever | None,
) -> BACognitionService:
    """Create the only supported BA execution service from verified components.

    Callers must pass persistence-backed, scope-enforcing adapters. Passing a
    global legacy repository or in-memory promotion adapter is intentionally not
    supported by this composition function.
    """
    _require_runtime_mode(settings)
    runtime = DSHRuntime(
        profile_spec=business_analyst_dsh_profile_spec(),
        timeout=settings.agent_os_dsh_timeout_seconds,
        dsh_home=Path(settings.agent_os_dsh_home),
        dsh_executable=(
            Path(settings.agent_os_dsh_executable) if settings.agent_os_dsh_executable else None
        ),
        max_task_bytes=settings.agent_os_dsh_max_task_bytes,
        max_command_bytes=settings.agent_os_dsh_max_command_bytes,
        max_stdout_bytes=settings.agent_os_dsh_max_stdout_bytes,
        max_stderr_bytes=settings.agent_os_dsh_max_stderr_bytes,
        shutdown_grace_seconds=settings.agent_os_dsh_shutdown_grace_seconds,
        profile_lock_timeout_seconds=settings.agent_os_dsh_profile_lock_timeout_seconds,
    )
    budget = PromptBudget(
        max_source_bytes=settings.ba_prompt_max_source_bytes,
        max_conversation_bytes=settings.ba_prompt_max_conversation_bytes,
        max_evidence_items=settings.ba_prompt_max_evidence_items,
        max_evidence_bytes=settings.ba_prompt_max_evidence_bytes,
        max_graph_nodes=settings.ba_prompt_max_graph_nodes,
        max_graph_edges=settings.ba_prompt_max_graph_edges,
        max_graph_bytes=settings.ba_prompt_max_graph_bytes,
        max_prompt_bytes=settings.ba_prompt_max_bytes,
    )

    def check_readiness() -> BAReadiness:
        runtime_readiness = runtime.preflight()
        if not runtime_readiness.ready:
            return BAReadiness(
                ready=False,
                reason_code=runtime_readiness.reason_code or "dsh_dependency_unavailable",
            )
        return BAReadiness(
            ready=True,
            profile_fingerprint=runtime_readiness.profile_fingerprint,
        )

    return _ReadinessAwareBACognitionService(
        readiness=check_readiness,
        provider=ScopedCognitionContextProvider(knowledge=knowledge, graph=graph),
        executor=DSHBAStageExecutor(runtime),
        budget=budget,
    )


def _require_runtime_mode(settings: AppSettings) -> None:
    """Reject native or fixture execution modes before application composition."""
    if settings.environment is Profile.PRODUCTION and settings.ba_runtime_mode != "dsh":
        raise BAExecutionUnavailable("production BA execution requires ba_runtime_mode=dsh")
    if settings.ba_runtime_mode != "dsh":
        raise BAExecutionUnavailable(
            "BA execution is disabled outside explicitly composed DSH mode"
        )
