# Plan: Sub-Agent Architecture with Real-Time Task Progress

## Overview
Replace single sequential ReAct loop with hierarchical orchestrator/sub-agent system. Main agent plans, dispatches sub-agents in parallel, compiles results. Each sub-agent gets its own 50-iteration budget. All progress streams to frontend via SSE.

## Architecture

```
User: "Explain repo" → Orchestrator → Plan → [Task1][Task2][Task3] (parallel)
                                        → Compile → Answer
```

## Implementation Steps (in order)

### Step 1: Add wrap-up call at iteration limit
**File:** `backend/ecms/agent/loop.py`
- When `iteration >= 50`, instead of returning hardcoded string
- Make one final LLM call with all findings: "Synthesize everything you've learned into a concise answer"
- Return that compiled answer

### Step 2: Add progress_callback to AgentLoop
**File:** `backend/ecms/agent/loop.py`
- Add `progress_callback: Callable | None = None` parameter
- On each tool call, emit: `{"type":"task_progress", "iteration":N, "tool_name":"..."}`

### Step 3: Create OrchestratorAgent
**File:** `backend/ecms/agent/orchestrator.py` (new)
- `async run(prompt) → AsyncIterator[dict]` — yields SSE events
- Phase 1: `_plan(prompt)` — one LLM call → JSON task list
- Phase 2: `_execute_parallel(tasks)` — `asyncio.gather()` sub-agents
- Phase 3: `_compile(prompt, results)` — one LLM call → final answer

### Step 4: Convert POST /chat to SSE streaming
**File:** `backend/ecms/api/rest/session_chat.py`
- Replace JSON response with `StreamingResponse` (text/event-stream)
- Wire `OrchestratorAgent` into the endpoint
- Yield SSE events: `data: {"type":"plan","tasks":[...]}\n\n`

### Step 5: Create TaskProgress component
**File:** `frontend/apps/web/src/components/TaskProgress.tsx` (new)
- Ant Design `Card` + `Table` showing task list
- Columns: #, Task, Status (pending/running/done/failed with colored tags)
- Spinning icon on running tasks

### Step 6: Update ChatView to SSE reader
**File:** `frontend/apps/web/src/components/ChatView.tsx`
- Replace `fetch → res.json()` with `fetch → reader.read()` stream
- Parse SSE events, update tasks array in real-time
- Show `TaskProgress` during execution phase instead of "thinking..."
- Transition: understanding → plan → executing → compiling → answer

### Step 7: Update nginx config
**File:** `docker/nginx.conf`
- Add `proxy_buffering off; proxy_cache off; proxy_read_timeout 300s;`
- For `/api/v1/sessions/` location block

## Budget System

| Budget | Scope | Value | On Hit |
|--------|-------|-------|--------|
| Max iterations | Per sub-agent | 50 | Wrap-up call → return partial |
| Max iterations | Orchestrator | 10 | Compile existing → answer |
| Time budget | Per sub-agent | 60s | Kill agent → mark timed_out |

## SSE Event Types

| Event | Payload | When |
|-------|---------|------|
| `plan` | `{tasks: [{id, title, description}]}` | After planning |
| `task_start` | `{id, title}` | Sub-agent begins |
| `task_progress` | `{id, iteration, tool}` | Each tool call |
| `task_done` | `{id, title}` | Sub-agent completes |
| `task_failed` | `{id, title, error}` | Sub-agent fails |
| `compiling` | `{}` | Orchestrator starts compile |
| `answer` | `{content}` | Final answer |
| `error` | `{message}` | Orchestrator fails |

## Files Created/Modified

| File | Action | Complexity |
|------|--------|------------|
| `backend/ecms/agent/loop.py` | Modify | Medium |
| `backend/ecms/agent/orchestrator.py` | Create | High |
| `backend/ecms/api/rest/session_chat.py` | Modify | Medium |
| `frontend/apps/web/src/components/TaskProgress.tsx` | Create | Low |
| `frontend/apps/web/src/components/ChatView.tsx` | Modify | Medium |
| `docker/nginx.conf` | Modify | Low |
