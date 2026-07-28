# Implementation Plan — BA Agent Designs a Per-Project Team

The BA agent, after finalizing requirements, designs a professional software-company
agent org chart scoped to the project. Reuses the deterministic `finalize` machinery
(one function-calling generation + validate/repair loop). No ReAct loop, no per-agent
tool. Team generation runs in the BACKGROUND; the workspace opens immediately and shows
a realistic "assembling team" state until the org chart is ready.

## Locked decisions
- **When:** automatically as part of Create Project.
- **How (NEW):** background generation. Navigate to workspace immediately (as today).
  Until the team exists, the Worker Hierarchy panel shows a realistic "Assigning your
  project team…" loading state. Workspace polls until ready, then renders the real tree.
- **Shape:** agents-only real software-services delivery org. Root = `delivery_manager`.
- **Depth:** NO constraint — BA decides depth & breadth from project needs.
- **Catalog-driven:** `model` ∈ `ai_models`; `tools` ⊆ real ~39-tool registry.
- **Scoping:** each project = its own org chart → new `project_id` column on `agents`.
- **Model storage:** new `model` column on `agents` (same migration).

## Role vocabulary (fixed enum)
- Management spine: `delivery_manager` (root), `engineering_manager`, `qa_lead`
- Advisory (report to DM): `architect`, `business_analyst`
- ICs (leaves): `senior_engineer`, `engineer`, `sre`, `security_engineer`, `qa_engineer`
- Department: backend, frontend, data_migration, integration, infrastructure,
  security, quality_assurance, deployment, documentation

## Team status lifecycle (drives the loading UX)
`business_projects.team_status`: `pending` → `generating` → `ready` | `failed`
- Set `generating` when design-team kicks off.
- Set `ready` when agents inserted; `failed` on LLM/validation error (regeneratable).

---

## Files to CREATE

1. `migrations/versions/0022_agent_project_model.py` (Pattern A — raw ALTER):
   - `ALTER TABLE agents ADD COLUMN IF NOT EXISTS project_id TEXT`
   - `ALTER TABLE agents ADD COLUMN IF NOT EXISTS model TEXT`
   - `ALTER TABLE business_projects ADD COLUMN IF NOT EXISTS team_status TEXT DEFAULT 'pending'`
   - `CREATE INDEX IF NOT EXISTS ix_agents_project_id ON agents (project_id)`
   - downgrade: pass

2. `ba/team_schema.py` — `TeamAgent` + `AgentTeam` pydantic. Flat list, tree via
   `reports_to` keys. `@model_validator` enforces GRAMMAR not depth:
   one `delivery_manager` root, valid reports_to refs, no cycles, only management roles
   may parent, model/tools ∈ catalog. `to_rows(project_id)` → agents columns.

3. `ba/team_exemplar.py` — `GOLDEN_TEAM` calibration example.

## Files to MODIFY

4. `models/agent.py` — add `project_id` + `model` columns + to_dict().
5. `repositories/agent.py` — add `list_by_project()`, `delete_by_project()`.
6. `ba/prompts.py` — `build_team_prompt(requirements, conversation)`,
   `build_team_tool(model_ids, tool_names)` (role/dept enums fixed; model/tool
   enums injected from live catalogs).
7. `ba/agent.py` — `design_team(...)`, a copy of `finalize()`'s validate/repair loop.
8. `ba/catalog.py` (small helper) — `get_model_ids()` (from ai_models),
   `get_tool_names()` (from ECMS + CommandCode + org tool registries).
9. `api/rest/discovery.py` — `POST /{session_id}/design-team`:
   - auth; require FINALIZED + linked project_id.
   - set business_projects.team_status='generating'; schedule background task
     (FastAPI BackgroundTasks / asyncio) and return 202 `{status:'generating'}` FAST.
   - background: run design_team → delete_by_project(pid) → insert rows →
     team_status='ready'; on error team_status='failed'.
   - Also add `GET /projects/{project_id}/team-status` (or reuse platform) returning
     `{team_status, agents:[...]}` for the workspace to poll.
   - Use db_session() (:name params), not the asyncpg pool.

10. `NewProject.tsx` — in `handleCreateProject`, after link-project and BEFORE navigate,
    fire-and-forget `ApiClient.post('/discovery/${sessionId}/design-team', {})` (don't
    await the generation; endpoint returns 202 immediately). Keep navigate as-is.

11. `ProjectWorkspace.tsx` —
    - On mount, GET team-status + agents. Build `WorkerHierarchyNode[]` from reports_to.
    - If team_status ∈ {pending,generating}: render realistic loading state in the
      Worker Hierarchy panel (skeleton rows + "Assigning your project team…" +
      subtle progress), and POLL every ~3s until ready/failed.
    - ready → render real tree (agents-only; drop human tier; role→display map).
    - failed → show inline error + "Regenerate team" button (re-POST design-team).
    - Remove hardcoded isMigration workerTree mock for real projects.

## Verification
- Backend: pytest for team_schema validators (one-root, cycle reject, IC-can't-parent,
  catalog membership) + design_team with a stubbed client. `alembic upgrade head` clean.
- Frontend: tsc + rebuild image; confirm loading state shows then real tree renders.

## Notes / risks
- design-team depends on link-project having set project_id; if link failed, skip
  gracefully (team_status stays pending; workspace offers Regenerate).
- Project creation never blocks on the LLM — generation is fully background.
- Scope: only the Worker Hierarchy is wired to real data; rest of workspace stays mock.
