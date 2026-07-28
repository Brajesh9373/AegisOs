# Policy Engine — Implementation Plan

## What We're Building

An Attribute-Based Access Control (ABAC) policy engine that gates access to memory (atoms) and knowledge graph (UKO nodes) based on an agent's position in the org hierarchy. Resources carry only intrinsic attributes. Policies are separate database rows evaluated at query time. C-suite (any agent with `reports_to = NULL`) gets unrestricted access. A policy recommendation agent scans connected sources and proposes policies based on the existing org chart.

---

## Database

### 1. `access_policies` table (migration 0009)

```sql
CREATE TABLE access_policies (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    effect TEXT NOT NULL CHECK (effect IN ('allow', 'deny')),
    -- Subject matching (who this policy applies to)
    agent_id TEXT REFERENCES agents(id) ON DELETE CASCADE,
    department TEXT,
    role_level_min INTEGER DEFAULT 1,
    -- Resource matching (what resources this covers)
    resource_type TEXT,           -- 'memory_atom', 'graph_node', 'file', or NULL = all
    path_pattern TEXT,            -- '/backend/**', '/workspace/infra/**', or NULL = all paths
    source_type TEXT,             -- 'git', 'mysql', 'jira', or NULL = all sources
    resource_attrs JSONB DEFAULT '{}',  -- {schema: 'billing', project: 'INFRA', labels: ['confidential']}
    -- Actions
    action TEXT NOT NULL CHECK (action IN ('read', 'write', 'delete')),
    -- Metadata
    priority INTEGER DEFAULT 100, -- lower = evaluated first
    created_by TEXT REFERENCES agents(id),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX ix_policies_agent ON access_policies(agent_id);
CREATE INDEX ix_policies_dept ON access_policies(department);
CREATE INDEX ix_policies_resource ON access_policies(resource_type);
```

### 2. `policy_recommendations` table (migration 0010)

```sql
CREATE TABLE policy_recommendations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    project_id TEXT REFERENCES projects(workspace_id) ON DELETE CASCADE,
    policies_json JSONB NOT NULL,       -- the full recommendation payload from the agent
    org_snapshot JSONB,                  -- org chart state when recommendation was made
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected','modified')),
    reviewed_by TEXT REFERENCES agents(id),
    reviewed_at TIMESTAMPTZ,
    created_by TEXT,                     -- which agent made the recommendation
    created_at TIMESTAMPTZ DEFAULT now()
);
```

---

## Backend Code

### 3. `backend/ecms/agent/access_engine.py` — NEW

```python
# Core policy evaluation — called at query time

def evaluate_access(agent: Agent, resource: dict, action: str) -> bool:
    """Evaluate whether an agent can access a resource.
    
    Rules:
    1. agent.reports_to IS NULL → ALLOW everything (C-suite)
    2. Evaluate DENY policies first — any match → DENIED
    3. Evaluate ALLOW policies — first match → ALLOWED  
    4. Default: DENY
    """
    # Root agent (C-suite): unrestricted access
    if agent.reports_to is None:
        return True
    
    policies = get_policies_for_agent(agent.id, agent.department, agent.role_level)
    
    # DENY first
    for p in policies:
        if p.effect == 'deny' and policy_matches(p, agent, resource, action):
            return False
    
    # Then ALLOW
    for p in policies:
        if p.effect == 'allow' and policy_matches(p, agent, resource, action):
            return True
    
    return False  # default deny


def get_policies_for_agent(agent_id, department, role_level):
    """Get all applicable policies for an agent."""
    return session.query(AccessPolicy).filter(
        or_(
            AccessPolicy.agent_id == agent_id,
            AccessPolicy.department == department,
            AccessPolicy.role_level_min <= role_level,
            AccessPolicy.agent_id.is_(None)  # global policies
        )
    ).order_by(AccessPolicy.priority).all()


def policy_matches(policy, agent, resource, action):
    """Check if a specific policy applies to this agent + resource + action."""
    if policy.action != action and policy.action != '*':
        return False
    if policy.resource_type and policy.resource_type != resource.get('type'):
        return False
    if policy.path_pattern and not fnmatch(resource.get('source_path', ''), policy.path_pattern):
        return False
    if policy.source_type and policy.source_type != resource.get('source'):
        return False
    for k, v in policy.resource_attrs.items():
        if resource.get(k) != v:
            return False
    return True


def filter_memory_results(agent, atoms, action='read'):
    """Post-filter search_memory results through policy engine."""
    return [a for a in atoms if evaluate_access(agent, a.to_policy_resource(), action)]


def inject_graph_constraints(agent, cypher):
    """Pre-filter query_graph by injecting path/source constraints."""
    paths = get_allowed_paths(agent)
    if not paths:  # empty = C-suite, no constraints
        return cypher
    constraints = " OR ".join(f"u.source_path STARTSWITH '{p}'" for p in paths)
    # Insert constraint into WHERE clause
    ...
```

### 4. `backend/ecms/agent/policy_agent.py` — NEW

```python
# Autonomous policy recommendation agent
# Scans connected sources + org chart → recommends policies + agent mappings

async def recommend_policies(project_id, connector_ids=None):
    """Scan a project's connected sources and recommend access policies."""
    
    # 1. Load org chart
    agents = get_agents()
    departments = {a.department for a in agents}
    org_tree = get_org_tree()
    
    # 2. Scan each connected source
    recommendations = []
    for source in get_connected_sources(project_id):
        if source.type == 'git':
            recs = _scan_git_repo(source, departments, org_tree)
        elif source.type == 'mysql':
            recs = _scan_mysql(source, departments, org_tree)
        elif source.type == 'jira':
            recs = _scan_jira(source, departments, org_tree)
        recommendations.extend(recs)
    
    # 3. Generate agent mapping (which agents get assigned to which resources)
    agent_mappings = _map_agents_to_resources(recommendations, agents)
    
    # 4. Save as a recommendation for CTO review
    save_recommendation(project_id, recommendations, agent_mappings)


def _scan_git_repo(source, departments, org_tree):
    """Scan a Git repo: map directories → departments → agents."""
    # glob top-level dirs → match to department names → generate allow policies
    ...

def _scan_mysql(source, departments, org_tree):
    """Scan MySQL: schemas with salary/confidential → higher clearance.
    Schemas matching department names → allow that department."""
    ...

def _scan_jira(source, departments, org_tree):
    """Scan Jira: projects + labels → department matching.
    Projects labeled 'confidential' → C-suite only."""
    ...
```

### 5. Integration Points

| File | Change |
|------|--------|
| `tools.py` — `search_memory()` | Post-filter results: `filter_memory_results(agent, atoms)` |
| `tools.py` — `query_graph()` | Pre-filter: `inject_graph_constraints(agent, cypher)` |
| `tools.py` — `read_file()` | Gate write operations: `evaluate_access(agent, resource, 'write')` |
| `tools.py` — `write_file()`, `edit_file()` | Same gate |
| `tool_capture.py` | No changes needed — atoms carry only intrinsic attributes |
| `loop.py` — `_build_messages()` | Inject agent identity OR no identity (default: all access) |

### 6. API Endpoints

```
GET    /policies              List all active policies
POST   /policies              Create a policy
PUT    /policies/{id}         Update a policy
DELETE /policies/{id}         Delete a policy
GET    /policies/recommendations    List pending recommendations
POST   /policies/recommendations    Trigger the policy agent for a project
POST   /policies/recommendations/{id}/approve   Approve a recommendation
POST   /policies/recommendations/{id}/reject    Reject a recommendation
```

---

## Frontend

### 7. `frontend/app/(dashboard)/admin/policies/page.tsx` — NEW

```
┌──────────────────────────────────────────────────────────────────┐
│ Access Policies                                                  │
│                                                                   │
│ Active Policies (12)                                 [+ Add]     │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ ALLOW │ backend dept │ /backend/**     │ read  │ ✕          │ │
│ │ DENY  │ frontend     │ /backend/**     │ read  │ ✕          │ │
│ │ ALLOW │ platform     │ /infra/**       │ read  │ ✕          │ │
│ │ ALLOW │ C-suite      │ /**             │ *     │ (system)   │ │
│ └──────────────────────────────────────────────────────────────┘ │
│                                                                   │
│ Pending Recommendations (1)                                       │
│ ┌──────────────────────────────────────────────────────────────┐ │
│ │ Monorepo analysis — 11 policies across 3 connectors          │ │
│ │ Source: Git (monorepo) + MySQL (billing) + Jira              │ │
│ │ Recommended: 2026-07-11 by Policy Agent                      │ │
│ │                                                               │ │
│ │ ☑ ALLOW backend → /backend/**         (Git, 92% conf)       │ │
│ │ ☑ ALLOW frontend → /frontend/**       (Git, 94% conf)       │ │
│ │ ☑ ALLOW backend → mysql:billing.*     (MySQL, 90% conf)     │ │
│ │ ☑ ALLOW C-suite → mysql:hr_portal.*   (MySQL, 96% conf)     │ │
│ │ ... (7 more)                                                  │ │
│ │                                                               │ │
│ │ Agent Mappings:                                               │ │
│ │ ☑ /backend/**    → EM Backend (owner) + Sr + Jr             │ │
│ │ ☑ /frontend/**   → EM Frontend (owner) + Sr + Jr            │ │
│ │ ☑ billing.*      → Sr Backend (owner) + Jr Backend          │ │
│ │                                                               │ │
│ │ [Approve All]    [Edit]    [Reject]                           │ │
│ └──────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────┘
```

---

## Implementation Order

| # | What | Files |
|---|------|-------|
| 1 | `access_policies` table migration | migration 0009 |
| 2 | `policy_recommendations` table migration | migration 0010 |
| 3 | Policy model + repository | `persistence/models/policy.py`, `repositories/policy.py` |
| 4 | Access engine (`evaluate_access`, filters) | `agent/access_engine.py` |
| 5 | Integration: search_memory post-filter | `agent/tools.py` |
| 6 | Integration: query_graph pre-filter | `agent/tools.py` |
| 7 | Integration: write gates on write_file, edit_file | `agent/tools.py` + `commandcode_tools/tools.py` |
| 8 | Policy CRUD API | `api/rest/policies.py` |
| 9 | Policy recommendation agent | `agent/policy_agent.py` |
| 10 | Frontend: admin policies panel | `app/(dashboard)/admin/policies/page.tsx` |
