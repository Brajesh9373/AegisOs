"""Prometheus metrics route (SECTION 102)."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from redis.asyncio import Redis
from sqlalchemy import text

from ecms.api.dependencies.providers import get_sdk
from ecms.configuration.schemas.settings import get_settings
from ecms.connectors.ingestion.parallel_queue import (
    EXTRACTION_GROUP,
    EXTRACTION_STREAM,
    GRAPH_WRITE_GROUP,
    GRAPH_WRITE_STREAM,
)
from ecms.connectors.ingestion.queue import (
    GROUP as INGESTION_GROUP,
)
from ecms.connectors.ingestion.queue import (
    HEALTH_PREFIX as INGESTION_HEALTH_PREFIX,
)
from ecms.connectors.ingestion.queue import (
    METRICS_KEY as INGESTION_METRICS_KEY,
)
from ecms.connectors.ingestion.queue import (
    STREAM as INGESTION_STREAM,
)
from ecms.infrastructure.telemetry import PROMETHEUS_CONTENT_TYPE
from ecms.persistence.database.rest_session import db_session
from ecms.persistence.repositories.knowledge_graph_snapshot import (
    KnowledgeGraphSnapshotRepository,
)
from ecms.sdk import EcmsSDK
from ecms.visualization.snapshot_queue import GROUP, HEALTH_PREFIX, METRICS_KEY, STREAM

router = APIRouter(tags=["system"])

EXTRACTION_HEALTH_PREFIX = "ecms:connector-ingestion:extractor-health:"


async def _stream_pending(redis: Redis, stream: str, group: str) -> int:
    """Return a stream's pending count, including before its group exists."""
    try:
        pending = await redis.xpending(stream, group)
    except Exception:
        return 0
    if isinstance(pending, dict):
        return int(pending.get("pending", 0))
    return int(pending[0]) if pending else 0


async def _count_scan_keys(redis: Redis, pattern: str) -> int:
    """Count heartbeat keys without the blocking Redis KEYS command."""
    total = 0
    cursor: int | str = 0
    while True:
        cursor, keys = await redis.scan(cursor, match=pattern, count=100)
        total += len(keys)
        if int(cursor) == 0:
            return total


@router.get("/metrics")
async def metrics(request: Request, sdk: EcmsSDK = Depends(get_sdk)) -> Response:
    """Return metrics in the Prometheus exposition format."""
    collectors = getattr(request.app.state, "knowledge_graph_metrics", None)
    if collectors is None:
        collectors = {
            "queue": sdk.metrics.gauge(
                "knowledge_graph_snapshot_queue_entries",
                "Total entries retained in the snapshot job stream.",
            ),
            "pending": sdk.metrics.gauge(
                "knowledge_graph_snapshot_pending_jobs",
                "Unacknowledged snapshot jobs.",
            ),
            "workers": sdk.metrics.gauge(
                "knowledge_graph_snapshot_active_workers",
                "Snapshot workers with a current heartbeat.",
            ),
            "age": sdk.metrics.gauge(
                "knowledge_graph_snapshot_age_seconds",
                "Age of the current ready snapshot.",
            ),
            "points": sdk.metrics.gauge(
                "knowledge_graph_snapshot_points",
                "Nodes in the current ready snapshot.",
            ),
            "links": sdk.metrics.gauge(
                "knowledge_graph_snapshot_links",
                "Edges in the current ready snapshot.",
            ),
            "bytes": sdk.metrics.gauge(
                "knowledge_graph_snapshot_bytes",
                "Combined bytes in current Arrow artifacts.",
            ),
            "builds_completed": sdk.metrics.gauge(
                "knowledge_graph_snapshot_builds_completed",
                "Completed snapshot builds retained in Redis operational telemetry.",
            ),
            "builds_failed": sdk.metrics.gauge(
                "knowledge_graph_snapshot_builds_failed",
                "Failed build attempts retained in Redis operational telemetry.",
            ),
            "build_retries": sdk.metrics.gauge(
                "knowledge_graph_snapshot_build_retries",
                "Snapshot build retries retained in Redis operational telemetry.",
            ),
            "builds_exhausted": sdk.metrics.gauge(
                "knowledge_graph_snapshot_builds_exhausted",
                "Snapshot jobs that exhausted their retry budget.",
            ),
            "build_duration_last": sdk.metrics.gauge(
                "knowledge_graph_snapshot_build_duration_seconds_last",
                "Duration of the most recent snapshot build attempt.",
            ),
            "ingestion_queue": sdk.metrics.gauge(
                "connector_ingestion_queue_entries",
                "Total entries retained in the connector ingestion stream.",
            ),
            "ingestion_pending": sdk.metrics.gauge(
                "connector_ingestion_pending_jobs",
                "Unacknowledged connector ingestion jobs.",
            ),
            "ingestion_workers": sdk.metrics.gauge(
                "connector_ingestion_active_workers",
                "Connector ingestion workers with a current heartbeat.",
            ),
            "ingestion_oldest": sdk.metrics.gauge(
                "connector_ingestion_oldest_queued_seconds",
                "Age of the oldest queued connector ingestion.",
            ),
            "ingestion_expired": sdk.metrics.gauge(
                "connector_ingestion_expired_leases",
                "Connector ingestion jobs with an expired durable lease.",
            ),
            "ingestion_running": sdk.metrics.gauge(
                "connector_ingestion_running_jobs",
                "Connector ingestion jobs currently owned by workers.",
            ),
            "ingestion_capacity": sdk.metrics.gauge(
                "connector_ingestion_worker_capacity",
                "Current connector ingestion worker capacity.",
            ),
            "ingestion_ready": sdk.metrics.gauge(
                "connector_ingestion_jobs_ready",
                "Connector ingestion attempts that reached ready.",
            ),
            "ingestion_failed": sdk.metrics.gauge(
                "connector_ingestion_jobs_failed",
                "Connector ingestion attempts that failed.",
            ),
            "ingestion_graph_write": sdk.metrics.gauge(
                "connector_ingestion_graph_write_seconds_last",
                "Duration of the latest connector graph chunk write.",
            ),
            "parallel_extraction_queue": sdk.metrics.gauge(
                "connector_ingestion_parallel_extraction_queue_entries",
                "Entries retained in the partition extraction stream.",
            ),
            "parallel_extraction_pending": sdk.metrics.gauge(
                "connector_ingestion_parallel_extraction_pending",
                "Unacknowledged partition extraction deliveries.",
            ),
            "parallel_extraction_workers": sdk.metrics.gauge(
                "connector_ingestion_parallel_extraction_workers",
                "Parallel extraction workers with a current heartbeat.",
            ),
            "parallel_graph_queue": sdk.metrics.gauge(
                "connector_ingestion_parallel_graph_queue_entries",
                "Entries retained in the graph-write stream.",
            ),
            "parallel_graph_pending": sdk.metrics.gauge(
                "connector_ingestion_parallel_graph_pending",
                "Unacknowledged graph-write deliveries.",
            ),
            "parallel_graph_writers": sdk.metrics.gauge(
                "connector_ingestion_parallel_graph_writers_active",
                "Graph writers currently holding a durable batch lease.",
            ),
            "parallel_partitions_pending": sdk.metrics.gauge(
                "connector_ingestion_partitions_pending",
                "Partitions waiting to be extracted.",
            ),
            "parallel_partitions_active": sdk.metrics.gauge(
                "connector_ingestion_partitions_active",
                "Partitions currently leased by extraction workers.",
            ),
            "parallel_partitions_failed": sdk.metrics.gauge(
                "connector_ingestion_partitions_failed",
                "Partitions in a failed or exhausted state.",
            ),
            "parallel_partition_expired": sdk.metrics.gauge(
                "connector_ingestion_partition_expired_leases",
                "Non-terminal partitions with an expired extraction lease.",
            ),
            "parallel_batches_staged": sdk.metrics.gauge(
                "connector_ingestion_stage_batches_staged",
                "Durable batches waiting to be written to the graph.",
            ),
            "parallel_batches_failed": sdk.metrics.gauge(
                "connector_ingestion_stage_batches_failed",
                "Durable graph batches in a failed or exhausted state.",
            ),
            "parallel_batch_expired": sdk.metrics.gauge(
                "connector_ingestion_stage_batch_expired_leases",
                "Non-terminal graph batches with an expired writer lease.",
            ),
            "parallel_staged_bytes": sdk.metrics.gauge(
                "connector_ingestion_staged_bytes",
                "Bytes retained by non-terminal staged graph batches.",
            ),
        }
        request.app.state.knowledge_graph_metrics = collectors

    redis = Redis.from_url(get_settings().redis_url)
    try:
        collectors["queue"].set(await redis.xlen(STREAM))
        collectors["pending"].set(await _stream_pending(redis, STREAM, GROUP))
        collectors["workers"].set(await _count_scan_keys(redis, f"{HEALTH_PREFIX}*"))
        build_metrics = await redis.hgetall(METRICS_KEY)
        decoded_metrics = {
            (key.decode() if isinstance(key, bytes) else str(key)): float(
                value.decode() if isinstance(value, bytes) else value
            )
            for key, value in build_metrics.items()
        }
        for field in (
            "builds_completed",
            "builds_failed",
            "build_retries",
            "builds_exhausted",
        ):
            collectors[field].set(decoded_metrics.get(field, 0))
        collectors["build_duration_last"].set(decoded_metrics.get("build_duration_seconds_last", 0))
        collectors["ingestion_queue"].set(await redis.xlen(INGESTION_STREAM))
        collectors["ingestion_pending"].set(
            await _stream_pending(redis, INGESTION_STREAM, INGESTION_GROUP)
        )
        ingestion_workers = await _count_scan_keys(redis, f"{INGESTION_HEALTH_PREFIX}*")
        collectors["ingestion_workers"].set(ingestion_workers)
        collectors["ingestion_capacity"].set(ingestion_workers)
        collectors["parallel_extraction_queue"].set(await redis.xlen(EXTRACTION_STREAM))
        collectors["parallel_extraction_pending"].set(
            await _stream_pending(redis, EXTRACTION_STREAM, EXTRACTION_GROUP)
        )
        collectors["parallel_extraction_workers"].set(
            await _count_scan_keys(redis, f"{EXTRACTION_HEALTH_PREFIX}*")
        )
        collectors["parallel_graph_queue"].set(await redis.xlen(GRAPH_WRITE_STREAM))
        collectors["parallel_graph_pending"].set(
            await _stream_pending(redis, GRAPH_WRITE_STREAM, GRAPH_WRITE_GROUP)
        )
        ingestion_metrics = await redis.hgetall(INGESTION_METRICS_KEY)
        decoded_ingestion_metrics = {
            (key.decode() if isinstance(key, bytes) else str(key)): float(
                value.decode() if isinstance(value, bytes) else value
            )
            for key, value in ingestion_metrics.items()
        }
        collectors["ingestion_graph_write"].set(
            decoded_ingestion_metrics.get("graph_write_seconds_last", 0)
        )
    finally:
        await redis.aclose()

    async with db_session() as session:
        current = await KnowledgeGraphSnapshotRepository(session).get_current("default")
        row = (
            await session.execute(
                text(
                    "SELECT "
                    "COALESCE(EXTRACT(EPOCH FROM (CURRENT_TIMESTAMP - "
                    "(MIN(created_at) FILTER (WHERE state = 'queued')))), 0), "
                    "COUNT(*) FILTER (WHERE lease_expires_at < CURRENT_TIMESTAMP "
                    "AND state NOT IN ('ready', 'failed', 'cancelled')), "
                    "COUNT(*) FILTER (WHERE lease_owner IS NOT NULL "
                    "AND state NOT IN ('ready', 'failed', 'cancelled')), "
                    "COUNT(*) FILTER (WHERE state = 'ready'), "
                    "COUNT(*) FILTER (WHERE state = 'failed') "
                    "FROM connector_ingestion_jobs"
                )
            )
        ).one()
        collectors["ingestion_oldest"].set(float(row[0] or 0))
        collectors["ingestion_expired"].set(int(row[1] or 0))
        collectors["ingestion_running"].set(int(row[2] or 0))
        collectors["ingestion_ready"].set(int(row[3] or 0))
        collectors["ingestion_failed"].set(int(row[4] or 0))
        partition_row = (
            await session.execute(
                text(
                    "SELECT "
                    "COUNT(*) FILTER (WHERE state IN ('pending', 'retry')), "
                    "COUNT(*) FILTER (WHERE state IN ('claimed', 'extracting')), "
                    "COUNT(*) FILTER (WHERE state = 'failed'), "
                    "COUNT(*) FILTER (WHERE lease_expires_at < CURRENT_TIMESTAMP "
                    "AND state NOT IN "
                    "('committed', 'failed', 'cancelled', 'superseded')) "
                    "FROM connector_ingestion_partitions"
                )
            )
        ).one()
        collectors["parallel_partitions_pending"].set(int(partition_row[0] or 0))
        collectors["parallel_partitions_active"].set(int(partition_row[1] or 0))
        collectors["parallel_partitions_failed"].set(int(partition_row[2] or 0))
        collectors["parallel_partition_expired"].set(int(partition_row[3] or 0))
        batch_row = (
            await session.execute(
                text(
                    "SELECT "
                    "COUNT(*) FILTER (WHERE state = 'staged'), "
                    "COUNT(*) FILTER (WHERE state = 'failed'), "
                    "COUNT(*) FILTER (WHERE writer_lease_expires_at < CURRENT_TIMESTAMP "
                    "AND state NOT IN ('committed', 'failed', 'cancelled')), "
                    "COALESCE(SUM(byte_count) FILTER "
                    "(WHERE state NOT IN ('committed', 'cancelled')), 0), "
                    "COUNT(DISTINCT writer_owner) FILTER "
                    "(WHERE writer_lease_expires_at >= CURRENT_TIMESTAMP) "
                    "FROM connector_ingestion_stage_batches"
                )
            )
        ).one()
        collectors["parallel_batches_staged"].set(int(batch_row[0] or 0))
        collectors["parallel_batches_failed"].set(int(batch_row[1] or 0))
        collectors["parallel_batch_expired"].set(int(batch_row[2] or 0))
        collectors["parallel_staged_bytes"].set(int(batch_row[3] or 0))
        collectors["parallel_graph_writers"].set(int(batch_row[4] or 0))
    if current:
        collectors["points"].set(current.point_count)
        collectors["links"].set(current.link_count)
        collectors["bytes"].set(current.points_bytes + current.links_bytes)
        if current.completed_at:
            completed_at = current.completed_at
            if completed_at.tzinfo is None:
                completed_at = completed_at.replace(tzinfo=UTC)
            collectors["age"].set(max(0, (datetime.now(UTC) - completed_at).total_seconds()))
    return Response(content=sdk.metrics.render(), media_type=PROMETHEUS_CONTENT_TYPE)
