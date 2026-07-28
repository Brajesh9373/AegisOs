# ECMS — Detailed Implementation Plan

> **Last updated:** 2026-07-04  
> **Status:** Foundation implementation complete through Phase 5 scaffold

The repository now contains runnable foundations for all planned phases:

- Phase 0: package scaffold, UKO model, provider contract, Graphiti adapter, FastAPI health endpoint
- Phase 1: Git provider with local/GitHub/Bitbucket sync, deterministic Python/Markdown/JSON/SQL structural extraction, ingestion route
- Phase 2: Jira provider, semantic concept extraction, temporal change events
- Phase 3: live MySQL connector, Slack/Confluence providers, and cross-system identity resolution
- Phase 4: working/session/long-term memory, GBrain notes, agent context assembly and query route
- Phase 5: graph-backed persistence mode, graph health check, API key middleware, request metrics, retry/rate-limit utilities, Docker deployment notes

---

## 1. Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Language** | Python 3.12+ | graphiti-core is Python-native; rich ecosystem for NLP/AST parsing |
| **Graph DB** | FalkorDB (via Docker) | Sub-10ms multi-hop queries, native Graphiti integration, multi-graph isolation |
| **Knowledge Engine** | graphiti-core 0.29.2 (FalkorDB driver) | Temporal context graphs, episodes, entity extraction, hybrid search |
| **LLM Provider** | OpenAI (default) + Anthropic/Gemini fallback | Structured output required for reliable entity/edge extraction |
| **Embeddings** | OpenAI text-embedding-3-small | Default Graphiti embedder; good cost/performance ratio |
| **Memory Layer** | GBrain-inspired self-wiring memory | Markdown-backed, agent-writable, graph-traversable memory |
| **API Layer** | FastAPI | Async-native, Pydantic models, OpenAPI docs, WebSocket support |
| **Task Queue** | Celery + Redis | Incremental sync, background ingestion, retry logic |
| **Infrastructure** | Docker Compose | FalkorDB + Redis + API in unified stack |
| **Package Manager** | uv | Fast, modern Python package management |

---

## 2. Project Structure

```
kgraph/
├── docs/
│   ├── vision.md                     # Vision document (already created)
│   └── implementation-plan.md        # This file
├── docker-compose.yml                # FalkorDB + Redis
├── pyproject.toml                    # Project config, dependencies
├── .env.example                      # Environment template
├── src/
│   ├── __init__.py
│   ├── main.py                       # FastAPI entry point
│   ├── config.py                     # Settings (pydantic-settings)
│   ├── core/
│   │   ├── __init__.py
│   │   ├── graph.py                  # Graphiti init, episode mgmt, search
│   │   ├── uko.py                    # Universal Knowledge Object model
│   │   ├── episode.py                # Episode factory from UKO
│   │   └── identity.py              # Identity resolution engine
│   │
│   ├── providers/                    # Knowledge Provider layer
│   │   ├── __init__.py
│   │   ├── base.py                   # Abstract base provider interface
│   │   ├── git/
│   │   │   ├── __init__.py
│   │   │   ├── provider.py           # GitProvider implementation
│   │   │   ├── auth.py               # Git authentication (SSH, HTTPS, token)
│   │   │   ├── discover.py           # Repo discovery, file walking
│   │   │   └── sync.py              # Incremental commit sync
│   │   ├── jira/
│   │   │   ├── __init__.py
│   │   │   ├── provider.py
│   │   │   ├── auth.py
│   │   │   ├── discover.py
│   │   │   └── sync.py
│   │   ├── mysql/
│   │   │   ├── __init__.py
│   │   │   ├── provider.py
│   │   │   ├── auth.py
│   │   │   ├── discover.py
│   │   │   └── sync.py
│   │   ├── slack/
│   │   │   ├── __init__.py
│   │   │   ├── provider.py
│   │   │   ├── auth.py
│   │   │   ├── discover.py
│   │   │   └── sync.py
│   │   └── confluence/
│   │       ├── __init__.py
│   │       ├── provider.py
│   │       ├── auth.py
│   │       ├── discover.py
│   │       └── sync.py
│   │
│   ├── pipeline/                     # Knowledge Processing Pipeline
│   │   ├── __init__.py
│   │   ├── orchestrator.py           # Pipeline orchestrator
│   │   ├── structural/
│   │   │   ├── __init__.py
│   │   │   ├── python_parser.py      # AST-based extraction
│   │   │   ├── sql_parser.py         # SQL schema extraction
│   │   │   ├── markdown_parser.py    # Markdown structure extraction
│   │   │   └── json_parser.py        # JSON structure extraction
│   │   ├── semantic/
│   │   │   ├── __init__.py
│   │   │   ├── llm_extractor.py      # LLM-based concept extraction
│   │   │   └── concept_mapper.py     # Map concepts to graph ontology
│   │   ├── temporal/
│   │   │   ├── __init__.py
│   │   │   └── change_tracker.py     # Track changes as temporal events
│   │   └── identity/
│   │       ├── __init__.py
│   │       └── resolver.py           # Cross-system entity resolution
│   │
│   ├── memory/                       # Memory Engine (GBrain-inspired)
│   │   ├── __init__.py
│   │   ├── working.py               # Working memory (in-process)
│   │   ├── session.py               # Session memory (Redis-backed)
│   │   ├── long_term.py             # Long-term memory (Graphiti/FalkorDB)
│   │   └── brain.py                 # GBrain: self-wiring memory layer
│   │
│   ├── agents/                       # AI Agent Layer
│   │   ├── __init__.py
│   │   ├── base_agent.py             # Base agent class
│   │   ├── context_assembler.py      # Assembles context from graph + memory
│   │   ├── reasoning.py              # LLM reasoning with assembled context
│   │   └── tools.py                  # Agent tools (search, traverse, etc.)
│   │
│   └── api/                          # API Layer
│       ├── __init__.py
│       ├── routes/
│       │   ├── __init__.py
│       │   ├── providers.py          # Provider CRUD + config
│       │   ├── ingest.py             # Episode ingestion endpoints
│       │   ├── search.py             # Knowledge graph search
│       │   ├── query.py              # Agent query endpoint
│       │   ├── memory.py             # Memory inspection endpoints
│       │   └── health.py             # Health check
│       └── middleware/
│           ├── __init__.py
│           ├── auth.py
│           └── logging.py
│
├── tests/
│   ├── conftest.py                   # Fixtures (Graphiti, FalkorDB, test data)
│   ├── test_providers/
│   │   ├── test_base.py
│   │   ├── test_git.py
│   │   ├── test_jira.py
│   │   └── test_mysql.py
│   ├── test_pipeline/
│   │   ├── test_structural.py
│   │   ├── test_semantic.py
│   │   └── test_temporal.py
│   ├── test_memory/
│   │   ├── test_working.py
│   │   ├── test_session.py
│   │   └── test_long_term.py
│   ├── test_agents/
│   │   ├── test_context.py
│   │   └── test_reasoning.py
│   └── test_api/
│       └── test_routes.py
│
└── scripts/
    ├── init_falkordb.py              # One-time FalkorDB init
    ├── seed_data.py                  # Seed test data
    └── run_provider.py               # Run a single provider manually
```

---

## 3. Core Data Model

### 3.1 Universal Knowledge Object (UKO)

Every provider outputs this standardized Pydantic model:

```python
from pydantic import BaseModel
from datetime import datetime
from enum import Enum
from typing import Any

class UKOType(str, Enum):
    FUNCTION = "function"
    CLASS = "class"
    API = "api"
    TABLE = "table"
    DOCUMENT = "document"
    MESSAGE = "message"
    TICKET = "ticket"
    PERSON = "person"
    CONCEPT = "concept"

class UKORelationship(BaseModel):
    target_id: str
    relationship: str  # e.g., "calls", "owns", "references", "assigned_to"
    target_type: UKOType

class UKOMetadata(BaseModel):
    source: str                    # e.g., "git", "jira", "mysql"
    source_id: str                 # platform-native ID
    source_url: str | None = None
    created_at: datetime
    modified_at: datetime
    authors: list[str] = []
    tags: list[str] = []

class UniversalKnowledgeObject(BaseModel):
    id: str                        # UUID generated by provider
    type: UKOType
    name: str                      # Human-readable name
    content: str                   # Original content / description
    metadata: UKOMetadata
    relationships: list[UKORelationship] = []
    raw_data: dict[str, Any] = {}  # Original platform data (for evidence layer)
```

### 3.2 Episode Mapping

UKOs are converted to Graphiti episodes:

```python
class EpisodePayload:
    uko: UniversalKnowledgeObject
    episode_body: str              # Formatted for Graphiti ingestion
    episode_type: str              # "text" | "json"
    reference_time: datetime
    source_description: str        # e.g., "Git commit abc123 by Brajesh"
```

### 3.3 Graph Entity Types

**Evidence Layer** (entitites that store raw artifacts):
- `SourceFile`, `DatabaseTable`, `JiraTicket`, `SlackMessage`, `ConfluencePage`
- `GitCommit`, `DatabaseMigration`, `ApiEndpoint`

**Knowledge Layer** (extracted concepts):
- `BusinessConcept`, `Person`, `Team`, `Service`, `Project`
- `Technology`, `Pattern`, `Requirement`

**Relationships:**
- `IMPLEMENTS` (File → Concept)
- `REFERENCES` (Ticket → File)
- `OWNS` (Person → Service)
- `BELONGS_TO` (Concept → Domain)
- `DEPENDS_ON` (Service → Service)
- `MODIFIED_IN` (File → Commit)
- `AUTHORED_BY` (Commit → Person)

---

## 4. Implementation Phases

### Phase 0: Foundation (Week 1-2)

**Goal:** Skeleton project with Graphiti/FalkorDB running, UKO model, and base provider interface.

**Tasks:**
- [ ] Initialize Python project with `uv` + `pyproject.toml`
- [ ] Docker Compose with FalkorDB + Redis
- [ ] `src/config.py` — pydantic-settings for all configuration
- [ ] `src/core/uko.py` — UniversalKnowledgeObject model
- [ ] `src/core/graph.py` — Graphiti init, build_indices, add_episode, search wrappers
- [ ] `src/core/episode.py` — UKO → Episode conversion
- [ ] `src/providers/base.py` — Abstract `KnowledgeProvider` base class
- [ ] `scripts/init_falkordb.py` — One-time setup script
- [ ] FastAPI skeleton with health endpoint

**Deliverable:** A running system that can initialize FalkorDB and ingest a hand-crafted UKO as an episode.

### Phase 1: Git Provider + Structural Pipeline (Week 3-4)

**Goal:** First end-to-end flow — Git repo → UKOs → Pipeline → Graphiti → FalkorDB.

**Tasks:**
- [ ] `src/providers/git/provider.py` — Full GitProvider:
  - Clone/fetch repos (pygit2 or GitPython)
  - Walk file tree, discover source files
  - Extract commit history incrementally
  - Generate UKOs for: files, functions, classes, commits
- [ ] `src/pipeline/structural/python_parser.py` — AST parsing (Python)
- [ ] `src/pipeline/structural/markdown_parser.py` — Markdown structure
- [ ] `src/pipeline/structural/json_parser.py` — JSON structure
- [ ] `src/pipeline/orchestrator.py` — Pipeline that runs structural → generates episodes → ingests
- [ ] `src/api/routes/providers.py` — Register/configure providers
- [ ] `src/api/routes/ingest.py` — Trigger ingestion
- [ ] Integration tests: clone a known repo, verify UKOs, verify graph nodes

**Deliverable:** Git repo ingested into knowledge graph. Code entities (functions, classes) discoverable via Graphiti search.

### Phase 2: Jira + Semantic Pipeline (Week 5-6)

**Goal:** Second provider. LLM-powered semantic extraction. Cross-system linking.

**Tasks:**
- [ ] `src/providers/jira/provider.py` — JiraProvider:
  - Jira REST API integration
  - Issue discovery (by project, sprint, filter)
  - Incremental sync (polling via `updated` field)
  - Generate UKOs for: tickets, comments, status changes
- [ ] `src/pipeline/semantic/llm_extractor.py` — LLM-based concept extraction:
  - Extract business concepts from code, tickets, docs
  - Map to ontology types
- [ ] `src/pipeline/semantic/concept_mapper.py` — Relate concepts to evidence
- [ ] `src/pipeline/temporal/change_tracker.py` — Capture change events
- [ ] `src/api/routes/search.py` — Hybrid search endpoint
- [ ] Integration tests: ingest Jira project + Git repo, verify cross-links

**Deliverable:** Jira tickets and Git commits linked in graph. Searchable by business concept.

### Phase 3: MySQL + Identity Resolution + More Providers (Week 7-8)

**Goal:** Database schema ingestion. Identity resolution across providers. Slack + Confluence.

**Tasks:**
- [ ] `src/providers/mysql/provider.py` — MySQLProvider:
  - Connect, introspect schema (information_schema)
  - Generate UKOs for: tables, columns, foreign keys, views, procedures
  - Track schema migrations as temporal events
- [ ] `src/pipeline/structural/sql_parser.py` — SQL DDL parsing
- [ ] `src/pipeline/identity/resolver.py` — Cross-system identity resolution:
  - Match persons across Git, Jira, Slack
  - Entity deduplication rules
  - Confidence scoring
- [ ] `src/providers/slack/provider.py` — SlackProvider
- [ ] `src/providers/confluence/provider.py` — ConfluenceProvider
- [ ] `src/api/routes/query.py` — Agent query endpoint (context assembly + reasoning)
- [ ] Integration tests: multi-provider identity resolution

**Deliverable:** 5 providers operational. Identity resolution working. Agent query endpoint functional.

### Phase 4: Memory Engine + GBrain (Week 9-10)

**Goal:** Three-layer memory. GBrain self-wiring memory. Full agent reasoning loop.

**Tasks:**
- [ ] `src/memory/working.py` — In-memory working memory (reasoning chain, scratchpad)
- [ ] `src/memory/session.py` — Redis-backed session memory (TTL-based expiry)
- [ ] `src/memory/long_term.py` — Graphiti-backed long-term memory (concepts, entities, episodes)
- [ ] `src/memory/brain.py` — GBrain integration:
  - Self-wiring: agent writes markdown → automatically linked into graph
  - Gap analysis: detect missing knowledge
  - Synthesis: combine evidence from multiple sources
- [ ] `src/agents/context_assembler.py` — Query → memory retrieval → graph traversal → context assembly
- [ ] `src/agents/reasoning.py` — LLM reasoning with assembled context
- [ ] `src/agents/tools.py` — search_graph, traverse_relationships, get_episode, add_note
- [ ] `src/api/routes/memory.py` — Memory inspection/management endpoints
- [ ] Integration tests: end-to-end agent reasoning loop

**Deliverable:** Full cognitive memory system. Agent asks "How does authentication work?" → retrieves from graph + memory → reasons with context → answers.

### Phase 5: Production Hardening (Week 11-12)

**Goal:** Performance, monitoring, documentation, security.

**Tasks:**
- [ ] Celery task queue for async ingestion
- [ ] Rate limiting + retry logic for LLM calls
- [ ] Metrics & monitoring (Prometheus endpoints)
- [ ] Authentication middleware (API keys, OAuth)
- [ ] Multi-tenancy (graph_name isolation per organization)
- [ ] Performance benchmarks (ingestion throughput, query latency)
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Deployment guide (Docker Compose, Kubernetes)
- [ ] Provider SDK documentation (how to write a new provider)

**Deliverable:** Production-ready system with monitoring, auth, multi-tenancy, and documentation.

---

## 5. Provider Interface Contract

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator

class KnowledgeProvider(ABC):
    """Every provider must implement this interface."""

    provider_name: str        # e.g., "git", "jira", "mysql"
    provider_version: str     # semantic version

    @abstractmethod
    async def authenticate(self, credentials: dict) -> bool:
        """Authenticate with the external platform. Returns success."""
        ...

    @abstractmethod
    async def discover(self) -> list[str]:
        """Discover available resources (repos, projects, databases).
        Returns list of resource identifiers."""
        ...

    @abstractmethod
    async def sync(
        self,
        resource_id: str,
        since: datetime | None = None
    ) -> AsyncIterator[UniversalKnowledgeObject]:
        """Incrementally sync data since given timestamp.
        Yields UniversalKnowledgeObjects as they're discovered.
        If since is None, performs full sync."""
        ...

    @abstractmethod
    async def validate(self) -> bool:
        """Validate that the provider is correctly configured and connected."""
        ...

    @abstractmethod
    async def get_status(self, resource_id: str) -> dict:
        """Get sync status for a resource (last sync time, count, errors)."""
        ...
```

---

## 6. Pipeline Orchestration

```python
class PipelineOrchestrator:
    """Orchestrates the full processing pipeline."""

    async def process_uko(self, uko: UniversalKnowledgeObject) -> list[str]:
        """Process a single UKO through all pipeline stages.
        Returns list of episode IDs created."""

        # Stage 1: Structural Extraction
        structural_artifacts = await self.structural.extract(uko)

        # Stage 2: Semantic Extraction (LLM)
        semantic_artifacts = await self.semantic.extract(uko, structural_artifacts)

        # Stage 3: Temporal Extraction
        temporal_events = self.temporal.extract(uko)

        # Stage 4: Identity Resolution
        resolved_entities = await self.identity.resolve(uko, semantic_artifacts)

        # Stage 5: Convert to Episodes
        episodes = self._build_episodes(
            uko,
            structural_artifacts,
            semantic_artifacts,
            temporal_events,
            resolved_entities
        )

        # Stage 6: Ingest into Graphiti
        episode_ids = []
        for episode in episodes:
            eid = await self.graph.add_episode(
                name=episode.name,
                episode_body=episode.body,
                reference_time=episode.reference_time,
                source_description=episode.source_description,
            )
            episode_ids.append(eid)

        return episode_ids
```

---

## 7. GBrain Integration

GBrain provides the "self-wiring" layer — where the agent itself can write observations back into the knowledge graph.

```python
class GBrain:
    """Self-wiring memory layer inspired by GBrain."""

    def __init__(self, graph: GraphitiClient, memory_root: Path):
        self.graph = graph
        self.memory_root = memory_root   # Directory of markdown memory files

    async def write(self, topic: str, content: str) -> str:
        """Agent writes a memory note. Automatically linked into graph."""
        # 1. Save as markdown file
        # 2. Ingest as episode into Graphiti
        # 3. Extract entities + relationships via LLM
        # 4. Return the episode ID

    async def read(self, query: str) -> list[dict]:
        """Agent reads from memory (graph search + markdown retrieval)."""
        # Hybrid search across Graphiti + raw markdown files

    async def gap_analysis(self, domain: str) -> list[str]:
        """Detect knowledge gaps in a domain."""
        # Compare what we have vs. what we should have

    async def synthesize(self, topic: str) -> str:
        """Synthesize knowledge across multiple sources into a summary."""
        # Graph traversal + LLM summarization
```

---

## 8. Docker Compose

```yaml
version: '3.8'
services:
  falkordb:
    image: falkordb/falkordb:latest
    ports:
      - "6379:6379"
      - "3000:3000"
    volumes:
      - falkordb_data:/data
    environment:
      - FALKORDB_password=${FALKORDB_PASSWORD:-admin}

  redis:
    image: redis:7-alpine
    ports:
      - "6380:6379"
    volumes:
      - redis_data:/data

  api:
    build: .
    ports:
      - "8000:8000"
    depends_on:
      - falkordb
      - redis
    environment:
      - FALKORDB_URI=falkor://falkordb:6379
      - REDIS_URL=redis://redis:6379
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./src:/app/src
      - ./memory:/app/memory

volumes:
  falkordb_data:
  redis_data:
```

---

## 9. Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Async or sync?** | Async (asyncio + FastAPI) | Graphiti is async-native; providers do I/O-heavy work |
| **Graphiti vs raw FalkorDB?** | Graphiti on FalkorDB | Graphiti handles episodes, entity extraction, temporal reasoning, dedup — we'd have to rebuild all of that |
| **How to handle LLM rate limits?** | SEMAPHORE_LIMIT + Celery retries | Graphiti env var for concurrency; Celery for retry with backoff |
| **Multi-tenancy?** | FalkorDB graph_name per org | Graphiti supports `graph_name` param for isolated graphs |
| **Schema or schemaless?** | Prescribed + Learned ontology | Graphiti supports both Pydantic types (prescribed) and emergent (learned) |
| **Evidence vs Knowledge separation** | Two entity type families in same graph | Rather than two separate graphs, use entity types to distinguish layers |

---

## 10. Risk Register

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Graphiti API breaking changes | High | Pin version; run CI against new releases before upgrading |
| LLM cost at scale | High | Cache semantic extraction results; batch episodes; use small models where possible |
| FalkorDB single point of failure | Medium | FalkorDB Cloud for HA; periodic backups |
| Provider API rate limits | Medium | Provider-level rate limiting; incremental sync reduces load |
| Identity resolution accuracy | Medium | Confidence scoring; human-in-the-loop for low-confidence matches |
| Schema evolution across providers | Low | UKO model versioned; providers declare their UKO schema version |

---

## 11. Success Metrics

- **Ingestion throughput:** UKOs/second per provider
- **Graph accuracy:** % of correctly extracted entities/relationships
- **Search relevance:** MRR (Mean Reciprocal Rank) on known queries
- **Query latency:** p50/p95/p99 for agent query endpoint
- **Identity resolution precision:** % of correct cross-system entity merges
- **Provider coverage:** number of enterprise platforms connected
- **Memory coherence:** agent answers grounded in graph evidence (citation rate)

---

## 12. Next Actions (Immediate)

1. Run `uv init` to bootstrap the project
2. Create `docker-compose.yml` with FalkorDB + Redis
3. Implement `src/core/uko.py` (UKO model)
4. Implement `src/providers/base.py` (abstract provider)
5. Implement `src/core/graph.py` (Graphiti wrapper)
6. Write `scripts/init_falkordb.py`
7. Create FastAPI skeleton with health endpoint
8. Write first integration test (UKO → Episode → Graphiti → Search)

---

## Appendix A: Graphiti API Reference (v0.29.2)

### Initialization
```python
from graphiti_core import Graphiti
from graphiti_core.driver.falkordb_driver import FalkorDriver

driver = FalkorDriver(host="localhost", port=6379, database="ecms")
graphiti = Graphiti(graph_driver=driver)

# One-time setup
await graphiti.build_indices_and_constraints()
```

### Adding Episodes
```python
from graphiti_core.nodes import EpisodeType
from datetime import datetime

await graphiti.add_episode(
    name="Git commit abc123",
    episode_body="Added authentication module with JWT support...",
    episode_type=EpisodeType.text,
    reference_time=datetime(2026, 7, 1, 12, 0, 0),
    source_description="Git commit abc123 by Brajesh",
)
```

### Searching
```python
# Hybrid search
results = await graphiti.search(query="authentication", num_results=10)

# Node search
nodes = await graphiti.retrieve_nodes(query="Brajesh", num_results=5)

# Episode search
episodes = await graphiti.retrieve_episodes(query="commit", num_results=5)

# Temporal search
results = await graphiti.search(
    query="authentication",
    reference_time=datetime(2026, 6, 1),
    num_results=10
)
```

### Custom Entity Types (Prescribed Ontology)
```python
from pydantic import BaseModel

class PersonEntity(BaseModel):
    name: str
    email: str | None = None
    role: str | None = None

class ServiceEntity(BaseModel):
    name: str
    language: str | None = None
    repository: str | None = None
```

---

## Appendix B: Environment Variables

```bash
# FalkorDB
FALKORDB_URI=falkor://localhost:6379
FALKORDB_PASSWORD=admin

# Redis (for Celery + session memory)
REDIS_URL=redis://localhost:6379

# LLM
OPENAI_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
EMBEDDING_MODEL=text-embedding-3-small
SEMAPHORE_LIMIT=10

# Graphiti
GRAPHITI_TELEMETRY_ENABLED=false

# API
API_HOST=0.0.0.0
API_PORT=8000
API_KEY=ecms-secret-key

# Providers (per-provider, loaded dynamically)
GIT_DEFAULT_CLONE_PATH=./data/repos
JIRA_URL=https://your-org.atlassian.net
JIRA_EMAIL=bot@org.com
JIRA_API_TOKEN=...
```

## Appendix C: UKO Examples

### From Git
```json
{
    "id": "uko-git-abc123-func-auth",
    "type": "function",
    "name": "authenticate_user",
    "content": "def authenticate_user(token: str) -> User:\n    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])\n    return User.get(payload['sub'])",
    "metadata": {
        "source": "git",
        "source_id": "src/auth/service.py:12-18",
        "source_url": "https://github.com/org/repo/blob/main/src/auth/service.py#L12",
        "created_at": "2026-06-15T10:30:00Z",
        "modified_at": "2026-07-01T14:22:00Z",
        "authors": ["Brajesh Patil"],
        "tags": ["authentication", "jwt", "security"]
    },
    "relationships": [
        {"target_id": "uko-git-abc123-class-user", "relationship": "returns", "target_type": "class"},
        {"target_id": "uko-git-abc123-import-jwt", "relationship": "uses", "target_type": "function"}
    ]
}
```

### From Jira
```json
{
    "id": "uko-jira-PROJ-1234",
    "type": "ticket",
    "name": "Implement JWT Authentication",
    "content": "As a user, I want to authenticate using JWT tokens so that sessions are stateless. Tasks: 1) Create JWT service 2) Add middleware 3) Write tests",
    "metadata": {
        "source": "jira",
        "source_id": "PROJ-1234",
        "source_url": "https://org.atlassian.net/browse/PROJ-1234",
        "created_at": "2026-06-10T09:00:00Z",
        "modified_at": "2026-07-01T16:00:00Z",
        "authors": ["Brajesh Patil"],
        "tags": ["authentication", "jwt", "epic:security"]
    },
    "relationships": [
        {"target_id": "uko-jira-PROJ-1230", "relationship": "child_of", "target_type": "ticket"},
        {"target_id": "person-brajesh", "relationship": "assigned_to", "target_type": "person"}
    ]
}
```

### From MySQL
```json
{
    "id": "uko-mysql-db1-users-table",
    "type": "table",
    "name": "users",
    "content": "CREATE TABLE users (id UUID PRIMARY KEY, email VARCHAR(255) UNIQUE, password_hash VARCHAR(255), created_at TIMESTAMP, updated_at TIMESTAMP)",
    "metadata": {
        "source": "mysql",
        "source_id": "mydb.users",
        "source_url": null,
        "created_at": "2025-01-01T00:00:00Z",
        "modified_at": "2026-06-20T11:00:00Z",
        "authors": ["DB Migration v14"],
        "tags": ["authentication", "users", "core"]
    },
    "relationships": [
        {"target_id": "uko-mysql-db1-sessions-table", "relationship": "references", "target_type": "table"}
    ]
}
```
