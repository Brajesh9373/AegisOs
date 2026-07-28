"""Ports for the replaceable reasoning and embedding providers (SECTION 5/10/286).

The LLM is only one replaceable reasoning component. Reasoning and embedding are
expressed as structural ports so the platform never depends on a specific
provider. A deterministic default keeps the cognitive pipeline fully testable and
replayable offline; real providers (OpenAI, Anthropic, local models) are supplied
as plugins and selected through configuration.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable

from pydantic import Field

from ecms.shared.value_objects.base import ValueObject

__all__ = [
    "EmbeddingProvider",
    "EmbeddingVector",
    "ReasoningProvider",
    "ReasoningRequest",
    "ReasoningResponse",
]


class ReasoningRequest(ValueObject):
    """An immutable request submitted to a reasoning provider (SECTION 286)."""

    instruction: str
    context: str = ""
    schema_hint: dict[str, Any] | None = None
    max_tokens: int | None = Field(default=None, ge=1)
    temperature: float = Field(default=0.0, ge=0.0, le=2.0)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReasoningResponse(ValueObject):
    """An immutable result produced by a reasoning provider (SECTION 286)."""

    content: str
    structured: dict[str, Any] | None = None
    tokens_used: int = Field(default=0, ge=0)
    provider: str = "unknown"
    model: str = "unknown"


class EmbeddingVector(ValueObject):
    """An immutable dense embedding vector for semantic operations (SECTION 95/157)."""

    values: tuple[float, ...]
    model: str = "unknown"

    @property
    def dimensions(self) -> int:
        """Return the dimensionality of the vector."""
        return len(self.values)


@runtime_checkable
class ReasoningProvider(Protocol):
    """Port for the replaceable reasoning (LLM) component (SECTION 5/286).

    Operations:
        name: A stable identifier for the provider implementation.
        reason: Produce a reasoning response for a request.
    """

    @property
    def name(self) -> str: ...

    async def reason(self, request: ReasoningRequest) -> ReasoningResponse: ...


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Port for the replaceable embedding component (SECTION 95/157).

    Operations:
        dimensions: The dimensionality of vectors this provider produces.
        embed: Return an embedding vector for a single text.
        embed_batch: Return embedding vectors for a batch of texts.
    """

    @property
    def dimensions(self) -> int: ...

    async def embed(self, text: str) -> EmbeddingVector: ...

    async def embed_batch(self, texts: Sequence[str]) -> list[EmbeddingVector]: ...
