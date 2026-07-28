# Memory Architecture

ECMS has **10 memory tiers** spanning 3 temporal layers. The agent doesn't just chat —
it reads from and writes to a multi-tier memory system that covers everything from
scratchpad notes (this turn) to semantic knowledge (permanent, vector-searchable).

---

## The Three Layers

| Layer | Scope | Lifetime | Examples |
|-------|-------|----------|----------|
| **Working** | This turn | Single ReAct loop iteration | Scratchpad, active atom IDs, tool results |
| **Session** | This conversation | Session duration (24h Redis TTL) | Chat history, user preferences, learned facts |
| **Long-Term** | Permanent | Survives sessions, projects, restarts | Knowledge atoms, graph nodes, semantic embeddings |

---

## All 10 Tiers

### Working Layer

#### 1. Working Memory
**Code:** `backend/ecms/agent/working_memory.py`
**What it stores:** The agent's scratchpad — notes it writes to itself, atom IDs it found,
tool call results, key-value variables.

**Where:** In-process only. Created fresh each time the agent runs. Gone after the response.

**How the agent uses it:** On every iteration of the ReAct loop, the agent's scratchpad and
active discoveries are injected into the system prompt so the LLM remembers what it already
found. Agent tools like `note()`, `set_working()`, and `get_working()` read/write here.

**Storage:** RAM only — zero persistence.

---

### Session Layer

#### 2. Chat History (PostgreSQL)
**Code:** `backend/ecms/persistence/models/session.py` · `backend/ecms/persistence/repositories/session.py`
**What it stores:** Every message — user and assistant — for every session. Full text,
timestamps, tool calls.

**Where:** PostgreSQL `sessions` + `session_messages` tables. Each session is scoped to a
workspace.

**How the agent uses it:** When a user opens a session, the full history loads from
`GET /sessions/{id}/messages`. The agent sees everything that was said.

**Storage:** PostgreSQL 16.

#### 3. Session Context (Redis)
**Code:** `backend/ecms/agent/session_context.py` · `legacy/src/legacy_ecms/memory/session_redis.py`
**What it stores:** Key-value facts remembered across questions in the same conversation.
Like "User prefers TypeScript" or "We're building auth for a FastAPI microservice."

**Where:** Redis keys: `ecms:session:{workspace_id}:{session_id}:{key}`. 24-hour TTL.

**How the agent uses it:** Agent tools `set_session()` and `get_session()`. Injected into
the system prompt alongside working memory on every ReAct iteration.

**Storage:** Redis 7.

#### 4. Conversation Files (Disk)
**Code:** `backend/ecms/agent/conversation.py`
**What it stores:** Raw LLM conversation JSON — user messages, assistant responses,
tool calls with arguments and results. Last 50 messages per session.

**Where:** `/app/memory/sessions/{session_id}/history.json`

**How the agent uses it:** Internal to the `AgentLoop` — builds the context window for
each LLM call. Not exposed to agent tools.

**Storage:** JSON file per session.

---

### Long-Term Layer

#### 5. Episodic Memory
**Code:** `backend/ecms/memory/episodic/__init__.py`
**What it stores:** Timestamped summaries of every conversation turn — question, answer,
auto-extracted keywords, links to structured atoms.

**Where:** `/app/memory/episodes.ndjson` (append-only NDJSON)

**How the agent uses it:** Agent tool `recall_past(query)` searches past episodes by
keyword overlap. The agent can ask "what did we discuss about authentication?" and get
past conversations back.

**Storage:** NDJSON file — one JSON line per turn, reverse-scanned for keyword matches.

#### 6. GBrain — Deliberative Notes
**Code:** `legacy/src/legacy_ecms/memory/brain.py`
**What it stores:** Markdown notes on topics. Think of it as the agent's personal wiki.
Each `.md` file covers one topic: "ECOS Architecture", "Authentication Patterns", etc.

**Where:** `/app/memory/{topic}.md`

**How the agent uses it:** Agent tool `search_memory()` reads GBrain notes. On every chat
turn, the agent fire-and-forget writes a summary note. Periodically, the
`CognitiveOrchestrator` clusters related mem0 memories and synthesizes a consolidated note.

**Storage:** Markdown files, one per topic. Searchable by keyword pattern matching.

#### 7. Mem0 — Semantic Memory
**Code:** `legacy/src/legacy_ecms/memory/mem0_layer.py`
**What it stores:** Facts extracted from conversations, stored as vector embeddings for
semantic search. Like "The codebase uses JWT auth in ecms/auth/" or "The catchment module
handles geolocation."

**Where:** Qdrant vector database — collection `ecms_mem0_{workspace_id}`. Also a
SQLite history database at `/app/data/mem0_home/history.db`.

**How the agent uses it:** On every chat turn, the conversation is auto-captured to mem0
(fire-and-forget). High-confidence facts (score ≥ 0.70) are promoted to the FalkorDB
knowledge graph. Agent can search mem0 via `search_memory()`.

**Storage:** Qdrant (vectors) + SQLite (metadata). Workspace-scoped.

#### 8. Atom Store — Structured Knowledge
**Code:** `legacy/src/legacy_ecms/memory/stores/file_store.py`
**What it stores:** Structured, typed, evidence-backed atoms. Each atom has:
- **Type** — fact, architecture, decision, convention, observation, bug, limitation, etc.
- **Confidence** — 0.0 to 1.0
- **Status** — draft, verified, superseded
- **Evidence** — links to source files, conversations, graph nodes
- **Relationships** — links to other atoms (depends on, supersedes, contradicts)

**Where:** `/app/memory/memory_atoms.ndjson` (one JSON line per atom)

**How the agent uses it:** This is the **primary search target**. Agent tool
`search_memory(query)` searches atoms first — it's the fastest, highest-quality context.
The `UnifiedMemoryBridge` syncs FalkorDB nodes and GBrain notes into atoms every 2 minutes,
so the atom store is always a distilled index of everything the system knows.

**Storage:** NDJSON with offset index for O(1) lookups.

#### 9. FalkorDB — The Knowledge Graph
**Code:** `backend/ecms/graph/` (modern) · `legacy/src/legacy_ecms/core/graph.py` (legacy)
**What it stores:** Every file, function, class, API endpoint, commit, workspace, and
schema as a node in a property graph. 13,000+ nodes with typed relationships.

**Where:** FalkorDB (Redis-native property graph)

**How the agent uses it:** Agent tool `query_graph(cypher)` runs Cypher queries directly.
Use for code-level detail — "find all functions in auth.py", "what imports this module".

**Storage:** FalkorDB — nodes as `:UKO`, edges as `:RELATES`.

#### 10. Procedural Memory + Organizational Patterns
**Code:** `backend/ecms/memory/procedural/__init__.py` · `backend/ecms/memory/organization/__init__.py`
**What it stores:** 
- **Procedures:** Learned multi-step workflows. "Deploy to prod" → run tests, build Docker, push, kubectl apply.
- **Organizational patterns:** Crowd-validated best practices. Other agents validate by incrementing a counter.

**Where:** `/app/memory/procedures.ndjson` + FalkorDB `:OrganizationalPattern` nodes

**How the agent uses it:** `recall_procedure(task)` returns matching workflows.
`search_org(query)` returns validated organizational knowledge.

---

## How Data Flows Between Tiers

```
A user asks: "Tell me about the android_code repo"
    │
    ▼
AgentLoop starts with:
    Working Memory (empty this turn)
    + Session Context (any facts from earlier in this conversation)
    │
    ▼
ReAct Loop — agent calls tools:
    search_memory("android_code") → Atom Store (NDJSON)
    query_graph("MATCH (u:UKO) WHERE u.source_id CONTAINS 'android' RETURN u") → FalkorDB
    read_file("/app/data/repos/.../build.gradle") → Filesystem
    │
    ▼
Agent synthesizes answer from what it found
    │
    ▼
After response, fire-and-forget writes:
    ├─ PostgreSQL: user message + assistant answer
    ├─ Episode Store: conversation turn logged
    ├─ Mem0: conversation captured as semantic memory (Qdrant)
    ├─ GBrain: markdown note written
    └─ Conversation Extractor: structured atoms extracted

Every 2 minutes (background):
    UnifiedMemoryBridge syncs:
        FalkorDB nodes → FDB-* atoms
        GBrain .md files → GB-* atoms
    Result: Atom Store is always current
```

---

## Workspace Scoping

All memory tiers are **workspace-scoped**, meaning each project has its own isolated
memory:

| Tier | Scoping Mechanism |
|------|-------------------|
| Chat History | `sessions.workspace_id` column |
| Session Context | Redis key: `ecms:session:{ws_id}:*` |
| Mem0 | Qdrant collection: `ecms_mem0_{workspace_id}` |
| FalkorDB | Node property: `group_id` |
| GBrain | Directory: `/app/memory/{workspace_id}/` |

When a project is deleted, **all 10 tiers cascade** — the delete endpoint removes data
from PostgreSQL, FalkorDB, Qdrant, Redis, disk files, and the atom store in one operation.

---

## Supporting Infrastructure

Memory doesn't work in isolation. These background systems keep tiers in sync:

| Component | Code | Purpose |
|-----------|------|---------|
| **UnifiedMemoryBridge** | `legacy/src/legacy_ecms/memory/bridge.py` | Syncs FalkorDB + GBrain → Atom Store every 2 min |
| **CognitiveOrchestrator** | `legacy/src/legacy_ecms/memory/cognitive_orchestrator.py` | Capture → Promote → Consolidate → Validate → Decay loop |
| **ConversationExtractor** | `legacy/src/legacy_ecms/memory/extraction.py` | Chat Q&A → structured MemoryAtoms |
| **SemanticValidator** | `legacy/src/legacy_ecms/memory/validation.py` | Duplicate/refine/extend/contradict detection |
| **RetrievalPipeline** | `legacy/src/legacy_ecms/memory/retrieval.py` | 6-step search: keyword → semantic → expand → rank → filter → trim |
| **MemoryDomain** | `legacy/src/legacy_ecms/memory/domain/__init__.py` | MemoryAtom, MemoryType, Evidence, MemoryRelationship models |
| **Agent Tools** | `backend/ecms/agent/tools.py` | 18 tool definitions bridging LLM → memory tiers |
| **Agent Loop** | `backend/ecms/agent/loop.py` | ReAct agent — context injection, tool dispatch |
| **Session Chat** | `backend/ecms/api/rest/session_chat.py` | POST /sessions/{id}/chat — fire-and-forget writes |
| **Project Delete** | `backend/ecms/api/rest/projects.py` | Cascade delete across all 6 storage backends |
