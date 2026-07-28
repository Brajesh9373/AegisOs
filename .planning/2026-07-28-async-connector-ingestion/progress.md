# Progress: Asynchronous connector ingestion

## Session: 2026-07-28

### Planning and current-system analysis

- **Status:** complete
- Traced the frontend connector submission to `/providers/git/sync`.
- Confirmed Nginx `/providers/` timeout is 600 seconds.
- Confirmed the route performs the complete ingestion before responding.
- Confirmed `BackgroundTasks` is unused.
- Confirmed Git subprocess timeout/cancellation is absent.
- Confirmed full-list file, commit, UKO and episode construction.
- Confirmed graph “batching” still issues per-node and per-relationship queries.
- Confirmed the API uses a single Uvicorn process.
- Defined a nine-phase implementation and qualification plan.

### Implementation

- **Status:** core production path complete
- Started four parallel workstreams for domain/API, worker/Git, frontend/operations,
  and graph batching/integration.
- Replaced per-node/per-relationship graph writes with parameterized `UNWIND`
  node and bounded relationship batches.
- Added organization, connection and ingestion revision provenance to graph writes.
- Added and passed the focused graph batching test.
- Added durable connector-ingestion jobs, legal lifecycle transitions, tenant-scoped
  APIs, cancellation/retry, idempotent active-job coalescing and migration 0040.
- Added the Redis Streams worker with bounded Git subprocesses, shallow acquisition,
  streaming file chunks, checkpoints, retry exhaustion, cancellation, worker
  heartbeat and renewable PostgreSQL leases.
- Retired the synchronous Git route with a machine-readable HTTP 410 response.
- Added asynchronous frontend progress with background-safe polling, cancel and retry.
- Added a dedicated worker and one-shot volume ownership initializer to development
  and production Compose.
- Added connector metrics, Prometheus alerts and an operator runbook.
- Rebuilt the backend, frontend and worker containers.

## Validation

| Check | Result |
|---|---|
| Plan addresses HTTP timeout rather than increasing it | Passed |
| API workload isolated from ingestion | Included |
| Durable state, retry, recovery and cancellation | Included |
| Redis Streams used without Kafka | Included |
| Large-repository memory and Git controls | Included |
| FalkorDB write amplification addressed | Included |
| Frontend async lifecycle addressed | Included |
| Snapshot consistency addressed | Included |
| Real FalkorDB batching unit test | Passed |
| Deployment, observability and rollback addressed | Included |
| Ruff focused regression | Passed |
| Backend focused tests | 11 passed |
| Frontend TypeScript check | Passed |
| Frontend production build | Passed |
| Development Compose validation | Passed |
| Migration 0040 applied in PostgreSQL | Passed |
| Backend/frontend/ingestion worker health | Healthy |
| Prometheus connector metrics | HTTP 200; worker, queue, lease and graph-write metrics present |
| Synchronous legacy route | HTTP 410 in under five seconds |
| Real public-repository async ingestion | Passed: queued → writing → snapshotting → ready |
| Worker-volume recovery | Initial permission failure reproduced; initializer added; retry completed |

### Production acceptance continuation

- Added revision-level incremental completion: an unchanged commit SHA is marked
  ready without rescanning, rewriting FalkorDB, or rebuilding a snapshot.
- Added bounded stale-node retirement by organization, connection and revision
  after all new chunks have committed and before snapshot publication.
- Added a worker regression proving unchanged revisions avoid graph writes.
- Worker regression suite now passes 12 tests; lint initially identified hard-coded
  temporary paths in the new test and those paths were replaced with `tmp_path`.
- OpenClaw large-repository submission returned in 52 ms. During 30 health probes,
  API p95 was 18 ms and maximum was 25 ms; backend used about 125 MiB and the
  ingestion worker about 82 MiB during clone.
- Restarted the worker deliberately during OpenClaw cloning. API health remained
  HTTP 200, the pending delivery was reclaimed after lease expiry, cloning resumed,
  and the same durable job advanced to WRITING.
- The first unbounded OpenClaw write eventually starved API and Docker operations.
  Stopped the stale worker, restarted Docker, and added explicit safeguards:
  10-file graph chunks, 0.1-second inter-chunk yielding, maximum 500 JSON artifacts
  per file, maximum JSON depth 12 and maximum 50 array items per level.
- The bounded retry remained responsive through 710 files in the first two minutes:
  health probes stayed 5–42 ms, worker memory was about 303 MiB of 2 GiB, and
  FalkorDB memory was about 148 MiB.
- Browser acceptance passed progress visibility, navigation persistence, reload
  persistence and zero browser errors.
- API restart acceptance passed: files advanced from 2,790 to 2,880 while the API
  container restarted and health returned HTTP 200.
- Hardened terminal-state handling for Redis acknowledgement outages: PostgreSQL
  READY/CANCELLED remains authoritative and the pending delivery is acknowledged
  after Redis recovery.
- The bounded run progressed to 11,110 files / 53,974 nodes before a binary WebP
  fixture exposed permissive UTF-8 replacement decoding. Added extension exclusion,
  NUL detection and strict UTF-8 decoding with a regression covering disguised
  binary text extensions and WebP.

## Reboot check

| Question | Answer |
|---|---|
| Where am I? | Core asynchronous ingestion is implemented, rebuilt and locally qualified. |
| Where am I going? | Representative large-repository load/soak and interruption testing before broad production rollout. |
| What is the goal? | Keep ECMS responsive while repositories ingest asynchronously and recoverably. |
| What have I learned? | See `findings.md`. |
| What have I done? | Implemented the isolated async path and proved a real ingestion reaches READY. |
