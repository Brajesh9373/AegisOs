"""Embedding generation and cosine similarity for the knowledge base.

Uses fastembed (local ONNX-based) with BAAI/bge-small-en-v1.5 — 384-dim
embeddings that run entirely on CPU with no API dependency. The model
(~100MB) is downloaded once on first use and cached in the container.

Embeddings are stored as float arrays in regular Postgres (no pgvector).
Cosine similarity is computed in Python — fast enough for <10K entries.
"""

from __future__ import annotations

import asyncio
import logging
import math

logger = logging.getLogger("ecms.knowledge.embeddings")

# Singleton model instance — loaded once per process.
_model = None
_MODEL_NAME = "BAAI/bge-small-en-v1.5"


def _get_model():
    """Load and cache the fastembed model (lazy, thread-safe)."""
    global _model
    if _model is None:
        from fastembed import TextEmbedding

        logger.info("[embeddings] loading model %s (first call, downloads ~100MB)", _MODEL_NAME)
        _model = TextEmbedding(_MODEL_NAME)
        logger.info("[embeddings] model loaded (dim=%d)", len(list(_model.embed(["test"]))[0]))
    return _model


def _embed_sync(texts: list[str]) -> list[list[float]]:
    """Synchronous embedding — called via asyncio.to_thread."""
    model = _get_model()
    return [emb.tolist() for emb in model.embed(texts)]


async def generate_embedding(text: str) -> list[float]:
    """Generate a 384-dim embedding for a piece of text."""
    results = await asyncio.to_thread(_embed_sync, [text[:8000]])
    return results[0]


async def generate_embeddings_batch(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for multiple texts. Fastembed handles batching internally."""
    if not texts:
        return []
    # Truncate and batch — fastembed processes all at once.
    truncated = [t[:8000] for t in texts]
    return await asyncio.to_thread(_embed_sync, truncated)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors. Pure Python, no deps."""
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)
