# Categorization Plan — Tech Domain Tagging via AI + Deterministic Apply

## Goal

After a connector syncs, every FalkorDB node gets a `domain` property
(frontend / backend / infrastructure / security / database / data-ml /
documentation / uncategorized, or any user-defined category). The domain is
derived from **content** (via AgentLoop with file tools, no memory), not just
file extension. The category taxonomy is **user-defined** — defaults are
provided but the user can add, edit, delete, and describe categories. The
categorizer uses the user's taxonomy as ground truth. No hardcoded assumptions.

---

## Design Decisions (locked)

1. **Trigger:** Background job runs after Git/MySQL/Jira sync completes.
   Non-blocking. Hook point: end of `sync_git_repo` / `sync_mysql_database` in
   `legacy/src/legacy_ecms/api/routes/providers.py`.
2. **Storage:** `domain` property on every FalkorDB node. Queryable via Cypher.
   Feeds the policy agent.
3. **Agent:** Dedicated AgentLoop session with the 20 file tools
   (glob, read_file, grep, read_directory, write_file, todo_write).
   **No memory access.** Prompt instructs: categorize by content, not extension.
4. **Method:** Hybrid.
   - Agent does ~15-20 strategic reads.
   - Agent writes `domain_mapping.json` (path_pattern → domain) to disk.
   - Deterministic Cypher pass applies mapping to ALL nodes in one query.
   - Low-confidence nodes → flagged `uncategorized` or second small pass.
5. **Taxonomy is user-owned.** Default categories seeded. User can add/edit/
   delete on a Categories page. Each category has a `description` the agent
   uses to classify. Agent receives the live taxonomy, never assumes.

---

## Categories Data Model

New table `categories`:

| Column | Purpose |
|--------|---------|
| `id` | uuid |
| `name` | `frontend`, `backend`, `security`, ... (unique) |
| `description` | User-provided description the agent uses to classify |
| `color` | UI badge color (hex) |
| `priority` | int — conflict resolution order (security > infra > ...) |
| `is_default` | bool — true for seeded 8 |
| `created_at`, `updated_at` | timestamps |

Seeded defaults (priority order):
1. security — "Code handling auth, tokens, secrets, encryption, credentials"
2. infrastructure — "IaC, Docker, K8s, CI/CD, cloud config, networking"
3. database — "Schemas, migrations, ORM models, queries, data layers"
4. frontend — "UI components, React/Vue, styles, client bundles"
5. backend — "APIs, services, business logic, server frameworks"
6. data-ml — "Notebooks, training, datasets, ML pipelines"
7. documentation — "Markdown, docs, READMEs, specs"
8. uncategorized — "Anything that does not match a defined category"

User can add e.g. `blockchain` → "Smart contracts, Solidity, chains" with
priority between security and infra. Agent uses that description.

---

## Components

### 1. Backend: categories table + repository + API
- `ecms/persistence/models/category.py` — Category model
- `ecms/persistence/repositories/category.py` — CRUD
- `ecms/api/rest/categories.py`:
  - `GET /categories` — list all (active taxonomy)
  - `POST /categories` — add (name, description, color, priority)
  - `PUT /categories/{id}` — edit
  - `DELETE /categories/{id}` — remove (cannot delete `uncategorized`)
- Alembic migration `0011_categories`

### 2. Backend: categorization engine
- `ecms/agent/categorize.py`:
  - `run_categorization(project_id, workspace_id)`:
    1. Load active taxonomy from `categories` table → prompt context
    2. Spawn AgentLoop (file tools only, no memory) with system prompt:
       "You are a code domain classifier. Given the file tree and sampled
        file contents of this repo, produce a JSON mapping of path patterns to
        one of these domains: [taxonomy names + descriptions]. Prefer content
        over extension. Output to /app/categorization/{project_id}.json"
    3. Agent does ~15-20 reads, writes `domain_mapping.json`
    4. Deterministic pass: `MATCH (n) WHERE n.group_id = {gid}
       SET n.domain = map_domain(n.source_id, json)` — one Cypher query
    5. Nodes with no match → `domain = 'uncategorized'`
    6. Update category counts in a `category_stats` cache (optional)
- Hook into `providers.py` sync completion: `background_tasks.add_task(
  run_categorization, workspace_id, project_id)`

### 3. Frontend: Categories panel INSIDE the Graph page
- No separate route. The Graph page (`app/(dashboard)/graph/page.tsx`) gets a
  "Categories" section in its left panel (replacing the fake `ontologyTypes`
  list):
  - List active categories with color badges, priority, description, live count
  - "Add Category" inline form: name, description, color picker, priority
  - Edit/Delete inline (cannot delete `uncategorized`)
  - Note shown: "The categorization agent uses these descriptions to classify.
    Add a category if your org has a domain not listed."
  - "Recategorize" button → triggers `POST /categorize?project_id=X` (re-run)
- Graph page rendering:
  - Replace hardcoded `ontologyTypes` with live categories from `GET /categories`
  - Count per category from node `domain` property (graph store computes it)
  - Click category → filter D3 graph to that domain

### 4. Graph store update
- `graph-store.ts`: compute `categoryCounts` map from `nodes[].domain`
- `loadFromRest` sets `domain` from node property
- UI badge shows real count per category

---

## AgentLoop Categorization Prompt (draft)

```
You are a code domain classifier. A repository was just synced into a
knowledge graph. Your job: decide the technical domain of each part.

Available categories (use ONLY these, with their descriptions):
{categories_json}

Rules:
- Read the actual file contents, not just extensions.
- A Frappe .json dashboard is BACKEND, not frontend.
- A webpack.config.js is FRONTEND, not backend.
- Prefer content over path when they conflict.
- Output a JSON file at {output_path} with this shape:
  {
    "patterns": [
      {"pattern": "**/package.json", "domain": "frontend", "reason": "..."},
      {"pattern": "**/*.tf", "domain": "infrastructure", "reason": "..."}
    ]
  }
- Cover ~15-20 strategic patterns. Be precise.
```

---

## Scale Handling

- Agent: ~15-20 tool calls (not 13,071).
- Deterministic apply: 1 Cypher query sets `domain` on all nodes.
- Re-sync: re-run categorization, overwrite `domain`.

---

## Connection to Policy Agent

Policy agent reads `domain` from FalkorDB nodes → maps to department.
One shared signal. The taxonomy the user defines for categorization is the
same taxonomy the policy agent uses for access scoping (department names
must align — documented in onboarding).

---

## Verification

1. Sync a repo → background categorization runs → nodes get `domain`.
2. Graph page Categories panel shows 8 defaults with real counts.
3. Add `blockchain` category in-panel → click Recategorize → nodes matching its
   description get `domain: blockchain`.
4. Graph page shows real per-category counts, not hardcoded 0.
5. Policy agent maps `domain: frontend` → frontend department.
