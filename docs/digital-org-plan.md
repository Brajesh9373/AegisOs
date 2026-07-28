# Digital Organization — Agent Hierarchy & Cross-Team Communication

## Vision

A digital replica of a tech organization where AI agents serve roles
(Junior Dev → Senior Dev → Tech Lead → Engineering Manager → CTO),
report through a hierarchy, work on assigned tasks, and communicate
across teams through a formal request/response protocol.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                     ORG CHART                           │
│                                                         │
│  CTO ──┬── EM Backend ──┬── SrDev-B1 ── JrDev-B1     │
│        │                └── SrDev-B2 ── JrDev-B2     │
│        │                                               │
│        └── EM Frontend ─┬── SrDev-F1 ── JrDev-F1     │
│                          └── SrDev-F2 ── JrDev-F2     │
│                                                         │
│  Cross-Team Communication:                              │
│  Frontend Senior ←→ Backend Senior (request/fulfill)  │
└─────────────────────────────────────────────────────────┘
```

---

## Phase 1 — Agent Identity & Hierarchy

### 1.1 `agents` table

```
Table: agents
├── id (PK)
├── name
├── role (junior_dev | senior_dev | tech_lead | engineering_manager | cto)
├── department (backend | frontend | devops | data | platform | qa)
├── reports_to (FK → agents.id, nullable for CTO)
├── tool_policy (JSON) — which tools are allowed
├── workspace_scope (JSON) — accessible paths
├── system_prompt_addon (TEXT) — role-specific instructions
├── status (active | inactive)
├── created_at, updated_at
```

### 1.2 Role → Tool Policy Mapping

```
CTO:
  tools: all 39
  write: /workspace/**
  shell: yes

Engineering Manager:
  tools: all except kill_shell (requires CTO)
  write: /workspace/**
  shell: yes

Tech Lead:
  tools: all except publish_pattern (requires EM+)
  write: /workspace/{own_department}/**
  shell: yes

Senior Developer:
  tools: read_file, write_file, edit_file, glob, grep, read_directory,
         search_memory, query_graph, web_search, shell_command, todo_write
  NO: publish_pattern, kill_shell, monitor_command, task delegation tools
  write: /workspace/{own_department}/**
  shell: yes (with permission callback)

Junior Developer:
  tools: read_file, glob, grep, read_directory, search_memory, note,
         set_working, get_working, todo_write
  NO: write_file, edit_file, shell_command, web_search, query_graph
  write: /workspace/{own_department}/{own_project}/**
  shell: no
```

### 1.3 Agent CRUD API

```
POST   /agents                    Create agent
GET    /agents                    List all agents (flat or tree)
GET    /agents/{id}               Get agent with reports
PUT    /agents/{id}               Update agent
DELETE /agents/{id}               Remove agent (cascade reassign tasks)

GET    /org-chart                 Full hierarchy tree
```

### 1.4 Session Identity Injection

When an agent session starts, their identity is loaded:

```
<context_environment>
Agent: JrDev-B1 (Junior Developer, Backend)
Role: junior_dev
Department: backend
Reports to: SrDev-B1
Workspace scope: /workspace/backend/rate-limiter/**
</context_environment>
```

Tools are filtered by `get_effective_tools(agent_role)` — same pattern as plan mode.

---

## Phase 2 — Task Delegation

### 2.1 `tasks` table

```
Table: tasks
├── id (PK)
├── title
├── description
├── inputs (JSON) — file paths, specs, references
├── expected_output (TEXT) — format and deliverables
├── assigner_id (FK → agents.id)
├── assignee_id (FK → agents.id)
├── status (pending | in_progress | submitted | approved | rejected)
├── review_feedback (TEXT) — from assigner when rejected
├── output_files (JSON array) — paths to produced files
├── output_summary (TEXT)
├── priority (low | normal | high | blocking)
├── parent_task_id (FK → tasks.id, nullable)
├── created_at, updated_at
```

### 2.2 Delegation Tools

```
assign_task(assignee, title, description, inputs?, expected_output?, priority?)
  → Creates task row
  → Validates assigner has authority over assignee (reports_to chain)
  → Returns task ID

my_tasks(status?, limit?)
  → Lists tasks assigned to the calling agent
  → Filterable by status

start_task(task_id)
  → Sets task → in_progress
  → Loads task context into current session
  → Injects inputs into <context_environment>
  → Injects expected_output into <context_memory>

submit_task(task_id, summary, output_files?)
  → Sets task → submitted
  → Stores output references
  → Notifies assigner

review_task(task_id, decision, feedback?)
  → decision: approved | rejected
  → If approved: task → approved, output published as org knowledge
  → If rejected: task → rejected, feedback stored, assignee can restart

delegate_plan(goal, plan[])
  → Creates multiple tasks from a plan
  → Each plan item: { assignee, title, description, inputs?, expected_output? }
  → Validates hierarchy for each assignee
```

### 2.3 Hierarchy Validation

```
can_assign(assigner, assignee) → bool:
  - CTO can assign to anyone
  - EM can assign to Tech Leads and below in their department
  - Tech Lead can assign to Seniors and below in their team
  - Senior can assign to Juniors reporting to them
  - Junior can assign to NO ONE
  - Cross-department: must go through cross_team_requests
```

---

## Phase 3 — Cross-Team Communication

### 3.1 `cross_team_requests` table

```
Table: cross_team_requests
├── id (PK)
├── title
├── description
├── requester_id (FK → agents.id)
├── target_dept (backend | frontend | devops | data | platform | qa)
├── target_senior_id (FK → agents.id, nullable — auto-resolved)
├── spawned_task_id (FK → tasks.id, nullable)
├── status (pending | accepted | in_progress | fulfilled | declined)
├── inputs (JSON) — specs, contracts, examples
├── output (JSON) — delivered results
├── priority (low | normal | high | blocking)
├── created_at, resolved_at
```

### 3.2 `task_dependencies` table

```
Table: task_dependencies
├── id (PK)
├── blocked_task_id (FK → tasks.id)
├── blocker_task_id (FK → tasks.id)
├── dependency_type (same_team | cross_team)
├── cross_team_request_id (FK → cross_team_requests.id, nullable)
```

### 3.3 Communication Tools

```
request_from_team(title, description, target_dept, priority?, inputs?)
  → Creates cross_team_requests row
  → Finds target department's lowest-level agent with accept permission (Tech Lead+)
  → Creates notification
  → Returns request ID

accept_request(request_id, assignee?)
  → Validates caller is target senior or their chain
  → Creates task from request spec
  → Links request.spawned_task_id → task
  → Sets request status → accepted
  → If assignee specified: auto-assigns task

fulfill_request(request_id, output)
  → Validates spawned task is approved
  → Sets request → fulfilled
  → Stores output references
  → Notifies requester

my_blockers()
  → Lists tasks blocked by dependencies
  → Shows status of each blocker
  → Returns: [{blocked_task, blocker, team, status, assigned_to}]
```

---

## Phase 4 — Context Injection System

### 4.1 What Gets Injected Per Agent Role

When an agent session loads (`_build_messages` in loop.py), the system injects:

```
<context_environment>
Agent: {name} ({designation}, {department})
Role: {role}
Department: {department}
Reports to: {manager_name}
Workspace scope: {paths}
Plan mode: OFF
</context_environment>

<context_tasks>
## Your Tasks
- task-42: "Implement rate limiter" (in_progress)
  Assigner: sr-dev-1, Priority: high
  Expected output: Single file at src/middleware/rate_limiter.py

- task-43: "Add unit tests for auth" (pending)
  Assigner: sr-dev-3, Priority: normal

## Your Assignments (for Seniors/Leads/Managers)
- task-42 → jr-dev-2 (in_progress)
- task-43 → jr-dev-3 (pending)

## Cross-Team Requests
Incoming: None
Outgoing: ctr-42 → backend (POST /api/submit, in_progress)
</context_tasks>

<context_dependencies>
## Blockers
- Task "Build submit button" → blocked by ctr-42 (POST /api/submit, backend, in_progress)

## Tasks Blocked by You
- None
</context_dependencies>
```

### 4.2 Context Blocks by Role

| Block | Junior | Senior | Lead | EM | CTO |
|-------|--------|--------|------|----|-----|
| `<context_tasks>` — your work | ✓ | ✓ | ✓ | ✓ | ✓ |
| `<context_tasks>` — your assignments | ✗ | ✓ | ✓ | ✓ | ✓ |
| `<context_dependencies>` — blockers | ✓ | ✓ | ✓ | ✓ | ✓ |
| `<context_org>` — full org chart | ✗ | ✗ | ✓ | ✓ | ✓ |
| `<context_cross_team>` — pending requests | ✗ | ✓ | ✓ | ✓ | ✓ |

---

## Phase 5 — Frontend Org Panel

### 5.1 Route: `/org`

```
┌─────────────────────────────────────────────────────┐
│  Organization                               [+ Add Agent]  │
│                                                       │
│  ┌─────────────────────────────────────────┐ │
│  │ 👤 CTO (You) — Full Access              │ │
│  └──────────┬──────────────────┘ │
│             │                                               │
│  ┌──────────┴──────────────────┐    │
│  │ 👤 EM Backend            │ 👤 EM Frontend   │    │
│  │   tools: 38/39             │   tools: 38/39    │    │
│  │   reports: CTO             │   reports: CTO    │    │
│  └──────┬──────────────┘ └──────┬──────────┘  │
│         │                               │                     │
│    ┌────┴────┐                   ┌────┴────┐       │
│    ▼              ▼                   ▼              ▼           │
│  ┌────────┐ ┌────────┐       ┌────────┐ ┌────────┐ │
│  │ SrDev  │ │ SrDev  │       │ SrDev  │ │ JrDev  │ │
│  │ B1     │ │ B2     │       │ F1     │ │ F1     │ │
│  └───┬────┘ └────────┘       └────────┘ └────────┘ │
│      │                                                          │
│  ┌───┴────┐                                                │
│  ▼              ▼                                                │
│ ┌────────┐ ┌────────┐                                  │
│ │ JrDev  │ │ JrDev  │                                  │
│ │ B1     │ │ B2     │                                  │
│ └────────┘ └────────┘                                  │
└─────────────────────────────────────────────────────┘
```

### 5.2 Agent Detail Panel (click on any agent)

```
┌─────────────────────────────────────────┐
│  👤 JrDev-B1                           │
│  Junior Developer, Backend             │
│                                         │
│  Reports to: SrDev-B1                  │
│  Department: Backend                   │
│  Status: Active                        │
│  Tools: 15/39 allowed                  │
│  Workspace: /workspace/backend/dev/** │
│                                         │
│  Current Tasks:                        │
│  ● task-42: Implement rate limiter     │
│  ○ task-45: Refactor auth tests        │
│                                         │
│  [Edit] [Deactivate]                   │
└─────────────────────────────────────────┘
```

### 5.3 Frontend Components

| Component | Purpose |
|-----------|---------|
| `OrgChart` | Tree visualization with expand/collapse |
| `AgentCard` | Compact role card |
| `AgentDetail` | Slide-out panel with tasks, tools, scope |
| `AddAgentForm` | Creates new agent with role, dept, reports_to |
| `AgentTaskList` | Tasks for a specific agent |
| `CrossTeamRequestList` | Incoming/outgoing requests |

---

## Phase 6 — Verification Flow

### Test Case 1: Intra-Team Delegation

```
1. CTO creates org: CTO → EM Backend → SrDev-B1 → JrDev-B1
2. SrDev-B1 opens session → assigns task "Build rate limiter" to JrDev-B1
3. JrDev-B1 opens session → sees task in my_tasks()
4. JrDev-B1 calls start_task("task-42") → context loads
5. JrDev-B1 writes file → submit_task("task-42", summary, files)
6. SrDev-B1 reviews → approve
7. ✓ Task status = approved, output published
```

### Test Case 2: Cross-Team Request

```
1. SrDev-F1 (Frontend) needs backend endpoint
2. SrDev-F1 calls request_from_team(target_dept="backend", title="POST /api/submit")
3. Backend Tech Lead opens session → sees incoming request
4. Backend Tech Lead calls accept_request → assigns to JrDev-B1
5. JrDev-B1 builds endpoint → submits → approved
6. Backend Tech Lead calls fulfill_request → output delivered
7. ✓ Frontend SrDev-F1 notified, dependency resolved
```

### Test Case 3: Permission Enforcement

```
1. JrDev-B1 tries to call assign_task → "ERROR: Junior developers cannot assign tasks"
2. JrDev-B1 tries to call request_from_team → "ERROR: Juniors must go through senior"
3. EM Backend tries to call publish_pattern → ✓ succeeds
4. ✓ Hierarchy + tool policy enforced
```

### Test Case 4: Dependency Injection

```
1. JrDev-F1 starts task "Build submit button"
2. Context shows: "BLOCKED: waiting on backend (ctr-42, in_progress)"
3. Context shows: "Tasks you can work on: Style login form, Add validation"
4. JrDev-F1 works on unblocked tasks while waiting
5. Backend fulfills ctr-42 → JrDev-F1's next load: blocker cleared
6. ✓ Dependency-aware context injection works
```

---

## Implementation Order

| # | Phase | What Gets Built | Key Files |
|---|-------|----------------|-----------|
| 1 | Agent Identity | `agents` table, migration, CRUD API, model | `models/agent.py`, `api/rest/agents.py` |
| 2 | Task Delegation | `tasks` table, migration, 6 tools | `models/task.py`, `api/rest/tasks.py` |
| 3 | Permission System | Role→tool mapping, `get_effective_tools(agent)` | `agent/permissions.py`, `loop.py` |
| 4 | Session Injection | Agent identity in context blocks | `loop.py` — `_build_messages()` |
| 5 | Cross-Team | `cross_team_requests` table, `task_dependencies` table, 4 tools | `agent/org_tools.py` |
| 6 | Context Enrichment | Task/dependency/org chart context blocks | `loop.py` — new context builders |
| 7 | Frontend | Org chart panel, agent CRUD UI, task list | `app/(dashboard)/org/` |
| 8 | Verification | All test cases above | Integration tests |
