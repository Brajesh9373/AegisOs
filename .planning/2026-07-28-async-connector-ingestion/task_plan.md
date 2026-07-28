# Task Plan: Production-grade asynchronous connector ingestion

## Goal

Replace request-bound Git ingestion with a durable, observable, cancellable Redis Streams worker pipeline that keeps the API responsive, processes large repositories incrementally, and activates a Knowledge Graph snapshot only after a successful ingestion.

## Current Phase

Core Phases 1–8 are implemented and locally qualified. Phase 9 representative
large-repository load, soak and dependency-interruption testing remains before a
broad production rollout.

## Non-negotiable outcomes

- `POST /providers/git/sync` no longer performs clone, extraction, graph writes, or snapshot work inline.
- Connector submission returns `202 Accepted` with a durable `connection_id` and `job_id` in under two seconds under normal database/Redis conditions.
- A large or stalled repository cannot block the API, other connectors, or Knowledge Graph reads.
- Job state survives browser disconnects, API restarts, and worker restarts.
- Duplicate submissions for the same organization/repository/branch are coalesced.
- Every long-running stage has bounded resource use, timeout, cancellation, progress, and retry behavior.
- Existing ready graph/snapshot remains available during a new or failed sync.
- Kafka is not introduced; Redis Streams is the durable queue.

## Target state machine

`QUEUED → VALIDATING → CLONING → SCANNING → EXTRACTING → WRITING → SNAPSHOTTING → READY`

Terminal/side states: `FAILED`, `CANCEL_REQUESTED`, `CANCELLED`, `RETRYING`.

## Phases

### Phase 1: Durable ingestion domain and database migration

- Add `connector_ingestion_jobs` with job ID, organization/workspace, connector ID, repository identity, requested revision, state, stage, progress counters, lease owner/expiry, attempts, checkpoint, error classification, timestamps, and cancellation flag.
- Extend the connection record with synchronization state, current job ID, last successful revision, last successful snapshot version, and last error summary.
- Define legal state transitions and terminal-state invariants in one service.
- Add uniqueness/idempotency rules for one active job per organization + normalized repository + branch.
- Store credentials by secret reference or encrypted connector configuration; never place access tokens in queue messages, logs, errors, or progress payloads.
- Add repository and service tests for transitions, idempotency, cancellation, and recovery.
- **Exit criteria:** migration upgrades and downgrades cleanly; illegal transitions fail; duplicate active submissions return the existing job.
- **Status:** complete

### Phase 2: Submission and status API contract

- Introduce an application-owned connector ingestion API instead of adding more behavior to the legacy route.
- Make submission validate syntax, authorization, repository scope, and queue availability only.
- Return `202 Accepted` containing `connection_id`, `job_id`, `status`, and status URL.
- Add endpoints to retrieve job state/progress, request cancellation, and retry a terminal failed job.
- Preserve compatibility by changing `/providers/git/sync` into a thin adapter that submits a job and returns `202`; remove synchronous response assumptions.
- Use stable machine-readable error codes; never return HTML proxy bodies or Python tracebacks to the frontend.
- Add API contract, authorization, Redis-unavailable, and idempotency tests.
- **Exit criteria:** request latency remains bounded and no clone/extraction code runs in an API process.
- **Status:** complete

### Phase 3: Redis Streams queue and dedicated ingestion worker

- Create a separate Redis stream and consumer group for connector ingestion, reusing the proven queue/lease patterns from the snapshot worker without coupling the two job types.
- Add a dedicated `connector-ingestion-worker` process/container built from the backend image.
- Implement database lease acquisition, heartbeat, bounded retry with jitter, dead-letter/terminal failure handling, and abandoned-job claiming.
- Enforce global worker concurrency and one active ingestion per repository; start conservatively at one job per worker.
- Add graceful shutdown that stops accepting work, requests subprocess termination, saves the last safe checkpoint, and releases/lets the lease expire.
- Configure CPU/memory limits and health checks independently from the API and snapshot worker.
- **Exit criteria:** killing a worker mid-job does not block the API and a replacement either resumes from a safe checkpoint or retries deterministically.
- **Status:** complete

### Phase 4: Bounded and cancellable Git acquisition

- Replace unbounded `subprocess.run` operations with a managed subprocess abstraction supporting explicit clone/fetch timeout, cancellation, process-group termination, sanitized output, and structured errors.
- Use a temporary clone/worktree and atomically promote it after successful acquisition so an interrupted clone cannot become the active repository.
- Default to partial/shallow acquisition where compatible; make history depth configurable.
- Record resolved commit SHA before scanning and use it as the immutable ingestion revision.
- Implement fetch/update behavior based on the last successful SHA instead of reprocessing unchanged repositories.
- Define safe repository limits: clone bytes/time, file count, commit count, and checkout size.
- **Exit criteria:** timeout/cancel terminates Git, leaves no active child process, and cannot corrupt the last successful clone.
- **Status:** complete (current-tree shallow acquisition; optimized SHA-delta fetch is deferred)

### Phase 5: Streaming scanner and incremental extraction

- Convert file and commit collection from full in-memory lists to iterators/async streams.
- Apply explicit exclusions for VCS metadata, dependency/vendor folders, build output, generated artifacts, caches, binaries, and unsupported extensions.
- Add configurable maximum file size and safe text detection.
- Process deterministic chunks and persist stage checkpoints/counters after each chunk.
- Separate current-tree ingestion from optional commit-history ingestion; do not make full history the default.
- Skip unchanged files using revision/path/content fingerprints and mark removed files deterministically.
- Bound extraction concurrency and periodically yield so cancellation and heartbeat checks remain responsive.
- **Exit criteria:** memory remains bounded as repository size grows and restart does not repeat completed chunks unnecessarily.
- **Status:** complete (bounded current-tree streaming; cross-revision fingerprint skipping is deferred)

### Phase 6: Genuine FalkorDB batching and safe graph publication

- Replace per-node/per-relationship round trips inside `_flush_raw_batch` with parameterized `UNWIND` node and relationship batches.
- Use bounded batch sizes selected through benchmarks, not a misleading outer list of 200 followed by individual queries.
- Write with `organization_id`, `connection_id`, and `ingestion_revision` provenance on every owned node/edge.
- Stage or revision-tag writes so failed ingestion does not replace the last successful connection revision.
- Finalize the revision atomically, then remove/retire stale nodes from the previous revision in bounded cleanup work.
- Apply backpressure based on FalkorDB latency/errors and keep graph write concurrency conservative.
- Add duplicate, retry, partial-write, and multi-organization isolation tests.
- **Exit criteria:** retry is idempotent, partial failure preserves the last ready revision, and query count scales with chunks rather than nodes.
- **Status:** complete for snapshot publication (revision-tagged batches; raw-graph stale cleanup remains follow-up)

### Phase 7: Snapshot handoff and frontend progress experience

- Enqueue exactly one coalesced Knowledge Graph snapshot after graph revision finalization, not during intermediate chunks.
- Track `SNAPSHOTTING` until the snapshot worker activates the new version; do not report `READY` prematurely.
- Update Administration Tools UI to show queued/running stages, progress counters, elapsed time, cancel, retry, and last error.
- Allow the drawer/page to close while work continues; reload state from the status API.
- Treat `202` as accepted/syncing, not connected or failed.
- Show the previous ready graph while synchronization runs, with a non-blocking freshness notice.
- Use polling initially with backoff and visibility awareness; add SSE only if polling load proves material.
- **Exit criteria:** a user can navigate elsewhere during ingestion and later see accurate progress/result without relying on the original HTTP request.
- **Status:** complete

### Phase 8: Operational controls, deployment, and compatibility rollout

- Add metrics for queue depth, stage duration, files/commits processed, graph write throughput, failures by classification, retries, cancellations, lease age, and worker saturation.
- Add structured logs correlated by organization, connection, job, and revision, with credential redaction tests.
- Add alerts for no active workers, old leases, queue age, repeated failures, and FalkorDB backpressure.
- Add production Compose service, health check, resource limits, environment defaults, and runbook.
- Roll out behind an async-ingestion feature flag: deploy schema/worker first, enable submission for administrators, then make it default.
- Keep a short-lived compatibility adapter for legacy clients; do not keep the old synchronous execution path.
- **Exit criteria:** rollback disables new submissions without deleting jobs or the last ready graph; operators can diagnose and recover stuck jobs.
- **Status:** complete (administrator path is the async cutover; private-repository secret storage is deferred)

### Phase 9: Qualification and production acceptance

- Unit-test state transitions, queue semantics, Git cancellation, scanners, checkpoints, batching, and redaction.
- Integration-test PostgreSQL + Redis + FalkorDB + object storage with worker interruption and dependency outages.
- Browser-test asynchronous submission, navigation during sync, progress reload, cancellation, failure, retry, and final graph refresh.
- Load-test API responsiveness while ingesting a representative large repository.
- Soak-test repeated incremental updates and verify no node/edge duplication or unbounded storage growth.
- Validate recovery from API restart, worker restart, Redis interruption, FalkorDB interruption, snapshot failure, and client disconnect.
- **Acceptance targets:**
  - Submission p95 under 2 seconds.
  - Health/auth/read endpoints remain within agreed latency during ingestion.
  - No ingestion work survives cancellation beyond the bounded termination window.
  - Worker peak memory stays within its configured limit on the qualification repository.
  - One job produces one finalized graph revision and one coalesced snapshot request.
- **Status:** in_progress (focused and real small-repository E2E passed; large-repository soak/fault matrix remains)

## Implementation order and release boundaries

1. Phases 1–3 establish durability and isolation before optimizing ingestion.
2. Phases 4–6 replace unsafe processing and writing inside the new worker.
3. Phase 7 exposes the asynchronous lifecycle to users.
4. Phase 8 deploys behind a feature flag with rollback.
5. Phase 9 is mandatory before removing the compatibility adapter.

Do not route production requests to the worker until Phases 1–6 pass integration tests. Do not enable the Cosmos graph freshness handoff until Phase 7 passes end-to-end tests.

## Primary files/modules expected to change

- `backend/ecms/persistence/migrations/versions/`
- `backend/ecms/persistence/models/`
- `backend/ecms/persistence/repositories/`
- `backend/ecms/api/rest/`
- `backend/ecms/configuration/schemas/settings.py`
- `backend/ecms/visualization/snapshot_queue.py` or a shared durable-stream abstraction
- New `backend/ecms/connectors/ingestion/` package
- `legacy/src/legacy_ecms/api/routes/providers.py` compatibility adapter
- `legacy/src/legacy_ecms/providers/git/provider.py`
- `legacy/src/legacy_ecms/pipeline/orchestrator.py`
- `legacy/src/legacy_ecms/core/graph.py`
- `frontend/apps/web/src/components/CollaborationPanel.tsx`
- `docker/docker-compose.yml`
- `docker/docker-compose.prod.yml`
- Prometheus/Grafana configuration and a connector-ingestion runbook

## Decisions made

| Decision | Rationale |
|---|---|
| Redis Streams, not Kafka | Redis already exists and the snapshot pipeline proves the operational model. |
| Dedicated ingestion worker | Prevents repository workload from starving the API process. |
| PostgreSQL is job-state authority | Durable state, querying, authorization and recovery should not depend solely on queue retention. |
| Return `202` immediately | HTTP connection lifetime must not equal ingestion lifetime. |
| Polling first | Simpler and reliable; SSE can be added based on measured need. |
| Incremental, revision-scoped graph writes | Retries and failures must not damage the last ready graph. |
| Full commit history is opt-in | It is expensive and not required for an initial useful knowledge graph. |
| Optimize graph writes with real batches | The existing batch wrapper still performs per-item round trips. |

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Partially written graph revision | Revision tagging plus atomic finalization and last-ready preservation. |
| Duplicate jobs/writes | Active-job uniqueness, idempotency key, deterministic IDs and revision-scoped upserts. |
| Worker death | Lease heartbeat, abandoned-job claim and durable checkpoints. |
| Large repository resource exhaustion | Limits, partial clone, streaming, bounded chunks and container resources. |
| Token leakage | Secret references/encryption, redaction tests and no credentials in Redis payloads. |
| FalkorDB contention | Genuine batching, conservative concurrency and latency-based backpressure. |
| Snapshot reflects partial data | Snapshot enqueue only after graph revision finalization. |
| Risky cutover | Feature flag, compatibility adapter and staged cohort rollout. |

## Errors encountered

| Error | Attempt | Resolution |
|---|---:|---|
| Nginx returns 504 while ingestion continues | Existing production behavior | Root cause recorded; plan replaces request-bound execution rather than increasing timeouts. |
| Legacy test environment could not import its historical `ecms` package | 1 | Moved the new batching test to backend tests and supplied the actual `legacy/src` PYTHONPATH. |
| Default uv cache path was inaccessible in the managed workspace | 1 | Used the repository-local `backend/.uv-cache`. |
| Local checkpoint rewind SQL escaped JSON incorrectly | 1 | Replaced the quoted JSON literal with PostgreSQL `jsonb_build_object`; update succeeded. |
