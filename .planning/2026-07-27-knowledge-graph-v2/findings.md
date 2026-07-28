# Findings: Knowledge Graph V2

Date: 2026-07-27

## Current measured behavior

- `GET /legacy-graph/data` returns the complete organization graph.
- Live local measurement: 17,637 nodes, 31,283 stored edges, 19,229,918 decompressed response bytes, 5.661 seconds.
- `KnowledgeGraph.tsx` adds connector and repository nodes plus a synthetic `contains` edge for most graph nodes, taking the rendered edge count close to 49,000.
- `D3Graph.tsx` creates one SVG line per edge and one SVG circle per node, then updates their coordinates on every D3 force-simulation tick.
- Search reconstructs the entire SVG and force simulation because `searchFilter` is an effect dependency.
- The legacy graph route executes synchronous FalkorDB queries inside an async FastAPI route and loads/deduplicates the complete graph for every request.

## Reusable current components

- FalkorDB remains the universal organization knowledge source of truth.
- `backend/ecms/infrastructure/storage/object_store.py` defines a binary `ObjectStore` protocol.
- `backend/ecms/infrastructure/storage/s3.py` implements S3/MinIO-compatible binary storage.
- MinIO and Redis already exist in the development and production Compose stacks.
- FastAPI, Pydantic and OpenTelemetry/Prometheus are already backend dependencies.
- The existing `KnowledgeGraph.tsx` shell provides node categories, toolbar, inspector, loading and empty states.
- The existing `D3Graph.tsx` remains available as a rollback path during V2 validation.

## Missing capabilities

- No PyArrow dependency or Arrow snapshot format.
- No Cosmograph/Cosmos.gl frontend dependency.
- No durable Redis-backed snapshot job runner.
- Existing CLI workers are tied to the current Kafka event system and should not be reused for Knowledge Graph V2.
- No snapshot manifest, lifecycle model, build lock, version history or atomic current-version pointer.
- No graph snapshot API or on-demand node metadata API.
- No benchmark harness for 100k/500k/1M-node datasets.
- No feature flag for switching D3 and V2 renderers.

## Confirmed architectural decisions

- The graph is universal organization knowledge; project or repository filtering is not the scaling mechanism.
- The complete graph should remain visible on one canvas, matching the current experience.
- FalkorDB and the ingestion model remain unchanged during renderer migration.
- V2 uses versioned immutable graph snapshots generated after graph-changing connector syncs.
- Snapshot transport uses Apache Arrow IPC.
- Snapshot storage uses the existing S3/MinIO abstraction; Redis stores only locks/status/current-version metadata.
- Rendering uses Cosmograph/Cosmos.gl with WebGL 2.
- Rendering data is minimal; heavy node metadata loads on selection.
- Kafka is not part of the Knowledge Graph V2 design.
- D3 remains behind a feature flag until V2 passes functional and scale gates.

## External technical evidence

- Cosmos.gl performs graph simulation and rendering on the GPU and accepts typed link arrays.
- Cosmograph React accepts Apache Arrow `ArrayBuffer` data.
- Apache Arrow provides language-neutral columnar binary transport and zero-copy-friendly access.
- These are candidate capabilities, not proof of performance in ECMS; the plan therefore starts with an explicit technical spike and benchmark gate.

## Risks

- WebGL 2 availability and GPU/driver variance.
- Browser memory duplication between Arrow buffers, JavaScript structures and GPU buffers.
- Cosmograph API/library upgrade risk.
- Snapshot generation duration and FalkorDB load at enterprise scale.
- Snapshot consistency while connector syncs are writing.
- Stable node-index mapping and referential integrity across point/link tables.
- Existing graph metadata comes from both legacy and modern graph layers.
- Full-graph readability at extreme zoom levels requires zoom-dependent labels without hiding nodes.

## 2026-07-28 production qualification audit

- Git and MySQL are the only provider-specific REST sync routes that currently write connector data into FalkorDB. Generic UKO ingestion is also implemented.
- Jira, Slack, and Confluence provider classes currently transform already-fetched dictionaries; they do not implement live REST collection or expose sync routes. They must not be represented as production-qualified live graph connectors.
- Workspace creation directly writes a workspace node to FalkorDB but does not currently trigger a snapshot refresh.
- Categorization mutates graph node properties after the connector sync snapshot trigger; it needs its own post-success refresh or the active snapshot can retain pre-categorization categories.
- The memory bridge reads FalkorDB into the memory store and is not itself a FalkorDB mutation source.
- The web package has no component test script yet, although the monorepo already includes Vitest and Playwright.
- Production qualification must cover implemented mutation paths precisely and remove misleading claims about Jira/Slack/Confluence integration rather than adding superficial trigger calls to non-existent sync flows.
## Plan refinement

- PostgreSQL is the reliable home for durable snapshot manifests and the current-version pointer because it is already the system database and supports transactional activation. Redis remains limited to jobs, coalescing, and expiring locks.
- The existing `ObjectStore` API transfers whole byte arrays; V2 needs a compatible streaming or presigned-read extension so large Arrow objects do not pass through FastAPI memory.
- The current frontend has no general persisted feature-flag facility. The renderer flag therefore needs an explicit backend/runtime configuration path rather than relying only on a build-time `VITE_` variable.
- The latest observed migration is `0038_normalize_governance_member_ids.py`; implementation must resolve the actual Alembic head before naming the new migration.

## Phase 0 implementation findings

- The current web app is Vite + React 18 and already has Playwright at the monorepo root, but the web package's `test` script is still a placeholder.
- `Administration.tsx` mounts `KnowledgeGraph` directly; the proof should therefore be exposed through an explicit development query flag inside the component or a separate development route, not by replacing that mount.
- Official Cosmograph v2 documentation lists object arrays and Apache Arrow buffers as supported inputs. The validation spike can use current object arrays now and preserve the same component boundary for later Arrow adoption.
- `@cosmograph/react` is currently published as 2.3.3. Compatibility with this repository's React/Vite versions must be verified by typecheck and build rather than assumed.
- `@cosmograph/react` and `@cosmograph/cosmograph` declare the non-commercial `CC-BY-NC-4.0` license. They were removed before integration.
- The underlying `@cosmos.gl/graph@3.3.0` engine declares the MIT license and exposes typed-array APIs, simulation lifecycle controls, selection/highlighting, and explicit `destroy()` cleanup. Phase 0 now targets this production-compatible engine.
- The production build code-splits the proof renderer into a separate approximately 511 KB minified chunk (about 127 KB gzip) plus its WebGL device chunk; it is not initialized on the default D3 path.
- Browser/GPU performance cannot be certified from TypeScript/build checks. Phase 0 remains a hard gate until downloadable measurements are captured on the agreed client hardware.

## Phase 0 measured results

- Automated current-graph D3 run: 17,639 nodes, 46,012 edges, 7,547 ms interactive, 1.9 FPS, 100% slow frames, 68,596 DOM elements, approximately 167 MB JavaScript heap.
- Automated current-graph cosmos.gl run: 17,639 nodes, 46,012 edges, 6,553 ms interactive, 1.0 FPS, 83.3% slow frames, 454 DOM elements, approximately 410 MB JavaScript heap.
- These runs used headless Chromium on Windows. Its WebGL path is software-rendered, so its cosmos.gl FPS and heap result cannot be treated as the agreed production GPU capacity result.
- The DOM reduction is valid and substantial, while the interactive time still includes the current 5–6 second legacy JSON API. Snapshot transport is expected to address transport/parse time, but must be measured rather than assumed.
- Hardware Chrome with simulation disabled by default passed the current renderer gate at 105.5 FPS, zero slow frames, approximately 66 MB heap, and 454 DOM elements. Overall interactive time remained 9,838 ms because it still used the legacy JSON endpoint.
- Initial capacity runs at the browser's default high-DPI pixel ratio did not meet 30 FPS: 100k nodes/200k edges reached 22.8 FPS and approximately 141 MB heap; 500k/1M reached 7.4 FPS and approximately 608 MB heap.
- The next bounded renderer adjustment is a one-to-one canvas pixel ratio for the dense administrative overview. This preserves every node and edge while avoiding unnecessary high-DPI fragment work.
- Final Phase 0 capacity with static-by-default rendering, pixel ratio 1, and the engine FPS monitor disabled: current graph 105.5 FPS; 100k nodes/200k edges 31.5 FPS and approximately 144 MB heap; 500k nodes/1M edges 7.5 FPS and approximately 610 MB heap.
- Supported interactive capacity on the measured hardware is therefore 100k nodes/200k edges. The 1M-node test was not run after the 500k test fell far below the gate, avoiding predictable browser/GPU instability.
