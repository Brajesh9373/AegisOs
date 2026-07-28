a# ECMS Memory System — How the Brain Remembers

## What is Memory in ECMS?

Think of ECMS as a **digital brain for your organization**. Just like a human brain has different types of memory — what you're thinking about right now, what happened yesterday, and skills you've mastered over years — ECMS has three tiers of memory that work together.

---

## The Three Tiers of Memory

```
┌──────────────────────────────────────────────────┐
│  TIER 1: SHORT-TERM  (seconds to hours)          │
│  "What am I working on right now?"               │
│                                                  │
│  Task Memory    →  Scratchpad (this moment)      │
│  Session Memory →  What we discussed today       │
├──────────────────────────────────────────────────┤
│  TIER 2: SEMANTIC   (days to weeks)              │
│  "What have I learned from conversations?"       │
│                                                  │
│  Episodic Memory    →  Auto-learned facts (mem0) │
│  Deliberative Memory →  Written notes (GBrain)   │
│  Consolidated Memory →  Grouped learnings        │
├──────────────────────────────────────────────────┤
│  TIER 3: LONG-TERM   (permanent)                 │
│  "What does the organization know?"              │
│                                                  │
│  Knowledge Graph  →  Structured facts            │
│  Promoted Memory  →  Upgraded learnings          │
└──────────────────────────────────────────────────┘
```

---

## Tier 1: Short-Term Memory (Seconds to Hours)

This is like your **working memory and today's conversations**. It disappears when the day ends.

### Task Memory (Working Memory)
**What it is:** A sticky note you scribble on while solving a problem.

**Real-world analogy:** You're fixing a bug. You jot down "check line 42" on a sticky note. When the bug is fixed, you throw the note away.

**How it works:**
- Lives in the computer's RAM
- Created fresh for every question
- Gone when the answer is returned
- Only visible to the current task

**Example:**
```
User asks: "What payment methods do we support?"
  → Task memory stores: {"last_query": "payment methods"}
  → After answer is sent, task memory is cleared
```

### Session Memory
**What it is:** Everything discussed in today's meeting.

**Real-world analogy:** You're in a 1-hour design review. Everything said during that hour is session memory. When the meeting ends, you still have your notes, but the exact words fade.

**How it works:**
- Lives for a configurable time (default: 1 hour)
- Shared across all questions during that time
- Automatically expires after timeout
- In production: stored in Redis so multiple servers can share it

**Example:**
```
User asks (minute 1): "Show me the auth system"
  → Session: {"topic": "authentication"}

User asks (minute 5): "How does it handle tokens?"
  → Session remembers topic is still "authentication"
  → Provides deeper context

User asks (minute 65): "What about payment?"
  → Session expired. Starts fresh.
```

---

## Tier 2: Semantic Memory (Days to Weeks)

This is like **what you've learned from past experiences and written down in your notebook**. It persists across restarts.

### Episodic Memory (Mem0 — Auto-Learned Facts)
**What it is:** Facts the system automatically extracts from every conversation without you asking.

**Real-world analogy:** You meet a new colleague. Without trying to memorize, you naturally remember "Alex works in backend, uses Python, has 5 years experience." You didn't write it down — your brain just captured it.

**How it works:**
- Every question-answer pair is analyzed by an AI
- The AI extracts key facts: who, what, how, why
- Facts are stored as embeddings (mathematical fingerprints)
- Search finds facts by meaning, not just keywords

**Example:**
```
You ask: "How does the payment service handle authentication?"

System answers with context it found.

Behind the scenes (automatic):
  → AI reads: "payment service...authentication...JWT tokens"
  → Extracts fact: "Payment service uses JWT tokens for authentication"
  → Stores with confidence score: 0.82 (high confidence)
  → Index: ready for semantic search

Later, you ask: "What security does the checkout use?"
  → Searches by MEANING (not keyword "checkout" or "security")
  → Finds: "Payment service uses JWT tokens" (even though words differ)
  → Returns with score: 0.45 (related but not exact match)
```

### Deliberative Memory (GBrain — Written Notes)
**What it is:** Notes you or the system explicitly write down.

**Real-world analogy:** Your notebook. You deliberately write "Authentication flow: User → Login → JWT token → 24h expiry → Refresh endpoint." This is conscious, deliberate memory.

**How it works:**
- Stored as markdown files on disk
- Also stored in the knowledge graph
- Search is keyword-based (fast, exact)
- Never auto-deleted

**Example:**
```
You explicitly write a note:
  Topic: "Authentication Flow"
  Content: "Users authenticate via JWT. Tokens last 24 hours.
            Refresh endpoint: POST /auth/refresh"

Stored:
  → File: memory/authentication-flow.md
  → Graph node: gbrain:note:authentication-flow

Later search: "How long do tokens last?"
  → Keyword match: "24 hours" found in note
  → Returns full note content
```

### Consolidated Memory (Auto-Grouped Learnings)
**What it is:** The system notices patterns in episodic memories and creates summary notes.

**Real-world analogy:** After 10 meetings about authentication, someone consolidates the key decisions into a single document: "Authentication Decisions — We use JWT, 24h expiry, OAuth2 for external."

**How it works:**
- After every 10 conversations (configurable)
- System groups similar episodic memories by topic
- Creates a GBrain note summarizing the cluster
- This note becomes permanent (promoted to Tier 3)

**Example:**
```
After 10 conversations, episodic memories include:
  → "Payment service uses JWT tokens"
  → "Auth tokens expire after 24 hours"
  → "Refresh endpoint at POST /auth/refresh"
  → "OAuth2 used for third-party login"

System detects overlap: all about "authentication"
  → Creates consolidated note: "Authentication Architecture"
  → Content: grouped summary of all 4 facts
  → Stored as: memory/authentication-architecture.md
  → Promoted to knowledge graph as permanent node
```

---

## Tier 3: Long-Term Memory (Permanent)

This is like **the organization's collective knowledge — facts, code structure, database schemas, all interconnected**.

### Knowledge Graph (Structured Facts)
**What it is:** A web of interconnected facts — every file, function, class, table, column, concept, and their relationships.

**Real-world analogy:** A giant whiteboard where every piece of knowledge is a circle, and lines connect related circles. "PaymentService" connects to "process_payment()" which connects to "payments" table which has a "customer_id" column.

**How it works:**
- Everything eventually lands here
- Stored in FalkorDB (graph database)
- Every fact has provenance: who created it, how, when, confidence level
- Facts are linked: function → file, column → table, concept → evidence

**Example view of the graph:**
```
                    ┌────────────────────┐
                    │   WORKSPACE        │
                    │ "catchment-project"│
                    └────────┬───────────┘
                             │ part_of_workspace
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
      ┌───────────┐   ┌────────────┐   ┌───────────────┐
      │ README.md │   │loan_service│   │   MySQL DB    │
      └─────┬─────┘   │   .py      │   │payments schema│
            │         └─────┬──────┘   └──────┬────────┘
       contained_in     contained_in     contained_in
            │               │                │
      ┌─────▼─────┐  ┌─────▼──────┐  ┌──────▼──────┐
      │ Heading:  │  │ Class:     │  │ Table: loans│
      │ Catchment │  │LoanService │  └──────┬──────┘
      └───────────┘  └─────┬──────┘         │ belongs_to
                           │ defined_in ┌───▼───────┐
                     ┌─────▼───────┐    │  Column:  │
                     │ Function:   │    │loan.amount│
                     │calculate_emi│    └───────────┘
                     └─────────────┘
```

### Promoted Memory (Upgraded Learnings)
**What it is:** Facts from Tier 2 that were deemed important enough to become permanent.

**Real-world analogy:** A sticky note you wrote during a meeting (Tier 2) gets typed up and added to the official documentation (Tier 3).

**How it works:**
- Automatic: episodic memories with confidence ≥ 70% auto-promote
- Deliberative: every GBrain note auto-promotes (confidence 100%)
- Consolidated: cluster summaries auto-promote
- Each promoted fact carries provenance: source, score, when extracted, by what method

**Promotion path:**
```
Episodic (mem0) ──┬── score < 70% → stays in Qdrant (semantic search only)
                  │
                  └── score ≥ 70% → UKO node in graph
                                    ├── type: DOCUMENT
                                    ├── source: "mem0"
                                    ├── provenance: mem0_auto, confidence=0.82
                                    └── status: active

Deliberative (GBrain) ── 100% confidence → UKO node in graph
                                           ├── type: DOCUMENT
                                           ├── source: "gbrain"
                                           └── provenance: gbrain_write, confidence=1.0
```

---

## Complete Flow: One Question Through All 7 Memory Types

```
YOU ASK: "How does the payment service handle JWT authentication?"
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ TIER 1: SHORT-TERM                                          │
│                                                             │
│ 1. TASK MEMORY: Created fresh for this question             │
│    Stores: {}  (nothing yet, just starting)                 │
│                                                             │
│ 2. SESSION MEMORY: Checks what we discussed earlier         │
│    Looks up session "alex"                                  │
│    Finds: {"previous_topics": ["auth", "payment"]}          │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ TIER 2: SEMANTIC                                            │
│                                                             │
│ 3. EPISODIC (mem0): Semantic search by meaning              │
│    Q: "payment JWT authentication"                          │
│    Finds: "Alex's payment service uses JWT tokens"          │
│           (score: 0.45 — related topic)                     │
│                                                             │
│ 4. DELIBERATIVE (GBrain): Keyword search on notes           │
│    Scans memory/*.md                                        │
│    Finds: authentication-flow.md                            │
│           "The system uses JWT tokens issued by auth        │
│            service. Tokens expire after 24 hours."          │
│                                                             │
│ 5. CONSOLIDATED: (none yet — only 2 episodic memories)      │
│    Needs ≥3 memories in a cluster to trigger                │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│ TIER 3: LONG-TERM                                           │
│                                                             │
│ 6. KNOWLEDGE GRAPH: Search FalkorDB                         │
│    MATCH (u:UKO) WHERE content CONTAINS "payment"           │
│    Finds: 9,274 nodes from code sync (files, classes, etc.) │
│    Returns structured data with provenance                  │
│                                                             │
│ 7. PROMOTED: Auto-promotion check                           │
│    Memory: "Payment uses JWT" (score: 0.82)                 │
│    Score: 0.82 ≥ threshold 0.70 → PROMOTE TO GRAPH          │
│    Creates UKO node: mem0:mem_abc123 → stored permanently   │
└─────────────────────────────────────────────────────────────┘
         │
         ▼
    ANSWER: "Context used: 2 mem0 episodic memories,
             1 GBrain memory note"
```

---

## Memory Lifecycle: Birth → Growth → Maturity → Fading

```
BIRTH (Tier 1)
  Task Memory: Born and dies within one request
  Session Memory: Born on first question, lives 1 hour

GROWTH (Tier 1 → Tier 2)
  Episodic: Every conversation auto-creates new memories
  Deliberative: Explicit writes by user or agent

MATURITY (Tier 2 → Tier 3)
  Consolidation (every 10 turns):
    Episodic memories grouped by topic → GBrain notes
  
  Promotion (real-time):
    Episodic score ≥ 70% → Knowledge Graph
    GBrain notes → Knowledge Graph (always)
    Consolidated notes → Knowledge Graph (always)

FADING (Tier 2)
  Decay (every 24 hours):
    Old episodic memories lose 0.05 confidence
    If score drops below 0.30 → effectively forgotten
    BUT: if same fact exists in graph → protected from decay

  Validation (periodic):
    Check episodic against graph for contradictions
    Flagged memories: "System uses JWT" vs graph says "uses OAuth2"
    Corrected memory gets re-evaluated
```

---

## Quick Reference: Which Memory When?

| Question | Memory Type | Why |
|----------|------------|-----|
| "What was I just asking about?" | Task Memory | Current request context |
| "What did we discuss earlier today?" | Session Memory | Within TTL window |
| "What has Alex told us over the past week?" | Episodic (mem0) | Semantic search by meaning |
| "Where are the detailed notes on auth?" | Deliberative (GBrain) | Explicit written notes |
| "How does the codebase actually work?" | Knowledge Graph | Structured code facts |
| "Is this fact reliable?" | Promoted (graph) | Confidence ≥ 70%, with provenance |

---

## Memory Statistics (Current System)

| Tier | Type | Where Stored | Survives Restart? | Search Method |
|------|------|-------------|-------------------|---------------|
| 1 | Task | RAM | ❌ | N/A |
| 1 | Session | RAM / Redis | ❌ / ✅ | Key lookup |
| 2 | Episodic | Qdrant + SQLite | ✅ | Embedding similarity |
| 2 | Deliberative | .md files + Graph | ✅ | Keyword regex |
| 2 | Consolidated | .md files + Graph | ✅ | Keyword regex |
| 3 | Knowledge Graph | FalkorDB | ✅ | Cypher query |
| 3 | Promoted | FalkorDB | ✅ | Cypher query (filtered by provenance) |
