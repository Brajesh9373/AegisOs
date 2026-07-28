# Knowledge Graph V2 — Design Brief

Date: 2026-07-27
Status: approved direction, implementation pending

## Problem

The Administration Knowledge tab renders the organization's complete knowledge graph with D3 force simulation and SVG. The current dataset already contains 17,637 nodes and roughly 49,000 rendered edges after client-generated relationships. Loading it transfers about 19 MB of decompressed JSON, takes about 5.7 seconds at the API, creates tens of thousands of DOM elements, and continuously performs a large number of attribute updates. This slows both the browser and the wider application.

The graph is universal organizational knowledge. Repository or project filtering is not an acceptable scalability strategy, and future organizations may connect hundreds of sources.

## Desired outcome

Keep the current whole-graph experience and visual structure, but make it production-capable:

- All organization nodes and edges remain present on the canvas.
- The graph uses the approved light canvas and darker, readable edges.
- Existing search, pan, zoom, fit, pause, selection, highlighting, category legend, and inspector behavior remain available.
- Opening or leaving Knowledge must not degrade the rest of the application.
- New connector knowledge becomes visible through an atomic, versioned refresh.
- The old D3 renderer remains available as a rollback until V2 proves itself.

## Architecture

```text
Connector sync
     |
     v
FalkorDB (source of truth)
     |
     | graph-changed trigger
     v
Redis job queue + org build lock
     |
     v
Dedicated snapshot worker
     |
     +--> Apache Arrow points + links --> MinIO/S3
     |
     +--> durable build/version record --> PostgreSQL

Administration Knowledge tab
     |
     +--> manifest API --> current immutable version
     +--> Arrow objects --> WebGL/Cosmograph
     +--> node click --> metadata API --> inspector
```

### Responsibility boundaries

- FalkorDB remains the authoritative graph database.
- PostgreSQL stores durable snapshot status, version, checksums, counts, object keys, timestamps, and current-version pointer.
- Redis provides the durable job queue, coalescing signal, and short-lived organization build lock; it is not the source of truth for the current snapshot.
- MinIO/S3 stores immutable Arrow snapshot objects.
- A dedicated worker builds snapshots outside FastAPI request handling.
- Cosmograph/cosmos.gl renders compact Arrow-backed columns through WebGL.
- Kafka is not part of the Knowledge Graph V2 path.

## Snapshot lifecycle

1. A connector completes a graph-changing transaction.
2. It enqueues an idempotent snapshot request for the organization.
3. The worker obtains the organization lock and records a build in PostgreSQL.
4. It reads a consistent graph view from FalkorDB and writes deterministic point and link Arrow objects under a new version.
5. It verifies schema, counts, referential integrity, checksums, and object readability.
6. In one database transaction, it marks the build ready and changes the current pointer.
7. Clients discover the new version through the manifest.
8. Failure leaves the last known-good version current. Repeated triggers are coalesced into at most one subsequent build.

## UI structure

The existing Knowledge tab shell is retained:

- Left: node-type legend and counts.
- Center: light WebGL canvas with search and simulation controls.
- Right: node inspector.
- Bottom: graph totals, interaction help, build freshness, and snapshot state.

The V2 renderer is lazy-loaded only when the Knowledge tab is active. Leaving the tab pauses or disposes simulation and GPU resources. Labels may be density-aware by zoom level, but no node or edge is removed from the canvas.

## States

- Loading manifest
- Loading graph, with transferred bytes/progress when available
- Ready
- New snapshot building while the last good graph remains usable
- Stale snapshot warning
- No snapshot yet
- Snapshot or network error with retry
- WebGL unavailable with controlled D3 fallback

## Compatibility and rollout

- `/legacy-graph/data` and the D3 component remain unchanged during rollout.
- A renderer feature flag selects `d3` or `cosmograph`.
- V2 is first enabled for internal administrators.
- Promotion to default requires the benchmark and resilience gates in the implementation plan.
- Removing D3 is a separate decision after at least one stable release.

## Measurable acceptance

- Current graph interactive within 5 seconds on agreed production hardware.
- At least 30 FPS during pan/zoom on current and agreed target datasets.
- Node selection feedback under 100 ms.
- Search/highlight feedback under 300 ms after load.
- No partial or corrupt snapshot can become current.
- Snapshot building does not make application APIs unhealthy.
- Browser resources are released when the tab is hidden or unmounted.
- Capacity is measured at current, 100k, 500k, and 1M nodes; supported limits are documented rather than assumed.

## Constraints and non-goals

- No project/repository filtering as the core scale solution.
- No graph model redesign or entity-resolution prerequisite.
- No migration away from FalkorDB.
- No Kafka dependency for this feature.
- No immediate deletion of the existing renderer.
- No production switch until the proof gate passes.

