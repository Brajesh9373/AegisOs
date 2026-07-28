# Backend Architecture

How the ECMS backend is organized, how a request flows through it, and where
each concern lives in the codebase.

---

## Directory Layout

```
backend/
├── ecms/                         # Distribution package (all imports start here)
│   ├── api/                      # REST + GraphQL + WebSocket gateways
│   │   ├── rest/                 # Individual route modules (18 files)
│   │   │   ├── health.py         # /health, /ready
│   │   │   ├── metrics.py        # /metrics (Prometheus)
│   │   │   ├── system.py         # /, /version, /whoami
│   │   │   ├── auth.py           # POST /login, /refresh, /logout
│   │   │   ├── cognition.py      # POST /execute, /knowledge/ingest, GET /graph/*
│   │   │   ├── session_chat.py   # POST /sessions, /{id}/chat, GET /messages
│   │   │   ├── projects.py       # GET/DELETE/PUT /projects
│   │   │   ├── agents.py         # Agent CRUD + assignment
│   │   │   ├── categories.py     # Category management
│   │   │   ├── categorize.py     # Categorization endpoints
│   │   │   ├── connector_ingestions.py  # Connector ingestion pipeline API
│   │   │   ├── discovery.py      # Business-analysis discovery endpoints
│   │   │   ├── governance.py     # Governance assignment endpoints
│   │   │   ├── knowledge_graph_snapshots.py  # Snapshot lifecycle
│   │   │   ├── meetings.py       # Meeting management
│   │   │   ├── organization.py   # Org member management
│   │   │   ├── platform.py       # Platform-level endpoints
│   │   │   └── policies.py       # Access policy management
│   │   ├── graphql/router.py     # Strawberry GraphQL
│   │   ├── websocket/            # /ws telemetry, /ws/terminal
│   │   ├── middleware/            # GZip, RateLimit, Metrics, Tracing, Ctx, CORS
│   │   └── errors/               # Exception handlers
│   │
│   ├── administration/           # Admin DDD module (hexagonal)
│   ├── agent/                    # Agent system — ReAct loop, categorization, policy, BA discovery
│   ├── analytics/                # Analytics DDD module (hexagonal)
│   ├── auth/                     # JWT auth, RBAC+ABAC, encryption, compliance
│   ├── cli/                      # Typer CLI (ecms serve, ecms worker)
│   ├── configuration/            # Pydantic-settings config with ECMS_ env vars + profiles
│   ├── connectors/               # Connector framework + async ingestion pipeline
│   │   └── ingestion/            # Coordinator, manifest, partitions, extraction, graph writer
│   ├── core/                     # Domain primitives — value objects, enums, base entities
│   ├── events/                   # Event bus (in-memory + persistent) + event store
│   ├── graph/                    # Global Cognitive Graph — nodes, edges, subgraph ops
│   ├── infrastructure/           # DI container, telemetry, cache, storage
│   ├── intelligence/             # Intelligence layer — planner, goals, strategies, decisions
│   ├── knowledge/                # Knowledge Engine — code analysis, ontology mapping
│   ├── main.py                   # FastAPI app factory (create_app)
│   ├── memory/                   # Memory Engine — ranking, activation, caching
│   ├── monitoring/               # Monitoring DDD module (hexagonal)
│   ├── persistence/              # PostgreSQL — models, repositories, migrations, UoW, saga
│   ├── plugins/                  # Plugin system DDD module (hexagonal)
│   ├── promotion/                # Promotion Engine — only write path for enterprise knowledge
│   ├── providers/                # Connector framework — filesystem, credentials, registry
│   ├── reflection/               # Reflection Engine — post-task pattern extraction
│   ├── runtime/                  # Runtime Kernel — 14-step pipeline, sessions, tasks, agents
│   ├── sdk/                      # EcmsSDK facade + CognitiveSystem assembly
│   ├── shared/                   # Base models, value objects, enums, interfaces
│   ├── telegram/                 # Telegram bot integration
│   ├── tools/                    # Tool runtime — filesystem, HTTP, sandbox, permissions
│   ├── visualization/            # Knowledge graph visualization + snapshot workers
│   └── websocket/                # WebSocket gateway for real-time updates
│
├── config/                       # Deployment profile YAML overlays
├── alembic.ini                   # Database migration config
└── pyproject.toml                # Package dependencies (uv)
```

### DDD Hexagonal Architecture

Most domain modules (`administration/`, `agent/`, `analytics/`, `connectors/`,
`events/`, `monitoring`, `plugins/`, `visualization/`) follow the same internal
hexagonal (ports-and-adapters) layout:

```
module/
├── domain/         # Entities, value objects, domain events, invariants
├── application/    # Use cases / command handlers
├── interfaces/     # Port interfaces (what the module needs from the outside)
├── infrastructure/ # Adapter implementations (DB, HTTP, message bus)
├── repositories/   # Repository interfaces + implementations
├── schemas/        # Pydantic request/response schemas
├── services/       # Domain services (stateless business logic)
├── events/         # Module-specific event definitions
└── tests/          # Module-scoped tests
```

Dependencies flow inward: `infrastructure → application → domain`. Modules
communicate only through the Event Bus or public interface contracts.

---

## How a Request Flows

### 1. API Gateway (`ecms/api/app.py`)

The FastAPI app factory wires everything at startup:

```
Browser / SDK
    │
    ▼
Middleware Stack (6 layers)
├── GZipMiddleware       — compress responses >= 500 bytes
├── RateLimitMiddleware   — per-IP rate limiting
├── MetricsMiddleware     — Prometheus request metrics
├── TracingMiddleware     — OpenTelemetry span injection
├── RequestContextMiddleware — correlation ID propagation
└── CORS                  — configurable origins
    │
    ▼
Route Handler  →  Kernel API  →  Engines  →  Response
```

### 2. Cognitive Pipeline

```
POST /api/v1/execute { prompt, organization_id, user_id }
    │
    ▼
RuntimeKernel.execute()
    │
    ├── 1.  Session Manager     — get or create session
    ├── 2.  Task Manager        — create task for this execution
    ├── 3.  Attach task to session
    ├── 4.  Emit PromptReceived event
    ├── 5.  Task Started
    ├── 6.  Agent Orchestrator  — create + assign agent
    ├── 7.  Planner (optional)  — decompose goals, build strategy
    ├── 8.  Memory Engine       — activate relevant knowledge
    ├── 9.  Knowledge Engine    — resolve activated UCOs from graph
    ├── 10. Tool Runner (opt)   — execute permission-gated tools
    ├── 11. Reflection (opt)    — extract patterns, lessons
    ├── 12. Promotion (opt)     — validate → dedup → approve → write
    ├── 13. Graph Engine        — update graph with new knowledge
    └── 14. Release Memory + Complete
    │
    ▼
ExecutionResult { session_id, task_id, ... }
```

Each step emits a typed event on the Enterprise Event Bus. Steps 7, 10, 11, and 12
are **optional** — the kernel skips them if their collaborators aren't wired.

### 3. Agentic Chat Flow (ReAct)

```
POST /sessions/{id}/chat { prompt }
    │
    ▼
AgentLoop (agent/loop.py)  —  max 20 iterations
    │
    ├── Build messages: system prompt + conversation history + working memory
    ├── LLM call (OpenAI-compatible) with tool definitions
    ├── Agent decides: RESPOND or CALL TOOLS
    │   ├── RESPOND → return answer
    │   └── CALL TOOLS → invoke tool → append result → loop again
    ▼
Return: answer + trace
    │
    ▼
Post-chat (fire-and-forget):
├── Persist user + assistant messages to PostgreSQL
├── Record episode in NDJSON log
├── Capture to mem0 semantic memory (if enabled)
├── Write GBrain markdown note
├── Extract structured atoms via ConversationExtractor
└── Sync FalkorDB + GBrain → atom store (every 2 min)
```

The agent system (`agent/`) includes:
- **ReAct loop** (`loop.py`) — iterative reason-act cycle with tool calling
- **Categorization** (`categorize.py`) — auto-classify incoming content
- **Policy agent** (`policy_agent.py`) — enforce access policies during execution
- **BA discovery** (`ba/`) — guided business-analysis discovery with team schemas
  and exemplars
- **Working memory** (`working_memory.py`) — per-session scratch space for agents
- **Access engine** (`access_engine.py`) — permission evaluation for tool calls

### 4. Connector Ingestion Pipeline (Async)

The old synchronous Git sync has been replaced by a fully async, parallel
ingestion pipeline:

```
POST /connector-ingestions { project_id, connector_type, config }
    │
    ▼
ConnectorIngestionCoordinator (coordinator.py)
│   — Creates ConnectorIngestionJob (status=pending)
│   — Launches parent dispatcher
    │
    ▼
ParentDispatcher (parent_dispatcher.py)
│   — Spawns extraction workers as separate processes
    │
    ▼
ExtractionWorker (extraction_worker.py)
│   — Reads ConnectorIngestionPartition
│   — Runs extraction_runtime (extraction_runtime.py)
│   — Produces extraction results → queues for graph writer
    │
    ▼
GraphWriter (graph_writer.py)
│   — Receives extraction results
│   — Acquires graph semaphore (graph_semaphore.py) — bounded concurrency
│   — Writes nodes/edges to graph database
    │
    ▼
FanIn (fan_in.py)
│   — Waits for all partitions to complete
│   — Aggregates results into ConnectorIngestionStageBatch
    │
    ▼
ConnectorIngestionManifest (manifest.py)
    — Final manifest with ingestion stats, errors, timing
```

Key components:
- **Coordinator** — orchestrates the full lifecycle: job creation, partition
  dispatch, monitoring, completion/failure handling
- **Manifest** — immutable record of what was ingested (files, commits, errors)
- **Partition** — unit of work assigned to a single extraction worker
- **Extraction workers** — run as separate processes; handle code parsing,
  AST extraction, file analysis
- **Graph writer** — writes extracted knowledge to the graph with bounded
  concurrency via a semaphore
- **Fan-in** — collects all partition results, builds the stage batch
- **Scanner** (`scanner.py`) — discovers source files to partition
- **Parallel health** (`parallel_health.py`) — monitors worker health
- **Staging cleanup** (`staging_cleanup.py`) — cleans up temp files after ingestion

### 5. Knowledge Graph Snapshots

```
Graph change detected
    │
    ▼
SnapshotQueue (snapshot_queue.py)  — debounced, coalesced
    │
    ▼
SnapshotWorker (snapshot_worker.py)
    │
    ▼
KnowledgeGraphSnapshot persisted (versioned, point-in-time)
```

The visualization module provides graph rendering and snapshot lifecycle
management through its own hexagonal module.

---

## Dual Codebase: Modern + Legacy

The backend has two code layers that both serve live traffic:

| Layer | Location | Role |
|-------|---------|------|
| **Modern** | `backend/ecms/` (28 modules) | API gateway, cognitive pipeline, agent loop, connector ingestion, persistence, auth, SDK, event bus |
| **Legacy** | `legacy/src/legacy_ecms/` (6 modules) | Git/MySQL providers, GBrain memory, mem0 semantic memory, pipeline orchestration, legacy graph query |

The legacy layer is **not deprecated** — it provides the actual Git sync, MySQL sync,
GBrain markdown notes, Qdrant-based semantic memory, and pipeline orchestration that
the modern routes depend on. Both are mounted inside the same FastAPI app in `create_app()`.

### Legacy modules serving live traffic

| Module | Purpose |
|--------|---------|
| `providers/git/`, `providers/mysql/` | Clone repos, parse code, extract UKOs |
| `pipeline/` | Structural/semantic/temporal/identity extraction |
| `memory/brain.py` | GBrain — markdown file-based deliberative notes |
| `memory/mem0_layer.py` | mem0 — Qdrant-based semantic memory with LLM extraction |
| `memory/bridge.py` | UnifiedMemoryBridge — syncs FalkorDB + GBrain to atom store |
| `memory/cognitive_orchestrator.py` | Consolidation, Promotion, Validation, Decay loop |
| `memory/stores/file_store.py` | NDJSON-based atom store with O(1) lookups |
| `core/graph.py` | GraphClient — FalkorDB read/write adapter |
| `core/uko.py` | UniversalKnowledgeObject model |

---

## SDK

The SDK (`sdk/`) provides the programmatic entry point for external consumers:

- **EcmsSDK** (`facade.py`) — high-level facade exposing all system capabilities
  through a single object. Handles auth, retries, connection management.
- **CognitiveSystem** (`cognitive.py`) — assembles the full cognitive pipeline
  (runtime kernel + engines + event bus) for standalone or embedded use.
- **Simulation** (`simulation.py`) — dry-run mode for testing without side effects.
- Sub-packages for auth, authz, config, events, health, logging, metrics,
  plugins, tracing, and utils.

---

## Event Bus

The events module (`events/`) provides a dual-mode event bus:

- **In-memory bus** — synchronous dispatch for same-process subscribers. Used
  for real-time event propagation within a single request lifecycle.
- **Persistent store** — events are persisted to the `event_store` table for
  replay, audit, and cross-process communication. Append-only with auto-
  incrementing sequence numbers.

Events are the **only** cross-module communication mechanism. Every mutation
publishes a typed event. Subscribers register for specific event types and
process them independently.

---

## Persistence Patterns

### Unit of Work

`persistence/unit_of_work.py` implements the Unit of Work pattern:

- Groups multiple repository operations into a single atomic transaction
- Commits all changes at once or rolls back on failure
- Ensures consistency across aggregate boundaries
- Used by application-layer use cases to coordinate writes

### Saga Pattern

`persistence/saga.py` implements the Saga pattern for long-running, multi-step
operations:

- Each step has an action and a compensating action
- If a step fails, compensating actions run in reverse order
- Used for operations that span multiple aggregates or external services
- Ensures eventual consistency without distributed locks

---

## Database Schema (PostgreSQL — 22 tables)

### Core Domain

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `agents` | Agent hierarchy (self-referential) | `id`, `parent_id` (FK self), `name`, `type`, `status` |
| `organization_members` | Org membership | `id`, `organization_id`, `user_id`, `role` |
| `projects` | Workspace projects | `id`, `workspace_id` (unique), `name`, `group_id` |
| `project_connectors` | Per-project connector configs | `project_id` (FK CASCADE), `connector_type`, `config` (JSON) |
| `tasks` | Task tracking (self-referential parent) | `id`, `parent_id` (FK self), `project_id`, `status` |
| `task_dependencies` | Task dependency graph | `task_id`, `depends_on_id` |
| `cross_team_requests` | Cross-team collaboration | `id`, `requester_org`, `target_org`, `status` |

### Governance & Access

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `project_agent_governance_assignments` | Agent governance rules | `project_id`, `agent_id`, `policy_id` |
| `access_policies` | Access control policies | `id`, `name`, `rules` (JSON), `scope` |
| `policy_recommendations` | AI-suggested policy changes | `id`, `policy_id`, `recommendation`, `confidence` |
| `categories` | Content categories | `id`, `name`, `parent_id`, `metadata` (JSON) |

### Sessions & Chat

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `sessions` | Chat sessions | `id`, `workspace_id`, `title`, `status` |
| `session_messages` | Chat message history | `session_id` (FK CASCADE), `role`, `content`, `created_at` |
| `session_context_kv` | Per-session key-value store | `session_id`, `key`, `value` (JSON) |

### Knowledge & Snapshots

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `knowledge_graph_snapshots` | Versioned graph snapshots | `id`, `project_id`, `version`, `snapshot_data` (JSON) |

### Connector Ingestion

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `connector_ingestion_jobs` | Ingestion job lifecycle | `id`, `project_id`, `connector_type`, `status`, `config` (JSON) |
| `connector_ingestion_manifests` | Immutable ingestion record | `job_id` (FK), `files_ingested`, `errors`, `timing` (JSON) |
| `connector_ingestion_partitions` | Unit of extraction work | `id`, `job_id` (FK), `partition_key`, `status`, `result` (JSON) |
| `connector_ingestion_stage_batches` | Fan-in aggregation | `job_id` (FK), `stage`, `batch_data` (JSON) |

### Infrastructure

| Table | Purpose | Key Columns |
|-------|---------|-------------|
| `aggregates` | Generic versioned JSON store | `id`, `aggregate_type`, `workspace_id`, `data` (JSON), `version` |
| `event_store` | Append-only event sourcing log | `sequence` (autoincrement), `event_id`, `event_type`, `payload` (JSON) |
| `audit_records` | Audit trail | `id`, `actor`, `action`, `resource`, `outcome` |

---

## Configuration

Settings use **Pydantic-settings** with the `ECMS_` environment variable prefix.
Deployment profiles are YAML overlays in `config/`:

```
config/
├── base.yaml           # Shared defaults
├── development.yaml    # Dev overrides (local services, debug flags)
├── staging.yaml        # Staging overrides
└── production.yaml     # Production overrides (TLS, replicas, resource limits)
```

Resolution chain: `base.yaml` → `{profile}.yaml` → `ECMS_*` environment variables.

The `Settings` class (`configuration/schemas/settings.py`) reads all config under
the `ECMS_` prefix. Key variables:

| Variable | Default | Purpose |
|----------|---------|---------|
| `ECMS_DATABASE_URL` | `postgresql+asyncpg://ecms:ecms@postgres:5432/ecms` | Primary database |
| `ECMS_FALKORDB_URL` | `redis://falkordb:6379` | Graph database |
| `ECMS_REDIS_URL` | `redis://redis:6379/0` | Session cache |
| `ECMS_MEM0_QDRANT_URL` | `http://qdrant:6333` | Vector store |
| `ECMS_OPENAI_API_KEY` | — | LLM API key |
| `ECMS_LLM_MODEL` | `gpt-4o-mini` | Default model |
| `ECMS_ENVIRONMENT` | `development` | Deployment profile (selects YAML overlay) |

---

## Invariants

- **Every mutation publishes an event.** No side-effects without an event.
- **Interfaces are frozen contracts.** Implementations may change; signatures may not.
- **Ports have in-memory defaults.** The system runs offline without external services.
- **Dependencies flow inward:** `domain ← application ← infrastructure`.
- **Subsystems communicate only through the Event Bus or public interfaces.**
- **Promotion is the only write path** for enterprise knowledge.
- **Unit of Work groups related mutations.** No partial commits across aggregate boundaries.
- **Connector ingestion is fully async.** Workers run as separate processes; graph
  writes are bounded by a semaphore.
