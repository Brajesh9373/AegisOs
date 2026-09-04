"""Request-scoped contracts for Business Analyst cognition.

DSH is deliberately not a cognition client. It receives a rendered, bounded
prompt built from these immutable host-side contracts and never receives store
credentials, raw authorization data, bearer tokens, or graph query capability.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from hashlib import sha256
from math import isfinite
from types import MappingProxyType
from typing import Protocol, TypeAlias, runtime_checkable

__all__ = [
    "AuthorizationScopeResolver",
    "BAExecutionContext",
    "BAExecutionResponse",
    "BAStage",
    "BAStageExecutor",
    "BAStageInvocation",
    "BAStageResult",
    "CognitionContextProvider",
    "ContextEvidence",
    "ContextRetrievalStatus",
    "DiscoveryMemoryWriter",
    "GraphDigest",
    "JSONValue",
    "PromptBudget",
    "PromptCitation",
    "PromptContextPacket",
    "PromptMessage",
    "RetrievalState",
]

JSONValue: TypeAlias = str | int | float | bool | None | list["JSONValue"] | dict[str, "JSONValue"]


class BAStage(StrEnum):
    """The fixed BA state-machine stages supported by the DSH profile."""

    UNDERSTAND = "understand"
    CLARIFY = "clarify"
    FINALIZE = "finalize"
    DESIGN_TEAM = "design_team"


class RetrievalState(StrEnum):
    """Truthful availability state for one host-side cognition source."""

    READY = "ready"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True, slots=True)
class PromptBudget:
    """Hard byte and cardinality limits for one host-rendered BA prompt."""

    max_source_bytes: int = 24 * 1024
    max_conversation_bytes: int = 32 * 1024
    max_evidence_items: int = 12
    max_evidence_bytes: int = 24 * 1024
    max_graph_nodes: int = 24
    max_graph_edges: int = 40
    max_graph_bytes: int = 12 * 1024
    max_prompt_bytes: int = 96 * 1024

    def __post_init__(self) -> None:
        """Reject non-positive limits before context generation begins."""
        for field_name, value in (
            ("max_source_bytes", self.max_source_bytes),
            ("max_conversation_bytes", self.max_conversation_bytes),
            ("max_evidence_items", self.max_evidence_items),
            ("max_evidence_bytes", self.max_evidence_bytes),
            ("max_graph_nodes", self.max_graph_nodes),
            ("max_graph_edges", self.max_graph_edges),
            ("max_graph_bytes", self.max_graph_bytes),
            ("max_prompt_bytes", self.max_prompt_bytes),
        ):
            if value <= 0:
                raise ValueError(f"{field_name} must be positive")


@dataclass(frozen=True, slots=True)
class BAExecutionContext:
    """Authenticated, authorization-resolved identity for one immutable BA run.

    Fields are opaque identifiers or non-secret revisions. Raw ACLs, source-system
    credentials, database URLs, and bearer tokens must never be added because this
    value can be referenced by rendering and execution diagnostics.
    """

    actor_id: str
    organization_id: str
    discovery_session_id: str
    correlation_id: str
    source_revision: str
    conversation_revision: str
    policy_revision: str
    classification_ceiling: str
    profile_hash: str
    template_hash: str
    schema_hash: str
    project_id: str | None = None
    workspace_id: str | None = None
    retention_policy: str = "default"
    scope_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Require stable execution identifiers and canonicalize scope membership."""
        required = {
            "actor_id": self.actor_id,
            "organization_id": self.organization_id,
            "discovery_session_id": self.discovery_session_id,
            "correlation_id": self.correlation_id,
            "source_revision": self.source_revision,
            "conversation_revision": self.conversation_revision,
            "policy_revision": self.policy_revision,
            "classification_ceiling": self.classification_ceiling,
            "profile_hash": self.profile_hash,
            "template_hash": self.template_hash,
            "schema_hash": self.schema_hash,
            "retention_policy": self.retention_policy,
        }
        invalid = [
            name for name, value in required.items() if not isinstance(value, str) or not value.strip()
        ]
        if invalid:
            raise ValueError(f"BA execution context requires: {', '.join(invalid)}")
        if any(not isinstance(scope_id, str) or not scope_id.strip() for scope_id in self.scope_ids):
            raise ValueError("scope_ids must contain only non-empty strings")
        object.__setattr__(self, "scope_ids", tuple(sorted(set(self.scope_ids))))

    @property
    def scope_partition(self) -> str:
        """Return a stable opaque authorization-cache partition identifier."""
        payload = {
            "actor_id": self.actor_id,
            "organization_id": self.organization_id,
            "project_id": self.project_id,
            "workspace_id": self.workspace_id,
            "policy_revision": self.policy_revision,
            "classification_ceiling": self.classification_ceiling,
            "scope_ids": self.scope_ids,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        return sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class PromptMessage:
    """One discovery message supplied as untrusted task data."""

    role: str
    content: str

    def __post_init__(self) -> None:
        """Ensure message role is present before prompt rendering."""
        if not isinstance(self.role, str) or not self.role.strip():
            raise ValueError("prompt message role must not be empty")
        if not isinstance(self.content, str):
            raise ValueError("prompt message content must be a string")


@dataclass(frozen=True, slots=True)
class PromptCitation:
    """Opaque provenance attached to host-authorized prompt evidence."""

    citation_id: str
    source_kind: str
    locator: str
    source_version: str
    trust_state: str

    def __post_init__(self) -> None:
        """Require auditable source provenance for every rendered evidence item."""
        fields = {
            "citation_id": self.citation_id,
            "source_kind": self.source_kind,
            "locator": self.locator,
            "source_version": self.source_version,
            "trust_state": self.trust_state,
        }
        invalid = [name for name, value in fields.items() if not isinstance(value, str) or not value.strip()]
        if invalid:
            raise ValueError(f"prompt citation requires: {', '.join(invalid)}")


@dataclass(frozen=True, slots=True)
class ContextEvidence:
    """One bounded evidence item already authorized at its storage boundary."""

    citation: PromptCitation
    content: str
    score: float
    classification: str = "internal"

    def __post_init__(self) -> None:
        """Reject malformed evidence before it can become a prompt snapshot."""
        if not isinstance(self.content, str) or not self.content.strip():
            raise ValueError("context evidence content must be a non-empty string")
        if not isinstance(self.score, (int, float)) or isinstance(self.score, bool) or not isfinite(self.score):
            raise ValueError("context evidence score must be finite")
        if not isinstance(self.classification, str) or not self.classification.strip():
            raise ValueError("context evidence classification must not be empty")


@dataclass(frozen=True, slots=True)
class GraphDigest:
    """Read-only bounded graph expansion produced by a trusted host adapter."""

    snapshot_version: str | None = None
    nodes: tuple[Mapping[str, str], ...] = ()
    edges: tuple[Mapping[str, str], ...] = ()

    def __post_init__(self) -> None:
        """Freeze records so a retry cannot observe a mutated graph snapshot."""
        if self.snapshot_version is not None and (
            not isinstance(self.snapshot_version, str) or not self.snapshot_version.strip()
        ):
            raise ValueError("graph snapshot_version must be a non-empty string when supplied")
        object.__setattr__(self, "nodes", tuple(_freeze_graph_record(node) for node in self.nodes))
        object.__setattr__(self, "edges", tuple(_freeze_graph_record(edge) for edge in self.edges))


@dataclass(frozen=True, slots=True)
class ContextRetrievalStatus:
    """Availability and omission information for one cognition source."""

    source: str
    state: RetrievalState
    omitted_count: int = 0
    reason_code: str | None = None

    def __post_init__(self) -> None:
        """Prevent contradictory availability telemetry."""
        if not isinstance(self.source, str) or not self.source.strip():
            raise ValueError("retrieval status source must not be empty")
        if self.omitted_count < 0:
            raise ValueError("omitted_count must be non-negative")
        if self.state is RetrievalState.READY and self.reason_code is not None:
            raise ValueError("ready retrieval status cannot include a reason code")
        if self.state is not RetrievalState.READY and not self.reason_code:
            raise ValueError("degraded and unavailable retrieval statuses require a reason code")


@dataclass(frozen=True, slots=True)
class PromptContextPacket:
    """Complete immutable context snapshot rendered into one DSH stage invocation."""

    context: BAExecutionContext
    source_text: str
    conversation: tuple[PromptMessage, ...]
    evidence: tuple[ContextEvidence, ...] = ()
    graph: GraphDigest = field(default_factory=GraphDigest)
    retrieval_statuses: tuple[ContextRetrievalStatus, ...] = ()
    omitted_evidence_count: int = 0

    def __post_init__(self) -> None:
        """Freeze packet collections before a DSH process can be launched."""
        if not isinstance(self.source_text, str) or not self.source_text.strip():
            raise ValueError("prompt context packet requires source_text")
        if self.omitted_evidence_count < 0:
            raise ValueError("omitted_evidence_count must be non-negative")
        object.__setattr__(self, "conversation", tuple(self.conversation))
        object.__setattr__(self, "evidence", tuple(self.evidence))
        object.__setattr__(self, "retrieval_statuses", tuple(self.retrieval_statuses))
        if any(not isinstance(item, PromptMessage) for item in self.conversation):
            raise ValueError("conversation must contain only PromptMessage values")
        if any(not isinstance(item, ContextEvidence) for item in self.evidence):
            raise ValueError("evidence must contain only ContextEvidence values")
        if any(not isinstance(item, ContextRetrievalStatus) for item in self.retrieval_statuses):
            raise ValueError("retrieval_statuses must contain only ContextRetrievalStatus values")

    @property
    def snapshot_hash(self) -> str:
        """Return a stable non-secret identity of this exact packet."""
        payload: dict[str, JSONValue] = {
            "context": {
                "actor_id": self.context.actor_id,
                "organization_id": self.context.organization_id,
                "project_id": self.context.project_id,
                "workspace_id": self.context.workspace_id,
                "discovery_session_id": self.context.discovery_session_id,
                "correlation_id": self.context.correlation_id,
                "source_revision": self.context.source_revision,
                "conversation_revision": self.context.conversation_revision,
                "policy_revision": self.context.policy_revision,
                "classification_ceiling": self.context.classification_ceiling,
                "retention_policy": self.context.retention_policy,
                "profile_hash": self.context.profile_hash,
                "template_hash": self.context.template_hash,
                "schema_hash": self.context.schema_hash,
                "scope_partition": self.context.scope_partition,
            },
            "source_text": self.source_text,
            "conversation": [
                {"role": item.role, "content": item.content} for item in self.conversation
            ],
            "evidence": [
                {
                    "citation": {
                        "citation_id": item.citation.citation_id,
                        "source_kind": item.citation.source_kind,
                        "locator": item.citation.locator,
                        "source_version": item.citation.source_version,
                        "trust_state": item.citation.trust_state,
                    },
                    "content": item.content,
                    "score": item.score,
                    "classification": item.classification,
                }
                for item in self.evidence
            ],
            "graph": {
                "snapshot_version": self.graph.snapshot_version,
                "nodes": [dict(node) for node in self.graph.nodes],
                "edges": [dict(edge) for edge in self.graph.edges],
            },
            "retrieval_statuses": [
                {
                    "source": status.source,
                    "state": status.state.value,
                    "omitted_count": status.omitted_count,
                    "reason_code": status.reason_code,
                }
                for status in self.retrieval_statuses
            ],
            "omitted_evidence_count": self.omitted_evidence_count,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        return sha256(encoded.encode("utf-8")).hexdigest()


@dataclass(frozen=True, slots=True)
class BAStageInvocation:
    """Opaque pre-rendered request received by the isolated stage executor."""

    stage: BAStage
    packet: PromptContextPacket
    rendered_prompt: str
    attempt: int = 1
    model_ids: tuple[str, ...] = ()
    tool_names: tuple[str, ...] = ()
    organization_member_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate fixed invocation attributes before execution."""
        if self.attempt not in (1, 2):
            raise ValueError("stage attempt must be either 1 or 2")
        if not isinstance(self.rendered_prompt, str) or not self.rendered_prompt.strip():
            raise ValueError("rendered_prompt must not be empty")


@dataclass(frozen=True, slots=True)
class BAExecutionResponse:
    """Non-secret result returned from the isolated stage executor."""

    output: str
    duration_seconds: float
    runtime_metadata: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Freeze audit metadata and reject invalid execution observations."""
        if not isinstance(self.output, str):
            raise ValueError("execution output must be a string")
        if (
            not isinstance(self.duration_seconds, (int, float))
            or isinstance(self.duration_seconds, bool)
            or not isfinite(self.duration_seconds)
            or self.duration_seconds < 0
        ):
            raise ValueError("execution duration_seconds must be a non-negative finite number")
        metadata = dict(self.runtime_metadata)
        if any(not isinstance(key, str) or not isinstance(value, str) for key, value in metadata.items()):
            raise ValueError("runtime_metadata must contain only string keys and values")
        object.__setattr__(self, "runtime_metadata", MappingProxyType(metadata))


@dataclass(frozen=True, slots=True)
class BAStageResult:
    """Strictly validated stage output tied to its immutable prompt packet."""

    stage: BAStage
    packet: PromptContextPacket
    output: JSONValue
    execution: BAExecutionResponse
    validation_attempts: int

    def __post_init__(self) -> None:
        """Limit validation retries to the fixed one-repair BA protocol."""
        if self.validation_attempts not in (1, 2):
            raise ValueError("validation_attempts must be either 1 or 2")


@runtime_checkable
class AuthorizationScopeResolver(Protocol):
    """Build a request-scoped authorization context before any retrieval occurs."""

    async def resolve(self, context: BAExecutionContext) -> BAExecutionContext:
        """Return a context whose scope is authorized by the server."""


@runtime_checkable
class CognitionContextProvider(Protocol):
    """Build bounded evidence and graph context for an authorized request."""

    async def build_packet(
        self,
        context: BAExecutionContext,
        *,
        source_text: str,
        conversation: tuple[PromptMessage, ...],
        budget: PromptBudget,
    ) -> PromptContextPacket:
        """Return a provenance-tagged packet with authorized cognition context."""


@runtime_checkable
class BAStageExecutor(Protocol):
    """Execute a pre-rendered BA stage without direct cognition-store access."""

    async def execute(self, invocation: BAStageInvocation) -> BAExecutionResponse:
        """Invoke the configured BA orchestration runtime."""


@runtime_checkable
class DiscoveryMemoryWriter(Protocol):
    """Durably record an accepted BA stage result and promotion work atomically."""

    async def record(self, result: BAStageResult) -> None:
        """Persist a validated stage receipt and any policy-approved candidates."""


def _freeze_graph_record(record: Mapping[str, str]) -> Mapping[str, str]:
    """Copy one host-produced graph record into an immutable string-only mapping."""
    if not isinstance(record, Mapping):
        raise ValueError("graph records must be mappings")
    frozen: dict[str, str] = {}
    for key, value in record.items():
        if (
            not isinstance(key, str)
            or not key.strip()
            or not isinstance(value, str)
            or not value.strip()
        ):
            raise ValueError("graph record keys and values must be non-empty strings")
        frozen[key] = value
    return MappingProxyType(frozen)
