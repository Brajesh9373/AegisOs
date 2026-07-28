"""Unit tests for the deterministic reasoning and embedding providers (SECTION 5)."""

from __future__ import annotations

import pytest

from ecms.infrastructure.reasoning import (
    DeterministicEmbeddingProvider,
    DeterministicReasoningProvider,
)
from ecms.shared.interfaces import (
    EmbeddingProvider,
    EmbeddingVector,
    ReasoningProvider,
    ReasoningRequest,
)


async def test_reasoning_is_deterministic() -> None:
    provider = DeterministicReasoningProvider()
    request = ReasoningRequest(instruction="plan the task", context="build a login form")
    first = await provider.reason(request)
    second = await provider.reason(request)
    assert first == second
    assert first.provider == "deterministic"
    assert first.tokens_used > 0


def test_reasoning_provider_satisfies_port() -> None:
    assert isinstance(DeterministicReasoningProvider(), ReasoningProvider)


async def test_embedding_is_deterministic_with_fixed_dimensions() -> None:
    provider = DeterministicEmbeddingProvider(dimensions=32)
    vector = await provider.embed("authentication service")
    again = await provider.embed("authentication service")
    assert vector.dimensions == 32
    assert vector == again


async def test_embedding_similarity_reflects_shared_tokens() -> None:
    provider = DeterministicEmbeddingProvider(dimensions=128)
    a = await provider.embed("jwt authentication middleware")
    b = await provider.embed("jwt authentication service")
    c = await provider.embed("database migration script")

    def cosine(x: EmbeddingVector, y: EmbeddingVector) -> float:
        return sum(i * j for i, j in zip(x.values, y.values, strict=True))

    assert cosine(a, b) > cosine(a, c)


async def test_embed_batch_returns_one_vector_per_text() -> None:
    provider = DeterministicEmbeddingProvider()
    vectors = await provider.embed_batch(["one", "two", "three"])
    assert len(vectors) == 3


def test_embedding_provider_satisfies_port() -> None:
    assert isinstance(DeterministicEmbeddingProvider(), EmbeddingProvider)


def test_embedding_rejects_non_positive_dimensions() -> None:
    with pytest.raises(ValueError, match="dimensions must be positive"):
        DeterministicEmbeddingProvider(dimensions=0)
