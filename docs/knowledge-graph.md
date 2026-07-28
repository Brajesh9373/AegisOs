# Knowledge Graph

AegisOS maintains a single enterprise cognitive graph. There are no per-workspace or per-connector copies -- every subsystem (agents, watchers, connectors, UI) reads and writes the same graph. Views (`Subgraph`) are filtered projections, never independent data stores.

---

## Core Domain Models

### Universal Knowledge Object (UKO)

A UKO captures raw information from an external provider exactly as collected. It never contains reasoning.

```python
class UniversalKnowledgeObject(AggregateRoot):
    uko_id: str
    provider: str                      # e.g. "github", "filesystem"
    provider_object_type: str          # e.g. "file", "commit", "issue"
    provider_object_id: str
    organization_id: str
    workspace_id: str | None
    project_id: str | None
    repository_id: str | None
    title: str
    description: str | None
    raw_content: str
    metadata: dict[str, Any]
    tags: list[str]
    labels: list[str]
    language: str | None
    embedding: list[float] | None
    relationships: list[ProviderRelationship]
    references: list[str]
    processing_status: ProcessingStatus  # pending | processing | processed | failed
    validation_status: ValidationStatus  # validated | rejected | needs_review
    security_classification: SecurityClassification
```

The legacy UKO model (`legacy_ecms.core.uko`) adds an explicit type enum and immutable provenance:

```python
class UKOType(str, Enum):
    FILE = "file"
    FUNCTION = "function"
    CLASS = "class"
    IMPORT = "import"
    API = "api"
    TABLE = "table"
    COLUMN = "column"
    DOCUMENT = "document"
    MESSAGE = "message"
    TICKET = "ticket"
    PERSON = "person"
    NAME = "name"
    COMMIT = "commit"
    CONCEPT = "concept"
    EVENT = "event"
    WORKSPACE = "workspace"
```

```python
class ExtractionProvenance(BaseModel):
    extraction_method: str
    extraction_timestamp: datetime
    confidence: float                  # 0.0 - 1.0
    evidence_snippet: str
    model_version: str
    pipeline_stage: str
```

UKOs carry `ProviderRelationship` objects for inter-provider edges discovered at ingestion time:

```python
class ProviderRelationship(DomainModel):
    target_object_id: str
    relationship_type: str
    metadata: dict[str, Any]
```

### Universal Cognitive Object (UCO)

A UCO is an immutable snapshot of enterprise understanding derived from one or more UKOs. UCOs are the source of truth; the graph is an index.

```python
class UniversalCognitiveObject(ImmutableModel):
    uco_id: str
    canonical_name: str
    display_name: str
    ontology_type: str
    description: str
    summary: str | None
    aliases: list[str]
    confidence: int                    # 0-100
    importance: int                    # 0-100
    business_value: int               # 0-100
    reusability: int                  # 0-100
    stability: int                    # 0-100
    lifecycle_state: LifecycleState   # draft | active | deprecated | archived | deleted
    evidence: list[Evidence]
    relationships: list[str]
    knowledge_sources: list[str]
    graph_node_id: str | None
    custom_attributes: dict[str, Any]
```

Updates create new versions rather than mutating an existing object.

### Evidence

Evidence links understanding back to the raw information that justifies it.

```python
class Evidence(DomainModel):
    uko_id: str
    description: str | None
    confidence: int                    # 0-100
    source: str | None
    origin: str | None
    checksum: str | None
    reference: str | None
    timestamp: datetime
```

### Relationship

A first-class domain object representing a semantic relationship between two UCOs.

```python
class Relationship(DomainModel):
    relationship_id: str
    source_uco: str
    target_uco: str
    relationship_type: str
    confidence: int                    # 0-100
    importance: int                    # 0-100
    weight: float                     # >= 0.0
    direction: RelationshipDirection  # directed | undirected | bidirectional
    evidence: list[str]
    episodes: list[str]
    status: LifecycleState
    version: int
```

### Episode

An immutable record of how knowledge evolved over time.

```python
class Episode(ImmutableModel):
    episode_id: str
    episode_type: str
    timestamp: datetime
    description: str
    trigger: str | None
    source_uko: str | None
    affected_uco: str | None
    graph_changes: list[dict[str, Any]]
    evidence: list[str]
    participants: list[str]
    affected_relationships: list[str]
```

### Relationship Types

Canonical semantic relationship types (`RelationshipType` enum):

| Type | Meaning |
|---|---|
| `USES` | One entity uses another |
| `DEPENDS_ON` | Import or compile-time dependency |
| `IMPLEMENTS` | Implements an interface or base class |
| `CALLS` | Runtime invocation |
| `OWNS` | Ownership or authorship |
| `BELONGS_TO` | Containment or membership |
| `CONTAINS` | Physical or logical containment |
| `CONNECTS_TO` | Network or service connection |
| `GENERATES` | Produces output or artifacts |
| `VALIDATES` | Tests or verifies correctness |
| `DEPLOYS` | Deploys or releases |
| `TESTS` | Test coverage |
| `SECURES` | Security boundary or auth enforcement |
| `CONFIGURES` | Configuration or setup |

The ontology is configurable; these are the canonical defaults and may be extended.

---

## Graph Engine

### GraphStore Protocol

The Graph Engine operates entirely through this storage port. The concrete backend is replaceable -- no subsystem talks to the persistence backend directly.

```python
class GraphStore(Protocol):
    async def upsert_node(self, node: GraphNode) -> None: ...
    async def get_node(self, node_id: str) -> GraphNode | None: ...
    async def delete_node(self, node_id: str) -> None: ...
    async def upsert_edge(self, edge: GraphEdge) -> None: ...
    async def delete_edge(self, edge_id: str) -> None: ...
    async def edges_of(self, node_id: str) -> list[GraphEdge]: ...
    async def neighbors(self, node_id: str) -> list[GraphNode]: ...
    async def all_nodes(self) -> list[GraphNode]: ...
    async def all_edges(self) -> list[GraphEdge]: ...
```

All nine operations are async. All store implementations conform to this protocol.

### Domain Objects

**GraphNode** -- projects one UCO into the graph index:

```python
class GraphNode(DomainModel):
    node_id: str
    ontology_type: str
    display_name: str
    canonical_name: str
    confidence: int                    # 0-100
    importance: int                    # 0-100
    version: int
    properties: dict[str, Any]
```

**GraphEdge** -- projects one relationship:

```python
class GraphEdge(DomainModel):
    edge_id: str                       # deterministic: sha256(source|target|type)[:12]
    source: str
    target: str
    relationship_type: str
    weight: float                     # >= 0.0
    confidence: int                    # 0-100
    version: int
    properties: dict[str, Any]
```

Edge IDs are deterministic (`deterministic_edge_id`) so repeated upserts with the same source, target, and type are idempotent.

**Subgraph** -- a projection of the one graph:

```python
class Subgraph(DomainModel):
    nodes: list[GraphNode]
    edges: list[GraphEdge]
```

A subgraph is a filtered view, not a separate copy.

### GraphEngine

High-level engine owning node and relationship lifecycle, traversal, graph views, and statistics.

| Method | Behavior |
|---|---|
| `upsert_uco(uco)` | Projects a UCO into a GraphNode, incrementing version on update |
| `create_relationship(source, target, type, weight, confidence)` | Creates an idempotent relationship edge |
| `find_node(node_id)` | Returns a node by ID |
| `neighbors(node_id)` | Returns adjacent nodes |
| `delete_node(node_id)` | Deletes a node and its incident edges |
| `delete_relationship(edge_id)` | Deletes a relationship edge |
| `shortest_path(source, target)` | BFS shortest path, returns list of node IDs |
| `expand(node_id, hops)` | Returns the neighborhood subgraph within N hops |
| `view(ontology_type, node_ids)` | Returns a filtered projection of the graph |
| `statistics()` | Returns node count, edge count, density, ontology distribution |

### InMemoryGraphStore

Adjacency-indexed in-memory store. Used for tests and offline development. Maintains separate `_outgoing` and `_incoming` index maps alongside the node and edge dictionaries.

### FalkorDBCypherStore

Production store backed by FalkorDB (Redis graph module).

- All sync `falkordb` calls wrapped in `asyncio.to_thread` for non-blocking async
- Node label: `:Node` with indexed `node_id` property
- Edge label: `:Edge` with indexed `edge_id` property
- `upsert_node` uses `MERGE (n:Node {node_id: $node_id}) SET ...`
- `upsert_edge` uses `MATCH (s), MATCH (t), MERGE (s)-[e:Edge {edge_id: $edge_id}]->(t) SET ...`
- `search_nodes` provides full-text substring search on `display_name` and `canonical_name`

### Event Sourcing

Every mutation emits an immutable event through the `EventBus`:

| Event | Trigger |
|---|---|
| `NodeCreated` | A new node is inserted |
| `NodeUpdated` | An existing node is versioned |
| `NodeDeleted` | A node is removed |
| `RelationshipCreated` | A new edge is inserted |
| `RelationshipDeleted` | An edge is removed |

Events are categorized under `EventCategory.GRAPH` and produced by `"graph-engine"`. This makes the graph's evolution fully auditable and replayable.

---

## Knowledge Engine

### Pipeline

The `DefaultKnowledgeEngine` transforms UKOs into validated, indexed UCOs through this pipeline:

```
UKO -> Analyze -> Extract entities -> Extract relationships -> Map to ontology
   -> Generate UCOs -> Validate -> Publish
```

| Stage | Description |
|---|---|
| **Discover** | `knowledge_discovered` event emitted |
| **Analyze** | Source code parsed by language-appropriate analyzer |
| **Normalize** | `knowledge_normalized` event emitted |
| **Generate UCO** | One UCO per extracted entity, mapped to ontology type |
| **Validate** | Requires `canonical_name` and at least one evidence trace |
| **Publish** | Indexed in repository; `knowledge_validated` and `knowledge_version_created` events emitted |

Confidence scoring:
- Base: 60
- +20 if the entity has a docstring
- +10 if the entity has inheritance (base classes)
- Capped at 100

Importance by entity kind: `api` = 80, `class` = 60, `module` = 50, `function` = 40.

### Code Analysis

**PythonCodeAnalyzer** -- uses the standard-library `ast` module:
- Extracts modules, classes, methods, functions (including `async` variants)
- Detects `@route`/`@get`/`@post` decorators as `api` kind
- Builds `DEPENDS_ON` relationships from `import` and `from X import Y`
- Builds `IMPLEMENTS` relationships from base classes
- Builds `BELONGS_TO` relationships from methods to their parent class
- Extracts docstrings, signatures, decorators, line numbers

**GenericCodeAnalyzer** -- language-agnostic regex scanner:
- Pattern matches imports across Python, JavaScript/TypeScript (`require`, `import from`), C/C++ (`#include`), and more
- Produces a module entity plus `DEPENDS_ON` relationships

**Language detection** (`detect_language`) resolves from explicit hints (file extension mapping for 40+ extensions) or content heuristics (first 2000 characters).

### Ontology Mapper

Maps extracted entities into the enterprise ontology using configurable keyword-to-type and type-to-category rules.

Default keyword rules (matched against entity name, bases, and decorators):

| Keyword | Ontology Type |
|---|---|
| `middleware`, `auth`, `security`, `crypto` | `security_component` |
| `service` | `service` |
| `controller`, `router`, `endpoint`, `gateway` | `api` |
| `repository`, `dao` | `data_access` |
| `model`, `entity`, `table`, `schema` | `database_entity` |
| `config`, `settings` | `configuration` |
| `client`, `connector`, `adapter` | `integration` |

Category mapping:

| Ontology Type | Category |
|---|---|
| `security_component` | `SECURITY` |
| `service`, `data_access`, `integration`, `component` | `TECHNOLOGY` |
| `api` | `ARCHITECTURE` |
| `database_entity`, `configuration` | `INFRASTRUCTURE` |
| `module`, `function` | `DEVELOPMENT` |

### Embedding-Indexed Repository

The `InMemoryKnowledgeRepository` stores UCOs indexed by embedding vectors. Retrieval is by cosine similarity, not keywords.

- Embedding text: `{display_name} {canonical_name} {ontology_type} {description}`
- `search(query)` embeds the query and returns the top-N most similar UCOs
- `reindex()` recomputes every embedding
- Production deployments swap this for a persistent store behind the same `KnowledgeRepository` interface

---

## Knowledge Watcher

The `KnowledgeWatcher` auto-ingests workspace files and builds a code-aware knowledge graph. It runs as a singleton.

### Two-Phase Scan

**Phase 1 -- Ingest all files to UCOs and graph nodes:**
1. Walk the workspace directory tree (skipping `node_modules`, `.git`, `__pycache__`, `.venv`, `dist`, `build`, `.next`)
2. SHA-256 hash each file; skip unchanged files
3. Create a UKO per file with `provider="filesystem"`, `provider_object_type="file"`
4. Run the full knowledge engine pipeline (`analyze` -> `ingest`)
5. Register UCO IDs in a `_uco_map` keyed by display name, canonical name, file path, and module stem
6. Upsert each UCO into the graph engine

**Phase 2 -- Create edges from AST relationships and regex imports:**
1. For each file's `CodeAnalysis.relationships`, resolve source and target UCO IDs and create edges with `weight=0.85`, `confidence=70`
2. For non-AST languages, scan for import patterns (`import`, `require`, `@import`, `link stylesheet`, `script src`) and create `depends_on` edges with `weight=0.6`, `confidence=50`

### Incremental Updates

File hashes are persisted to `/workspace/.ecms_hashes.json` across restarts. On subsequent scans, only files whose SHA-256 hash has changed are re-ingested. The `_uco_map` is rebuilt on every scan so inter-file edges always resolve correctly.

### Continuous Mode

`watch_forever(interval=3.0)` runs the scan loop every 3 seconds indefinitely.

---

## Legacy Graph Client

The legacy `GraphClient` (`legacy_ecms.core.graph`) operates in two modes depending on API key availability.

### Raw FalkorDB Mode

When no OpenAI API key is configured:
- Directly uses `falkordb-py` to select a graph by name
- Batch-writes UKOs using `UNWIND` + `MERGE (u:UKO {id: row.id}) SET ...`
- Creates relationships using `MERGE (t:UKO {id: row.target_id}) ON CREATE SET ...` then `MERGE (u)-[r:RELATES {label: row.relationship}]->(t) SET ...`
- Supports schema enforcement (`strict`, `warn`, `off`) via relationship validation
- Tracks per-batch `BatchWriteResult` with `WriteFailure` details
- Search returns raw episodes and edges via Cypher queries

### Graphiti LLM-Enhanced Mode

When an API key is available and `graphiti-core` is installed:
- Initializes a `Graphiti` instance with a FalkorDB driver, LLM client, and embedder
- Supports OpenAI, OpenAI-compatible, and HuggingFace embedders
- Episodes are added via `graphiti.add_episode` or `graphiti.add_episode_bulk` (chunked at 15)
- Falls back to raw mode on bulk failures
- Search delegates to `graphiti.search`

---

## Knowledge Graph Snapshots

### Lifecycle

Each snapshot transitions through states: `building` -> `ready` or `failed`.

The `KnowledgeGraphSnapshot` ORM model tracks:

| Field | Purpose |
|---|---|
| `id` | Primary key (`kgs-{uuid}`) |
| `organization_id` | Tenant isolation |
| `version` | Unique per-organization version (UUID hex) |
| `state` | `building`, `ready`, or `failed` |
| `is_current` | Atomic current-pointer (partial unique index) |
| `points_object_key` | MinIO/S3 path to points Arrow file |
| `links_object_key` | MinIO/S3 path to links Arrow file |
| `points_checksum` | SHA-256 hex of points file |
| `links_checksum` | SHA-256 hex of links file |
| `point_count`, `link_count` | Row counts |
| `points_bytes`, `links_bytes` | Byte sizes for integrity verification |
| `source_watermark` | What triggered this build |
| `error_summary` | Failure reason (if failed) |

A partial unique index on `(organization_id, is_current)` ensures exactly one current snapshot per organization.

### Apache Arrow Format

Snapshots are serialized as two Apache Arrow IPC files:

**Points schema:**
```
index: int32, id: utf8, label: utf8, group: utf8, category: utf8,
source_group: utf8 nullable, confidence: float32, x: float32, y: float32
```

**Links schema:**
```
index: int32, id: utf8, source: int32, target: int32, label: utf8
```

Edge `source` and `target` are integer indices into the points array (not string IDs). This enables zero-copy columnar access in the browser.

Layout positions are computed deterministically using a golden-angle disc algorithm with degree-based radial compression, seeded by node ID hash. No browser-side force simulation is required.

### Snapshot Service

`GraphSnapshotService.build()` orchestrates the full lifecycle:
1. Create a `building` metadata row
2. Load nodes and edges from the `GraphSource` (legacy FalkorDB projection)
3. Build Arrow artifacts via `build_arrow_artifacts`
4. Upload to object store (MinIO/S3)
5. Verify uploaded sizes match
6. Activate atomically via the repository (swap `is_current` pointer)
7. On failure, clean up uploaded objects and mark state as `failed`

Retention: `apply_retention(keep_non_current=3)` removes old non-current snapshots and their object store artifacts.

### Snapshot Worker

A dedicated Redis Streams worker (`run_worker`) consumes durable snapshot jobs.

**Queue coalescing:**
- `enqueue()` uses a Redis `SET NX` pending key per organization
- If already pending, a dirty flag is set instead of adding a duplicate job
- On `complete()`, if a dirty flag exists, a follow-up job is enqueued automatically
- This ensures connector bursts produce at most one build per pending cycle

**Worker lifecycle:**
1. Read one job from the consumer group (4s block)
2. Claim stale jobs abandoned by dead workers (30s idle threshold)
3. Acquire an organization-level build lock (60s TTL)
4. Maintain lock renewal and heartbeat in a background task
5. Build the snapshot within a 30-minute timeout
6. Apply retention
7. Acknowledge the job and enqueue coalesced follow-up if dirty

**Retry policy:** Up to 3 retries per message. Exhausted retries are acknowledged and the dirty flag is checked for a follow-up.

**Metrics:** Redis hash `ecms:knowledge-graph:metrics` tracks `builds_completed`, `builds_failed`, `build_retries`, `builds_exhausted`, `build_duration_seconds_total`, `build_duration_seconds_last`.

### Graph Changed Hook

`graph_changed(organization_id, source, revision)` is the entry point called after any successful graph mutation (connector persistence, categorization, admin rebuild). It enqueues a coalesced snapshot build.

### API Endpoints

All endpoints are prefixed with `/api/knowledge-graph/v2` and require bearer token authentication (SDK JWT or platform UI session).

| Endpoint | Method | Description |
|---|---|---|
| `/manifest` | GET | Returns current snapshot details plus transient build state. Supports ETag/304. |
| `/config` | GET | Returns renderer selection (`cosmos` or `d3`) based on role and feature flag. |
| `/status` | GET | Admin-only diagnostics: queue depth, pending count, active workers, artifact health. |
| `/rebuild` | POST | Admin-only. Queues an audited rebuild request. Returns `accepted` + `queued`/`coalesced`. |
| `/snapshots/{version}/points` | GET | Streams the points Arrow file. Supports `Range` headers and `206 Partial Content`. |
| `/snapshots/{version}/links` | GET | Streams the links Arrow file. Same streaming and range support. |
| `/nodes/{node_id}` | GET | Fetches full inspector data for a selected node from FalkorDB. |
| `/client-metrics` | POST | Records allow-listed browser renderer telemetry (ready, load_failed, webgl_fallback). |

The manifest response includes a `capacity.supported` flag that is `false` when node or link counts exceed configurable maximums (`knowledge_graph_max_client_nodes`, `knowledge_graph_max_client_links`). The client refuses to load unsupported snapshots.

Artifact delivery uses presigned URLs when the object store supports them, with a server-side fallback. Responses set `Cache-Control: public, max-age=31536000, immutable` and `ETag` set to the SHA-256 checksum.

---

## Graph Visualization

### Snapshot Client

The frontend `loadKnowledgeGraphSnapshot()` function orchestrates the browser-side load:

1. Fetch the manifest (authenticated, no cache)
2. Validate state is `ready` and capacity is supported
3. Fetch points and links Arrow buffers in parallel
4. Verify SHA-256 checksum and byte size for each buffer
5. Decode in a Web Worker
6. Return `{ manifest, nodes, edges }`

### Web Worker Decoder

The `snapshotDecoder.worker.ts` uses `apache-arrow`'s `tableFromIPC` to deserialize Arrow IPC files. It maps integer `source`/`target` indices in links to string node IDs from the points array. All decoding happens off the main thread.

### D3.js Renderer

The default renderer in production. Uses the force-directed layout from the legacy graph UI.

### Cosmos.gl WebGL Renderer

The new renderer, default in development and feature-flagged for production.

Configuration:
- `enableSimulation: false` (positions are pre-computed in the Arrow file)
- `fitViewOnInit: true`
- `pixelRatio: min(devicePixelRatio, 1.5)`
- `spaceSize: 4096`
- Drag, click selection, neighbor highlighting, and background click deselection
- Search filter highlights matching nodes by label or group
- Category highlight filters by domain category

Category color mapping:

| Category | Color |
|---|---|
| backend | `#2563EB` |
| frontend | `#7C3AED` |
| security | `#DC2626` |
| documentation | `#16A34A` |
| configuration | `#F59E0B` |
| testing | `#EC4899` |
| database | `#0891B2` |
| ci/cd | `#EA580C` |
| infrastructure | `#6366F1` |
| dependencies | `#8B5CF6` |
| code | `#3B82F6` |
| data | `#14B8A6` |
| other | `#64748B` |

Node sizes scale with degree: root = 18, source hubs = 13, others = `min(11, 3.1 + sqrt(degree) * 1.05)`.

### Renderer Selection

The `/config` endpoint returns `{ "renderer": "cosmos" }` or `{ "renderer": "d3" }` based on:
- `knowledge_graph_renderer` setting must be `"cosmos"`
- User's roles must intersect `cosmos_roles` (or contain `"*"`)

### Benchmark Badge

`GraphBenchmarkBadge` samples 5 seconds of `requestAnimationFrame` after the `ecms:knowledge-graph-ready` custom event and reports:
- Interactive time (ms)
- Average FPS
- Slow frame percentage (frames > 33.34ms)
- DOM element count
- Heap size (Chrome-only)

Results are downloadable as JSON.

### Synthetic Graph

`createSyntheticGraph(nodeCount)` generates deterministic scale fixtures (100K, 500K, 1M nodes) with two edges per node (ring + skip) for benchmarking. Uses the same `KnowledgeGraphNode`/`KnowledgeGraphEdge` interfaces as the real data path.

### Performance Targets

- 5 seconds to interactive for production graph sizes
- 30 FPS sustained during interaction
- 100ms node selection response time

---

## Categories

User-defined taxonomy stored in the `categories` PostgreSQL table. The categorization agent uses each category's description as ground truth.

Default categories:

| Name | Description | Priority |
|---|---|---|
| security | Auth, tokens, secrets, encryption, credentials, access control | 1 |
| infrastructure | IaC, Docker, K8s, CI/CD, cloud config, networking, Terraform | 2 |
| database | Schemas, migrations, ORM models, SQL, data access layers | 3 |
| frontend | UI components, React/Vue/Svelte, styles, client-side bundles | 4 |
| backend | APIs, services, business logic, server frameworks, route handlers | 5 |
| data-ml | Notebooks, model training, datasets, ML pipelines, data science | 6 |
| documentation | Markdown, docs, READMEs, specs, wikis, architectural write-ups | 7 |
| uncategorized | Catch-all for unclassified nodes | 99 |

Users can add, edit, and delete categories. Each category has a name, description, color, priority, and `is_default` flag.

---

## Categorization Agent

The `run_categorization(workspace_id, project_id)` function explores codebases and classifies every FalkorDB UKO node into a domain category.

### Workflow

1. **Pre-scan**: Walk repository directories up to depth 3 (skipping `node_modules`, `.git`, etc.)
2. **Agent exploration**: Launch an `AgentLoop` with `read_directory`, `read_file`, `glob`, and `grep` tools. The agent reads 15-20 sample files.
3. **Pattern extraction**: The agent returns 25-35 glob patterns mapping file paths to domains. If the agent returns prose instead of JSON, a second LLM call extracts patterns from the full conversation context.
4. **Fallback**: LLM patterns are combined with 50+ built-in fallback patterns covering common extensions and directories.
5. **Apply to FalkorDB**: For each UKO node in the group, classify by matching `source_id` against patterns using `fnmatch`. Set the `domain` property on the node.
6. **Trigger snapshot**: Call `graph_changed` to queue a snapshot rebuild.

### Classification Logic

Pattern matching order:
1. Specific directory patterns (priority 1-10)
2. Broad extension patterns (priority 90-100)
3. Git commits default to `infrastructure`
4. Extension-based fallback (e.g., `.py` -> backend, `.js`/`.tsx` -> frontend, `.yaml` -> infrastructure)

---

## Key Principles

1. **Single graph.** There is exactly one enterprise cognitive graph. All subsystems read and write the same graph. Views are filtered projections, never separate copies.

2. **UCOs are immutable.** Updates create new versions rather than mutating existing objects. The graph index is updated to point to the latest version.

3. **Memory activates, never owns.** Memory workspaces activate knowledge for a session; they do not own or isolate it.

4. **Replaceable stores.** The `GraphStore` protocol decouples the engine from any specific backend. In-memory for tests, FalkorDB for production -- the engine does not change.

5. **Event-sourced mutations.** Every graph mutation emits an immutable event. The graph's evolution is fully auditable and replayable.

6. **Evidence chains.** Every UCO traces back through `Evidence` objects to the UKOs that justify it. Evidence includes source, origin, checksum, and confidence.
