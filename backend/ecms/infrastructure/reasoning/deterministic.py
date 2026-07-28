"""Deterministic, dependency-free reasoning and embedding providers (SECTION 5).

These default providers require no external service or API key. They derive their
output solely from the input, so identical inputs always yield identical outputs,
making the cognitive pipeline fully testable and replayable offline. Real
model-backed providers are supplied as plugins and swapped in via configuration.
"""

from __future__ import annotations

import hashlib
import math
from collections.abc import Sequence

from ecms.shared.interfaces.reasoning import (
    EmbeddingVector,
    ReasoningRequest,
    ReasoningResponse,
)

__all__ = ["DeterministicEmbeddingProvider", "DeterministicReasoningProvider"]


def _digest(text: str) -> str:
    """Return a hex SHA-256 digest of ``text`` (used for stable, non-secret hashing)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class DeterministicReasoningProvider:
    """A reasoning provider that returns deterministic, structured responses.

    The response is a pure function of a stable digest of the request, so the
    provider never calls an external model. It is the offline default and doubles
    as a fixture that makes the execution pipeline deterministic in tests.
    """

    def __init__(self, *, model: str = "deterministic-v1") -> None:
        """Initialize the provider with a stable model identifier."""
        self._model = model

    @property
    def name(self) -> str:
        """Return the provider's stable identifier."""
        return "deterministic"

    async def reason(self, request: ReasoningRequest) -> ReasoningResponse:
        """Return a deterministic response derived from the request.

        Args:
            request: The reasoning request to answer.

        Returns:
            A response whose content and structured payload are a pure function
            of the request instruction and context.
        """
        digest = _digest(f"{request.instruction}\n{request.context}")
        content = f"{request.instruction.strip()} :: {digest[:16]}"
        tokens = len(request.instruction.split()) + len(request.context.split())
        return ReasoningResponse(
            content=content,
            structured={"digest": digest, "instruction": request.instruction.strip()},
            tokens_used=tokens,
            provider=self.name,
            model=self._model,
        )


class DeterministicEmbeddingProvider:
    """A feature-hashing embedding provider requiring no external model.

    Text is tokenized and hashed into a fixed-dimensional, L2-normalized vector.
    The mapping is deterministic and produces meaningful cosine similarity between
    texts that share tokens, which is sufficient for offline tests and as the
    default embedding provider.
    """

    def __init__(self, *, dimensions: int = 64, model: str = "deterministic-embed-v1") -> None:
        """Initialize the provider with a fixed vector dimensionality."""
        if dimensions < 1:
            raise ValueError(f"dimensions must be positive, got {dimensions}")
        self._dimensions = dimensions
        self._model = model

    @property
    def dimensions(self) -> int:
        """Return the dimensionality of produced vectors."""
        return self._dimensions

    async def embed(self, text: str) -> EmbeddingVector:
        """Return a deterministic embedding vector for ``text``."""
        return EmbeddingVector(values=self._vectorize(text), model=self._model)

    async def embed_batch(self, texts: Sequence[str]) -> list[EmbeddingVector]:
        """Return deterministic embedding vectors for a batch of texts."""
        return [await self.embed(text) for text in texts]

    def _vectorize(self, text: str) -> tuple[float, ...]:
        """Hash the tokens of ``text`` into a normalized fixed-length vector."""
        buckets = [0.0] * self._dimensions
        for token in text.lower().split():
            bucket = int.from_bytes(hashlib.sha256(token.encode("utf-8")).digest()[:8], "big")
            buckets[bucket % self._dimensions] += 1.0
        norm = math.sqrt(sum(value * value for value in buckets)) or 1.0
        return tuple(value / norm for value in buckets)
