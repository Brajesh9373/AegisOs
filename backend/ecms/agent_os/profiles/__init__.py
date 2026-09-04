"""Deployment-owned Agent OS profile contracts and plugin interfaces."""

from ecms.agent_os.profiles.contracts import (
    AgentStepEnvelope,
    CapabilityRequest,
    DSHProfileSpec,
    EnvelopeValidationError,
    ProfileExecutionBudget,
    RuntimeReadiness,
    StageSpec,
    StepOutcomeKind,
    TerminalResult,
    parse_step_envelope,
)
from ecms.agent_os.profiles.plugin import (
    AgentProfileCatalog,
    AgentProfilePlugin,
    ProfileContractError,
    ProfileNotRegisteredError,
)

__all__ = [
    "AgentProfileCatalog",
    "AgentProfilePlugin",
    "AgentStepEnvelope",
    "CapabilityRequest",
    "DSHProfileSpec",
    "EnvelopeValidationError",
    "ProfileContractError",
    "ProfileExecutionBudget",
    "ProfileNotRegisteredError",
    "RuntimeReadiness",
    "StageSpec",
    "StepOutcomeKind",
    "TerminalResult",
    "parse_step_envelope",
]
