# Progress: Knowledge Graph V2 Planning

## 2026-07-27

- Completed read-only audit of the current Knowledge Graph frontend and legacy FalkorDB endpoint.
- Measured the live graph response and documented the current bottlenecks.
- Confirmed user requirements: universal organization graph, whole-graph canvas, no Kafka, low-risk migration.
- Researched Cosmograph/Cosmos.gl and Apache Arrow capabilities from official sources.
- Inspected existing object storage, MinIO, Redis, Docker, frontend dependencies and worker paths.
- Began scoped implementation plan; no product implementation performed.
## 2026-07-27 — Plan completed

- Created the approved architecture/design brief.
- Broke implementation into 20 risk-first, independently verifiable vertical slices.
- Made the renderer benchmark a stop/go gate before building snapshot infrastructure.
- Assigned durable state to PostgreSQL, object payloads to MinIO/S3, and job/lock duties to Redis.
- Preserved the current D3 route and renderer for controlled rollback.
- Explicitly excluded Kafka from the Knowledge Graph V2 execution path.

## 2026-07-27 — Phase 0 started

- Tagged the synchronized deployed baseline as annotated Git tag `v2`.
- Re-read the active plan and inspected current React routing, package tooling, and Knowledge graph mounting.
- Confirmed the production Administration Knowledge tab can remain on D3 while a development-only Cosmograph proof is introduced.
- Installed `@cosmograph/react@2.3.3` in the web workspace for the isolated proof.

### Installation notes

- pnpm completed successfully.
- On Windows, pnpm warned that it could not create the optional Apache Arrow `arrow2csv` executable shims because it looked for a `.EXE` variant of the package's `.cjs` script. The browser library installation itself completed; typecheck/build and runtime proof will determine whether this warning is harmless.
- Removed the Cosmograph wrapper after discovering its non-commercial license and replaced it with MIT-licensed `@cosmos.gl/graph@3.3.0`.
- Added deterministic 100k/500k/1M scale fixtures, D3 and WebGL benchmark events, downloadable browser metrics, and a localhost-only lazy WebGL proof path.
- Web typecheck and production build pass. The WebGL renderer is emitted as a separate lazy chunk and is absent from the normal initial execution path.
- Rebuilt and restarted the local frontend Docker container successfully.
- Added operator instructions for D3 baseline, current-data WebGL, and ascending synthetic-capacity runs.
- Verified the rebuilt Nginx frontend returns HTTP 200 for the application, main bundle, and lazy `CosmosGraph` chunk.
- Direct ESLint reports no errors in the changed graph files; one existing `console.error` statement remains a warning.
- Phase 0 remains open pending real browser/GPU benchmark JSON from the agreed client hardware.
- Added a repeatable Playwright benchmark runner that authenticates normally, selects Knowledge, waits for metrics, and exercises WebGL fit/zoom/pan.
- Captured D3 and WebGL current-graph headless results. D3 confirms severe DOM/main-thread cost; WebGL confirms DOM reduction, but headless software rendering is not a valid GPU capacity gate.
- Re-ran in hardware Chrome with static-by-default positioning. The current graph passed the renderer FPS/memory gate; transport remains over budget.
- Ran 100k and 500k capacity fixtures. Both missed the 30-FPS target at the default high-DPI canvas setting, so the 1M run was correctly deferred.
- Set the dense overview to pixel ratio 1 and disabled the engine's own FPS overlay. The 100k fixture then passed at 31.5 FPS; 500k remained unsupported at 7.5 FPS.
- Completed Phase 0 with a measured 100k-node/200k-edge supported capacity and moved Phase 1 into progress.

## 2026-07-28 — Phase 1 completed

- Added PostgreSQL snapshot metadata migration/model and transactional repository.
- Added deterministic versioned Arrow point/link contracts with stable indexes and static source-cluster positions.
- Added corruption, duplicate, and missing-edge-endpoint validation.
- Extended the existing MinIO/S3 abstraction with multipart file upload, object metadata, and bounded streaming.
- Added an end-to-end snapshot service that reads the established FalkorDB projection off-thread, uploads immutable objects, validates sizes, and only then activates the version.
- Improved the legacy graph endpoint so its synchronous FalkorDB work no longer blocks FastAPI's event loop.
- Six focused snapshot tests pass; changed modern-backend files pass Ruff.
- Moved Phase 2 into progress. The real manual build remains KG-07 and will be exercised through the dedicated worker/administrative trigger.

## 2026-07-28 — Phase 2 completed

- Added a Kafka-independent Redis Streams queue with organization-level coalescing and one guaranteed follow-up after changes during a build.
- Added abandoned-message recovery, bounded retries, expiring ownership locks with renewal, build timeout, and worker heartbeat.
- Added the dedicated `knowledge-snapshot-worker` Compose service and idempotent MinIO bucket initialization; Compose configuration validates.
- Added the shared `graph_changed` hook after successful Git, MySQL, and generic UKO persistence, plus graph-changing connection deletion.
- Added focused queue tests for coalescing, restart recovery, and retry exhaustion.
- Nine snapshot/queue tests pass and all changed modern snapshot modules pass Ruff.
- Moved Phase 3 into progress; the real end-to-end snapshot build will be validated through its administrator endpoint.

## 2026-07-28 — Phase 3 completed

- Added UI-session/JWT authenticated V2 manifest, immutable Arrow artifact, node metadata, and administrator rebuild routes.
- Added tenant-scoped snapshot lookup, ETags, no-store transient manifests, year-long immutable artifact caching, bounded streaming, and byte ranges.
- Rebuilt the backend and worker; migration `0039` applied successfully.
- Triggered a real administrator rebuild through the API. The worker generated and activated a 17,637-node / 31,283-edge snapshot in MinIO.
- Verified the authenticated manifest reports the ready current version and a 64-byte range request returns HTTP 206 with the correct content range.
- Eighteen focused backend tests pass and changed V2 API/storage modules pass Ruff.
- Moved Phase 4 into progress.

## 2026-07-28 — Phases 4 and 5 completed

- Added the Apache Arrow browser decoder and kept it in a separate lazy chunk.
- Connected the existing light Knowledge shell to snapshot-backed Cosmos.gl with server-provided static positions.
- Preserved search, category emphasis, pause/resume, fit, selection, connected highlighting, and GPU disposal.
- Added stale, first-build, failure, retry, abort, and WebGL2-to-D3 fallback behavior.
- Added on-demand inspector metadata with cancellation on rapid selection.
- Added the authenticated runtime `d3|cosmos` setting; production Compose defaults to D3 while local validation enables Cosmos.
- Rebuilt the real frontend and measured 2.36 seconds to interactive for 17,637 nodes / 31,283 edges with 394 DOM elements.
- Added production Compose parity and a rollback/deployment operations runbook.
- Moved Phase 6 into progress.

## 2026-07-28 — Phases 6 and 7 completed

- Added authenticated operational status with queue, worker heartbeat, snapshot state, counts, and live artifact integrity.
- Added Prometheus gauges, three production alert rules, and the provisioned `Knowledge Graph V2` Grafana dashboard.
- Added safe automatic retention that preserves the current snapshot and the three newest non-current builds.
- Verified 12 concurrent 64 KiB range downloads all returned HTTP 206 while the API and worker remained healthy.
- Verified a real MinIO outage leaves API health at HTTP 200 and the last-ready manifest available, returns a controlled HTTP 503 for artifacts, and recovers after MinIO restarts.
- Existing focused tests cover duplicate delivery/coalescing, abandoned-job recovery, retry exhaustion, corrupt snapshots, missing endpoints, and last-known-good activation.
- Added role-based internal-administrator rollout control; production remains D3 by default and supports an instant configuration-only rollback.
- All 20 implementation tasks and all eight phases are complete.

## 2026-07-28 — Production qualification reopened

- Corrected the earlier completion claim after distinguishing local/internal-beta completion from production qualification.
- Reopened the plan with release-blocking gates for connector coverage, client integrity, browser automation, complete telemetry, chaos recovery, representative load, capacity enforcement, and production deployment hygiene.
- Phase 8 is in progress; the system must not be described as fully production-qualified until these gates pass.

## 2026-07-28 — Phase 8 production qualification completed

- Wired the remaining implemented UKO graph mutation routes (workspace,
  project delete/update, and categorization) through the shared coalesced
  snapshot hook. Successful/no-op/queue-failure behavior is tested.
- Added browser SHA-256 and byte-size verification before Arrow decode, plus a
  cancellable Web Worker for decoding.
- Added browser automation for Cosmos loading, rapid search, route cleanup,
  and WebGL2 fallback; all pass against the rebuilt stack.
- Added durable build success/failure/retry/exhaustion telemetry, manifest and
  artifact metrics, browser outcome/load metrics, alerts, and dashboard panels.
- Proved Redis outage recovery and killed a worker while it held an active
  build lock; the replacement activated a new ready snapshot.
- Enforced the measured 100k-node/200k-edge browser ceiling in the manifest and
  client instead of allowing unqualified datasets to freeze the browser.
- Added short-lived signed object downloads and an immutable same-origin cache.
  A cold-cache 100-viewer run completed 200 range requests with zero errors,
  p50 197 ms, p95 628 ms, p99 716 ms, and 274 requests/second.
- Hardened production Compose with required secrets, required pinned dependency
  image references, internal-only data services, Grafana authentication, real
  worker health checks, and a required browser-reachable S3/CDN endpoint.
- Corrected provider documentation: Git and MySQL have live sync; Jira, Slack,
  and Confluence remain transformation adapters, not production collectors.
