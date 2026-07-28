# Knowledge Graph V2 — Implementation Tasks

Ordered as risk-first vertical slices. Each checked task should leave a demonstrable, testable increment.

## Validation gate

- [x] **KG-01 — Establish the reproducible baseline**
  - Reuse `frontend/apps/web/src/components/KnowledgeGraph.tsx`, `D3Graph.tsx`, and `GET /legacy-graph/data`.
  - Add a non-production benchmark harness that records API duration/bytes and browser load time, FPS, main-thread blocking, DOM count, and heap use.
  - Add deterministic synthetic fixtures for the current scale and 100k/500k/1M-node targets with representative edge ratios.
  - Done when one command produces a versioned baseline report and fixture metadata without changing the production UI.

- [x] **KG-02 — Prove the WebGL renderer in isolation**
  - Add Cosmograph in the existing pnpm workspace and create a temporary lazy-loaded `CosmographGraph` spike behind a development-only flag.
  - Feed it the existing graph response so renderer viability is tested before snapshot infrastructure is built.
  - Demonstrate whole-graph rendering, category colors, darker edges, pan, zoom, fit, pause, node selection, connected-edge highlighting, and cleanup on unmount.
  - Done when the current dataset meets the initial 5-second/30-FPS interaction gate on agreed hardware, or a stop report documents why it does not.

- [x] **KG-03 — Establish and approve supported capacity**
  - Run the spike against current, 100k, 500k, and 1M fixtures.
  - Record load time, steady FPS, peak/settled memory, selection latency, and search latency.
  - Done when the team has an evidence-based supported capacity and client hardware profile. Do not continue to platform build if the required capacity fails.

## End-to-end snapshot foundation

- [x] **KG-04 — Add durable snapshot metadata**
  - Add a new PostgreSQL migration after the current migration head and a repository/service for organization-scoped snapshot builds.
  - Store version, state, point/link object keys, schema version, counts, byte sizes, checksums, timestamps, error summary, and current status.
  - Make activation transactional and guarantee at most one current ready snapshot per organization.
  - Done when repository tests prove valid activation, failed-build retention, organization isolation, and concurrent activation safety.

- [x] **KG-05 — Define and serialize the Arrow contract**
  - Add PyArrow and a focused module under `backend/ecms/visualization/`.
  - Define versioned point, link, and manifest schemas using compact numeric node indexes while retaining stable source IDs and renderer-required attributes.
  - Serialize a FalkorDB fixture deterministically and validate unique IDs, link endpoints, counts, schema version, and checksums.
  - Done when repeated builds from identical input are byte/checksum stable and malformed graphs are rejected by unit tests.

- [x] **KG-06 — Make snapshot object storage production-safe**
  - Extend or wrap the existing `ObjectStore`/`S3ObjectStore` rather than replacing MinIO/S3 integration.
  - Support content type, streamed upload/download or presigned reads, metadata, and immutable versioned keys without holding entire production snapshots in FastAPI memory.
  - Publish objects before changing the PostgreSQL current pointer.
  - Done when object-store contract tests cover large streamed objects, missing/corrupt objects, checksum verification, and cleanup of abandoned non-current builds.

- [x] **KG-07 — Deliver one snapshot manually end to end**
  - Add an administrator-only build command or endpoint that invokes the builder synchronously outside normal connector traffic for validation.
  - Produce Arrow objects in MinIO and a ready/current PostgreSQL record from the real FalkorDB graph.
  - Done when the generated manifest/counts/checksums match FalkorDB and failure leaves the prior snapshot active.

## Durable execution without Kafka

- [x] **KG-08 — Add the dedicated Redis snapshot worker**
  - Add a Redis-backed job library such as ARQ, a worker entry point, health reporting, and a dedicated Compose service.
  - Implement idempotent jobs, organization locks with expiry/renewal, bounded retries, timeouts, and structured failure recording.
  - Keep this worker independent of the current Kafka-coupled ECMS worker commands.
  - Done when enqueue, restart recovery, duplicate delivery, retry exhaustion, and last-known-good behavior pass integration tests.

- [x] **KG-09 — Connect graph mutations to snapshot refresh**
  - Introduce one shared `graph_changed(org_id, source, revision)` hook after successful FalkorDB writes.
  - Call it from each connector/provider persistence path instead of embedding queue details in providers.
  - Coalesce bursts during an active build and guarantee one follow-up build if changes arrive after the build's source watermark.
  - Done when connector sync tests prove failed/no-op syncs do not publish, successful changes do publish, and rapid changes cannot create an unbounded queue.

## Delivery API

- [x] **KG-10 — Expose the authenticated snapshot manifest**
  - Add a new V2 route rather than changing `/legacy-graph/data`.
  - Return the current ready version, schema version, immutable object URLs or API paths, counts, sizes, checksums, generated time, source watermark, and build/stale state.
  - Enforce `require_identity`, organization isolation, ETag/conditional requests, and no-store behavior for transient build status.
  - Done when API tests cover unauthorized/cross-org access, no snapshot, ready, building-with-last-good, failed-with-last-good, and conditional requests.

- [x] **KG-11 — Stream immutable snapshot objects**
  - Serve or sign point/link Arrow objects without full buffering in FastAPI.
  - Apply immutable cache headers keyed by version and support range requests where the chosen MinIO/proxy path supports them.
  - Done when large-object tests verify bounded API memory, correct checksums/content types, cache behavior, and interrupted downloads.

- [x] **KG-12 — Add lightweight node metadata lookup**
  - Add an authenticated organization-scoped endpoint that fetches full node details and connections only after selection.
  - Keep large descriptions and source metadata out of the initial Arrow point payload.
  - Done when current inspector fields are available, unknown/cross-org nodes are rejected, and latency is measured on the real graph.

## Production V2 UI

- [x] **KG-13 — Load versioned Arrow snapshots in the browser**
  - Add a typed manifest client and a cancellable, lazy graph-loading hook.
  - Decode compact Arrow columns off the critical React render path; use a Web Worker if profiling shows main-thread decoding violates the gate.
  - Cache immutable versions safely and discard partial/aborted loads.
  - Done when reload, version change, navigation-away, retry, checksum mismatch, and stale-last-good cases are covered.

- [x] **KG-14 — Replace only the center renderer with V2**
  - Reuse the current Administration Knowledge shell, node-type legend/palette, toolbar, footer, and inspector layout.
  - Mount the production `CosmographGraph` only while Knowledge is active.
  - Preserve the whole graph and current light-canvas direction, with readable darker edges and the current zoomed-out/fit behavior.
  - Done when visual and interaction parity is verified for search, pan, zoom, fit, pause, reset, selection, connected highlighting, and category toggles that change emphasis rather than remove organizational data.

- [x] **KG-15 — Make inspector data on-demand**
  - Show immediate compact selection data from Arrow, then fetch full metadata through KG-12.
  - Handle rapid selection with cancellation and prevent stale responses from replacing the current selection.
  - Done when the inspector matches current useful content and selection feedback stays below 100 ms.

- [x] **KG-16 — Add lifecycle and recovery states**
  - Add loading progress, no snapshot, building, stale, failed, retry, WebGL unavailable, and fallback states within the existing shell.
  - Pause simulation when the document/tab is hidden and dispose GPU/listener/worker resources on unmount.
  - Done when browser profiling confirms no continuing simulation and reclaimed memory after leaving Knowledge.

## Safe rollout and operations

- [x] **KG-17 — Add renderer flag and lossless rollback**
  - Add a backend/runtime setting `knowledge_graph_renderer=d3|cosmograph`; start with D3 as default.
  - Lazy-load only the selected renderer and retain `/legacy-graph/data`.
  - Provide an authorized non-production toggle and document rollback; switching renderers must require no data migration or rebuild.
  - Done when both renderers pass smoke tests and a failed V2 load can fall back without taking down Administration.

- [x] **KG-18 — Add observability and operational controls**
  - Reuse existing metrics/tracing helpers for queue depth, build duration, graph counts, bytes, snapshot age, failures, retries, manifest latency, download failures, renderer load duration, and client failure rate.
  - Add health checks and alerts for stuck locks, missing current objects, stale snapshots, repeated failures, and capacity threshold breaches.
  - Add retention policy and an audited administrator rebuild action.
  - Done when dashboards/alerts are exercised with injected failures and no sensitive connector metadata is logged.

- [x] **KG-19 — Run resilience and concurrency qualification**
  - Test concurrent viewers, connector sync during build, coalesced changes, worker termination/restart, Redis outage, MinIO outage, FalkorDB interruption, corrupt objects, and PostgreSQL activation races.
  - Confirm FastAPI remains healthy and the last known-good graph remains available.
  - Done when results and remediation are attached to the benchmark report and all release-blocking failures are closed.

- [x] **KG-20 — Roll out in controlled stages**
  - Enable V2 for internal administrators, compare D3/V2 telemetry and behavior, then widen by configuration.
  - Promote V2 to default only after the acceptance gates and an agreed observation window.
  - Retain D3 rollback for one stable release; removal is a separate reviewed task.
  - Done when rollout/rollback runbooks are tested and production telemetry stays within thresholds.

## Production qualification corrections

- [ ] **KG-21 — Complete connector mutation coverage**
- [ ] **KG-22 — Verify browser snapshot integrity**
- [ ] **KG-23 — Add automated browser lifecycle and fallback tests**
- [ ] **KG-24 — Complete operational telemetry**
- [ ] **KG-25 — Pass dependency-outage and active-build recovery tests**
- [ ] **KG-26 — Pass representative concurrency and memory qualification**
- [ ] **KG-27 — Enforce the measured supported-capacity contract**
- [ ] **KG-28 — Harden and validate production deployment configuration**

## Definition of done for every task

- Tests are added at the appropriate unit, contract, integration, or browser level.
- Existing behavior outside the selected slice remains unchanged.
- New configuration, migrations, operational steps, and rollback are documented.
- Performance claims include measured evidence and hardware/dataset context.
- No Kafka dependency is introduced into the Knowledge Graph V2 path.
