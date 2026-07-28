"""Mem0Memory — production-grade semantic episodic memory layer wrapping mem0.

Supports two Qdrant modes:
  - Local (dev): file-based Qdrant at mem0_qdrant_path (default)
  - Server (prod): Qdrant at mem0_qdrant_host:mem0_qdrant_port

Connection pooling via module-level singleton — multiple callers share
one Mem0 instance. All paths async-safe via asyncio.to_thread.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from legacy_ecms.config import Settings

logger = logging.getLogger(__name__)

# ── Module-level singleton for connection pooling ──────────────────
_instances: dict[str, "Mem0Memory"] = {}


def get_mem0(settings: Settings, workspace_id: str = "default") -> "Mem0Memory":
    """Return cached Mem0Memory instance for the given workspace.

    Ensures one Qdrant connection + LLM client per process, shared across
    all API requests. Workspace-scoped by workspace_id key.
    """
    global _instances
    cache_key = f"{workspace_id}"
    if cache_key not in _instances:
        _instances[cache_key] = Mem0Memory(settings, workspace_id=workspace_id)
    return _instances[cache_key]


def reset_mem0() -> None:
    """Reset all cached instances (useful for testing)."""
    global _instances
    _instances = {}


class Mem0Memory:
    """Semantic memory backed by mem0.

    - LLM: CommandCode API via openai_compatible_chat adapter
    - Embeddings: OpenAI-compatible (reuses openai_base_url)
    - Vector DB: Qdrant (local file or server)
    - History: SQLite

    Lazy-init: heavy init (LLM client, Qdrant, embedder) happens on
    first add() or search() call, not at import time.
    """

    def __init__(
        self,
        settings: Settings,
        workspace_id: str = "default",
    ) -> None:
        self._settings = settings
        self._workspace_id = workspace_id
        self._memory: Any = None
        self._enabled = getattr(settings, "mem0_enabled", False)
        self._init_lock = asyncio.Lock()

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def _ensure_init(self) -> None:
        """Thread-safe lazy init with lock."""
        if self._memory is not None:
            return
        async with self._init_lock:
            if self._memory is not None:
                return
            await self._do_init()

    async def _do_init(self) -> None:
        from legacy_ecms.memory.mem0_llm_adapter import patch_mem0_llm, patch_mem0_embedder
        patch_mem0_embedder()  # Must run BEFORE mem0 imports to prevent sentence_transformers ImportError
        from mem0 import Memory
        patch_mem0_llm()

        embedding_dims = 384  # MiniLM-L6-v2 

        # Determine Qdrant config: server mode vs local file mode
        qdrant_host = getattr(self._settings, "mem0_qdrant_host", "")
        qdrant_port = getattr(self._settings, "mem0_qdrant_port", 6333)
        qdrant_api_key = getattr(self._settings, "mem0_qdrant_api_key", "")

        if qdrant_host:
            vector_config: dict[str, Any] = {
                "provider": "qdrant",
                "config": {
                    "host": qdrant_host,
                    "port": qdrant_port,
                    "embedding_model_dims": embedding_dims,
                },
            }
        else:
            qdrant_path = str(
                getattr(self._settings, "mem0_qdrant_path", "./data/mem0_qdrant")
            )
            vector_config = {
                "provider": "qdrant",
                "config": {
                    "path": qdrant_path,
                    "embedding_model_dims": embedding_dims,
                    "on_disk": True,
                },
            }

        if qdrant_api_key:
            vector_config["config"]["api_key"] = qdrant_api_key

        # Workspace-scoped collection name (Phase 3)
        collection = (
            f"ecms_mem0_{self._workspace_id}"
            if self._workspace_id != "default"
            else "ecms_mem0"
        )
        vector_config["config"]["collection_name"] = collection

        mem0_home = str(
            getattr(self._settings, "mem0_home_path", "./data/mem0_home")
        )

        config = {
            "llm": {
                "provider": "openai",
                "config": {
                    "model": self._settings.llm_model,
                    "temperature": 0.1,
                    "api_key": self._settings.openai_api_key,
                    "openai_base_url": self._settings.openai_base_url or "https://api.openai.com/v1",
                },
            },
            "embedder": {
                "provider": "openai",
                "config": {
                    "model": "text-embedding-3-small",
                    "api_key": self._settings.openai_api_key,
                    "openai_base_url": self._settings.openai_base_url or "https://api.openai.com/v1",
                    "embedding_dims": 1536,
                },
            },
            "vector_store": vector_config,
            "history_db_path": f"{mem0_home}/history.db",
            "custom_fact_extraction_prompt": "Return the input text unchanged as a single memory fact.",
            "version": "v1.1",
        }

        self._memory = await asyncio.to_thread(Memory.from_config, config)
        logger.info(
            "Mem0 initialized (workspace=%s, qdrant=%s)",
            self._workspace_id,
            "server" if qdrant_host else "local",
        )

    async def add(
        self,
        content: str,
        user_id: str = "default",
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Add a memory to mem0. Returns the raw mem0 result dict."""
        if not self._enabled:
            return {"results": []}
        await self._ensure_init()
        kwargs: dict[str, Any] = {"user_id": user_id}
        if metadata:
            kwargs["metadata"] = metadata
        try:
            return await asyncio.to_thread(self._memory.add, content, infer=True, **kwargs)
        except Exception as exc:
            logger.warning("Mem0 add failed (workspace=%s): %s", self._workspace_id, exc)
            return {"results": []}

    async def add_from_messages(
        self,
        messages: list[dict[str, str]],
        user_id: str = "default",
    ) -> dict[str, Any]:
        """Add memory from a conversation turn."""
        if not self._enabled:
            return {"results": []}
        await self._ensure_init()
        try:
            return await asyncio.to_thread(self._memory.add, messages, user_id=user_id)
        except Exception as exc:
            logger.warning("Mem0 add_from_messages failed: %s", exc)
            return {"results": []}

    async def search(
        self,
        query: str,
        user_id: str = "default",
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """Semantic search over mem0. Returns list of memory dicts."""
        if not self._enabled:
            return []
        await self._ensure_init()
        try:
            result = await asyncio.to_thread(
                self._memory.search,
                query,
                filters={"user_id": user_id},
                limit=limit,
            )
            return result.get("results", []) if isinstance(result, dict) else []
        except Exception as exc:
            logger.warning("Mem0 search failed (workspace=%s): %s", self._workspace_id, exc)
            return []

    async def get_all(self, user_id: str = "default") -> list[dict[str, Any]]:
        """List all memories for a user."""
        if not self._enabled:
            return []
        await self._ensure_init()
        try:
            return await asyncio.to_thread(
                self._memory.get_all, filters={"user_id": user_id}
            )
        except Exception as exc:
            logger.warning("Mem0 get_all failed: %s", exc)
            return []

    async def update(self, memory_id: str, content: str) -> dict[str, Any]:
        """Update an existing memory by ID."""
        if not self._enabled:
            return {}
        await self._ensure_init()
        try:
            return await asyncio.to_thread(self._memory.update, memory_id, content)
        except Exception as exc:
            logger.warning("Mem0 update failed: %s", exc)
            return {}

    async def delete(self, memory_id: str) -> dict[str, Any]:
        """Delete a memory by ID."""
        if not self._enabled:
            return {}
        await self._ensure_init()
        try:
            return await asyncio.to_thread(self._memory.delete, memory_id)
        except Exception as exc:
            logger.warning("Mem0 delete failed: %s", exc)
            return {}

    async def promote_to_graph(
        self,
        memory_entry: dict[str, Any],
        graph_client: Any,
    ) -> Any:
        from legacy_ecms.core.uko import (
            ExtractionProvenance,
            UKOMetadata,
            UKOType,
            UniversalKnowledgeObject,
        )
        from legacy_ecms.memory.long_term import LongTermMemory

        score = memory_entry.get("score", 0)
        threshold = getattr(self._settings, "mem0_promotion_threshold", 0.70)
        if score < threshold:
            return None

        memory_id = memory_entry.get("id", "unknown")
        content = memory_entry.get("memory", "")
        created_str = memory_entry.get("created_at", "")
        created_at = datetime.now(timezone.utc)
        if created_str:
            try:
                created_at = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
            except (ValueError, TypeError):
                pass

        uko = UniversalKnowledgeObject(
            id=f"mem0:{memory_id}",
            type=UKOType.DOCUMENT,
            name=f"Memory: {content[:80]}",
            content=content,
            metadata=UKOMetadata(
                source="mem0",
                source_id=memory_id,
                created_at=created_at,
                modified_at=created_at,
                tags=["mem0-memory", "auto-promoted"],
            ),
            provenance=ExtractionProvenance(
                extraction_method="mem0_auto",
                extraction_timestamp=datetime.now(timezone.utc),
                confidence=score,
                evidence_snippet=content[:200],
                pipeline_stage="memory",
            ),
            status="active",
            version=1,
        )
        try:
            return await LongTermMemory(graph=graph_client).remember(uko)
        except Exception as exc:
            logger.warning("Mem0 promotion to graph failed: %s", exc)
            return None
