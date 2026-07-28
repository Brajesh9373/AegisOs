# ECMS Architecture

The **Enterprise Cognitive Memory System** is an operating system for organizational
knowledge — 18+ containers, 6 storage backends, and a dual-layer Python/TypeScript
runtime that together ingest, understand, organize, activate, and execute enterprise
knowledge.

---

## System Overview

```
┌────────────────────────────────────────────────────────────────┐
│  FRONTEND  ·  React 18 + Vite + Ant Design  ·  :3000          │
│  Mission Control: sessions, graph, projects, agents, tasks     │
└─────────┬──────────────────────────────┬───────────────────────┘
          │ REST API (:8000)             │ WebSocket /ws
          ▼                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  BACKEND  ·  FastAPI  ·  :8000                                 │
│  ═══════════════════════════════════════════════════════════    │
│  Modern routes (ecms/api/rest/)     Legacy routes (live)       │
│  /health  /metrics  /api/v1/*       /providers/git/sync        │
│  /sessions/*  /projects/*           /providers/mysql/sync      │
│  /graphql  /api/v1/auth/*           /workspaces/*  /memory/*   │
│                                     /ingest/uko  /query         │
│                                                              │
│  Cognitive Pipeline:                                          │
│  Knowledge → Graph → Memory → Runtime → Tools                 │
│  Reflection → Promotion → Intelligence                        │
│  Agent Loop (ReAct) + WebSocket Telemetry                     │
│                                                              │
│  Connector Ingestion:                                         │
│  Coordinator → Manifest → Partition → Extraction Workers      │
│  → Graph Writer → Fan-in → Snapshot                           │
└──┬───────┬──────────┬──────────┬───────────┬──────────────────┘
   │       │          │          │           │
   ▼       ▼          ▼          ▼           ▼
┌─────┐ ┌──────┐ ┌──────┐ ┌─────┐ ┌──────────────────────┐
│ PG  │ │Falkor│ │Qdrant│ │Redis│ │ MinIO (:9000)        │
│:5432│ │DB    │ │:6333 │ │:6379│ │ S3-compatible        │
│     │ │:6380 │ │      │ │     │ │ Object Store         │
│Sess-│ │Graph │ │Vector│ │Cache│ │                      │
│ions │ │UKOs  │ │mem0  │ │Queue│ │                      │
│Proj-│ │Edges │ │      │ │     │ │                      │
│ects │ │      │ │      │ │     │ │                      │
└─────┘ └──────┘ └──────┘ └─────┘ └──────────────────────┘

OBSERVABILITY: Prometheus :9090 + Loki :3100 + Tempo :3200 → Grafana :3300
```

---

## Architecture Style: DDD Hexagonal

The backend follows **Domain-Driven Design with Hexagonal (Ports & Adapters) architecture**.
Each bounded context is a self-contained module with its own domain models, ports (interfaces),
and adapters (implementations). Heavy dependencies (LLMs, graph DB, vector DB) sit behind
frozen port interfaces with in-memory defaults, making every component replaceable.

### Bounded Contexts (29 modules)

| Module | Responsibility |
|--------|---------------|
| `knowledge/` | Knowledge ingestion, transformation, UKO → UCO pipeline |
| `memory/` | Atom store, episodic memory, memory bridge (FalkorDB + GBrain sync) |
| `graph/` | FalkorDB graph operations, traversal, consistency checks |
| `intelligence/` | LLM integration, embeddings, semantic analysis |
| `reflection/` | Post-execution reflection, learning from outcomes |
| `promotion/` | Knowledge promotion — the **only** write path for enterprise knowledge |
| `runtime/` | Execution runtime, tool dispatch, session lifecycle |
| `events/` | Event sourcing, immutable event store, event replay |
| `auth/` | JWT authentication, RBAC, access policies |
| `connectors/ingestion/` | Connector ingestion pipeline (Git, GitHub, GitLab, Bitbucket) |
| `configuration/` | Settings, schemas, environment management |
| `agent/` | ReAct loop, categorization agent, policy agent, BA discovery agent |
| `administration/` | Org management, user administration |
| `analytics/` | Usage analytics, metrics aggregation |
| `api/` | REST + GraphQL + WebSocket endpoints |
| `cli/` | CLI entry points, worker commands |
| `core/` | Shared domain primitives, value objects |
| `infrastructure/` | Cross-cutting concerns, DI container |
| `monitoring/` | Health checks, readiness probes |
| `persistence/` | SQLAlchemy models, Alembic migrations, repositories |
| `plugins/` | Plugin system, extension points |
| `providers/` | External system adapters (Git, MySQL) |
| `sdk/` | Developer SDK, client libraries |
| `shared/` | Shared utilities, common types |
| `telegram/` | Telegram bot integration |
| `tools/` | Tool definitions, tool registry |
| `visualization/` | Knowledge graph snapshot worker, rendering |
| `websocket/` | WebSocket manager, telemetry bridge |

---

## Connector Ingestion Pipeline

The connector ingestion system supports **Git, GitHub, GitLab, and Bitbucket** sources.
Two execution paths exist:

### Single Worker (Active by Default)

```
Connector Source → Coordinator → Manifest → Partition → Worker (sequential)
  (Git/GitHub/       (scan,       (file     (group     (extract, encode,
   GitLab/BB)         plan)        list)     files)     write to graph)
```

### Parallel Partitioned (Disabled by Default)

```
Connector Source → Coordinator → Manifest → Partitions → Extraction Workers (N)
  (Git/GitHub/       (scan,       (file     (group     (parallel extraction,
   GitLab/BB)         plan)        list)     files)     encode to Arrow batches)
                                                            │
                                                            ▼
                                                     Graph Writer (1)
                                                      (write to FalkorDB)
                                                            │
                                                            ▼
                                                        Fan-in
                                                      (merge results)
                                                            │
                                                            ▼
                                                       Snapshot
                                                  (KnowledgeGraphSnapshot)
```

**Key components:**
- **Coordinator** — scans connector source, builds manifest of files to process
- **Manifest** — ordered list of files with metadata (path, size, SHA)
- **Partitioning** — groups files into partitions (target ~100 files each)
- **Extraction Workers** — process partitions in parallel (configurable count, default 4)
- **Graph Writer** — writes extracted knowledge to FalkorDB (configurable concurrency)
- **Fan-in** — merges partition results, triggers snapshot
- **Semaphore** — limits concurrent graph writes to prevent overload

**Configuration:**
- `ECMS_CONNECTOR_PARALLEL_INGESTION_ENABLED` — toggle parallel mode (default: `false`)
- `ECMS_CONNECTOR_EXTRACTION_WORKER_COUNT` — parallel extraction workers (default: `4`)
- `ECMS_CONNECTOR_GRAPH_WRITER_CONCURRENCY` — concurrent graph writers (default: `1`)
- `ECMS_CONNECTOR_INGESTION_PARTITION_TARGET_FILES` — files per partition (default: `100`)
- `ECMS_CONNECTOR_INGESTION_MAX_ACTIVE_PARTITIONS_PER_ORG` — per-org limit (default: `8`)
- `ECMS_CONNECTOR_INGESTION_MAX_STAGED_BYTES_PER_ORG` — staged data cap (default: `10GB`)

---

## Agent System

The agent system implements a **ReAct (Reason + Act) loop** with specialized sub-agents:

### Core Loop (`agent/loop.py`)
```
User Message → Context Assembly → LLM (ReAct) → Tool Dispatch → Observation → Loop
                                    ↑                                    │
                                    └────────────────────────────────────┘
                                    (until final answer or max iterations)
```

### Specialized Agents

| Agent | File | Purpose |
|-------|------|---------|
| **Categorization Agent** | `agent/categorize.py` | Classifies incoming messages, routes to appropriate handler |
| **Policy Agent** | `agent/policy_agent.py` | Evaluates access policies, enforces RBAC before actions |
| **BA Discovery Agent** | `agent/ba/` | Guided business analysis discovery, requirement extraction |
| **Orchestrator** | `agent/orchestrator.py` | Multi-step task coordination, sub-agent delegation |

### Supporting Infrastructure

- **Working Memory** (`agent/working_memory.py`) — scratchpad for multi-step reasoning
- **Session Context** (`agent/session_context.py`) — per-session state, conversation history
- **Tool Capture** (`agent/tool_capture.py`) — records tool invocations for replay/audit
- **Access Engine** (`agent/access_engine.py`) — enforces access policies at runtime
- **Permissions** (`agent/permissions.py`) — permission evaluation, role resolution

---

## Legacy Runtime

The legacy runtime (`legacy/src/legacy_ecms/`) remains partially active for backward
compatibility:

### Active Legacy Components

| Component | Purpose |
|-----------|---------|
| **UKO Pipeline** (`pipeline/`) | Git clone → AST parse → UKO extraction → FalkorDB write |
| **GBrain** (`core/`) | Graph-based reasoning, workspace-scoped knowledge |
| **Mem0** (via `memory/`) | Semantic memory with Qdrant embeddings |
| **GraphClient** (`core/graph.py`) | FalkorDB client, Cypher query execution |

### Memory Bridge

A background process syncs **FalkorDB + GBrain** into the atom store every **2 minutes**:
- Reads UKOs from FalkorDB
- Transforms into memory atoms (NDJSON)
- Updates `memory_atoms.ndjson`, `memory_index.json`, `memory_rels.json`
- Maintains `memory_bridge_hashes.json` for change detection (SHA-based)

---

## Services (18+ Docker containers)

| Service | Port | Purpose |
|---------|------|---------|
| **frontend** | `3000` | React 18 + Vite Mission Control UI — ~46 pages, real-time telemetry, graph visualization |
| **backend** | `8000` | FastAPI API gateway — REST, GraphQL (Strawberry), WebSocket, SSE, full cognitive pipeline |
| **postgres** | `5432` | Primary database — 20+ tables, 42 sequential Alembic migrations |
| **falkordb** | `6380` | Property graph — all UKOs (13K+ nodes), edges, workspaces |
| **qdrant** | `6333` | Vector store — semantic memory (mem0 embeddings) |
| **redis** | `6379` | Session cache, workspace-scoped context (24h TTL), rate limiting |
| **minio** | `9000` | S3-compatible object store — memory persistence, artifacts, knowledge graph snapshots |
| **minio-init** | — | One-shot: creates S3 buckets on first boot |
| **prometheus** | `9090` | Metrics collection — 20 alert rules (knowledge graph + connector ingestion) |
| **loki** | `3100` | Log aggregation |
| **tempo** | `3200` | Distributed tracing (OpenTelemetry OTLP) |
| **grafana** | `3300` | Unified dashboards |
| **knowledge-snapshot-worker** | — | Builds knowledge graph snapshots for visualization |
| **connector-ingestion-init** | — | One-shot: creates workspace directories |
| **connector-ingestion-worker** | — | Connector ingestion pipeline (single-worker or parent dispatcher) |
| **connector-ingestion-extractor** | — | Parallel extraction worker (profile: `parallel-ingestion`, disabled by default) |
| **connector-ingestion-graph-writer** | — | Parallel graph writer (profile: `parallel-ingestion`, disabled by default) |
| **worker-knowledge** | — | Knowledge engine tasks |
| **worker-reflection** | — | Post-execution reflection |
| **worker-promotion** | — | Knowledge promotion pipeline |
| **telegram-bot** | — | Telegram bot integration |

---

## Data Flow

```
External Systems  →  Connectors  →  UKO  →  Knowledge Engine  →  UCO  →  Graph
  (Git, GitHub,      (providers)    (raw)     (AST, ontology)     (truth)   (index)
   GitLab, BB,
   MySQL, Jira...)
                                                                     ▲
                                          Reflection → Promotion ────┘
                                                ↑
                                          Memory Activation
                                                ↑
                                          Agent Loop (ReAct)
```

- **Connectors** ingest from external systems (Git repos, GitHub, GitLab, Bitbucket, MySQL databases)
- **UKO** (Universal Knowledge Object) = raw extracted knowledge
- **Knowledge Engine** transforms UKOs into typed **UCOs** (Universal Cognitive Objects)
- **Graph** indexes UCOs as nodes and relationships in FalkorDB
- **Memory** activates relevant knowledge for the current task
- **Agent Loop** uses LLM + tools to reason, plan, and execute
- **Reflection → Promotion** is the **only** write path for permanent enterprise knowledge

---

## Frontend — Mission Control

- **Framework:** React 18 + TypeScript + Vite
- **UI library:** Ant Design v6
- **State:** Component-local `useState` + `LifecycleContext`
- **Graph viz:** D3.js + Cosmos.gl (WebGL) + Apache Arrow
- **Real-time:** WebSocket telemetry bridge, SSE for streaming agent chat

### Routes (~46 pages)

| Route | Purpose |
|-------|---------|
| `/login` | Authentication |
| `/install` | Installation wizard (first-run setup) |
| `/home` | Dashboard — health cards, execution status, summary stats |
| `/users` | User management (Org Admin only) |
| `/customers` | Customer registry |
| `/customers/:id` | Customer details |
| `/opportunities` | Opportunity pipeline |
| `/opportunities/new` | New opportunity wizard |
| `/opportunities/:id` | Opportunity details |
| `/opportunities/:id/discovery` | AI-powered general discovery |
| `/opportunities/:id/rfq` | RFQ builder |
| `/opportunities/:id/budget` | Budget estimation |
| `/opportunities/:id/proposal` | Proposal generation |
| `/opportunities/:id/approve` | Opportunity approval |
| `/opportunities/:id/init` | Project initialization |
| `/projects` | Projects list |
| `/projects/:id` | Project details |
| `/projects/:id/workspace` | Project workspace |
| `/projects/new` | Create new project |
| `/queue` | Human queue — tasks awaiting human input |
| `/notifications` | Notification center |
| `/artifacts` | Artifact browser |
| `/administration` | Platform administration |
| `/connectors` | Connector management |
| `/connectors/catalog` | Connector catalog |
| `/connectors/:id` | Connector details |
| `/knowledge` | Knowledge browser |
| `/knowledge/catalog` | Knowledge catalog |
| `/knowledge/:id` | Knowledge details |
| `/graph` | Knowledge graph explorer |
| `/employees` | Employee list |
| `/employees/:id` | Employee details |
| `/implementation` | Implementation studio |
| `/skills` | Skill catalog |
| `/skills/:id` | Skill details |
| `/settings` | Platform settings |
| `/operations` | Operations console |
| `/workspace` | Workspace management |
| `/workspace/tokens` | Workspace tokens |
| `/chat` | AI agent chat |

---

## Backend — API Gateway

### Route Inventory

**Modern routes** (`backend/ecms/api/rest/`):

| Prefix | Key Endpoints | Purpose |
|--------|--------------|---------|
| (root) | `/health`, `/ready`, `/metrics` | Ops probes |
| `/api/v1` | `POST /execute`, `POST /knowledge/ingest`, `GET /knowledge/search`, `GET /graph/*` | Cognitive pipeline, knowledge CRUD, graph traversal |
| `/sessions` | `POST /sessions`, `POST /sessions/{id}/chat`, `GET /sessions`, `GET /sessions/{id}/messages` | Agentic chat (SSE streaming), session history |
| `/projects` | `GET /projects`, `DELETE /projects/{id}`, `PUT /projects/{id}` | Workspace management, cascade delete |
| `/api/v1/auth` | `POST /login`, `POST /refresh`, `POST /logout` | JWT authentication |
| `/graphql` | Strawberry GraphQL | Query endpoint |

**Legacy routes** (live, not deprecated — mounted in the same app):

| Prefix | Key Endpoints | Purpose |
|--------|--------------|---------|
| `/providers` | `POST /git/sync`, `POST /mysql/sync` | Git clone + MySQL schema sync → UKOs |
| `/workspaces` | `POST /workspaces`, `GET /workspaces/{id}/graph` | Workspace node CRUD |
| `/memory` | `POST /notes`, `GET /notes`, `POST /remember`, `POST /consolidate` | GBrain + mem0 memory |
| `/ingest` | `POST /uko` | Direct UKO ingestion |
| `/legacy-graph` | `GET /data`, `GET /consistency` | Graph retrieval + repair |
| `/query` | `POST /` | Legacy agent query |

**Real-time Protocols:**

| Path | Protocol | Purpose |
|------|---------|---------|
| `/ws` | WebSocket | Telemetry bridge — event bus → Mission Control, with replay + gap recovery |
| `/ws/terminal` | WebSocket | PTY-bridged CLI (`command-code`) |
| `/sessions/{id}/chat` | SSE | Streaming agent responses (Server-Sent Events) |

### Middleware Stack (6 layers, applied in order)
1. **GZipMiddleware** — compress responses >= 500 bytes
2. **RateLimitMiddleware** — per-IP rate limiting
3. **MetricsMiddleware** — Prometheus request metrics
4. **TracingMiddleware** — OpenTelemetry span injection
5. **RequestContextMiddleware** — correlation ID propagation
6. **CORS** — configurable origins, credentials, methods

---

## Storage — 6 Backends

| Store | Technology | What It Holds |
|-------|-----------|---------------|
| **Relational** | PostgreSQL 16 (via SQLAlchemy 2.0 async + Alembic, 42 migrations) | Agent, OrganizationMember, ProjectAgentGovernanceAssignment, Project, ProjectConnector, Task, TaskDependency, CrossTeamRequest, Session, SessionMessage, SessionContextKV, AccessPolicy, PolicyRecommendation, Category, KnowledgeGraphSnapshot, AggregateRecord, AuditRecord, EventRecord, ConnectorIngestionJob, ConnectorIngestionManifest, ConnectorIngestionPartition, ConnectorIngestionStageBatch |
| **Graph** | FalkorDB (Redis-native property graph) | All UKOs (13K+ nodes), edges, workspaces, `part_of_workspace` relationships |
| **Vector** | Qdrant | Semantic embeddings (mem0) — workspace-scoped collections: `ecms_mem0_{workspace_id}` |
| **Cache** | Redis 7 | Session context keys (`ecms:session:{ws_id}:{session_id}:*`), rate limiting |
| **Object Store** | MinIO (S3-compatible) | Memory persistence, artifacts, knowledge graph snapshots |
| **File-based** | NDJSON + JSON (inside backend container at `/app/memory/`) | Memory atoms, episodes, procedures, session history |

### File-based memory (inside backend container at `/app/memory/`)

| File | Content |
|------|---------|
| `memory_atoms.ndjson` | Structured knowledge atoms — one JSON line per fact |
| `memory_index.json` | Atom ID -> file offset for O(1) lookups |
| `memory_rels.json` | Relationships between atoms |
| `memory_bridge_hashes.json` | UKO -> SHA hash cache for change detection |
| `episodes.ndjson` | Episodic event log — every chat turn |
| `procedures.ndjson` | Learned repeatable procedures |
| `sessions/{id}/history.json` | Per-session LLM conversation history (last 50 messages) |
| `chat-*.md` | GBrain markdown notes from chat |

---

## Key Invariants

- **One Global Cognitive Graph.** Task, session, and knowledge graphs are filtered *views* — never separate graphs.
- **UCOs are the source of truth.** The graph is an index, never reversed.
- **Event-driven.** Every mutation publishes an immutable event.
- **Promotion is the only write path** for enterprise knowledge.
- **Everything is replaceable.** All heavy dependencies (LLMs, graph DB, vector DB) sit behind frozen port interfaces with in-memory defaults.
- **Delete cascades across all 6 stores.** Deleting a project removes data from PostgreSQL, FalkorDB, Qdrant, Redis, disk files, and session tables in one atomic operation.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Language | Python 3.12+ (backend), TypeScript (frontend) |
| API Framework | FastAPI + Strawberry GraphQL + WebSocket + SSE |
| Frontend | React 18 + Vite + Ant Design v6 + D3.js + Cosmos.gl |
| ORM | SQLAlchemy 2.0 async + Alembic (42 migrations) |
| Graph DB | FalkorDB |
| Vector DB | Qdrant |
| Cache | Redis 7 |
| Object Store | MinIO (S3) |
| AI/ML | OpenAI-compatible API, mem0ai |
| Observability | Prometheus (20 alert rules) + Grafana + Loki + Tempo + OpenTelemetry |
| Infrastructure | Docker + Kubernetes (Kustomize + Helm) + Terraform |
| Linting | ruff + mypy (strict) |
