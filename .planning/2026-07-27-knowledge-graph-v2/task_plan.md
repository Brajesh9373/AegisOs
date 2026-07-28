# Implementation Plan: Production Knowledge Graph V2

Date: 2026-07-27
Status: production qualification in progress

## Goal

Replace the resource-heavy D3/SVG whole-organization graph with a benchmarked WebGL renderer backed by versioned Apache Arrow snapshots, while preserving the current Administration Knowledge experience, FalkorDB source data, and a feature-flagged D3 rollback.

## Non-goals

- Do not redesign the universal knowledge model.
- Do not introduce project/repository filtering as the scale solution.
- Do not migrate away from FalkorDB.
- Do not introduce Kafka into the V2 pipeline.
- Do not remove D3 until V2 passes acceptance gates.
- Do not add entity resolution or semantic clustering as a prerequisite.

## Phase 0 — Baseline and proof gate
Status: complete

- Capture browser CPU, memory, FPS, load time and API timings for the current 17,637-node graph.
- Build an isolated Cosmograph proof using the current graph data without changing the production Knowledge tab.
- Verify whole-graph rendering, pan, zoom, fit, pause, selection and connected-edge highlighting.
- Generate 100k/500k/1M-node synthetic datasets with representative edge ratios.
- Record supported capacity on agreed client hardware.
- Stop if WebGL renderer or memory limits fail the agreed thresholds; do not build the snapshot platform before this gate passes.

## Phase 1 — Snapshot contracts and persistence
Status: complete

- Define versioned point, link, manifest and build-status schemas.
- Add PyArrow and implement deterministic FalkorDB-to-Arrow serialization.
- Validate stable numeric indexes, edge referential integrity, counts and checksums.
- Extend the existing object-store abstraction as needed for content type, streaming and atomic publication.
- Persist current-version/build metadata outside the snapshot payload.
- Add unit tests for serialization, corruption rejection and atomic activation.

## Phase 2 — Snapshot build execution without Kafka
Status: complete

- Add a Redis-backed durable graph-snapshot job with idempotency and an organization-level build lock.
- Add a dedicated snapshot-worker container and health/status reporting.
- Trigger snapshot rebuilds only after successful graph-changing connector syncs.
- Coalesce repeated triggers while a build is active.
- Retain the last known-good snapshot when a build fails.
- Add retry limits, timeout handling, structured logs and Prometheus/OpenTelemetry measurements.

## Phase 3 — Snapshot delivery API
Status: complete

- Add authenticated manifest, point-snapshot and link-snapshot endpoints.
- Stream snapshot objects rather than loading complete files into FastAPI memory.
- Add immutable cache headers, ETag/checksum validation and range-request support where supported by storage/proxy.
- Add on-demand node metadata endpoint for the inspector.
- Enforce organization isolation without filtering the organization graph contents.
- Keep `/legacy-graph/data` unchanged for D3 rollback.

## Phase 4 — Knowledge Graph V2 UI
Status: complete

- Add Cosmograph dependencies through the existing pnpm workspace.
- Create a lazy-loaded V2 renderer component so WebGL code is loaded only when Knowledge is opened.
- Reuse the current Knowledge shell, category palette, toolbar and inspector.
- Load manifest and Arrow buffers, then pass compact columns to Cosmograph.
- Match current interactions: whole-graph view, category colors, dark edges, fit, zoom, pan, pause, node focus and reset.
- Load heavy metadata only after node selection.
- Use zoom-dependent labels while keeping every node and edge rendered.
- Stop simulation and release or pause GPU resources when the Knowledge tab is hidden.
- Add WebGL-unavailable, snapshot-building, stale-snapshot, error and retry states.

## Phase 5 — Feature flag and compatibility
Status: complete

- Add `knowledge_graph_renderer=d3|cosmograph` configuration with D3 as initial default.
- Add an authorized runtime toggle for test environments.
- Preserve current graph refresh behavior by switching to snapshot-version refresh in V2.
- Verify connector-created knowledge appears after snapshot activation.
- Document rollback and ensure switching to D3 requires no data migration.

## Phase 6 — Production performance and resilience
Status: complete

- Run current, 100k, 500k and 1M benchmark suites.
- Test concurrent users opening the same immutable snapshot.
- Test connector sync during snapshot build, worker restart, MinIO outage, Redis outage and corrupted snapshot.
- Verify backend responsiveness while snapshot generation is active.
- Verify browser memory is released on tab navigation.
- Add Grafana panels and alert thresholds for build failures, age, size, duration and renderer load failures.

## Phase 7 — Controlled rollout
Status: complete

- Enable V2 for internal administrators only.
- Compare V2 telemetry and functional behavior against D3.
- Expand rollout gradually after acceptance gates pass.
- Make Cosmograph the default only after the observation period.
- Retain D3 rollback for one release, then decide separately whether to remove it.

## Phase 8 — Release-blocking production qualification
Status: complete

- Wire every implemented graph-writing connector path through the shared graph-change hook and prove success/no-op/failure behavior.
- Verify Arrow checksums in the browser before decoding and reject partial/corrupt downloads.
- Add automated browser coverage for runtime rollout, D3 fallback, cancellation, rapid selection, renderer cleanup, and WebGL unavailability.
- Add build-duration, retry, failure, download-failure, manifest-latency, renderer-load, and client-failure telemetry.
- Exercise active-build worker termination/recovery, Redis outage/recovery, FalkorDB interruption, corrupt/missing objects, and connector changes during a build.
- Run a materially representative concurrent-viewer/load test with latency, error rate, backend memory, and last-known-good evidence.
- Reconcile the supported-capacity claim with the product requirement: enforce the measured 100k/200k ceiling or introduce a safe higher-scale overview mode.
- Verify production Compose contains no Knowledge Graph dependency on Kafka, no embedded production credentials, valid health checks, and documented environment requirements.
- Keep this phase open until every release-blocking check has automated evidence or an explicit, documented product constraint.

## Acceptance gates

- Current graph becomes interactive within 5 seconds on agreed production hardware.
- Pan and zoom sustain at least 30 FPS for the current and agreed target dataset.
- Selection feedback is under 100 ms.
- Search/highlight feedback is under 300 ms after snapshot load.
- Browser memory stays below the agreed hardware-specific limit.
- Snapshot generation never replaces a valid snapshot with an invalid or partial version.
- API remains healthy during snapshot builds.
- Hidden/unmounted Knowledge UI does not continue consuming simulation resources.
- No Kafka dependency exists in the Knowledge Graph V2 execution path.

## Errors encountered

| Error | Resolution |
|---|---|
| None during planning | N/A |
| Phase 0 typecheck rejected `String.replaceAll` under the app's ES2020 lib | Replaced it with an ES2020-compatible regular expression. |
| PowerShell parsed an unquoted scoped package after a statement separator as splatting syntax | Re-ran the pnpm command with quoted package arguments. |
| `pnpm exec eslint` could not traverse the restricted Windows user-profile path (`EPERM`) | Run the repository's installed ESLint executable directly, avoiding pnpm's temporary-directory discovery. |
| Docker build could not read the restricted user-profile Buildx directory | Re-ran the approved Docker build with managed escalation. |
| Phase 1 test command could not initialize uv's user-profile cache | Re-run with a task-specific cache inside the writable backend workspace. |
| ARQ 0.28 forced incompatible Redis/FalkorDB downgrades | Removed ARQ, restored the existing dependency versions, and implemented the durable queue directly with Redis Streams consumer groups. |
| Redis Streams blocking read matched the runtime client's socket timeout and restarted an idle worker | Shortened each blocking read below the socket timeout; the rebuilt worker remained stable and completed the real snapshot. |
| The frontend benchmark command resolved the Compose file relative to `frontend/` | Corrected the command to use `../docker/docker-compose.yml`; no product code was affected. |
| A Redis status scan was initially written with JavaScript-style `do/while` syntax | Replaced it with a valid Python loop before the status endpoint was built or deployed. |
| MinIO outage validation showed boto3 retries could exceed the browser's 20-second request timeout | Bounded S3 connect/read timeouts and retries so the streaming API can return its controlled 503 promptly. |
| Scoped connector validation ran Ruff across the pre-existing categorization module and exposed 24 unrelated legacy lint issues | Lint newly added trigger modules directly and compile-test the categorization integration; the module's prior debt remains a separate cleanup item. |
| The in-memory Redis test double does not implement Lua `EVAL`, so a new lock test could not exercise renewal | Kept the real atomic Lua renewal and scoped the fake-Redis test to the crash-recovery TTL it can faithfully verify. |
| The first production frontend build invocation used an incorrect root-level Vite binary path | Re-ran the same build with the web workspace's installed Vite executable; the production build passed. |
| The first final worker-profile assertion treated Docker's multi-line environment output as a scalar string | Inspected the two exact variables directly; the worker is restored to `production` with the qualification delay set to `0`. |
