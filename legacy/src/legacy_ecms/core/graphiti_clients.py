import hashlib
import json
from copy import copy
from collections.abc import Iterable
from typing import Any


def OpenAICompatibleChatClient(
    config: Any | None = None,
    cache: bool = False,
    client: Any = None,
    max_tokens: int = 16384,
    reasoning: str = "auto",
    verbosity: str = "low",
    response_format: str = "json_object",
) -> Any:
    """Return a Graphiti LLMClient using chat completions for structured output."""

    from graphiti_core.llm_client.openai_base_client import BaseOpenAIClient
    from openai import AsyncOpenAI

    class _OpenAICompatibleChatClient(BaseOpenAIClient):
        def __init__(self) -> None:
            super().__init__(config, cache, max_tokens, reasoning, verbosity)
            self.client = client or AsyncOpenAI(api_key=config.api_key, base_url=config.base_url)
            self._response_model: type | None = None

        async def _create_structured_completion(
            self,
            model: str,
            messages: list,
            temperature: float | None,
            max_tokens: int,
            response_model: type,
            reasoning: str | None = None,
            verbosity: str | None = None,
        ) -> Any:
            self._response_model = response_model
            messages = _with_response_schema_instruction(messages, response_model)
            return await self._chat_completion(model, messages, temperature, max_tokens)

        async def _create_completion(
            self,
            model: str,
            messages: list,
            temperature: float | None,
            max_tokens: int,
            response_model: type | None = None,
            reasoning: str | None = None,
            verbosity: str | None = None,
        ) -> Any:
            self._response_model = response_model
            return await self._chat_completion(model, messages, temperature, max_tokens)

        async def _chat_completion(
            self,
            model: str,
            messages: list,
            temperature: float | None,
            max_tokens: int,
        ) -> Any:
            request_kwargs: dict[str, Any] = {
                "model": model,
                "messages": messages,
                "max_tokens": max_tokens,
            }
            if response_format != "none":
                request_kwargs["response_format"] = {"type": response_format}
            if temperature is not None:
                request_kwargs["temperature"] = temperature
            return await self.client.chat.completions.create(**request_kwargs)

        def _handle_structured_response(self, response: Any) -> tuple[dict[str, Any], int, int]:
            return self._handle_json_response(response)

        def _handle_json_response(self, response: Any) -> tuple[dict[str, Any], int, int]:
            result = response.choices[0].message.content or "{}"
            input_tokens = 0
            output_tokens = 0
            if hasattr(response, "usage") and response.usage:
                input_tokens = getattr(response.usage, "prompt_tokens", 0) or 0
                output_tokens = getattr(response.usage, "completion_tokens", 0) or 0
            parsed = _loads_json(result)
            return _normalize_response_model(parsed, self._response_model), input_tokens, output_tokens

    return _OpenAICompatibleChatClient()


def _with_response_schema_instruction(messages: list, response_model: type) -> list:
    schema = json.dumps(response_model.model_json_schema(), ensure_ascii=True)
    instruction = (
        "Return only valid JSON matching this schema. "
        "Do not include markdown, prose, comments, or fields outside the schema.\n"
        f"{schema}"
    )
    updated = [dict(message) for message in messages]
    for message in reversed(updated):
        if message.get("role") == "user":
            message["content"] = f"{message.get('content', '')}\n\n{instruction}"
            return updated
    updated.append({"role": "user", "content": instruction})
    return updated


def _loads_json(value: str) -> Any:
    cleaned = value.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            return json.loads(cleaned[start : end + 1])
        raise


def _normalize_response_model(value: Any, response_model: type | None) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if response_model is not None:
        fields = getattr(response_model, "model_fields", {})
        if len(fields) == 1:
            return {next(iter(fields)): value}
    if isinstance(value, list):
        return {"items": value}
    return {"value": value}


_HF_MODEL: Any = None
_HF_DIM: int = 1024


def HuggingFaceEmbedder(model_name: str = "intfloat/multilingual-e5-large", device: str = "cpu") -> Any:
    """Return a Graphiti EmbedderClient backed by a local HuggingFace model."""
    import os
    global _HF_MODEL, _HF_DIM

    from graphiti_core.embedder.client import EmbedderClient

    if _HF_MODEL is None:
        os.environ.setdefault("HF_HUB_CACHE", "./data/models")
        from sentence_transformers import SentenceTransformer
        try:
            _HF_MODEL = SentenceTransformer(model_name, device=device)
        except Exception as exc:
            logging.getLogger(__name__).warning("Failed to load HuggingFace model %s: %s", model_name, exc)
        try:
            _HF_DIM = _HF_MODEL.get_sentence_embedding_dimension() if _HF_MODEL else 1024
        except AttributeError:
            _HF_DIM = 1024

    class _HuggingFaceEmbedder(EmbedderClient):
        def __init__(self) -> None:
            self.embedding_dim = _HF_DIM

        async def create(self, input_data, *args, **kwargs) -> list[float]:
            if _HF_MODEL is None:
                return _hash_vec(str(input_data), self.embedding_dim)
            import asyncio
            text = input_data if isinstance(input_data, str) else json.dumps(list(input_data), sort_keys=True)
            loop = asyncio.get_running_loop()
            result = await loop.run_in_executor(
                None,
                lambda: _HF_MODEL.encode(f"query: {text}", normalize_embeddings=True).tolist(),
            )
            return list(result)

        async def create_batch(self, input_data_list: list[str]) -> list[list[float]]:
            if _HF_MODEL is None:
                return [_hash_vec(t, self.embedding_dim) for t in input_data_list]
            import asyncio
            loop = asyncio.get_running_loop()
            prefixed = [f"passage: {t}" for t in input_data_list]
            result = await loop.run_in_executor(
                None,
                lambda: _HF_MODEL.encode(prefixed, normalize_embeddings=True).tolist(),
            )
            return [list(e) for e in result]

    return _HuggingFaceEmbedder()


def _hash_vec(text: str, dim: int) -> list[float]:
    import hashlib
    vector = [0.0] * dim
    for i, token in enumerate(str(text).lower().split()):
        d = hashlib.sha256(token.encode()).digest()
        bucket = int.from_bytes(d[:4], "big") % dim
        sign = 1.0 if d[4] % 2 == 0 else -1.0
        vector[bucket] += sign * (1.0 + (i % 7) / 10.0)
    norm = sum(v * v for v in vector) ** 0.5
    return [v / norm for v in vector] if norm else vector


def HashEmbedder(embedding_dim: int = 1024) -> Any:
    """Return a Graphiti EmbedderClient backed by deterministic local hashing."""

    from graphiti_core.embedder.client import EmbedderClient

    class _HashEmbedder(EmbedderClient):
        def __init__(self) -> None:
            self.embedding_dim = embedding_dim

        async def create(
            self,
            input_data: str | list[str] | Iterable[int] | Iterable[Iterable[int]],
        ) -> list[float]:
            text = input_data if isinstance(input_data, str) else json.dumps(list(input_data), sort_keys=True)
            return self._embed_text(text)

        async def create_batch(self, input_data_list: list[str]) -> list[list[float]]:
            return [self._embed_text(item) for item in input_data_list]

        def _embed_text(self, text: str) -> list[float]:
            vector = [0.0] * self.embedding_dim
            for index, token in enumerate(text.lower().split()):
                digest = hashlib.sha256(token.encode("utf-8")).digest()
                bucket = int.from_bytes(digest[:4], "big") % self.embedding_dim
                sign = 1.0 if digest[4] % 2 == 0 else -1.0
                vector[bucket] += sign * (1.0 + (index % 7) / 10.0)
            norm = sum(value * value for value in vector) ** 0.5
            if norm:
                vector = [value / norm for value in vector]
            return vector

    return _HashEmbedder()


def FalkorDBSearchCompatibility() -> Any:
    """Return a Graphiti search adapter for FalkorDB builds without edge fulltext search."""

    from graphiti_core.driver.search_interface.search_interface import SearchInterface
    from graphiti_core.search import search_utils

    class _FalkorDBSearchCompatibility(SearchInterface):
        async def edge_fulltext_search(
            self,
            driver: Any,
            query: str,
            search_filter: Any,
            group_ids: list[str] | None = None,
            limit: int = 100,
        ) -> list[Any]:
            return []

        async def edge_similarity_search(
            self,
            driver: Any,
            search_vector: list[float],
            source_node_uuid: str | None,
            target_node_uuid: str | None,
            search_filter: Any,
            group_ids: list[str] | None = None,
            limit: int = 100,
            min_score: float = 0.7,
        ) -> list[Any]:
            return await search_utils.edge_similarity_search(
                _delegate_driver(driver),
                search_vector,
                source_node_uuid,
                target_node_uuid,
                search_filter,
                group_ids,
                limit,
                min_score,
            )

        async def node_fulltext_search(
            self,
            driver: Any,
            query: str,
            search_filter: Any,
            group_ids: list[str] | None = None,
            limit: int = 100,
        ) -> list[Any]:
            return await search_utils.node_fulltext_search(
                _delegate_driver(driver), query, search_filter, group_ids, limit
            )

        async def node_similarity_search(
            self,
            driver: Any,
            search_vector: list[float],
            search_filter: Any,
            group_ids: list[str] | None = None,
            limit: int = 100,
            min_score: float = 0.7,
        ) -> list[Any]:
            return await search_utils.node_similarity_search(
                _delegate_driver(driver), search_vector, search_filter, group_ids, limit, min_score
            )

        async def episode_fulltext_search(
            self,
            driver: Any,
            query: str,
            search_filter: Any,
            group_ids: list[str] | None = None,
            limit: int = 100,
        ) -> list[Any]:
            return await search_utils.episode_fulltext_search(
                _delegate_driver(driver), query, search_filter, group_ids, limit
            )

        async def edge_bfs_search(
            self,
            driver: Any,
            bfs_origin_node_uuids: list[str] | None,
            bfs_max_depth: int,
            search_filter: Any,
            group_ids: list[str] | None = None,
            limit: int = 100,
        ) -> list[Any]:
            return await search_utils.edge_bfs_search(
                _delegate_driver(driver),
                bfs_origin_node_uuids,
                bfs_max_depth,
                search_filter,
                group_ids,
                limit,
            )

        async def node_bfs_search(
            self,
            driver: Any,
            bfs_origin_node_uuids: list[str] | None,
            search_filter: Any,
            bfs_max_depth: int,
            group_ids: list[str] | None = None,
            limit: int = 100,
        ) -> list[Any]:
            return await search_utils.node_bfs_search(
                _delegate_driver(driver),
                bfs_origin_node_uuids,
                search_filter,
                bfs_max_depth,
                group_ids,
                limit,
            )

        async def community_fulltext_search(
            self,
            driver: Any,
            query: str,
            group_ids: list[str] | None = None,
            limit: int = 100,
        ) -> list[Any]:
            return await search_utils.community_fulltext_search(
                _delegate_driver(driver), query, group_ids, limit
            )

        async def community_similarity_search(
            self,
            driver: Any,
            search_vector: list[float],
            group_ids: list[str] | None = None,
            limit: int = 100,
            min_score: float = 0.6,
        ) -> list[Any]:
            return await search_utils.community_similarity_search(
                _delegate_driver(driver), search_vector, group_ids, limit, min_score
            )

        async def get_embeddings_for_communities(
            self,
            driver: Any,
            communities: list[Any],
        ) -> dict[str, list[float]]:
            return await search_utils.get_embeddings_for_communities(
                _delegate_driver(driver), communities
            )

        async def node_distance_reranker(
            self,
            driver: Any,
            node_uuids: list[str],
            center_node_uuid: str,
            min_score: float = 0,
        ) -> tuple[list[str], list[float]]:
            return await search_utils.node_distance_reranker(
                _delegate_driver(driver), node_uuids, center_node_uuid, min_score
            )

        async def episode_mentions_reranker(
            self,
            driver: Any,
            node_uuids: list[list[str]],
            min_score: float = 0,
        ) -> tuple[list[str], list[float]]:
            return await search_utils.episode_mentions_reranker(
                _delegate_driver(driver), node_uuids, min_score
            )

        def build_node_search_filters(self, search_filters: Any) -> Any:
            return search_filters

        def build_edge_search_filters(self, search_filters: Any) -> Any:
            return search_filters

    return _FalkorDBSearchCompatibility()


def _delegate_driver(driver: Any) -> Any:
    delegate = copy(driver)
    delegate.search_interface = None
    return delegate
