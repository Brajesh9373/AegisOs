# Memory Implementation

How memory actually works — the code paths, data structures, and algorithms that power
the 10-tier memory system.

---

## 1. The Agent Loop — How Memory Gets Used

Every time a user sends a message, the `AgentLoop` (ReAct pattern) runs:

```python
# backend/ecms/agent/loop.py
class AgentLoop:
    def __init__(self, session_id):
        self._working = WorkingMemory()            # Tier 1 — ephemeral
        self._session = SessionContext(session_id)  # Tier 3 — Redis-backed
        self._conv = Conversation(session_id)       # Tier 4 — file-based history
```

### Context Injection

On every ReAct iteration, the agent builds its prompt by merging:

```python
def _build_messages(self):
    wm = self._working.summary_for_agent()    # "You're working on: fix auth bug"
    sm = self._session.summary_for_agent()    # "User prefers TypeScript, session vars: ..."
    memory_block = wm + sm
    system = AGENTIC_SYSTEM_PROMPT + memory_block
    return [system] + self._conv.as_list()    # + full conversation history
```

The LLM sees everything it needs: who the user is, what was discussed, what tools found,
and what it noted in its scratchpad. Zero retrieval latency — it's all in the prompt.

### Tool Dispatch

18 tools registered as OpenAI function-calling definitions. When the LLM calls a tool:

```python
# backend/ecms/agent/tools.py — invoke_tool()
async def invoke_tool(name: str, args: dict) -> str:
    if name == "search_memory":
        return await _search_memory(args["query"], args.get("limit", 10))
    elif name == "query_graph":
        return await _query_graph(args["cypher"])
    elif name == "read_file":
        return await _read_file(args["path"])
    # ... 15 more tools
```

Each tool directly hits its storage backend — no middleware, no orchestration overhead.

---

## 2. Search Memory — The Primary Retrieval Path

When the agent calls `search_memory("auth module")`, here's what happens:

```
search_memory("auth module")
    │
    ▼
FileMemoryStore.search_atoms("auth module", limit=10)
    │
    ▼
RetrievalPipeline (6-step strategy chain)
    │
    ├── Step 1: Keyword Search
    │   └── Split query into tokens → scan memory_index.json for matching atoms
    │       → return atoms where topic or summary contains any token
    │
    ├── Step 2: Semantic Search (optional)
    │   └── If embeddings available → embed query → cosine similarity against
    │       stored embeddings → return top matches
    │
    ├── Step 3: Relationship Expansion
    │   └── For each match: follow related_atoms → memory_rels.json
    │       → return atoms 1–2 hops away
    │
    ├── Step 4: Confidence Ranking
    │   └── Sort by: confidence × evidence_weight × recency
    │
    ├── Step 5: Evidence Quality Filter
    │   └── Prioritize atoms with VERIFIED status + multiple evidence sources
    │       → deprioritize DRAFT status + single-source evidence
    │
    └── Step 6: Budget Trim
        └── Trim to `limit` results, keeping highest-ranked
    │
    ▼
Return: ["GB-AUTH-ARCHITECTURE (0.95) JWT auth lives in ecms/auth/...", ...]
```

The agent gets structured results with confidence scores, so it can distinguish
"this is well-established" from "this is a tentative observation."

### The File Store Internals

```python
# legacy/src/legacy_ecms/memory/stores/file_store.py
class FileMemoryStore:
    def __init__(self, root: Path):
        self._atoms_path = root / "memory_atoms.ndjson"  # append-only
        self._index_path = root / "memory_index.json"     # id → {offset, length}
        self._rels_path = root / "memory_rels.json"        # relationships

        self.indexes = AtomIndexes()  # by_tag, by_topic, by_scope, by_type
        self.cache = AtomCache(max_size=500)  # LRU in-memory cache
```

**Design:** The store never loads all atoms into memory. Instead:
- **Index file** maps atom ID → byte offset + length in the NDJSON file
- **On read:** seek to offset, read exactly `length` bytes, parse JSON
- **On write:** append to NDJSON, update index, warm cache

This gives O(1) single-atom lookups with constant memory usage, suitable for
10K–1M atoms on a single node.

---

## 3. Query Graph — Direct Cypher Access

```python
async def _query_graph(cypher: str) -> str:
    settings = get_settings()
    db = falkordb.FalkorDB(host=settings.falkordb_host, port=settings.falkordb_port)
    g = db.select_graph(settings.falkordb_database)
    result = g.query(cypher)
    rows = result.result_set if hasattr(result, "result_set") else result
    return json.dumps(rows[:20])  # cap at 20 rows
```

The agent writes raw Cypher. No abstraction layer. Examples:
- `MATCH (u:UKO) WHERE u.name CONTAINS 'auth' RETURN u.name, u.type`
- `MATCH (u:UKO)-[r:RELATES]->(t:UKO) WHERE u.name='Authentication' RETURN t.name, r.label`

---

## 4. How Atoms Get Created — The Conversation Extractor

After every chat response, the `ConversationExtractor` transforms the Q&A into
structured atoms:

```python
# legacy/src/legacy_ecms/memory/extraction.py
class ConversationExtractor:
    def __init__(self, store, min_confidence=0.70, max_atoms_per_conversation=8):
        self._store = store
        self._min_confidence = min_confidence
        self._max_atoms = max_atoms_per_conversation

    async def extract_and_persist(self, question, answer, session_id):
        # 1. Segment answer into sentences (≥30 chars)
        segments = [s for s in answer.split('.') if len(s) >= 30]

        # 2. Classify each segment using keyword patterns
        for segment in segments:
            atom_type = classify_segment(segment)
            # EXTRACTION_PATTERNS map keywords → MemoryType:
            # "architecture" → ARCHITECTURE, "trade-off" → TRADE_OFF,
            # "must" → CONVENTION, "prefer" → BEST_PRACTICE, etc.

        # 3. Run SemanticValidator — detect duplicates, refinements, contradictions
        for candidate in candidates:
            for existing in self._store.search_atoms(candidate.topic):
                similarity = SequenceMatcher(candidate.summary, existing.summary).ratio()
                if similarity >= 0.90: resolution = DUPLICATE
                elif similarity >= 0.75: resolution = REFINE (update existing)
                elif similarity >= 0.55: resolution = EXTEND (add as related)
                # Contradiction check: antonym pairs (always/never, jwt/oauth, etc.)

        # 4. Persist valid atoms
        for atom in validated:
            self._store.upsert_atom(atom)  # append to NDJSON + update index
```

**Keyword pattern example:**
```python
EXTRACTION_PATTERNS = [
    (r"architecture|design|structure|pattern", MemoryType.ARCHITECTURE),
    (r"trade.?off|pros.*cons|alternative", MemoryType.TRADE_OFF),
    (r"must|should always|standard is", MemoryType.CONVENTION),
    (r"prefer|best practice|recommend", MemoryType.BEST_PRACTICE),
    (r"bug|issue|broken|fails|error", MemoryType.BUG),
    (r"security|auth|vulnerab|exploit", MemoryType.SECURITY),
]
```

---

## 5. The UnifiedMemoryBridge — Continuous Sync

Every 2 minutes, a background worker syncs FalkorDB and GBrain into the atom store:

```python
# legacy/src/legacy_ecms/memory/bridge.py
class UnifiedMemoryBridge:
    def sync_all(self, atom_store) -> int:
        total = 0
        total += self._sync_falkordb(atom_store)  # UKO nodes → FDB-* atoms
        total += self._sync_gbrain(atom_store)     # .md files → GB-* atoms
        return total

    def _sync_falkordb(self, atom_store) -> int:
        # Paginated: process 100 nodes at a time
        # SKIP {offset} LIMIT 100
        # Only knowledge/decision layer nodes (skip raw evidence)
        for skip in range(0, total_nodes, 100):
            rows = g.query(
                "MATCH (u:UKO) WHERE u.layer IN ['knowledge', 'decision'] "
                "RETURN u.id, u.name, u.type, u.layer, u.content, "
                "u.source, u.source_id, u.extraction_method, u.pipeline_stage, "
                "u.node_confidence ORDER BY u.id SKIP {skip} LIMIT 100"
            )
            for row in rows:
                # Hash the node content → skip if unchanged (incremental sync)
                content_hash = sha256(json.dumps(row).encode()).hexdigest()
                if self._hashes.get(uko_id) == content_hash:
                    continue  # unchanged — skip

                # Create MemoryAtom
                atom = MemoryAtom(
                    id=f"FDB-{uko_id}",
                    type=infer_type(node_type, extraction_method),
                    topic=name,
                    summary=truncate(content, 500),
                    confidence=node_confidence or 0.5,
                    status=MemoryStatus.VERIFIED if node_confidence > 0.7 else MemoryStatus.DRAFT,
                    scope=MemoryScope.PROJECT,
                    evidence=[Evidence(source=source_id, source_type="graph_node")],
                )
                atom_store.upsert_atom(atom)
                self._hashes[uko_id] = content_hash

        # Then sync edges → MemoryRelationships (paginated, 1000 at a time)
```

**Incremental sync:** On the first run, all nodes are processed. On subsequent runs,
only nodes whose content hash changed are re-synced. The hash cache at
`/app/memory/memory_bridge_hashes.json` persists across restarts.

**Type inference from graph metadata:**
```
node_type="class" + structural extraction  → architecture
node_type="function" + pipeline_stage=null → observation
node_type="document"                        → fact
node_type="api" + confidence >= 0.7        → best_practice
```

---

## 6. GBrain — Markdown File-Based Notes

```python
# legacy/src/legacy_ecms/memory/brain.py
class GBrain:
    def __init__(self, root: Path):
        self._root = root  # /app/memory/

    async def write(self, topic: str, content: str):
        filename = slugify(topic) + ".md"   # "ECOS Architecture" → "ecos-architecture.md"
        filepath = self._root / filename

        existing = filepath.read_text() if filepath.exists() else ""
        new_content = f"# {topic}\n\n{content}" + (f"\n\n{existing}" if existing else "")
        filepath.write_text(new_content)

        # Also create a UKO in FalkorDB
        uko = UniversalKnowledgeObject(
            name=topic, content=content, type="document", source="gbrain"
        )
        await LongTermMemory().remember(uko)  # → PipelineOrchestrator → FalkorDB

    def read(self, query: str) -> list[str]:
        # Keyword search across all .md files
        results = []
        for md_file in self._root.glob("*.md"):
            content = md_file.read_text()
            if any(word.lower() in content.lower() for word in query.split()):
                results.append(content)
        return results
```

**Upsert semantics:** Writing to an existing topic appends above previous content.
The file grows over time as more is learned about each topic.

---

## 7. Mem0 — Semantic Memory with Vector Search

```python
# legacy/src/legacy_ecms/memory/mem0_layer.py
class Mem0Memory:
    def __init__(self, settings, workspace_id="default"):
        # Qdrant collection: ecms_mem0_{workspace_id}
        # LLM: OpenAI-compatible (CustomOpenAI via mem0_llm_adapter)
        # Embedder: text-embedding-3-small (1536 dims)
        self._memory = Memory.from_config(config)

    async def add_from_messages(self, messages, user_id):
        # Sends conversation to mem0 → LLM extracts facts → embeds → stores in Qdrant
        result = await asyncio.to_thread(self._memory.add, messages, user_id=user_id)
        # Returns list of memory IDs

    def search(self, query, user_id, limit=5):
        # Vector search → returns semantically similar memories
        results = self._memory.search(query, user_id=user_id, limit=limit)
        return results

    async def promote_to_graph(self, entry, graph_client):
        # If score ≥ 0.70 → create UKO node in FalkorDB
        if entry.get("score", 0) >= 0.70:
            uko = UniversalKnowledgeObject(
                name=entry["memory"], content=entry["memory"],
                source="mem0", source_id=f"mem0-{entry['id']}",
            )
            await LongTermMemory().remember(uko)
```

**Custom prompt override:** Instead of mem0's default LLM extraction prompt, ECMS uses:
> "Return the input text unchanged as a single memory fact."

This bypasses mem0's attempt to rephrase or summarize — the raw conversation text
is stored directly as a vector embedding.

---

## 8. The Cognitive Orchestrator — Consolidation Loop

```python
# legacy/src/legacy_ecms/memory/cognitive_orchestrator.py
class CognitiveOrchestrator:
    async def process_turn(self, question, answer, user_id, session_id):
        # 1. Capture: store Q&A in mem0
        mem0_ids = await self._mem0.add_from_messages(messages, user_id)

        # 2. Auto-promote high-confidence facts
        for entry in self._mem0.get_all(user_id):
            if entry.score >= 0.70:
                await self._mem0.promote_to_graph(entry, graph_client)

        self._turn_counter += 1
        if self._turn_counter % 10 == 0:
            await self.consolidate()

    async def consolidate(self):
        # 1. Fetch all mem0 memories
        memories = await self._mem0.get_all()

        # 2. Cluster by keyword overlap
        clusters = cluster_by_keyword(memories, min_overlap=2)

        # 3. For each cluster: synthesize a GBrain note
        for topic, cluster_memories in clusters.items():
            note = synthesize_note(topic, cluster_memories)
            await self._brain.write(topic, note)

    async def validate(self):
        # Check mem0 memories against the graph for contradictions
        for memory in self._mem0.get_all():
            related = graph_client.search(memory["memory"])
            if has_contradiction(memory, related):
                memory["memory"] = f"[FLAGGED] {memory['memory']}"

    async def decay(self):
        # Dock confidence by 0.05 for memories older than 24h, floor at 0.30
        for memory in self._mem0.get_all():
            if age_hours(memory) > 24 and memory.score > 0.30:
                memory.score = max(0.30, memory.score - 0.05)
```

**The 4-phase loop:**
| Phase | Trigger | What Happens |
|-------|---------|--------------|
| Capture | Every chat turn | Q&A → mem0 vector store |
| Promote | Immediately | Score ≥ 0.70 facts → FalkorDB graph |
| Consolidate | Every 10 turns | Cluster related mem0 facts → GBrain note |
| Validate | Periodic | Detect contradictions between mem0 and graph |
| Decay | Every 24h | Lower confidence of old memories by 0.05 |

---

## 9. Cascade Delete — Cleaning All Tiers

When a project is deleted, a single API call removes data from all stores:

```python
# backend/ecms/api/rest/projects.py — delete_project()
# 1. FalkorDB — DETACH DELETE all UKOs with matching group_id
# 2. PostgreSQL — DELETE FROM sessions WHERE workspace_id = X (CASCADE messages)
# 3. PostgreSQL — DELETE FROM projects WHERE workspace_id = X (CASCADE connectors)
# 4. Qdrant — delete collection "ecms_mem0_{workspace_id}"
# 5. Redis — SCAN + DELETE "ecms:session:{workspace_id}:*"
# 6. Disk — shutil.rmtree "/app/memory/{workspace_id}/"
# 7. Disk — shutil.rmtree "/app/memory/{group_id}/"
# Note: Atom store atoms scoped by workspace are also cleaned via the bridge's
# next sync detecting missing graph nodes
```

---

## 10. Key Implementation Details

### Why two graph layers?

The system has two FalkorDB connectivity layers:

| Layer | Labels | Used By |
|-------|--------|---------|
| **Modern** (`GraphEngine` + `FalkorDBCypherStore`) | `:Node`, `:Edge` | `RuntimeKernel`, `CognitiveSystem` |
| **Legacy** (`GraphClient`) | `:UKO`, `:RELATES` | Git/MySQL providers, pipeline, GBrain, mem0 promotion |

Both write to the **same FalkorDB graph** (`ecms`) but use different label conventions.
The `UnifiedMemoryBridge` reads from the legacy `:UKO` labels to sync into atoms.

### Why two memory engines?

| Engine | Location | Role |
|--------|----------|------|
| `DefaultMemoryEngine` | `backend/ecms/memory/` | Modern — ranking + activation through `CognitiveSystem` |
| `FileMemoryStore` + GBrain + mem0 | `legacy/src/legacy_ecms/memory/` | Legacy — actual persistence (atoms, markdown, vectors) |

The modern engine provides the *interface* (ranking, caching, activation); the legacy
layer provides the *storage* (files, Qdrant, FalkorDB). The `CognitiveSystem` assembly
in `create_cognitive_system()` wires them together.

### Why no single "memory" database?

ECMS deliberately uses 6 storage backends instead of one because each memory problem
has different access patterns:
- **Atoms:** append-heavy, read-by-ID or keyword-search → NDJSON is perfect
- **Semantic search:** needs vector similarity → Qdrant
- **Graph traversal:** needs relationship-based queries → FalkorDB
- **Session state:** needs low-latency key-value → Redis
- **History replay:** needs relational queries → PostgreSQL
- **Deliberative notes:** human-readable, version-controllable → Markdown files
