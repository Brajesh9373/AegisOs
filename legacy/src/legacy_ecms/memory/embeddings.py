"""Embedding provider protocol — pluggable semantic similarity engine.

Storage-agnostic, model-agnostic. Implementations can use:
  - Deterministic hash embedding (dev/testing, zero deps)
  - Sentence-transformers (local, no API cost)
  - OpenAI embeddings (production, API-based)
  - Any custom embedder satisfying the protocol
"""

from __future__ import annotations

import hashlib
import math
from typing import Protocol, runtime_checkable

import numpy as np


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Protocol for computing embeddings and semantic similarity.

    Implementations must be stateless (no per-call side effects).
    All methods are synchronous — callers should use asyncio.to_thread
    for non-blocking async.
    """

    @property
    def dimension(self) -> int:
        """Output dimension of embedding vectors."""
        ...

    def embed(self, text: str) -> list[float]:
        """Compute embedding vector for a single text."""
        ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Compute embeddings for a batch of texts (optimized path)."""
        ...

    def similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two embedding vectors.

        Returns a float between 0.0 (completely different) and 1.0 (identical).
        """
        ...


# ── Deterministic Hash Embedder (dev/testing, zero external deps) ──

class HashEmbedder:
    """Deterministic embedding via SHA-256 hash folding.

    NOT suitable for production semantic search. Use for testing
    and as a reference implementation. Swap for sentence-transformers
    or OpenAI embeddings in production.

    Produces stable, repeatable embeddings so tests are deterministic.
    """

    def __init__(self, dimension: int = 128) -> None:
        self._dim = dimension

    @property
    def dimension(self) -> int:
        return self._dim

    def embed(self, text: str) -> list[float]:
        """Hash-fold text into a fixed-dimension float vector."""
        h = hashlib.sha256(text.encode("utf-8")).digest()
        vec = np.zeros(self._dim, dtype=np.float32)
        for i in range(self._dim):
            # XOR-fold bytes into float in [-1, 1]
            byte_val = h[i % len(h)] ^ h[(i + 7) % len(h)]
            vec[i] = (float(byte_val) / 127.5) - 1.0
        # Normalize to unit length
        norm = float(np.linalg.norm(vec))
        if norm > 0:
            vec = vec / norm
        return vec.tolist()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(t) for t in texts]

    def similarity(self, a: list[float], b: list[float]) -> float:
        """Cosine similarity between two vectors."""
        va = np.array(a, dtype=np.float32)
        vb = np.array(b, dtype=np.float32)
        dot = float(np.dot(va, vb))
        return max(0.0, min(1.0, (dot + 1.0) / 2.0))


# ── Embedding Index (in-memory, for scalability: replace with FAISS/Qdrant) ──

class EmbeddingIndex:
    """In-memory embedding index with cosine similarity search.

    Stores (atom_id, embedding) pairs and supports top-k nearest-neighbor
    lookup. Thread-safe via single-threaded access.

    At scale (>100K atoms), replace with FAISS or push search to Qdrant.
    """

    def __init__(self, embedder: EmbeddingProvider | None = None) -> None:
        self._embedder = embedder or HashEmbedder()
        self._embeddings: dict[str, list[float]] = {}
        self._ids: list[str] = []

    @property
    def size(self) -> int:
        return len(self._ids)

    def index(self, atom_id: str, text: str) -> None:
        """Index or update an atom's embedding."""
        emb = self._embedder.embed(text)
        self._embeddings[atom_id] = emb
        if atom_id not in self._ids:
            self._ids.append(atom_id)

    def index_batch(self, items: list[tuple[str, str]]) -> None:
        """Index multiple atoms at once (optimized batch path)."""
        texts = [text for _, text in items]
        embs = self._embedder.embed_batch(texts)
        for (atom_id, _), emb in zip(items, embs):
            self._embeddings[atom_id] = emb
            if atom_id not in self._ids:
                self._ids.append(atom_id)

    def remove(self, atom_id: str) -> None:
        """Remove an atom from the index."""
        self._embeddings.pop(atom_id, None)
        if atom_id in self._ids:
            self._ids.remove(atom_id)

    def search(self, query: str, top_k: int = 10) -> list[tuple[str, float]]:
        """Return top-k atom IDs by cosine similarity to query."""
        if not self._ids:
            return []
        query_emb = self._embedder.embed(query)
        scores: list[tuple[str, float]] = []
        for atom_id in self._ids:
            emb = self._embeddings.get(atom_id)
            if emb is None:
                continue
            sim = self._embedder.similarity(query_emb, emb)
            scores.append((atom_id, sim))
        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:top_k]

    def rebuild(self, items: list[tuple[str, str]]) -> None:
        """Full rebuild — clears and reindexes all items."""
        self._embeddings.clear()
        self._ids.clear()
        self.index_batch(items)
