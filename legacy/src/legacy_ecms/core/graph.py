from __future__ import annotations

import logging
import traceback
from dataclasses import dataclass, field
from typing import Any

from legacy_ecms.config import Settings
from legacy_ecms.core.episode import EpisodePayload, EpisodePayloadType
from legacy_ecms.core.graphiti_clients import (
    FalkorDBSearchCompatibility,
    HashEmbedder,
    HuggingFaceEmbedder,
    OpenAICompatibleChatClient,
)
from legacy_ecms.core.schema_validator import validate_relationship
from legacy_ecms.core.uko import UKOType

logger = logging.getLogger(__name__)


class GraphNotInitializedError(RuntimeError):
    pass


@dataclass
class WriteFailure:
    node_id: str
    error_type: str
    error_message: str
    stage: str  # "node" | "relationship"


@dataclass
class BatchWriteResult:
    success_count: int = 0
    failure_count: int = 0
    failures: list[WriteFailure] = field(default_factory=list)
    orphan_stubs_created: list[str] = field(default_factory=list)


class GraphClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._graphiti: Any | None = None
        self._driver: Any | None = None
        self._raw_mode: bool = False
        self._raw_graph: Any = None

    async def initialize(self) -> None:
        import os
        import falkordb

        api_key = (self.settings.openai_api_key or "").strip()

        # Fast path: no API key → raw FalkorDB mode (keyword extraction, no LLM)
        if not api_key:
            db = falkordb.FalkorDB(
                host=self.settings.falkordb_host,
                port=self.settings.falkordb_port,
                password=self.settings.falkordb_password or None,
            )
            self._raw_graph = db.select_graph(self.settings.falkordb_database)
            self._raw_mode = True
            return

        # Slow path: graphiti-core available → LLM-enhanced extraction
        try:
            from graphiti_core.driver.falkordb_driver import FalkorDriver
        except ImportError:
            import logging
            logging.getLogger(__name__).warning(
                "graphiti-core not installed — running in raw (keyword) mode"
            )
            db = falkordb.FalkorDB(
                host=self.settings.falkordb_host,
                port=self.settings.falkordb_port,
                password=self.settings.falkordb_password or None,
            )
            self._raw_graph = db.select_graph(self.settings.falkordb_database)
            self._raw_mode = True
            return

        driver_kwargs: dict[str, Any] = {
            "host": self.settings.falkordb_host,
            "port": self.settings.falkordb_port,
            "database": self.settings.falkordb_database,
        }
        if self.settings.falkordb_password:
            driver_kwargs["password"] = self.settings.falkordb_password

        driver = FalkorDriver(**driver_kwargs)
        try:
            driver.search_interface = FalkorDBSearchCompatibility()
        except ModuleNotFoundError:
            if driver.__class__.__module__.startswith("graphiti_core"):
                raise

        self._driver = driver
        self._raw_graph = (
            driver._get_graph(self.settings.falkordb_database)
            if hasattr(driver, "_get_graph")
            else None
        )

        from graphiti_core import Graphiti
        from graphiti_core.llm_client.config import LLMConfig

        base_url = (self.settings.openai_base_url or "").strip()
        if self.settings.graphiti_embedder == "hash":
            embedder = HashEmbedder(self.settings.embedding_dim)
        elif self.settings.graphiti_embedder == "huggingface":
            embedder = HuggingFaceEmbedder()
        else:
            from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
            embedder = OpenAIEmbedder(OpenAIEmbedderConfig(
                api_key=api_key, embedding_model=self.settings.embedding_model,
                embedding_dim=self.settings.embedding_dim, base_url=base_url or None))

        llm_config = LLMConfig(api_key=api_key, model=self.settings.llm_model,
                               small_model=self.settings.llm_small_model or self.settings.llm_model,
                               base_url=base_url or None)

        saved_key = os.environ.get("OPENAI_API_KEY")
        saved_url = os.environ.get("OPENAI_BASE_URL")
        os.environ["OPENAI_API_KEY"] = api_key
        os.environ["OPENAI_BASE_URL"] = base_url
        try:
            if self.settings.graphiti_llm_client == "openai_compatible_chat":
                llm = OpenAICompatibleChatClient(config=llm_config, response_format=self.settings.graphiti_response_format)
            else:
                from graphiti_core.llm_client.openai_client import OpenAIClient
                llm = OpenAIClient(config=llm_config)
            self._graphiti = Graphiti(graph_driver=driver, llm_client=llm, embedder=embedder)
            await self._graphiti.build_indices_and_constraints()
        finally:
            if saved_key: os.environ["OPENAI_API_KEY"] = saved_key
            if saved_url: os.environ["OPENAI_BASE_URL"] = saved_url

    @property
    def raw_mode(self) -> bool:
        return self._raw_mode

    async def add_episode(self, episode: EpisodePayload) -> BatchWriteResult:
        if self._raw_mode:
            return await self._add_raw_episode(episode)
        from graphiti_core.nodes import EpisodeType
        et = EpisodeType.json if episode.episode_type == EpisodePayloadType.JSON else EpisodeType.text
        await self._graphiti.add_episode(
            name=episode.name, episode_body=episode.episode_body, source=et,
            reference_time=episode.reference_time, source_description=episode.source_description,
            group_id=episode.group_id)
        return BatchWriteResult(success_count=1)

    async def add_episodes_bulk(self, episodes: list[EpisodePayload]) -> BatchWriteResult:
        if self._raw_mode or len(episodes) == 0:
            return await self.add_episodes_raw_batch(episodes)

        from graphiti_core.utils.bulk_utils import RawEpisode

        CHUNK = 15
        aggregated = BatchWriteResult()
        for start in range(0, len(episodes), CHUNK):
            chunk = episodes[start : start + CHUNK]
            bulk = [
                RawEpisode(
                    name=ep.name,
                    content=ep.episode_body[:6000],
                    source_description=ep.source_description,
                    source="text",
                    reference_time=ep.reference_time,
                )
                for ep in chunk
            ]
            try:
                await self._graphiti.add_episode_bulk(bulk)
                aggregated.success_count += len(chunk)
            except Exception as exc:
                logger.warning("Graphiti bulk add failed for chunk, falling back to raw: %s", exc)
                fallback = await self.add_episodes_raw_batch(chunk)
                aggregated.success_count += fallback.success_count
                aggregated.failure_count += fallback.failure_count
                aggregated.failures.extend(fallback.failures)
        return aggregated

    async def add_episode_raw(self, episode: EpisodePayload) -> BatchWriteResult:
        return await self.add_episodes_raw_batch([episode])

    async def add_episodes_raw_batch(self, episodes: list[EpisodePayload]) -> BatchWriteResult:
        if not episodes:
            return BatchWriteResult()
        g = self._raw_graph
        batch_size = 200
        queue: list[dict] = []
        aggregated = BatchWriteResult()
        schema_mode = self.settings.schema_enforcement if hasattr(self.settings, "schema_enforcement") else "warn"
        for ep in episodes:
            queue.append(self._raw_record_for_episode(ep))
            if len(queue) >= batch_size:
                result = await self._flush_raw_batch(g, queue, schema_enforcement=schema_mode)
                aggregated.success_count += result.success_count
                aggregated.failure_count += result.failure_count
                aggregated.failures.extend(result.failures)
                aggregated.orphan_stubs_created.extend(result.orphan_stubs_created)
                queue = []
        if queue:
            result = await self._flush_raw_batch(g, queue, schema_enforcement=schema_mode)
            aggregated.success_count += result.success_count
            aggregated.failure_count += result.failure_count
            aggregated.failures.extend(result.failures)
            aggregated.orphan_stubs_created.extend(result.orphan_stubs_created)
        return aggregated

    async def _add_raw_episode(self, episode: EpisodePayload) -> BatchWriteResult:
        if self._raw_graph is None:
            import falkordb
            db = falkordb.FalkorDB(
                host=self.settings.falkordb_host, port=self.settings.falkordb_port,
                password=self.settings.falkordb_password or None)
            self._raw_graph = db.select_graph(self.settings.falkordb_database)
        return await self.add_episodes_raw_batch([episode])

    def _raw_record_for_episode(self, ep: EpisodePayload) -> dict[str, Any]:
        uko = ep.uko
        node_provenance = {}
        if uko.provenance:
            node_provenance = {
                "extraction_method": uko.provenance.extraction_method,
                "extraction_timestamp": uko.provenance.extraction_timestamp.isoformat(),
                "confidence": uko.provenance.confidence,
                "evidence_snippet": uko.provenance.evidence_snippet[:1000],
                "model_version": uko.provenance.model_version,
                "pipeline_stage": uko.provenance.pipeline_stage,
            }
        return {
            "id": uko.id,
            "name": uko.name,
            "type": uko.type.value,
            "layer": "knowledge" if uko.type.value == "concept" else "evidence",
            "content": uko.content[:5000],
            "episode_name": ep.name,
            "source": uko.metadata.source,
            "source_id": uko.metadata.source_id,
            "source_description": ep.source_description[:500],
            "source_url": uko.metadata.source_url or str(uko.raw_data.get("repo_url") or ""),
            "group_id": ep.group_id or "",
            "modified_at": ep.reference_time.isoformat(),
            "status": uko.status,
            "version": uko.version,
            "previous_version_id": uko.previous_version_id or "",
            "ingestion_batch_id": uko.ingestion_batch_id or "",
            "organization_id": str(uko.raw_data.get("organization_id") or ""),
            "connection_id": str(uko.raw_data.get("connection_id") or ""),
            "ingestion_revision": str(
                uko.raw_data.get("ingestion_revision")
                or uko.ingestion_batch_id
                or ""
            ),
            "provenance": node_provenance,
            "relationships": [
                {
                    "target_id": rel.target_id,
                    "target_type": rel.target_type.value,
                    "relationship": rel.relationship,
                    "confidence": rel.confidence,
                    "metadata": rel.metadata,
                    "provenance": {
                        "extraction_method": rel.provenance.extraction_method,
                        "extraction_timestamp": rel.provenance.extraction_timestamp.isoformat(),
                        "confidence": rel.provenance.confidence,
                        "evidence_snippet": rel.provenance.evidence_snippet[:1000],
                        "model_version": rel.provenance.model_version,
                        "pipeline_stage": rel.provenance.pipeline_stage,
                    }
                    if rel.provenance
                    else {},
                }
                for rel in uko.relationships
            ],
        }

    @staticmethod
    async def _flush_raw_batch(g: Any, batch: list[dict], schema_enforcement: str = "warn") -> BatchWriteResult:
        result = BatchWriteResult()
        if not batch:
            return result

        node_rows: list[dict[str, Any]] = []
        for item in batch:
            node_prov = item.get("provenance", {})
            node_rows.append(
                {
                    "id": item["id"],
                    "name": item["name"],
                    "type": item["type"],
                    "layer": item["layer"],
                    "content": item["content"],
                    "episode_name": item["episode_name"],
                    "source": item["source"],
                    "source_id": item["source_id"],
                    "source_description": item["source_description"],
                    "source_url": item["source_url"],
                    "modified_at": item["modified_at"],
                    "group_id": item["group_id"],
                    "status": item.get("status", "active"),
                    "extraction_method": node_prov.get("extraction_method", ""),
                    "pipeline_stage": node_prov.get("pipeline_stage", ""),
                    "node_confidence": node_prov.get("confidence", 0.0),
                    "organization_id": item.get("organization_id", ""),
                    "connection_id": item.get("connection_id", ""),
                    "ingestion_revision": item.get("ingestion_revision", ""),
                }
            )

        try:
            await _query_graph(
                g,
                "UNWIND $rows AS row "
                "MERGE (u:UKO {id: row.id}) "
                "SET u.name = row.name, u.type = row.type, u.layer = row.layer, "
                "u.content = row.content, u.episode_name = row.episode_name, "
                "u.source = row.source, u.source_id = row.source_id, "
                "u.source_description = row.source_description, u.source_url = row.source_url, "
                "u.modified_at = row.modified_at, u.group_id = row.group_id, "
                "u.status = row.status, "
                "u.version = coalesce(u.version, 0) + 1, "
                "u.extraction_method = row.extraction_method, "
                "u.pipeline_stage = row.pipeline_stage, "
                "u.node_confidence = row.node_confidence, "
                "u.organization_id = row.organization_id, "
                "u.connection_id = row.connection_id, "
                "u.ingestion_revision = row.ingestion_revision",
                {"rows": node_rows},
            )
            result.success_count = len(node_rows)
        except Exception as exc:
            for item in batch:
                result.failure_count += 1
                result.failures.append(WriteFailure(
                    node_id=item.get("id", "unknown"),
                    error_type=type(exc).__name__,
                    error_message=str(exc)[:500],
                    stage="node",
                ))
            logger.warning(
                "Graph batch write failed for %d nodes: %s\n%s",
                len(batch),
                exc,
                traceback.format_exc(),
            )
            return result

        relationship_rows: list[dict[str, Any]] = []
        for item in batch:
            node_id = item.get("id", "unknown")
            for rel in item["relationships"]:
                rel_target = rel.get("target_id", "unknown")
                rel_label = rel.get("relationship", "?")
                target_type_str = rel.get("target_type", "")
                try:
                    target_type = UKOType(target_type_str) if target_type_str else None
                except ValueError:
                    target_type = None

                if target_type is not None and schema_enforcement != "off":
                    is_valid, reason = validate_relationship(rel_label, target_type)
                    if not is_valid:
                        if schema_enforcement == "strict":
                            result.failure_count += 1
                            result.failures.append(WriteFailure(
                                node_id=node_id,
                                error_type="SchemaViolation",
                                error_message=reason[:500],
                                stage="relationship",
                            ))
                            logger.warning("Schema violation for %s->%s: %s", node_id, rel_target, reason)
                            continue
                        else:
                            logger.debug(
                                "Schema violation (warn mode) for %s->%s: %s",
                                node_id,
                                rel_target,
                                reason,
                            )

                rprov = rel.get("provenance", {})
                relationship_rows.append(
                    {
                        "source_id": item["id"],
                        "target_id": rel["target_id"],
                        "target_name": rel["target_id"][:120],
                        "target_type": rel["target_type"],
                        "target_layer": "knowledge" if rel["target_type"] == "concept" else "evidence",
                        "relationship": rel["relationship"],
                        "confidence": rel["confidence"],
                        "metadata": json_dumps(rel["metadata"]),
                        "extraction_method": rprov.get("extraction_method", ""),
                        "pipeline_stage": rprov.get("pipeline_stage", ""),
                        "evidence_snippet": rprov.get("evidence_snippet", "")[:500],
                        "organization_id": item.get("organization_id", ""),
                        "connection_id": item.get("connection_id", ""),
                        "ingestion_revision": item.get("ingestion_revision", ""),
                    }
                )

        relationship_batch_size = 1_000
        for start in range(0, len(relationship_rows), relationship_batch_size):
            rows = relationship_rows[start : start + relationship_batch_size]
            try:
                await _query_graph(
                    g,
                    "UNWIND $rows AS row "
                    "MERGE (t:UKO {id: row.target_id}) "
                    "ON CREATE SET t.name = row.target_name, t.type = row.target_type, "
                    "t.layer = row.target_layer "
                    "WITH row, t "
                    "MATCH (u:UKO {id: row.source_id}) "
                    "MERGE (u)-[r:RELATES {label: row.relationship}]->(t) "
                    "SET r.confidence = row.confidence, r.metadata = row.metadata, "
                    "r.extraction_method = row.extraction_method, "
                    "r.pipeline_stage = row.pipeline_stage, "
                    "r.evidence_snippet = row.evidence_snippet, "
                    "r.organization_id = row.organization_id, "
                    "r.connection_id = row.connection_id, "
                    "r.ingestion_revision = row.ingestion_revision",
                    {"rows": rows},
                )
            except Exception as exc:
                for row in rows:
                    result.failure_count += 1
                    result.failures.append(WriteFailure(
                        node_id=row["source_id"],
                        error_type=type(exc).__name__,
                        error_message=(
                            f"relationship {row['relationship']} -> "
                            f"{row['target_id']}: {exc!s}"
                        )[:500],
                        stage="relationship",
                    ))
                logger.warning(
                    "Graph batch write failed for %d relationships: %s\n%s",
                    len(rows),
                    exc,
                    traceback.format_exc(),
                )
        return result

    async def search(self, query: str = "", num_results: int = 100) -> Any:
        if self._graphiti is not None:
            return await self._graphiti.search(query=query, num_results=num_results)
        if self._raw_graph is not None:
            return await self._search_raw(query, num_results)
        return type("R", (), {"episodes": [], "nodes": [], "edges": []})()

    async def _search_raw(self, query: str, num_results: int = 100) -> Any:
        g = self._raw_graph
        cypher = "MATCH (u:UKO) RETURN u.id, u.name, u.source_description, u.content, u.type, u.layer LIMIT $limit"
        result = await _query_graph(g, cypher, {"limit": num_results})
        episodes = []
        for row in (result.result_set if hasattr(result, "result_set") else result):
            if hasattr(row, "__getitem__") and len(row) >= 2:
                episodes.append({"uuid": row[0] or "", "name": row[1] or "",
                                 "source_description": row[2] if len(row) > 2 else "",
                                 "content": row[3] if len(row) > 3 else "",
                                 "type": row[4] if len(row) > 4 else "",
                                 "layer": row[5] if len(row) > 5 else ""})

        edges = []
        try:
            edge_result = await _query_graph(
                g,
                "MATCH (u:UKO)-[r:RELATES]->(t:UKO) RETURN u.id, r.label, t.id, t.name, r.confidence LIMIT 2000",
            )
            for row in (edge_result.result_set if hasattr(edge_result, "result_set") else edge_result):
                if hasattr(row, "__getitem__") and len(row) >= 3:
                    edges.append({"from": row[0] or "", "relationship": row[1] or "", "to": row[2] or "",
                                  "confidence": row[4] if len(row) > 4 else None})
        except Exception as exc:
            logger.warning("Edge query in _search_raw failed: %s", exc)

        r = type("R", (), {})()
        r.episodes = episodes
        r.edges = edges
        r.nodes = []
        return r

    async def close(self) -> None:
        close = getattr(self._graphiti, "close", None)
        if close:
            r = close()
            if hasattr(r, "__await__"): await r
        self._graphiti = None
        self._driver = None
        self._raw_graph = None


def _esc(s: str) -> str:
    result = []
    for c in s:
        if c == "'":
            result.append("\\'")
        elif c == "\\":
            result.append("\\\\")
        elif ord(c) < 32:
            result.append(" ")
        else:
            result.append(c)
    return "".join(result)


async def _query_graph(graph: Any, query: str, params: dict[str, Any] | None = None) -> Any:
    result = graph.query(query, params or {})
    if hasattr(result, "__await__"):
        return await result
    return result


def json_dumps(value: Any) -> str:
    import json

    return json.dumps(value or {}, sort_keys=True)
