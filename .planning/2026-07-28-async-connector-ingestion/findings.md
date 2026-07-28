# Findings: Asynchronous connector ingestion

## User requirement

- A large public Git repository caused `POST /providers/git/sync` to return an Nginx `504 Gateway Time-out`.
- Ingestion continued in the background after the response failed.
- The deployed system became unresponsive while that work continued.
- The requested deliverable for this phase is an implementation plan, not runtime changes.

## Confirmed current implementation

- `legacy/src/legacy_ecms/api/routes/providers.py::sync_git_repository` performs authentication, discovery, clone/fetch, scanning, extraction, graph persistence and snapshot handoff before returning.
- The FastAPI route accepts `BackgroundTasks` but never schedules work through it.
- The frontend `CollaborationPanel.handleConnect` waits on the entire `/providers/git/sync` response and classifies a non-2xx/HTML timeout as connection failure.
- Nginx allows `/providers/` to wait 600 seconds, after which it returns 504.
- Git commands are executed with `subprocess.run` and no timeout. The `TimeoutExpired` handler in the route is therefore ineffective for normal clone/fetch calls.
- File collection and commit collection each return full lists. The route then creates a full UKO list.
- `PipelineOrchestrator.process_batch` builds source and derived episode lists for the entire ingestion before graph persistence completes.
- `GraphClient.add_episodes_raw_batch` groups records into 200-item queues, but `_flush_raw_batch` still executes a separate graph query for each node and each relationship.
- The backend entry point launches one Uvicorn process with no worker count.
- The Knowledge Graph snapshot pipeline already uses Redis Streams, a dedicated worker, heartbeat, recovery and immutable snapshot activation patterns that can inform—but should not be coupled to—the connector worker.

## Root cause

The 504 is a symptom of coupling a long-running, resource-intensive ingestion lifecycle to an HTTP request and the main API process. Extending proxy timeouts cannot provide isolation, cancellation, durability, progress, or recovery.

## Architectural direction

- PostgreSQL-backed ingestion job state.
- Redis Streams durable queue.
- Dedicated connector ingestion worker.
- Immediate `202 Accepted`.
- Bounded Git subprocesses and repository limits.
- Streaming/checkpointed extraction.
- Genuine FalkorDB batches and revision-scoped finalization.
- One snapshot request after successful graph finalization.
- Frontend progress, cancellation, retry and reload-safe state.

## Production acceptance findings

- The initial worker volume mounted a named volume over an image-owned directory,
  so the runtime UID could not create tenant directories. A root one-shot Compose
  initializer now owns the mounted directory for UID/GID 1000 before the worker starts.
- Re-ingesting the same resolved commit previously repeated all graph and snapshot
  work. The worker now compares the resolved SHA with the connection's durable last
  successful revision and completes without graph writes when unchanged.
- Repository nodes carry organization, connection and ingestion revision provenance.
  This supports bounded removal of paths absent from the newest successful revision
  immediately before snapshot publication.
- The local repeated-ingestion proof reached READY in 4.59 seconds with zero files,
  zero nodes and no increase in snapshot rows (4 before and after).
- The bounded OpenClaw run reached 11,110 files and 53,974 nodes without service
  starvation, then deterministically failed because `large-noisy.webp` was treated
  as UTF-8 using replacement decoding. Its binary/control content produced a
  FalkorDB `Failed to parse query parameter 'rows' value` error. The scanner now
  excludes WebP and rejects NUL-containing or invalid UTF-8 payloads regardless of
  extension.

## Out of scope for the planning turn

- Killing the currently running production ingestion.
- Modifying application runtime code.
- Selecting final numeric limits without benchmark evidence.
- Removing legacy compatibility before the asynchronous path is qualified.
