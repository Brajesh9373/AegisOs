# AegisOS Agent System

A comprehensive technical reference for the agent architecture powering AegisOS — from identity and governance through the ReAct execution loop to the frontend digital-employee experience and future SDK exploration.

---

## Table of Contents

1. [Agent Identity Model](#1-agent-identity-model)
2. [Agent Hierarchy and Governance](#2-agent-hierarchy-and-governance)
3. [The ReAct Agent Loop](#3-the-react-agent-loop)
4. [Memory Tiers](#4-memory-tiers)
5. [Agent Tools](#5-agent-tools)
6. [Specialized Agents](#6-specialized-agents)
7. [Task System](#7-task-system)
8. [Intelligence Layer](#8-intelligence-layer)
9. [Runtime Kernel](#9-runtime-kernel)
10. [Agent Chat Flow (API)](#10-agent-chat-flow-api)
11. [Frontend Agent Experience](#11-frontend-agent-experience)
12. [Agent Observability](#12-agent-observability)
13. [Access Control and Policy Engine](#13-access-control-and-policy-engine)
14. [Future Agent SDK Exploration](#14-future-agent-sdk-exploration)

---

## 1. Agent Identity Model

Every agent in AegisOS is a first-class entity stored in the `agents` PostgreSQL table. The ORM model is defined in `backend/ecms/persistence/models/agent.py`.

### Schema

| Column              | Type         | Description                                                                 |
|---------------------|--------------|-----------------------------------------------------------------------------|
| `id`                | String(128)  | Primary key (e.g., `agent-cto`, `agent-backend-lead`)                      |
| `name`              | String(255)  | Display name                                                                |
| `role`              | String(64)   | Role identifier, indexed (e.g., `cto`, `backend_lead`, `qa_engineer`)      |
| `designation`       | String(255)  | Formal title (e.g., "Chief Technology Officer")                             |
| `role_description`  | Text         | Free-form description of responsibilities                                   |
| `skills`            | JSON         | Array of skill identifiers                                                  |
| `department`        | String(128)  | Department name, indexed (e.g., `platform`, `backend`, `frontend`)          |
| `project_id`        | String(128)  | Optional project scoping                                                    |
| `model`             | String(255)  | LLM model override for this agent                                           |
| `reports_to`        | String(128)  | FK to `agents.id` — self-referential hierarchy parent                       |
| `tool_policy`       | JSON         | Tool access policy: `{"allowed_tools": ["*"], "blocked_tools": [...]}`      |
| `workspace_scope`   | JSON         | File access scope: `{"write": "/workspace/**", "read": "/**"}`              |
| `system_prompt_addon` | Text       | Custom system prompt appended to the base agentic prompt                    |
| `status`            | String(32)   | `active`, `inactive`, `disabled`                                            |
| `automation`        | JSON         | Automation rules and triggers                                               |
| `features`          | JSON         | Feature flags per agent                                                     |
| `certificates`      | JSON         | Array of capability certificates                                            |
| `created_at`        | DateTime     | Creation timestamp                                                          |
| `updated_at`        | DateTime     | Last update timestamp                                                       |

### Key Relationships

- **Self-referential hierarchy**: `reports_to` references `agents.id`. The `manager` / `reports` relationship pair enables walking the org tree.
- **Tasks**: Agents are linked as `assigner_id` and `assignee_id` on the `tasks` table.
- **Governance**: `ProjectAgentGovernanceAssignment` links `OrganizationMember` to `Agent` with a `responsibility` field (`primary_owner`, `monitor`, `approver`).

---

## 2. Agent Hierarchy and Governance

### Hierarchy

The agent org chart is a tree rooted at the CTO agent (`reports_to = NULL`). Every other agent has exactly one parent.

**Seeding the root**: `permissions.seed_cto_if_needed()` creates the default CTO agent on first run:

```python
await repo.create(
    id="agent-cto",
    name="CTO",
    role="cto",
    designation="Chief Technology Officer",
    department="platform",
    reports_to=None,
    tool_policy={"allowed_tools": ["*"], "blocked_tools": []},
    workspace_scope={"write": "/workspace/**", "read": "/**"},
)
```

**Walking the chain**: `permissions.can_assign()` walks up from an assignee to verify the assigner is in their management chain. `permissions.find_senior_in_dept()` locates the first agent in a department who has direct reports.

### Governance Assignments

Human stakeholders are linked to agents through governance assignments. Each assignment has a `responsibility`:

| Responsibility   | Meaning                                                      |
|------------------|--------------------------------------------------------------|
| `primary_owner`  | Human accountable for this agent's outputs                   |
| `monitor`        | Human who monitors agent activity and KPIs                   |
| `approver`       | Human who must approve high-risk agent actions               |

These assignments drive the Human Queue UI — pending approvals surface to the right approver.

---

## 3. The ReAct Agent Loop

The core of the agent system is the ReAct (Reason + Act) loop in `backend/ecms/agent/loop.py`. The `AgentLoop` class manages the full lifecycle of a single chat turn.

### How It Works

```
User prompt
    |
    v
[Build messages] -- system prompt + context blocks + conversation history
    |
    v
[LLM call] -- OpenAI-compatible API, tool_choice="auto"
    |
    +---> No tool_calls? --> RESPOND (return answer)
    |
    +---> Has tool_calls? --> EXECUTE each tool
    |                              |
    |                              v
    |                        [capture_tool_result] (fire-and-forget memory capture)
    |                              |
    +<-----------------------------+
    |
    (loop back to Build messages)
    |
    Max iterations (50) reached? --> Wrap-up call: "Synthesize everything you've learned"
```

### Initialization

```python
loop = AgentLoop(
    session_id="...",
    lightweight=False,       # if True, skip context blocks
    model="...",             # LLM model override
    api_key="...",           # API key override
    base_url="...",          # base URL override (auto-appends /v1)
    progress_callback=fn,    # SSE progress emitter
    agent_id="...",          # agent identity for governance
    event_queue=queue,       # async queue for streaming
    agent_profile={...},     # pre-loaded profile (system_prompt_addon, tool_policy)
)
```

### Context Blocks

Each iteration builds context blocks injected into the system prompt:

| Block                          | Content                                                        |
|--------------------------------|----------------------------------------------------------------|
| `<context_environment>`        | Live system data — workspace, project, time                    |
| `<context_skills>`             | Bundled skill definitions from disk                            |
| `<context_tools>`              | Tool names and JSON schemas                                    |
| `<context_memory>`             | Working memory snapshot + session context (agent-controlled)   |
| `<context_knowledge_graph>`    | Active atom IDs and graph refs from this turn                  |

### Agent Trace

Every run produces an `AgentTrace` — a structured record of every step:

```python
@dataclass
class AgentTrace:
    session_id: str
    trace_id: str
    started_at: str
    steps: list[dict]       # each step: {kind, detail, ms, data}
    total_tool_calls: int
    total_llm_calls: int
    total_ms: float
```

Step kinds: `start`, `thinking`, `tool_call`, `respond`, `wrapup`, `error`.

### Sub-Agent Spawning

The orchestrator tool (`backend/ecms/agent/orchestrator.py`) exposes `spawn_subagent` as an LLM-callable tool. Each sub-agent:

- Gets a fresh `AgentLoop` with its own 50-iteration budget
- Runs as an `asyncio.Task` with a 180-second timeout
- Emits SSE progress events (`task_start`, `task_progress`, `task_done`, `task_failed`)
- Returns its answer to the parent agent for compilation

---

## 4. Memory Tiers

AegisOS implements a multi-tier memory system. The agent tools provide direct access to each tier.

### Working Memory (Ephemeral)

Defined in `backend/ecms/agent/working_memory.py`. Lives for one chat turn, zero persistence.

| Field              | Purpose                                           |
|--------------------|---------------------------------------------------|
| `scratchpad`       | Agent notes (tool: `note`)                        |
| `active_atom_ids`  | Memory atoms discovered this turn                 |
| `active_graph_refs`| Graph node references                             |
| `tool_results`     | Tool outputs (truncated to 500 chars each)        |
| `variables`        | Key-value pairs (tools: `set_working`, `get_working`) |
| `task_list`        | CommandCode todo items                            |
| `plan_mode`        | Whether plan mode is active (blocks file writes)  |
| `active_skill`     | Currently loaded skill                            |

### Session Context (Cross-Request)

Defined in `backend/ecms/agent/session_context.py`. Dual-write: Redis (sub-ms reads) + PostgreSQL (permanence).

- **TTL**: 24 hours (Redis default)
- **Scope**: Workspace-scoped via `RedisSessionMemory`
- **Tools**: `set_session`, `get_session`
- **Read path**: Redis first, PostgreSQL fallback, backfill Redis on PG hit

### Long-Term Memory

- **Episodic**: Past conversations searchable via `recall_past`
- **Procedural**: Learned workflows via `learn_procedure` / `recall_procedure`
- **Long-term preferences**: `remember` / `recall` for persistent key-value facts
- **Organizational**: `publish_pattern` / `search_org` for cross-agent knowledge sharing

### Knowledge Graph (FalkorDB)

- **search_memory**: Queries the `FileMemoryStore` atom store, returns typed atoms with confidence scores
- **query_graph**: Direct Cypher queries against FalkorDB (read-only: MATCH, RETURN, CALL)
- **expand_atom**: Traverses relationships from a known atom

### Tool Result Capture

After every knowledge-producing tool call, `tool_capture.capture_tool_result()` fire-and-forget creates a `MemoryAtom` in the store. This ensures agent discoveries persist across sessions.

---

## 5. Agent Tools

The agent has access to 39 tools total: 19 ECMS tools + 20 CommandCode native tools. All registered as OpenAI function-calling definitions.

### ECMS Tools (19)

**Knowledge Graph:**
- `search_memory` — Search the atom store (first resort)
- `query_graph` — Cypher queries against FalkorDB
- `expand_atom` — Follow relationships from an atom

**Code:**
- `search_code` — Grep-based code search
- `read_file` — Read workspace files (delegates to CommandCode for absolute paths)

**Semantic Memory:**
- `understand_term` — Define business/technical terms

**Working Memory:**
- `note` — Write to scratchpad
- `set_working` / `get_working` — Key-value in working memory

**Session Memory:**
- `set_session` / `get_session` — Cross-request persistent KV

**Episodic Memory:**
- `recall_past` — Search past conversations

**Procedural Memory:**
- `learn_procedure` — Store a multi-step workflow
- `recall_procedure` — Match a task to known procedures

**Long-Term Memory:**
- `remember` / `recall` — Permanent key-value facts

**Organizational Learning:**
- `publish_pattern` — Share validated patterns across all agents
- `search_org` — Discover organizational knowledge

**Sub-Agent:**
- `spawn_subagent` — Delegate work to independent sub-agents

### Organization Tools (7)

- `assign_task` — Delegate tasks within the reporting chain
- `my_tasks` — List assigned tasks with status filter
- `start_task` — Begin work on a pending task
- `submit_task` — Submit completed work for review
- `review_task` — Approve or reject submitted work
- `request_from_team` — Cross-department dependency requests
- `my_blockers` — Show blocking dependencies

### CommandCode Tools (20)

File operations: `edit_file`, `write_file`, `read_file`, `read_directory`, `read_multiple_files`
Search: `grep`, `glob`
Shell: `shell_command`, `monitor_command`, `monitor_events`, `shell_tasks`, `kill_shell`
Planning: `todo_write`, `enter_plan_mode`, `exit_plan_mode`
Web: `web_search`, `web_fetch`
Other: `ask_user_question`, `diagnostics`, `get_self_knowledge`

### Tool Policy Enforcement

Tool access is governed by the agent's `tool_policy` JSON:

```json
{
  "allowed_tools": ["*"],        // "*" = all, or explicit list
  "blocked_tools": ["kill_shell", "web_search"]
}
```

`permissions.get_effective_tools_for_agent()` filters the full tool list. `blocked_tools` always takes precedence.

Plan mode further restricts tools: when active, file-writing and shell operations are blocked.

---

## 6. Specialized Agents

### Categorization Agent

**File**: `backend/ecms/agent/categorize.py`

Explores codebases and produces JSON glob-pattern classifications. The flow:

1. **Pre-scan**: Walk repos up to depth 3, build directory tree
2. **Agent exploration**: `AgentLoop` reads directories, samples files, globs for composition, greps for framework markers
3. **Pattern extraction**: Parse JSON from agent output. If prose, a second LLM extraction call converts the full conversation context into patterns
4. **Fallback heuristics**: If LLM produces no patterns, 50+ fallback patterns by file extension
5. **Graph application**: Classify every UKO node in FalkorDB by matching its `source_id` against patterns

The agent uses a reward system in its prompt (+10 for JSON, -50 for prose) to enforce structured output.

### Policy Agent

**File**: `backend/ecms/persistence/models/agent.py`

Deterministic analysis (no agent loop). Scans connected sources, classifies directories by file types, matches to org chart departments, generates allow/deny policies.

- **Git repos**: Walk files, count by department, generate allow for dominant department, deny for others
- **MySQL databases**: Match database names to departments, flag sensitive databases (salary, payroll) for C-suite-only access
- **Output**: `PolicyRecommendation` records with confidence scores and evidence

### BA Discovery Agent

**File**: `backend/ecms/agent/ba/agent.py`

A state-machine-driven business analyst agent for requirements gathering.

**States**: `DRAFT` -> `INGESTED` -> `UNDERSTANDING` -> `CLARIFYING` -> `FINALIZING` -> `FINALIZED`

**Stages**:
1. **Understand**: Generate a "What I understood" recap (Markdown)
2. **Clarify**: Structured, category-specific question batches (function-calling enforced)
3. **Assess Coverage**: Score every requirement dimension, identify open gaps
4. **Chat Reply**: Coverage-driven replies that acknowledge answers and interrogate gaps
5. **Finalize**: Produce `FinalizedRequirements` with validate/repair loop (2 attempts)
6. **Design Team**: Generate per-project agent org charts with model/tool constraints

Each stage uses forced function-calling at temperature 0 with a 2-attempt validate/repair loop.

### Orchestrator Agent

**File**: `backend/ecms/agent/orchestrator.py`

Not a standalone agent class — it's a tool (`spawn_subagent`) that the main `AgentLoop` can call. The orchestrator pattern is:

1. Main agent plans: decomposes work into tasks
2. Dispatches sub-agents via `spawn_subagent` (each gets 50 iterations, 180s timeout)
3. Sub-agents run in parallel via `asyncio.gather()`
4. Main agent compiles results into a final answer

---

## 7. Task System

### Task Model

**File**: `backend/ecms/persistence/models/task.py`

| Field             | Type         | Description                                              |
|-------------------|--------------|----------------------------------------------------------|
| `id`              | String(128)  | Primary key                                              |
| `title`           | String(512)  | Task title                                               |
| `description`     | Text         | Detailed instructions                                    |
| `assigner_id`     | String(128)  | FK to `agents.id` — who assigned this task               |
| `assignee_id`     | String(128)  | FK to `agents.id` — who should execute                   |
| `status`          | String(32)   | `pending` -> `in_progress` -> `submitted` -> `approved`/`rejected` |
| `priority`        | String(32)   | `low`, `normal`, `high`, `blocking`                      |
| `inputs`          | JSON         | File paths, specs, references                            |
| `expected_output` | Text         | What format/output is expected                           |
| `output_files`    | JSON         | Files produced by the assignee                           |
| `output_summary`  | Text         | Summary of completed work                                |
| `review_feedback` | Text         | Reviewer comments                                        |
| `parent_task_id`  | String(128)  | FK to `tasks.id` — sub-task relationship                 |

### Task Dependencies

**File**: `backend/ecms/persistence/models/task.py` (`TaskDependency`)

Links a `blocked_task_id` to a `blocker_task_id`. Dependencies can be `same_team` or `cross_team`.

### Cross-Team Requests

**File**: `backend/ecms/persistence/models/task.py` (`CrossTeamRequest`)

When an agent needs work from another department:

1. Agent calls `request_from_team(title, target_department, ...)`
2. System finds the senior agent in the target department via `find_senior_in_dept()`
3. Creates a `CrossTeamRequest` with status `pending`
4. Target senior accepts/declines, which spawns a task in their department

Status flow: `pending` -> `accepted` -> `in_progress` -> `fulfilled` (or `declined`)

---

## 8. Intelligence Layer

**Directory**: `backend/ecms/intelligence/services/`

### Goal Engine

Decomposes a user prompt into a goal tree. Splits on "and then", "then", semicolons, and "and". Returns a root goal with sub-goals.

### Strategy Engine

Selects an execution strategy dynamically based on prompt analysis:

| Strategy           | Trigger                                           |
|--------------------|---------------------------------------------------|
| `TEST_DRIVEN`      | Prompt contains "test"                            |
| `HUMAN_APPROVAL`   | Prompt contains "approve" or "review"             |
| `PARALLEL`         | Prompt contains "parallel"                        |
| `HIERARCHICAL`     | More than 2 goals                                 |
| `ITERATIVE`        | Prompt contains "iterate" or "refine"             |
| `SEQUENTIAL`       | Default                                           |

### Decision Engine

Produces explainable, traceable decision records. Every decision records:
- The question asked
- The chosen option
- The rationale
- All considered alternatives
- Rejected options with reasons
- Confidence score

### Planner

The `DefaultPlanner` orchestrates the above engines:

1. Decompose prompt into goals (GoalEngine)
2. Select strategy (StrategyEngine)
3. Record the decision (DecisionEngine)
4. Compile a versioned `ExecutionPlan` with steps, validation points, and reflection points

---

## 9. Runtime Kernel

**File**: `backend/ecms/runtime/services/kernel.py`

The `RuntimeKernel` is the deterministic execution pipeline. Every request flows through:

1. **Create session and task**
2. **Assign an agent** (via `AgentOrchestrator`)
3. **Plan** (if planner is wired)
4. **Activate memory and retrieve knowledge**
5. **Execute tools** (if tool runner is wired)
6. **Reflect** (if reflector is wired)
7. **Promote candidates** (if promoter is wired)
8. **Update the graph**
9. **Release working memory**
10. **Complete the task**

Steps whose engines are not wired are skipped. The kernel emits an event at each stage via the `EventBus`.

### Agent Orchestrator (Runtime)

**File**: `backend/ecms/runtime/services/agent_orchestrator.py`

The runtime agent orchestrator manages agent lifecycle:

```python
agent = await orchestrator.create(AgentRole.PLANNER, reasoning_model="deterministic")
await orchestrator.assign(agent.agent_id, task.task_id)
# ... agent executes ...
await orchestrator.stop(agent.agent_id)
```

Agents are created with scoped permissions and tool access. The orchestrator tracks status transitions: `CREATED` -> `EXECUTING` -> `STOPPED`.

---

## 10. Agent Chat Flow (API)

**File**: `backend/ecms/api/rest/session_chat.py`

### Endpoint

```
POST /sessions/{session_id}/chat
```

### Request Body

```json
{
  "prompt": "Explain the authentication flow",
  "workspace_id": "default",
  "model": "gpt-4",
  "model_api_key": "...",
  "model_base_url": "...",
  "agent_id": "agent-backend-lead"
}
```

### Flow

1. **Ensure session** exists in PostgreSQL
2. **Persist user message** to session history
3. **Load agent profile** (system_prompt_addon, tool_policy) from agents table
4. **Create AgentLoop** with profile, model config, and progress callback
5. **SSE streaming** via `StreamingResponse`:
   - `data: {"type": "status", "phase": "understanding"}` — initial phase
   - `data: {"type": "task_progress", "iteration": N, "tool_name": "..."}` — per tool call
   - `data: {"type": "task_start", "id": "...", "title": "..."}` — sub-agent starts
   - `data: {"type": "task_done", "id": "...", "title": "..."}` — sub-agent completes
   - `data: {"type": "answer", "content": "...", "show_finalize": false}` — final answer
6. **Post-response** (fire-and-forget):
   - Persist assistant message to PostgreSQL
   - Record episodic memory
   - Extract knowledge atoms from conversation
   - GBrain capture

### Session Management

- `POST /sessions` — Create a new session
- `GET /sessions?workspace_id=...` — List sessions for a workspace
- `GET /sessions/{id}/messages` — Full message history (PostgreSQL, fallback to file-based)
- `DELETE /sessions/{id}` — Delete session and messages

---

## 11. Frontend Agent Experience

### Digital Employees Workspace

**File**: `frontend/apps/web/src/pages/EmployeeList.tsx`

A table view of all agents (displayed as "Digital Employees"). Each row shows name, role, department, and status (Draft/Configured/Ready/Disabled). Clicking "Configure" navigates to the detail page.

### Agent Detail Page

**File**: `frontend/apps/web/src/pages/EmployeeDetail.tsx`

Tabbed interface for agent configuration:

| Tab           | Content                                      |
|---------------|----------------------------------------------|
| Configuration | Role, department, purpose, human owner, manager |
| Skills        | JSON skill definitions                       |
| Knowledge     | Knowledge base references                    |
| Memory        | Memory configuration                         |
| Assignments   | Active task assignments                      |

Status can be changed via dropdown: Draft -> Configured -> Ready -> Disabled.

### AI Agent Chat

**File**: `frontend/apps/web/src/pages/AIAgentChat.tsx`

A chat interface for discussing ticket escalations with the AI agent that flagged the item. Shows agent identity (name, ticket reference), message history with timestamps, and an input bar.

### ProjectWorkspace

The `digital-employee-workspace` frontend package provides the worker hierarchy tree visualization — human managers connected to their digital agent reports. The hierarchy mirrors the `agents.reports_to` chain.

### Agent Governance UI

Governance assignments (primary_owner, monitor, approver) are managed through the frontend. The Human Queue (`human-queue` package) surfaces pending approvals for human reviewers.

### Frontend Agent Packages

| Package                | Purpose                                                      |
|------------------------|--------------------------------------------------------------|
| `agent`                | Agent identity, state, registry, factory, capabilities, lifecycle, events, discovery |
| `agent-runtime`        | Runtime execution: skill executor, tool resolver, knowledge resolver, memory resolver, supervisor, scheduler |
| `orchestrator`         | Execution planning with resolvers for agents, skills, tools, knowledge, memory, dependencies, context, policy, approval. Coordinators for retry, timeout, rollback, compensation, events |
| `multi-agent-runtime`  | Team collaboration: team runtime, agent pool, team manager, shared memory/knowledge layers |
| `skill`                | Skill registry, factory, metadata, categories, versioning, discovery, validation, dependency graph, permissions, lifecycle, events |
| `tool`                 | Tool registry, factory, metadata, categories, manifest, discovery, validation, lifecycle, permissions, dependency graph, versioning, capability mapping |
| `workflow`             | Workflow definition: nodes, edges, steps, sequential/conditional/parallel/switch/loop patterns, approval, human-task, wait-state, event/schedule triggers, retry, timeout, rollback, compensation |
| `workflow-runtime`     | Workflow execution: scheduler, instance management, node executors, edge traversal, persistence contracts, metrics |
| `execution-runtime`    | Base execution engine used by agent-runtime and workflow-runtime |

---

## 12. Agent Observability

### Agent Harness

**File**: `backend/ecms/agent/harness.py`

The `AgentHarness` wraps agent runs and tracks KPIs:

| Metric              | Description                              |
|---------------------|------------------------------------------|
| `execution_count`   | Total runs                               |
| `last_active_at`    | Timestamp of last execution              |
| `error_count_30d`   | Errors in the last 30 days               |
| `active_workspaces` | Number of active workspaces              |

Updated after every `AgentLoop.run()` — success increments `execution_count`, failure also increments `error_count_30d`.

### Collaboration Panel

The frontend `CollaborationPanel` component displays live agent activity, connecting the harness KPIs to the UI.

---

## 13. Access Control and Policy Engine

**File**: `backend/ecms/agent/access_engine.py`

### Policy Evaluation

Every resource access goes through the policy engine:

1. **Root agents** (`reports_to IS NULL`) get unrestricted access — always ALLOW
2. **DENY policies** evaluated first — any match -> DENIED
3. **ALLOW policies** — first match -> ALLOWED
4. **Default** -> DENY

### Policy Matching

Policies match on multiple dimensions:

| Dimension        | Match Logic                                    |
|------------------|------------------------------------------------|
| `agent_id`       | Exact match to agent                           |
| `department`     | Exact match to agent's department              |
| `role_level_min` | Agent's level must be >= policy minimum        |
| `action`         | `read`, `write`, or `*` (any)                  |
| `resource_type`  | `memory_atom`, `graph_node`, etc.              |
| `path_pattern`   | Glob pattern matched against resource path     |
| `source_type`    | `git`, `mysql`, etc.                           |
| `resource_attrs` | Arbitrary key-value matching                   |

### Integration Points

- `filter_atom_results_async()` — Post-filters memory search results
- `filter_graph_results()` — Post-filters graph query results
- `get_allowed_paths()` — Returns paths an agent can access

The policy agent (`recommend_policies_for_project`) generates policy recommendations that, when approved, become enforceable `AccessPolicy` records.

---

## 14. Future Agent SDK Exploration

AegisOS is designed as an agent-agnostic platform. The current implementation uses a custom ReAct loop, but the architecture supports plugging in external agent SDKs and frameworks.

### Platform Foundations for SDK Integration

The platform provides several abstractions that any SDK can leverage:

**The .agents/ Directory**: Currently empty, planned for agent definitions. This is the intended entry point for SDK-specific agent configurations.

**The CommandCode CLI Layer**: Provides 20 built-in tools (file, shell, web, planning) as a tool execution layer. Any SDK can use these tools by calling into the CommandCode context — the tools are already decoupled from the agent loop.

**The Memory System (10 tiers)**: Working memory, session context, episodic, procedural, long-term, organizational, knowledge graph, semantic, and tool-captured memory are all SDK-agnostic. They expose simple `get`/`set`/`search` interfaces that any agent framework can read and write.

**The Governance Model**: RBAC/ABAC policies, human approvals, tool policies, and workspace scopes are enforced at the tool dispatch layer (`invoke_tool`), not inside the agent loop. Any SDK that dispatches tools through `invoke_tool` automatically inherits governance.

### Frontend Packages Suggesting Future Directions

The frontend package ecosystem reveals the planned trajectory:

**`multi-agent-runtime`**: Already implements team-based multi-agent collaboration:
- `TeamRuntime` with states: Forming -> Collaborating -> Escalated -> Completed
- `AgentPool` for managing multiple agent instances
- `TeamManager` with delegation strategies: round-robin, skill-based
- `SharedMemoryLayer` and `SharedKnowledgeLayer` for inter-agent communication
- `SupervisorPolicy` with max escalations, auto-resolve conflicts

**`workflow-runtime`**: Implements structured multi-step workflow execution:
- `WorkflowScheduler` with node executors and edge traversal
- Parallel branch execution via `ParallelExecutor`
- Compensation handling via `CompensationExecutor`
- Human approval wait states
- Workflow states: Pending -> Running -> WaitingForApproval -> Compensating -> Completed -> Failed

**`orchestrator`**: A comprehensive execution planning system with resolvers for:
- Agent resolution, skill resolution, tool resolution
- Knowledge resolution, memory resolution
- Dependency resolution, context resolution
- Policy resolution, approval resolution
- Coordinators for retry, timeout, rollback, compensation, events

**`skill`** and **`tool`**: Full registry systems with:
- Factory patterns, metadata, categories, manifests
- Discovery, validation, dependency graphs
- Versioning, permissions, lifecycle management
- Capability mapping (tools can declare which skills they support)

### Potential SDK Integrations

The platform is designed to integrate with external agent frameworks through adapter patterns. The following categories of integrations are being explored:

**Chain-based workflow frameworks**
- Strength: Structured multi-step agent workflows with tool composition
- Integration path: Map external tools to the CommandCode tool interface, use workflow chains for complex multi-step orchestration
- Governance fit: Wrap workflow nodes with policy checks at tool dispatch

**Multi-agent collaboration frameworks**
- Strength: Role-based collaboration with defined roles and goals
- Integration path: Map external agent crews to `TeamRuntime`, roles to agent profiles
- Governance fit: Role delegation maps naturally to the `reports_to` hierarchy

**Conversational multi-agent frameworks**
- Strength: Multi-agent conversations with human-in-the-loop
- Integration path: Conversation patterns map to the session/chat system
- Governance fit: Human-in-the-loop aligns with the Human Queue approval system

**Commercial LLM provider agent capabilities**
- Strength: Native tool calling, file search, code interpreter, extended thinking
- Integration path: Use provider APIs as the LLM backend for `AgentLoop`, map provider assistants to agent profiles
- Governance fit: Tool policies map to provider-level tool restrictions

**Lightweight agent frameworks**
- Strength: Simple task agents, code generation agents
- Integration path: Lightweight agents for simple tasks, full `AgentLoop` for complex ones
- Governance fit: Tool restrictions map to framework-level tool access

### Sub-Agent Architecture (Planned)

The `.commandcode/plans/sub-agent-architecture.md` describes the planned orchestrator:

```
User: "Explain repo" -> Orchestrator -> Plan -> [Task1][Task2][Task3] (parallel)
                                             -> Compile -> Answer
```

**Budget system:**

| Budget           | Scope        | Value  | On Hit                          |
|------------------|--------------|--------|---------------------------------|
| Max iterations   | Per sub-agent| 50     | Wrap-up call -> return partial  |
| Max iterations   | Orchestrator | 10     | Compile existing -> answer      |
| Time budget      | Per sub-agent| 60s    | Kill agent -> mark timed_out    |

**SSE event types:** `plan`, `task_start`, `task_progress`, `task_done`, `task_failed`, `compiling`, `answer`, `error`

### Design Principles for SDK Integration

1. **Tool dispatch is the governance boundary**: Any SDK must dispatch tools through `invoke_tool()` to inherit policy enforcement
2. **Memory is SDK-agnostic**: The 10-tier memory system exposes simple interfaces — any framework can read/write
3. **Agent identity is persistent**: The `agents` table stores identity, hierarchy, and policies regardless of which SDK runs the agent
4. **The runtime kernel is the pipeline**: SDKs plug into the kernel's pipeline stages (plan, execute, reflect, promote)
5. **Human approval is a gate**: The Human Queue and governance assignments must wrap any agent action that requires approval

---

## Source File Reference

| Component                  | File Path                                                    |
|----------------------------|--------------------------------------------------------------|
| Agent ORM model            | `backend/ecms/persistence/models/agent.py`                   |
| Task ORM model             | `backend/ecms/persistence/models/task.py`                    |
| ReAct loop                 | `backend/ecms/agent/loop.py`                                 |
| Working memory             | `backend/ecms/agent/working_memory.py`                       |
| Session context            | `backend/ecms/agent/session_context.py`                      |
| Conversation manager       | `backend/ecms/agent/conversation.py`                         |
| ECMS + CC tools            | `backend/ecms/agent/tools.py`                                |
| CommandCode tools          | `backend/ecms/agent/commandcode_tools/tools.py`              |
| Organization tools         | `backend/ecms/agent/org_tools.py`                            |
| Categorization agent       | `backend/ecms/agent/categorize.py`                           |
| Policy agent               | `backend/ecms/agent/policy_agent.py`                         |
| BA Discovery agent         | `backend/ecms/agent/ba/agent.py`                             |
| Orchestrator (sub-agents)  | `backend/ecms/agent/orchestrator.py`                         |
| Agent harness              | `backend/ecms/agent/harness.py`                              |
| Permissions                | `backend/ecms/agent/permissions.py`                          |
| Access policy engine       | `backend/ecms/agent/access_engine.py`                        |
| Tool result capture        | `backend/ecms/agent/tool_capture.py`                         |
| Session chat API           | `backend/ecms/api/rest/session_chat.py`                      |
| Agents API                 | `backend/ecms/api/rest/agents.py`                            |
| Runtime kernel             | `backend/ecms/runtime/services/kernel.py`                    |
| Agent orchestrator (runtime)| `backend/ecms/runtime/services/agent_orchestrator.py`        |
| Planner                    | `backend/ecms/intelligence/services/planner.py`              |
| Strategy engine            | `backend/ecms/intelligence/services/strategy_engine.py`      |
| Decision engine            | `backend/ecms/intelligence/services/decision_engine.py`      |
| Goal engine                | `backend/ecms/intelligence/services/goal_engine.py`          |
| Sub-agent architecture plan| `.commandcode/plans/sub-agent-architecture.md`               |
| Agent package (frontend)   | `frontend/packages/agent/src/`                               |
| Agent runtime (frontend)   | `frontend/packages/agent-runtime/src/`                       |
| Multi-agent runtime        | `frontend/packages/multi-agent-runtime/src/`                 |
| Orchestrator (frontend)    | `frontend/packages/orchestrator/src/`                        |
| Skill package              | `frontend/packages/skill/src/`                               |
| Tool package               | `frontend/packages/tool/src/`                                |
| Workflow package           | `frontend/packages/workflow/src/`                            |
| Workflow runtime           | `frontend/packages/workflow-runtime/src/`                    |
| Employee list page         | `frontend/apps/web/src/pages/EmployeeList.tsx`               |
| Employee detail page       | `frontend/apps/web/src/pages/EmployeeDetail.tsx`             |
| AI Agent Chat page         | `frontend/apps/web/src/pages/AIAgentChat.tsx`                |
