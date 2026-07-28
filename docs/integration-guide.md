# Memory Integration Guide

A step-by-step guide for integrating the ECMS 10-tier memory system into a new
application or service. Each step is self-contained — complete it before moving
to the next.

---

## Prerequisites

Before starting, confirm your environment matches:

| Requirement | Minimum | Verified With |
|-------------|---------|---------------|
| Python | 3.12+ | `uv run python --version` |
| PostgreSQL | 16 | `psql --version` |
| Redis | 7 | `redis-cli --version` |
| FalkorDB | latest | `redis-cli -p 6380 PING` → `PONG` |
| Qdrant | latest | `curl http://localhost:6333/health` → `{"title":"...","version":"..."}` 
| Docker (optional) | 24+ | `docker compose version` |
| Node.js (frontend only) | 20+ | `node --version` |

---

## Part 1 — Infrastructure Setup (15 minutes)

### Step 1 — Clone and configure the repository

```bash
git clone <repository-url> ecms
cd ecms
```

Copy the environment template:

```bash
cp .env.example .env   # or create from scratch
```

Set these required variables:

```bash
ECMS_DATABASE_URL=postgresql+asyncpg://ecms:ecms@localhost:5432/ecms
ECMS_FALKORDB_URL=redis://localhost:6380
ECMS_REDIS_URL=redis://localhost:6379/0
ECMS_MEM0_QDRANT_URL=http://localhost:6333
ECMS_OPENAI_API_KEY=sk-...
ECMS_LLM_MODEL=gpt-4o-mini
ECMS_ENVIRONMENT=development
```

### Step 2 — Start the infrastructure services

**Option A: Docker Compose (recommended for full stack)**

```bash
docker compose -f docker/docker-compose.yml up -d postgres redis falkordb qdrant
```

Wait for all services to report healthy:

```bash
docker compose -f docker/docker-compose.yml ps
# All services should show "healthy" or "running"
```

**Option B: Manual (for custom environments)**

Install and start each service individually, then configure connection
strings to point to your instances.

### Step 3 — Install backend dependencies

```bash
cd backend
uv venv --python 3.12
uv sync
```

Verify the installation:

```bash
uv run python -c "import ecms; print(ecms.__version__)"
# 0.1.0
```

### Step 4 — Run database migrations

```bash
uv run alembic upgrade head
```

Expected output:

```
INFO  [alembic.runtime.migration] Running upgrade 0001 → 0002
INFO  [alembic.runtime.migration] Running upgrade 0002 → 0003
INFO  [alembic.runtime.migration] Running upgrade 0003 → 0004
INFO  [alembic.runtime.migration] Running upgrade 0004 → 0005
```

Verify the tables exist:

```bash
uv run python -c "
import asyncio, os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

async def check():
    engine = create_async_engine(os.environ['ECMS_DATABASE_URL'])
    async with engine.connect() as conn:
        result = await conn.execute(text(
            \"SELECT table_name FROM information_schema.tables WHERE table_schema='public'\"
        ))
        print([row[0] for row in result])

asyncio.run(check())
"
# ['projects', 'project_connectors', 'sessions', 'session_messages',
#  'aggregates', 'audit_records', 'event_store']
```

---

## Part 2 — Backend Integration (Core API)

### Step 5 — Start the backend server

```bash
uv run uvicorn ecms.main:app --reload --host 0.0.0.0 --port 8000
```

Verify it's running:

```bash
curl http://localhost:8000/health
# {"status":"ok","service":"ecms","version":"0.1.0"}
```

### Step 6 — Create your first project

A project (workspace) is the top-level container for all memory. All data is
workspace-scoped — create one before anything else.

```bash
curl -X POST http://localhost:8000/workspaces \
  -H "Content-Type: application/json" \
  -d '{"workspace_id": "my-project", "name": "My First Project"}'
# {"workspace_id":"my-project","created":true}
```

Verify in PostgreSQL:

```bash
psql $ECMS_DATABASE_URL -c "SELECT workspace_id, name FROM projects;"
#  workspace_id |      name
# --------------+-----------------
#  my-project   | My First Project
```

### Step 7 — Connect a knowledge source

**Option A: Sync a Git repository (async connector ingestion)**

> The legacy `POST /providers/git/sync` endpoint has been retired (HTTP 410).
> Use the new async connector ingestion API instead.

```bash
curl -X POST http://localhost:8000/api/connector-ingestions \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "my-project",
    "connector_type": "git",
    "config": {
      "repo_url": "https://github.com/your-org/your-repo",
      "access_token": "ghp_...",
      "platform": "github",
      "branch": "main"
    }
  }'
# {"job_id":"...","status":"queued","workspace_id":"my-project","connector_type":"git"}
```

The ingestion runs asynchronously. Poll the job status:

```bash
curl http://localhost:8000/api/connector-ingestions/{job_id}
# {"job_id":"...","status":"completed","uko_count":142,...}
```

**Option B: Sync a MySQL database**

```bash
curl -X POST http://localhost:8000/api/connector-ingestions \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "my-project",
    "connector_type": "mysql",
    "config": {
      "host": "db.example.com",
      "port": 3306,
      "user": "reader",
      "password": "secret",
      "database": "app_db"
    }
  }'
```

**Option C: Direct UKO ingestion**

```bash
curl -X POST http://localhost:8000/ingest/uko \
  -H "Content-Type: application/json" \
  -d '{
    "uko": {
      "title": "API Documentation",
      "content": "Our API uses JWT auth...",
      "provider": "manual",
      "language": "python"
    },
    "persist": true
  }'
```

After syncing, the knowledge graph has nodes. Verify:

```bash
curl http://localhost:8000/projects
# [{"workspace_id":"my-project","name":"My First Project","node_count":142,...}]
```

### Step 8 — Create a chat session

```bash
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"workspace_id": "my-project", "title": "First Conversation"}'
# {"session_id":"abc123...","status":"created","workspace_id":"my-project"}
```

Save the `session_id` — you'll use it for all messages in this conversation.

### Step 9 — Send a message (agent reads memory automatically)

```bash
curl -X POST http://localhost:8000/sessions/abc123.../chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain the authentication system", "workspace_id": "my-project"}'
# {"session_id":"abc123...","answer":"Based on your codebase...","trace":{...}}
```

The agent automatically:
1. Creates working memory for this turn
2. Loads session context from Redis
3. Reads conversation history from PostgreSQL
4. Searches the atom store for relevant knowledge
5. Queries the FalkorDB graph if needed
6. Reads files if needed
7. Synthesizes an answer grounded in your actual codebase

After the response, fire-and-forget writes happen:
- Messages persisted to PostgreSQL
- Episode logged to `/app/memory/episodes.ndjson`
- Captured to mem0 semantic memory (if enabled)
- GBrain markdown note written
- Structured atoms extracted

### Step 10 — Retrieve message history

```bash
curl http://localhost:8000/sessions/abc123.../messages
# {"messages":[
#   {"id":"1","role":"user","content":"Explain the authentication system",...},
#   {"id":"2","role":"assistant","content":"Based on your codebase...",...}
# ]}
```

### Step 11 — List sessions for your project

```bash
curl "http://localhost:8000/sessions?workspace_id=my-project"
# {"sessions":[{"session_id":"abc123...","title":"First Conversation","message_count":2,...}]}
```

---

## Part 3 — Memory Tiers (Enable Layer by Layer)

### Step 12 — Enable semantic memory (mem0)

mem0 stores conversation facts as vector embeddings in Qdrant for semantic search.

In your `.env` or environment:

```bash
ECMS_MEM0_ENABLED=true
ECMS_MEM0_QDRANT_URL=http://localhost:6333
ECMS_MEM0_PROMOTION_THRESHOLD=0.70
ECMS_MEM0_CONSOLIDATION_TURNS=10
ECMS_MEM0_DECAY_INTERVAL_HOURS=24
```

Restart the backend. After a few chat turns, verify mem0 has data:

```bash
curl http://localhost:6333/collections
# {"result":{"collections":[{"name":"ecms_mem0_my-project"}]}}
```

Now when the agent calls `search_memory()`, it searches both the atom store
(keyword) and mem0 (semantic vector search) and returns the combined results.

### Step 13 — Seed initial knowledge atoms

The atom store starts empty. Seed it with verified facts to give the agent
immediate context:

```python
# seed_knowledge.py
import asyncio, json
from pathlib import Path
from legacy_ecms.memory.stores.file_store import FileMemoryStore
from legacy_ecms.memory.domain import MemoryAtom, MemoryType, MemoryStatus, MemoryScope, Evidence

store = FileMemoryStore(Path("/app/memory"))

atoms = [
    MemoryAtom(
        id="SEED-ARCH-001",
        type=MemoryType.ARCHITECTURE,
        topic="System Architecture",
        summary="The platform uses FastAPI on port 8000 with PostgreSQL for persistence and FalkorDB for the knowledge graph.",
        confidence=0.95,
        status=MemoryStatus.VERIFIED,
        scope=MemoryScope.GLOBAL,
        evidence=[Evidence(source="architecture-docs", source_type="documentation")],
        tags=["architecture", "platform"],
    ),
]

for atom in atoms:
    store.upsert_atom(atom)
store.flush()
print(f"Seeded {len(atoms)} atoms")
```

Run it:

```bash
uv run python seed_knowledge.py
```

Verify atoms exist:

```bash
cat /app/memory/memory_atoms.ndjson | head -1 | python -m json.tool
```

### Step 14 — Trigger a manual memory consolidation

The cognitive orchestrator runs the capture → promote → consolidate → validate → decay
loop automatically, but you can trigger it manually:

```bash
curl -X POST http://localhost:8000/memory/consolidate
# {"consolidated": 3, "gbrain_notes": ["my-project auth patterns", ...]}
```

---

## Part 4 — Frontend Integration

### Step 15 — Install and start the frontend

```bash
cd frontend
pnpm install
pnpm dev
```

The frontend runs at `http://localhost:3000`. The project switcher in the top
nav reads from `GET /projects` and filters sessions by workspace automatically.

### Step 16 — Integrate the ChatView component

The `ChatView` component handles history loading, message sending, and
workspace scoping. Import it into any page that needs a chat interface:

```tsx
// pages/your-chat-page.tsx
import { ChatView } from "@/features/sessions/components/chat-view";

export default function YourChatPage() {
  const sessionId = "abc123...";  // From your session creation logic
  return <ChatView sessionId={sessionId} />;
}
```

The component automatically:
- Fetches history from `GET /sessions/{id}/messages` on mount
- Sends `workspace_id` from the global store on every message
- Persists messages via `POST /sessions/{id}/chat`

### Step 17 — Wire the project switcher

```tsx
// In your layout or navigation
import { useGlobalStore } from "@/store/global-store";
import { useProjects } from "@/hooks/use-api";

function ProjectSwitcher() {
  const { workspaceId, setWorkspace, setProject } = useGlobalStore();
  const { data: projects } = useProjects();

  return (
    <select value={workspaceId ?? ""} onChange={(e) => {
      setWorkspace(e.target.value);
      setProject(e.target.value);
    }}>
      {projects?.map(p => (
        <option key={p.workspace_id} value={p.workspace_id}>
          {p.name} ({p.node_count} nodes)
        </option>
      ))}
    </select>
  );
}
```

---

## Part 5 — Cleaning Up (Cascade Delete)

### Step 18 — Delete a project and all its data

A single API call removes all data from all 6 storage backends:

```bash
curl -X DELETE http://localhost:8000/projects/my-project
# {
#   "deleted": true,
#   "workspace_id": "my-project",
#   "falkordb_nodes_removed": 142,
#   "db_deleted": true,
#   "sessions_deleted": 3,
#   "mem0_deleted": true,
#   "redis_sessions_cleared": 5,
#   "gbrain_deleted": true
# }
```

This cascade deletes:
1. **FalkorDB** — all UKOs with matching `group_id`
2. **PostgreSQL** — project row + connectors (CASCADE) + sessions + messages
3. **Qdrant** — mem0 collection `ecms_mem0_my-project`
4. **Redis** — all keys matching `ecms:session:my-project:*`
5. **Disk** — GBrain directory `/app/memory/my-project/`
6. **Disk** — GBrain directory `/app/memory/{group_id}/` (if different)

---

## Part 6 — Configuration Reference

### Environment Variables

| Variable | Default | Required | Purpose |
|----------|---------|----------|---------|
| `ECMS_DATABASE_URL` | `postgresql+asyncpg://ecms:ecms@postgres:5432/ecms` | Yes | Primary database |
| `ECMS_FALKORDB_URL` | `redis://localhost:6380` | Yes | Graph database |
| `ECMS_REDIS_URL` | `redis://localhost:6379/0` | Yes | Session cache |
| `ECMS_MEM0_QDRANT_URL` | `http://localhost:6333` | If mem0 enabled | Vector store |
| `ECMS_OPENAI_API_KEY` | — | For LLM features | OpenAI API key |
| `ECMS_LLM_MODEL` | `gpt-4o-mini` | No | Default model |
| `ECMS_MEM0_ENABLED` | `false` | No | Enable semantic memory |
| `ECMS_MEM0_PROMOTION_THRESHOLD` | `0.70` | No | Auto-promotion confidence floor |
| `ECMS_MEM0_CONSOLIDATION_TURNS` | `10` | No | Turns between consolidations |
| `ECMS_MEM0_DECAY_INTERVAL_HOURS` | `24` | No | Hours before confidence decay |
| `ECMS_ENVIRONMENT` | `development` | No | Deployment profile |
| `ECMS_DEBUG` | `false` | No | Verbose logging |
| `ECMS_RATE_LIMIT_PER_MINUTE` | `1000` | No | API rate limit |

### Port Map (Default)

| Service | Port | Protocol |
|---------|------|----------|
| Backend API | `8000` | HTTP/WS |
| Frontend | `3000` | HTTP |
| PostgreSQL | `5432` | TCP |
| Redis | `6379` | TCP |
| FalkorDB | `6380` | TCP (Redis protocol) |
| Qdrant | `6333` / `6334` | HTTP / gRPC |
| MinIO | `9000` / `9001` | S3 / Console |
| Prometheus | `9090` | HTTP |
| Grafana | `3300` | HTTP |

---

## Part 7 — Verification Checklist

After completing all steps, verify the system is working:

- [ ] `GET /health` returns `{"status":"ok"}`
- [ ] `POST /workspaces` creates a project
- [ ] `GET /projects` shows the project with node count
- [ ] `POST /api/connector-ingestions` queues a job that completes with `workspace_id` scoping
- [ ] `POST /sessions` creates a session scoped to a workspace
- [ ] `POST /sessions/{id}/chat` returns an answer grounded in actual codebase knowledge
- [ ] `GET /sessions/{id}/messages` returns full chat history
- [ ] `GET /sessions?workspace_id=X` filters to one project only
- [ ] `GET /projects` shows `connector_configs` with git repo details
- [ ] Mem0 collection `ecms_mem0_{workspace_id}` exists in Qdrant (if enabled)
- [ ] GPrain `.md` files appear in `/app/memory/` after chat turns
- [ ] `DELETE /projects/{id}` returns success with deletion counts for all stores
- [ ] After delete: PostgreSQL has no project/session rows, FalkorDB has no matching UKOs, Redis has no workspace-scoped keys, Qdrant collection is gone, disk directories are removed

---

## Troubleshooting

| Symptom | Check |
|---------|-------|
| `GET /projects` returns empty | Run the migration: `uv run alembic upgrade head` |
| Chat returns generic answers | Sync a repository first so the graph has code-level nodes |
| `502 Bad Gateway` on chat | LLM API key not set or invalid: check `ECMS_OPENAI_API_KEY` |
| FalkorDB connection errors | Verify `ECMS_FALKORDB_URL` points to the correct host:port |
| Mem0 not capturing | Set `ECMS_MEM0_ENABLED=true` and restart backend |
| Build fails on missing module | Run `uv sync` — dependencies are installed per-stage |
| Migration fails | Check PostgreSQL is running: `pg_isready -U ecms -h localhost` |

---

## Next Steps

- **Add more connectors:** The provider framework supports adding new connectors
  (Jira, Slack, Confluence) by implementing the `BaseProvider` interface.
- **Enable mem0:** Set `ECMS_MEM0_ENABLED=true` for semantic vector search
  across conversations.
- **Deploy to production:** See the [Kubernetes Helm chart](../kubernetes/helm/ecms)
  and [Terraform configuration](../terraform/).
- **Customize the agent:** Edit the system prompt in `backend/ecms/memory/system_prompt.py`
  to match your organization's conventions.
- **Add tool definitions:** Register new agent tools in `backend/ecms/agent/tools.py`
  by adding a function definition and implementing an async handler.
