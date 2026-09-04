"""Production Business Analyst cognition boundaries and DSH orchestration."""

from ecms.agent.ba.cognition.contracts import (
    BAExecutionContext,
    BAExecutionResponse,
    BAStage,
    BAStageInvocation,
    BAStageResult,
    ContextEvidence,
    ContextRetrievalStatus,
    GraphDigest,
    PromptBudget,
    PromptCitation,
    PromptContextPacket,
    PromptMessage,
    RetrievalState,
)

__all__ = [
    "BACognitionService",
    "BAExecutionContext",
    "BAExecutionResponse",
    "BAStage",
    "BAStageInvocation",
    "BAStagePromptRenderer",
    "BAStageResult",
    "BAStageValidationError",
    "ContextEvidence",
    "ContextRetrievalStatus",
    "DSHBAStageExecutor",
    "GraphDigest",
    "PromptBudget",
    "PromptBudgetExceeded",
    "PromptCitation",
    "PromptContextPacket",
    "PromptMessage",
    "RetrievalState",
    "ScopedCognitionContextProvider",
]


def __getattr__(name: str) -> object:
    """Load integration adapters only when their dependency graph is needed."""
    if name == "DSHBAStageExecutor":
        from ecms.agent.ba.cognition.executor import DSHBAStageExecutor

        return DSHBAStageExecutor
    if name in {"BAStagePromptRenderer", "PromptBudgetExceeded"}:
        from ecms.agent.ba.cognition.renderer import BAStagePromptRenderer, PromptBudgetExceeded

        return {"BAStagePromptRenderer": BAStagePromptRenderer, "PromptBudgetExceeded": PromptBudgetExceeded}[name]
    if name == "ScopedCognitionContextProvider":
        from ecms.agent.ba.cognition.provider import ScopedCognitionContextProvider

        return ScopedCognitionContextProvider
    if name in {"BACognitionService", "BAStageValidationError"}:
        from ecms.agent.ba.cognition.service import BACognitionService, BAStageValidationError

        return {"BACognitionService": BACognitionService, "BAStageValidationError": BAStageValidationError}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
