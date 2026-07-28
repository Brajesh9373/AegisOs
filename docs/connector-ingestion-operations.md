# Connector ingestion operations

## Emergency submission rollback

Set `ECMS_CONNECTOR_INGESTION_ENABLED=false` on the backend and recreate only the
backend service. New submissions return the stable
`CONNECTOR_INGESTION_DISABLED` error with HTTP 503. Existing job records, the
worker queue, and the last ready graph snapshot are retained. Stop or scale the
connector ingestion worker separately only when existing work must also pause.

Connector ingestion is asynchronous. The API records a durable job and publishes its
identifier to Redis Streams; `connector-ingestion-worker` performs repository
acquisition, extraction, graph publication, and snapshot handoff. A proxy timeout or
browser disconnect must not affect a running job.

## Deployment

Apply database migrations before enabling asynchronous submissions, then start the API,
ingestion worker, and snapshot worker:

```bash
docker compose -f docker/docker-compose.prod.yml up -d --build backend connector-ingestion-worker knowledge-snapshot-worker
docker compose -f docker/docker-compose.prod.yml ps
```

Start with one ingestion worker. Increase replicas only after FalkorDB write latency and
worker memory have been qualified:

```bash
docker compose -f docker/docker-compose.prod.yml up -d --scale connector-ingestion-worker=2
```

Keep the worker repository volume mounted. Its temporary acquisitions and checkpoints
are isolated from the API process. Configure CPU and memory limits through
`ECMS_CONNECTOR_INGESTION_CPU_LIMIT` and
`ECMS_CONNECTOR_INGESTION_MEMORY_LIMIT`.

## User-visible lifecycle

`QUEUED → VALIDATING → CLONING → SCANNING → EXTRACTING → WRITING →
SNAPSHOTTING → READY`

`FAILED` and `CANCELLED` are terminal. `CANCEL_REQUESTED` means the worker is stopping a
Git subprocess or finishing the current safe chunk. The previous ready graph stays
available until a new revision and snapshot are finalized.

## Triage

1. Confirm the API remains healthy; never increase the reverse-proxy timeout as a fix.
2. Check worker health and recent correlated logs:

   ```bash
   docker compose -f docker/docker-compose.prod.yml ps connector-ingestion-worker
   docker compose -f docker/docker-compose.prod.yml logs --tail=200 connector-ingestion-worker
   ```

3. Inspect the job through `GET /api/connector-ingestions/{job_id}`. Record its state,
   stage, attempt, lease expiry, checkpoint, and safe error code.
4. For old queued jobs, confirm Redis health and that at least one worker heartbeat is
   current.
5. For expired leases, restart the worker. The replacement claims abandoned work after
   lease expiry and resumes or retries from a safe checkpoint.
6. For repeated graph-write failures, inspect FalkorDB latency and capacity before
   retrying. A partial revision must not be promoted.
7. Use the cancellation endpoint for runaway jobs. Do not remove temporary repositories
   while their worker lease is live.

## Alerts

- `ConnectorIngestionWorkerMissing`: restore a worker before accepting more jobs.
- `ConnectorIngestionQueueOldestJobStale`: check worker capacity, leases, and Redis.
- `ConnectorIngestionLeaseExpired`: restart or replace the failed worker.
- `ConnectorIngestionFailuresElevated`: group failures by safe error classification.
- `ConnectorIngestionWorkerSaturated`: validate resource headroom before scaling.
- `ConnectorIngestionGraphBackpressure`: reduce concurrency and inspect FalkorDB.

## Rollback

Disable new asynchronous submissions with the feature flag, but leave PostgreSQL job
records, Redis data, and the last ready graph intact. Allow running jobs to finish or
cancel them through the API. Do not restore the old request-bound ingestion path.

Credentials must never appear in job payloads, status responses, logs, or connection
metadata. Rotate any credential that appears in proxy or worker output.

## Partitioned ingestion rollout

The partitioned implementation is a second execution path, not permission to scale the
existing `connector-ingestion-worker` without bounds. Keep
`ECMS_CONNECTOR_PARALLEL_INGESTION_ENABLED=false` until every rollout gate below passes.
With the flag off, production behavior remains the qualified single-worker flow.

### Runtime controls

| Variable | Safe initial value | Purpose |
| --- | ---: | --- |
| `ECMS_CONNECTOR_PARALLEL_INGESTION_ENABLED` | `false` | Routes new jobs to the partitioned coordinator only when explicitly enabled. |
| `ECMS_CONNECTOR_EXTRACTION_WORKER_COUNT` | `4` | Desired extraction fan-out; this does not increase graph-write concurrency. |
| `ECMS_CONNECTOR_GRAPH_WRITER_CONCURRENCY` | `1` | Global graph-write ceiling. Keep at one until FalkorDB has been load-qualified. |
| `ECMS_CONNECTOR_INGESTION_PARTITION_TARGET_FILES` | `100` | Approximate partition size used by deterministic weighted partitioning. |
| `ECMS_CONNECTOR_INGESTION_MAX_ACTIVE_PARTITIONS_PER_ORG` | `8` | Fairness and resource ceiling for one organization. |
| `ECMS_CONNECTOR_INGESTION_MAX_STAGED_BYTES_PER_ORG` | `10737418240` | Backpressure threshold for durable staged output (10 GiB). |

`ECMS_CONNECTOR_EXTRACTION_WORKER_COUNT` is both the planned extraction-lane count and
the required extractor replica count. Compose cannot expand an environment variable into
replicas, so operators must pass the same number explicitly with `--scale`. The
qualified topology requires exactly one graph writer.

### Exact enable procedure

The `connector-ingestion-worker` service is a dispatcher and is the **only** consumer of
the parent stream. At startup it selects either the legacy runtime or the parallel
coordinator from the feature flag; never deploy a separate coordinator beside it.

```bash
export ECMS_CONNECTOR_PARALLEL_INGESTION_ENABLED=true
export ECMS_CONNECTOR_EXTRACTION_WORKER_COUNT=4
export ECMS_CONNECTOR_GRAPH_WRITER_CONCURRENCY=1

docker compose --profile parallel-ingestion \
  -f docker/docker-compose.prod.yml up -d --build \
  --scale connector-ingestion-extractor=4 \
  connector-ingestion-worker connector-ingestion-extractor \
  connector-ingestion-graph-writer knowledge-snapshot-worker
```

Verify one parent dispatcher, four healthy extractors, and one healthy graph writer.
Changing the mode requires recreating `connector-ingestion-worker`; the dispatcher reads
the flag once at startup. The parallel child services use a Compose profile, so a normal
deployment with the default false flag neither creates them nor causes dormant
restart-loops.

### Rollout gates

1. Apply the partition schema migration while the feature flag is off.
2. Verify single-worker submissions still reach `READY` and the previous ready snapshot
   remains readable during ingestion.
3. Run shadow manifest creation and prove deterministic, complete, non-overlapping
   partition coverage without publishing graph changes.
4. Qualify one repository with one extractor and one graph writer.
5. Repeat with four extractors and one graph writer; verify API p95, Redis backlog,
   staging growth, worker RSS, FalkorDB write latency, and final graph counts.
6. Test extractor termination, stale-lease reclaim, retry exhaustion, cancellation, and
   coordinator restart. A failed partition must not publish a partial graph revision.
7. Enable the partitioned path for an internal organization or allowlisted connection
   before broader rollout.

### Scaling rules

- Scale extraction from one to four only when extraction is the measured bottleneck.
- Never scale graph writers from queue depth alone. Increase above one only after
  concurrent-write load tests prove FalkorDB latency and memory remain within budget.
- Reduce or pause extraction when staged bytes approach the organization limit or graph
  write latency breaches its alert threshold.
- Keep repository acquisition clone-once. All extractors read the immutable resolved
  revision and must not mutate the shared checkout.
- Keep Redis messages identifier-only; manifests, credentials, staged payloads, and
  errors belong in durable storage.

### Parallel-path rollback

Set `ECMS_CONNECTOR_PARALLEL_INGESTION_ENABLED=false`, stop the two profile-gated child
services after active work is reconciled, and recreate the parent dispatcher:

```bash
docker compose -f docker/docker-compose.prod.yml stop \
  connector-ingestion-extractor connector-ingestion-graph-writer
docker compose -f docker/docker-compose.prod.yml up -d --force-recreate \
  connector-ingestion-worker
```

This sends only *new* jobs through the
single-worker path. Let active partitioned jobs finish, or cancel them through the API;
do not delete their manifests or staged output while leases are active. Confirm the last
ready snapshot remains served, then drain partition and graph-write streams according to
the incident runbook. Re-enabling requires reconciliation of all parent, partition, and
staged-batch states.

### Parallel-path observability

The backend `/metrics` endpoint exports the parent-job metrics plus these
partition-specific signals:

| Signal | Operational meaning |
| --- | --- |
| `ecms_connector_ingestion_parallel_extraction_workers` | Extractor heartbeat count. A queued partition with zero workers is not healthy. |
| `ecms_connector_ingestion_parallel_extraction_pending` | Delivered extraction messages awaiting acknowledgement. |
| `ecms_connector_ingestion_partitions_pending` | Durable partitions waiting for extraction, including retries. |
| `ecms_connector_ingestion_partitions_active` | Claimed or extracting partitions. |
| `ecms_connector_ingestion_partition_expired_leases` | Extraction work eligible for recovery. |
| `ecms_connector_ingestion_parallel_graph_pending` | Delivered graph-write messages awaiting acknowledgement. |
| `ecms_connector_ingestion_stage_batches_staged` | Durable batches waiting for graph publication. |
| `ecms_connector_ingestion_parallel_graph_writers_active` | Distinct writers holding an unexpired durable batch lease. |
| `ecms_connector_ingestion_stage_batch_expired_leases` | Graph batches eligible for writer recovery. |
| `ecms_connector_ingestion_staged_bytes` | Non-committed staged payload pressure. |

Redis stream length is a retained-entry diagnostic, not backlog: acknowledged entries
can remain in a stream. Use durable pending partition/batch counts and consumer-group
pending counts to determine whether work is draining.

The initial staging alert is fixed at 8 GiB, below the safe 10 GiB per-organization
default. If the configured organization limit changes, update the Prometheus threshold
to preserve at least 20 percent intervention headroom.

### Parallel-path incident triage

1. Determine the bottleneck from durable state: pending partitions indicate extraction
   pressure; staged batches indicate graph-write pressure.
2. If extractor heartbeats are zero, restore extractor processes before reclaiming
   expired partitions. Do not manually acknowledge their Redis messages.
3. If staged batches grow while a writer lease remains active, inspect FalkorDB latency,
   Redis health, and writer logs. Do not add graph writers as the first response.
4. If a lease expires, allow the normal stale-delivery and durable-lease recovery path
   to claim it. A staged batch checksum makes replay idempotent.
5. If staging exceeds the warning threshold, pause or scale down extraction. Preserve
   staged objects until database state and graph publication have been reconciled.
6. For failed partitions or batches, retry only the failed unit after confirming its
   parent job is not cancelled or superseded.

After recovery, verify that all manifest partitions are represented exactly once, all
staged batches are committed, the parent reached its terminal ready state, and only one
snapshot was published for the resolved revision.

### Staged-object retention

Committed staged objects are retained for seven days by default
(`ECMS_CONNECTOR_INGESTION_STAGED_RETENTION_DAYS`). Failed, staged, and writing objects
are never automatically deleted because they may be required for recovery. Preview the
bounded cleanup set first, then execute it from the current backend image:

```bash
docker compose -f docker/docker-compose.prod.yml run --rm backend \
  python -m ecms.connectors.ingestion.staging_cleanup
docker compose -f docker/docker-compose.prod.yml run --rm backend \
  python -m ecms.connectors.ingestion.staging_cleanup --execute --limit 1000
```

The command retains PostgreSQL audit metadata and deletes only object payloads whose
batch is committed and older than the configured retention period. Schedule the
executable externally (for example, a daily Kubernetes CronJob) only after the dry-run
count has been monitored.
