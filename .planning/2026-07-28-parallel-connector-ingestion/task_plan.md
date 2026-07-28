# Task Plan: Partitioned Parallel Connector Ingestion

## Goal

Reduce large-repository ingestion time by parallelizing deterministic file
extraction across multiple workers while preserving one authoritative repository
job, bounded FalkorDB writes, exact recovery, cancellation, tenant isolation, and
single-snapshot publication.

## Current phase

Implementation is in progress. Durable partition state, immutable manifest
partitioning, identifier-only Redis transport, and feature-flagged compatibility
controls are being built in parallel.

## Core architecture

```text
Repository ingestion job
        |
        v
Coordinator: clone once, resolve SHA, create immutable manifest
        |
        +--> Partition 1 --> extraction worker --+
        +--> Partition 2 --> extraction worker --+
        +--> Partition 3 --> extraction worker --+--> staged graph batches
        +--> Partition 4 --> extraction worker --+
                                                 |
                                      bounded graph-writer queue
                                                 |
                                      one graph publication revision
                                                 |
                                      one immutable snapshot
```

The repository job owns lifecycle and publication. Child partitions own only a
deterministic slice of the immutable manifest. Extraction workers never finalize
the repository and never write snapshots.

## Non-negotiable invariants

- A file belongs to exactly one partition for a specific repository revision.
- One coordinator owns the parent job lease.
- Extraction retries are idempotent by `job_id + revision + relative_path`.
- Multiple workers never update the same partition concurrently under valid leases.
- FalkorDB write concurrency is globally bounded independently from extraction count.
- Partial extraction or graph failure cannot activate a snapshot.
- The last ready snapshot remains readable until the new revision is complete.
- Cancellation propagates to coordinator, partitions, Git subprocesses, staged
  graph batches and snapshot handoff.
- Queue messages contain identifiers only; credentials remain outside Redis.
- Autoscaling improves extraction throughput without permitting unbounded graph load.
- Redis Streams and PostgreSQL remain the queue and state authorities; Kafka is not used.

## Target state model

Parent job:

`QUEUED → ACQUIRING → MANIFESTING → EXTRACTING → WRITING → FINALIZING → SNAPSHOTTING → READY`

Partition:

`PENDING → CLAIMED → EXTRACTING → STAGED → COMMITTED`

Side/terminal states:

`RETRYING`, `CANCEL_REQUESTED`, `CANCELLED`, `FAILED`, `SUPERSEDED`.

## Phase 1: Schema and durable partition domain

- Add `connector_ingestion_manifests`:
  - parent job, organization, connection, resolved revision;
  - manifest version and immutable object/path reference;
  - total files/bytes, partition count, checksum and creation timestamp.
- Add `connector_ingestion_partitions`:
  - partition ID/index, parent job and manifest version;
  - deterministic start/end boundaries or explicit file-list reference;
  - state, attempts, lease owner/expiry and cancellation flag;
  - files/bytes processed, nodes/edges staged and error classification;
  - created, started, updated and completed timestamps.
- Add `connector_ingestion_stage_batches`:
  - partition, sequence, checksum, object reference or bounded payload metadata;
  - `pending`, `committing`, `committed`, `failed` lifecycle;
  - graph-writer lease and retry counters.
- Add uniqueness constraints for:
  - one manifest per parent job/revision/version;
  - one partition index per manifest;
  - one staged batch sequence per partition;
  - one active lease owner per partition/batch.
- Extend the parent job with partition totals and aggregation counters.
- Add repositories and state services; reject illegal parent/child transitions.
- **Exit criteria:** upgrade/downgrade passes; duplicate manifest/partition creation
  is idempotent; lease recovery and tenant isolation tests pass.
- **Status:** completed

## Phase 2: Clone-once coordinator and immutable manifest

- Split the existing all-in-one worker into a repository coordinator.
- Acquire the repository once into shared read-only storage.
- Record the resolved SHA before manifest generation.
- Enumerate files using current binary, size, extension and directory safeguards.
- Persist an immutable, checksummed manifest containing:
  - relative path;
  - byte size;
  - content hash;
  - supported extractor type;
  - optional previous-revision fingerprint match.
- Detect unchanged revisions before partition creation and complete immediately.
- Skip unchanged files against the prior successful manifest where safe.
- Mark removed paths in a revision-scoped deletion set.
- Partition by weighted estimated work, not only file count:
  - byte size;
  - source type;
  - historical extraction duration;
  - JSON/AST complexity estimate.
- Publish partition IDs to a dedicated extraction Redis Stream.
- **Exit criteria:** the same revision produces the same manifest checksum and
  partition assignments; clone happens once regardless of worker count.
- **Status:** completed

## Phase 3: Parallel extraction workers

- Introduce a dedicated extraction worker process separate from graph writers.
- Each worker:
  - claims one partition and renewable PostgreSQL lease;
  - reads only its manifest slice from shared repository storage;
  - enforces file and derived-artifact ceilings;
  - extracts source/structural/semantic records in bounded chunks;
  - writes immutable staged batches rather than FalkorDB directly;
  - checkpoints only after a stage batch is durably persisted.
- Use deterministic IDs based on organization, connection, revision and path.
- Add per-partition cancellation polling and graceful subprocess/task shutdown.
- Recover abandoned partitions using Redis `XAUTOCLAIM` plus expired DB leases.
- Configure worker-local CPU and memory limits.
- Start with four extraction workers; make count configurable.
- **Exit criteria:** four workers process disjoint manifest slices; killing one
  reclaims only its partition; retries produce identical stage-batch checksums.
- **Status:** completed

## Phase 4: Durable staging and bounded graph writers

- Choose a staging representation after benchmark:
  - preferred: compressed Arrow/Parquet objects in MinIO with PostgreSQL metadata;
  - fallback: bounded PostgreSQL JSONB batches only for small payloads.
- Do not put extracted content in Redis messages.
- Add one graph-writer stream containing stage-batch IDs only.
- Graph writer:
  - claims batches in deterministic order where ordering matters;
  - validates checksum and revision ownership;
  - commits genuine bounded `UNWIND` node/relationship batches;
  - records committed checksum and counters transactionally;
  - applies latency-aware delay/backpressure;
  - limits global write concurrency, initially one.
- Use an explicit distributed graph-write semaphore so scaling extraction workers
  cannot increase FalkorDB concurrency.
- Clear staged objects according to retention only after parent publication succeeds.
- **Exit criteria:** extraction concurrency can rise without increasing concurrent
  FalkorDB queries; replaying a committed batch is a no-op.
- **Status:** completed

## Phase 5: Fan-in aggregation and atomic publication

- Coordinator aggregates partition and stage-batch state from PostgreSQL.
- Parent enters `WRITING` while any staged batch remains uncommitted.
- Parent can enter `FINALIZING` only when:
  - every partition is `COMMITTED`;
  - every staged batch checksum is committed;
  - aggregate counts reconcile with partition totals;
  - no live/expired child leases remain.
- Finalization:
  - validates organization/connection/revision provenance;
  - retires stale nodes from the prior revision in bounded batches;
  - records one successful graph revision pointer;
  - emits exactly one coalesced snapshot request.
- Parent remains `SNAPSHOTTING` until the exact watermark is active.
- Failure preserves the prior ready snapshot and staged evidence for diagnosis/retry.
- **Exit criteria:** incomplete partitions cannot publish; one job produces exactly
  one graph revision and one active snapshot.
- **Status:** completed

## Phase 6: Scheduling, fairness and adaptive concurrency

- Add organization-level quotas:
  - maximum active repository jobs;
  - maximum active partitions;
  - maximum staged bytes.
- Use fair scheduling so a large repository cannot starve smaller connectors.
- Start with:
  - four extraction workers;
  - one partition per worker;
  - one graph writer globally;
  - 10–25 files per extraction batch;
  - graph batches selected by node/relationship and encoded-byte ceilings.
- Add adaptive extraction concurrency:
  - scale up when extraction queue is old and staging capacity is available;
  - scale down when staged backlog, graph latency, CPU or memory crosses thresholds.
- Pause partition claiming under FalkorDB/object-store/database backpressure.
- Never autoscale graph writers solely from queue depth.
- **Exit criteria:** small jobs meet latency targets while a large job runs; graph
  pressure automatically slows extraction before shared services become unhealthy.
- **Status:** partially implemented; quotas/backpressure complete, fair scheduling and
  adaptive autoscaling remain rollout work

## Phase 7: API and frontend aggregation

- Keep the existing parent-job API contract stable.
- Extend status payload with:
  - partitions total/running/completed/failed;
  - files total/processed;
  - extraction throughput;
  - staged/committed graph batches;
  - estimated completion time when statistically meaningful.
- Add an optional partition diagnostic endpoint restricted to administrators.
- Parent cancellation marks all non-terminal partitions and batches cancel-requested.
- Retry only failed partitions when the manifest/revision is unchanged.
- Update the Administration Tools progress card with:
  - overall progress;
  - parallel worker count;
  - extraction and graph-publication stages;
  - expandable failed-partition details.
- Persist polling state across route changes and browser reload.
- **Exit criteria:** users see one repository job, not implementation-level noise;
  operators can inspect partition failures without database access.
- **Status:** API aggregation and cancellation complete; expanded frontend partition
  diagnostics remain pending

## Phase 8: Observability, security and operations

- Metrics:
  - manifest build duration/files/bytes;
  - partition queue age and duration;
  - active extraction workers and leases;
  - extraction files/bytes/nodes per second;
  - staged bytes and oldest staged batch;
  - graph-writer queue, latency and throughput;
  - parent critical-path duration;
  - retries, cancellations and checksum failures.
- Structured correlation fields:
  `organization_id`, `connection_id`, `job_id`, `revision`, `manifest_id`,
  `partition_id`, `stage_batch_id`.
- Add alerts for:
  - missing coordinator/extraction/graph workers;
  - expired leases;
  - stalled partition;
  - staging growth;
  - graph backpressure;
  - aggregation mismatch;
  - snapshot watermark timeout.
- Validate staged content encryption/access policies and credential redaction.
- Extend the runbook with scale-up/down, stuck partition, staged cleanup, and
  rollback procedures.
- **Exit criteria:** an operator can identify the critical-path partition and safely
  recover it without replaying the whole repository.
- **Status:** completed

## Phase 9: Deployment and compatibility rollout

- Add separate Compose/Kubernetes services:
  - `connector-ingestion-coordinator`;
  - `connector-extraction-worker`;
  - `connector-graph-writer`.
- Use shared repository storage read-only for extraction workers.
- Give each service independent CPU/memory limits and health checks.
- Add feature flags:
  - parallel ingestion enabled;
  - extraction worker count;
  - graph writer concurrency;
  - tenant cohort allowlist.
- Deploy schema and dormant workers first.
- Shadow-build manifests and partitions without publication.
- Enable one internal organization, then selected large repositories.
- Keep the current single-worker path available for rollback until acceptance passes.
- Rollback stops new parallel jobs while retaining manifests, partitions, staged
  objects and the last ready snapshot.
- **Exit criteria:** feature flag can route new jobs back to the single-worker path
  without corrupting active or completed revisions.
- **Status:** completed behind disabled-by-default feature flag and Compose profile

## Phase 10: Qualification and production acceptance

- Unit tests:
  - deterministic partitioning;
  - no overlap/gaps;
  - lease acquisition/recovery;
  - checksum/idempotency;
  - cancellation propagation;
  - aggregation invariants.
- Integration tests:
  - PostgreSQL + Redis + MinIO + FalkorDB;
  - coordinator, extraction and writer restart;
  - Redis/object-store/FalkorDB interruption;
  - failed partition retry without whole-job replay.
- Load matrix using OpenClaw or an equivalent fixed revision:
  - one, two, four and eight extraction workers;
  - one and two graph writers;
  - record wall time, API p95, CPU, memory, stage backlog and graph latency.
- Soak repeated unchanged and changed revisions.
- Verify removed-file cleanup, no duplicate nodes/edges and bounded staged storage.
- Browser-test navigation/reload/cancel/retry and final graph refresh.
- **Acceptance targets:**
  - submission p95 under two seconds;
  - health/read p95 under 250 ms during ingestion;
  - four workers materially outperform one without exceeding service budgets;
  - zero manifest file overlap or omission;
  - peak memory within each container limit;
  - failed worker recovery affects only its partition;
  - graph-write concurrency never exceeds configured global limit;
  - one parent job produces one active snapshot;
  - unchanged revision completes without partition extraction.
- **Status:** static, unit, persistence, container-build and import-smoke gates pass;
  live OpenClaw load/soak matrix remains mandatory before default enablement

## Implementation order

1. Phases 1–2 establish immutable work ownership.
2. Phase 3 introduces parallel extraction without graph concurrency.
3. Phases 4–5 add staged writes and safe fan-in publication.
4. Phase 6 adds fairness and adaptive scaling.
5. Phases 7–8 expose and operate the lifecycle.
6. Phase 9 rolls out behind a reversible feature flag.
7. Phase 10 is mandatory before making parallel ingestion the default.

## Expected code areas

- `backend/ecms/persistence/migrations/versions/`
- `backend/ecms/persistence/models/`
- `backend/ecms/persistence/repositories/`
- `backend/ecms/connectors/ingestion/`
- `backend/ecms/api/rest/connector_ingestions.py`
- `backend/ecms/configuration/schemas/settings.py`
- `legacy/src/legacy_ecms/core/graph.py`
- `frontend/apps/web/src/components/CollaborationPanel.tsx`
- `docker/docker-compose.yml`
- `docker/docker-compose.prod.yml`
- `docker/prometheus/`
- `docs/connector-ingestion-operations.md`

## Key decisions

| Decision | Reason |
|---|---|
| Parallelize extraction, not unrestricted graph writes | Extraction is CPU-heavy; FalkorDB is the shared contention point. |
| Clone once | Multiple clones waste bandwidth/storage and can resolve different moving revisions. |
| Immutable manifest | Guarantees partition coverage, reproducibility and safe recovery. |
| Durable staged batches | Separates parallel CPU work from controlled graph commits. |
| One initial graph writer | Preserves API/read capacity and avoids database saturation. |
| Weighted deterministic partitions | File counts alone do not represent JSON/AST extraction cost. |
| Parent/child state machines | One user-visible job needs independently recoverable work units. |
| PostgreSQL state + Redis identifiers | Matches the current durable architecture without Kafka. |
| Feature-flagged dual path | Provides a safe rollback during qualification. |

## Principal risks

| Risk | Mitigation |
|---|---|
| Duplicate or missing files across partitions | Immutable checksummed manifest and partition coverage validation. |
| Faster extraction overwhelms FalkorDB | Durable staging, global write semaphore and backlog-based throttling. |
| Shared clone mutation | Read-only revision directory addressed by resolved SHA. |
| Worker death | Partition leases, checkpoints and idempotent staged checksums. |
| Staging storage growth | Per-tenant quotas, alerts, retention and admission control. |
| One slow partition delays publication | Weighted scheduling, work splitting before claim, critical-path metrics. |
| Cancellation races | Parent cancellation generation checked before every claim/commit. |
| Mixed software versions change partition semantics | Persist manifest/schema version and require compatible worker capability. |
