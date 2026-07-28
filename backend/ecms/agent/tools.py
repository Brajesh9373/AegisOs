"""ECOS Agent tools — instruments for memory access, code search, and reasoning.

Merged with CommandCode's 20 native Python tools (file/shell/web/planning).
All 39 tools registered with LLM as OpenAI function-calling definitions.
"""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path
from typing import Any

import falkordb

from legacy_ecms.config import get_settings
from legacy_ecms.memory.stores.file_store import FileMemoryStore

# ── CommandCode tool integration ──────────────────────────────────────

from ecms.agent.commandcode_tools import (
    CC_TOOL_DEFINITIONS,
    ToolContext,
    get_tools_for_mode,
    cc_invoke_tool,
    set_context as cc_set_context,
)
from ecms.agent.org_tools import ORG_TOOL_DEFINITIONS, ORG_TOOL_NAMES, invoke_org_tool, set_org_context, get_org_context
from ecms.agent.orchestrator import SPAWN_SUBAGENT_TOOL, spawn_subagent
from ecms.agent.access_engine import filter_atom_results_async, filter_graph_results

_CC_CONTEXT: ToolContext | None = None


def set_cc_context(context: ToolContext) -> None:
    global _CC_CONTEXT
    _CC_CONTEXT = context
    cc_set_context(context)


# ── ECMS Tool registry (19 tools) ─────────────────────────────────────

ECMS_TOOL_DEFINITIONS: list[dict[str, Any]] = [
    # -- Knowledge graph tools --
    {
        "type": "function",
        "function": {
            "name": "search_memory",
            "description": "Search the knowledge atom store. Use first — it returns distilled, verified knowledge. Returns atom summaries with confidence scores.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query. Use keywords from the user's question."},
                    "limit": {"type": "integer", "description": "Max results (default 10, max 20)."},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_graph",
            "description": "Run a Cypher query against the FalkorDB evidence graph. Use when memory atoms are insufficient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "cypher": {"type": "string", "description": "Cypher query. Example: MATCH (u:UKO) WHERE u.name CONTAINS 'auth' RETURN u.name, u.type"},
                },
                "required": ["cypher"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "expand_atom",
            "description": "Follow relationships from a known memory atom. Shows connected atoms up to specified depth.",
            "parameters": {
                "type": "object",
                "properties": {
                    "atom_id": {"type": "string", "description": "The atom ID to expand from (e.g., 'GB-ECOS-ARCHITECTURE')."},
                    "depth": {"type": "integer", "description": "Relationship depth (1 = direct neighbors, 2 = neighbors of neighbors)."},
                },
                "required": ["atom_id"],
            },
        },
    },
    # -- Code tools --
    {
        "type": "function",
        "function": {
            "name": "search_code",
            "description": "Search for patterns in workspace source code using grep. Returns matching file paths.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern": {"type": "string", "description": "Grep pattern. Example: 'class JwtAuth' or 'def create_user'."},
                    "path": {"type": "string", "description": "Optional subdirectory to search in (default: entire workspace)."},
                },
                "required": ["pattern"],
            },
        },
    },
    # Note: read_file is handled by CC tools — kept for backward compat alias
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file from the workspace. Returns content up to 4000 characters. Uses absolute path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path relative to workspace root or absolute. Example: 'backend/ecms/api/app.py'."},
                },
                "required": ["path"],
            },
        },
    },
    # -- Semantic memory --
    {
        "type": "function",
        "function": {
            "name": "understand_term",
            "description": "Define a business/technical term using the knowledge graph and memory atoms. Returns definition, related concepts, and file locations.",
            "parameters": {
                "type": "object",
                "properties": {
                    "term": {"type": "string", "description": "Term to understand. Example: 'loan_status', 'JwtAuthenticationService'."},
                },
                "required": ["term"],
            },
        },
    },
    # -- Working memory --
    {
        "type": "function",
        "function": {
            "name": "note",
            "description": "Write a brief note to your scratchpad. Use to track what you've discovered.",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "Note text. Keep it brief."},
                },
                "required": ["text"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "set_working",
            "description": "Store a value in working memory for the current task.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Variable name."},
                    "value": {"type": "string", "description": "Value to store."},
                },
                "required": ["key", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_working",
            "description": "Read a value from working memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Variable name to retrieve."},
                },
                "required": ["key"],
            },
        },
    },
    # -- Session memory --
    {
        "type": "function",
        "function": {
            "name": "set_session",
            "description": "Store a value in session memory — persists across questions in this conversation.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Storage key."},
                    "value": {"type": "string", "description": "Value to persist."},
                },
                "required": ["key", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_session",
            "description": "Read a value from session memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Storage key to retrieve."},
                },
                "required": ["key"],
            },
        },
    },
    # -- Episodic memory --
    {
        "type": "function",
        "function": {
            "name": "recall_past",
            "description": "Search past conversations for similar questions. Returns Q&A from previous interactions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "What to search for in past conversations."},
                },
                "required": ["query"],
            },
        },
    },
    # -- Procedural memory --
    {
        "type": "function",
        "function": {
            "name": "learn_procedure",
            "description": "Teach the agent a reusable procedure. Store a multi-step workflow.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Procedure name."},
                    "description": {"type": "string", "description": "What this procedure accomplishes."},
                    "steps": {"type": "string", "description": "Comma-separated list of steps."},
                },
                "required": ["name", "description", "steps"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recall_procedure",
            "description": "Recall a previously learned procedure that matches a task description.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task": {"type": "string", "description": "Task description to match against known procedures."},
                },
                "required": ["task"],
            },
        },
    },
    # -- Long-term memory --
    {
        "type": "function",
        "function": {
            "name": "remember",
            "description": "Store a long-term preference or fact. Persists across all sessions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Preference key."},
                    "value": {"type": "string", "description": "Value to persist permanently."},
                },
                "required": ["key", "value"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "recall",
            "description": "Recall a long-term preference or fact from permanent memory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "description": "Preference key to retrieve."},
                },
                "required": ["key"],
            },
        },
    },
    # -- Organizational learning --
    {
        "type": "function",
        "function": {
            "name": "publish_pattern",
            "description": "Publish a validated best practice, known bug, or convention to the organization. All ECOS agents can discover and use it.",
            "parameters": {
                "type": "object",
                "properties": {
                    "pattern_type": {"type": "string", "description": "Type: 'best_practice', 'known_bug', 'optimization', or 'convention'."},
                    "description": {"type": "string", "description": "What was learned. Example: 'SQL Validator catches 95% of syntax errors using Rule X'."},
                },
                "required": ["pattern_type", "description"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_org",
            "description": "Search organizational knowledge — validated patterns shared across all agents. Use before implementing something new.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "What to search for in org knowledge."},
                    "pattern_type": {"type": "string", "description": "Optional filter: 'best_practice', 'known_bug', 'optimization', 'convention'."},
                },
                "required": ["query"],
            },
        },
    },
]

# ── Merged TOOL_DEFINITIONS: ECMS first (memory/graph), then CC (file/shell/web/planning) ──

TOOL_DEFINITIONS = ECMS_TOOL_DEFINITIONS + [
    t for t in CC_TOOL_DEFINITIONS
    if t["function"]["name"] != "read_file"  # ECMS has its own read_file
] + [SPAWN_SUBAGENT_TOOL]

# ── Lazy singletons ───────────────────────────────────────────────────

_store: FileMemoryStore | None = None
_falkordb_graph: Any = None


def _get_store() -> FileMemoryStore:
    global _store
    if _store is None:
        _store = FileMemoryStore(Path("/app/memory"))
    return _store


def _get_falkordb() -> Any:
    global _falkordb_graph
    if _falkordb_graph is None:
        s = get_settings()
        db = falkordb.FalkorDB(
            host=s.falkordb_host, port=s.falkordb_port,
            password=s.falkordb_password or None,
        )
        _falkordb_graph = db.select_graph(s.falkordb_database)
    return _falkordb_graph


# ── Working/Session memory context (set by AgentLoop) ──────────────────

_WORKING_MEMORY: Any = None
_SESSION_CONTEXT: Any = None


def set_agent_context(working_memory: Any, session_context: Any) -> None:
    global _WORKING_MEMORY, _SESSION_CONTEXT
    _WORKING_MEMORY = working_memory
    _SESSION_CONTEXT = session_context


def get_working_memory() -> Any:
    return _WORKING_MEMORY


# ── Tool implementations ──────────────────────────────────────────────


async def search_memory(query: str, limit: int = 10) -> str:
    store = _get_store()
    results = store.search_atoms(query, limit=min(limit, 20))

    # Policy filter: scope results to agent's access level
    agent_id, agent_data = get_org_context()
    if agent_id and agent_data:
        results = await filter_atom_results_async(agent_data, results)

    if _WORKING_MEMORY and results:
        for a in results:
            if a.id not in _WORKING_MEMORY.active_atom_ids:
                _WORKING_MEMORY.active_atom_ids.append(a.id)
    if not results:
        return "No memory atoms found for this query."
    lines = []
    for a in results:
        lines.append(f"- [{a.id}] ({a.type.value}/{a.confidence:.0%}) {a.topic}: {a.summary[:200]}")
    return "\n".join(lines)


async def query_graph(cypher: str) -> str:
    if not cypher.strip().upper().startswith(("MATCH", "RETURN", "CALL")):
        return "Error: only read queries (MATCH, RETURN, CALL) are allowed."
    try:
        g = _get_falkordb()
        result = await asyncio.to_thread(g.query, cypher)
        rows = result.result_set if hasattr(result, "result_set") else result
        if not rows:
            return "No results."

        # Policy filter: scope graph results to agent's access level
        agent_id, agent_data = get_org_context()
        if agent_id and agent_data:
            nodes = _rows_to_graph_resources(rows, cypher)
            filtered = await filter_graph_results(agent_data, nodes)
            rows = [list(_resource_to_row(r)) for r in filtered]

        formatted = []
        for i, row in enumerate(rows[:50]):
            formatted.append(f"[{i}] " + " | ".join(str(v) for v in row))
        return "\n".join(formatted)
    except Exception as e:
        return f"Graph query failed: {e}"


def _rows_to_graph_resources(rows, cypher):
    resources = []
    for row in rows:
        res = {"type": "graph_node", "action": "read"}
        if len(row) > 0:
            res["name"] = str(row[0]) if row[0] else ""
        for v in row:
            sv = str(v) if v else ""
            if sv.startswith("/") or "/" in sv:
                res["source_path"] = sv
                break
        resources.append(res)
    return resources


def _resource_to_row(res):
    return [res.get("name", "")]


async def expand_atom(atom_id: str, depth: int = 1) -> str:
    store = _get_store()
    main = store.get_atom(atom_id)
    if not main:
        return f"Atom {atom_id} not found."
    related = store.get_related_atoms(atom_id, depth=min(depth, 3))
    lines = [f"## {atom_id}: {main.topic}"]
    lines.append(f"   {main.summary[:200]}")
    if not related:
        lines.append("   (no related atoms)")
    else:
        lines.append(f"\n   Related atoms ({len(related)}):")
        for r in related:
            lines.append(f"   - [{r.id}] {r.topic} — {r.summary[:150]}")
    return "\n".join(lines)


async def search_code(pattern: str, path: str = "/app") -> str:
    result = await asyncio.to_thread(
        subprocess.run, ["grep", "-rnl", pattern, path],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode not in (0, 1):
        return f"Search failed: {result.stderr.strip()}"
    lines = result.stdout.strip().split("\n") if result.stdout else []
    if not lines:
        return f"No matches for '{pattern}'."
    display = [l for l in lines[:20]]
    count = len(lines)
    prefix = f"Found {count} files:\n" if count > 20 else "Found:\n"
    return prefix + "\n".join(f"  {p}" for p in display)


async def read_file(path: str) -> str:
    """ECMS read_file — delegates to CC read_file if path is absolute, otherwise legacy relative."""
    # If it looks like an absolute path, delegate to CC's read_file
    if path.startswith("/") or Path(path).is_absolute():
        if _CC_CONTEXT:
            return await cc_invoke_tool("read_file", {"absolutePath": path}, context=_CC_CONTEXT)
    # Legacy relative path resolution
    clean = path.lstrip("/")
    for root in (Path("/app"), Path("/app/memory")):
        full = root / clean
        if full.is_file():
            try:
                content = full.read_text(encoding="utf-8", errors="replace")
                return content[:4000] + ("\n... (truncated)" if len(content) > 4000 else "")
            except Exception:
                continue
    return f"File not found: {path}"


# ── Working memory tools ──────────────────────────────────────────────


async def note(text: str) -> str:
    if _WORKING_MEMORY is None:
        return "Working memory not available."
    if _WORKING_MEMORY.scratchpad:
        _WORKING_MEMORY.scratchpad += "\n" + text
    else:
        _WORKING_MEMORY.scratchpad = text
    return f"Noted: {text[:200]}"


async def set_working(key: str, value: str) -> str:
    if _WORKING_MEMORY is None:
        return "Working memory not available."
    _WORKING_MEMORY.set(key, value)
    return f"Working memory: {key} = {value}"


async def get_working(key: str) -> str:
    if _WORKING_MEMORY is None:
        return "Working memory not available."
    val = _WORKING_MEMORY.get(key)
    return f"{key} = {val}" if val is not None else f"No value stored for '{key}'"


# ── Session memory tools ──────────────────────────────────────────────


async def set_session(key: str, value: str) -> str:
    if _SESSION_CONTEXT is None:
        return "Session memory not available."
    await _SESSION_CONTEXT.set(key, value)
    return f"Session memory: {key} = {value}"


async def get_session(key: str) -> str:
    if _SESSION_CONTEXT is None:
        return "Session memory not available."
    val = await _SESSION_CONTEXT.get(key)
    return f"{key} = {val}" if val is not None else f"No session value for '{key}'"


# ── Semantic memory tool ──────────────────────────────────────────────


async def understand_term(term: str) -> str:
    from ecms.memory.semantic.concept_registry import get_registry
    registry = get_registry()
    return await registry.define(term)


# ── Episodic memory tool ──────────────────────────────────────────────


async def recall_past(query: str) -> str:
    from ecms.memory.episodic import get_event_store
    store = get_event_store()
    results = store.search(query, limit=5)
    if not results:
        return "No past conversations found matching this query."
    lines = [f"Found {len(results)} past conversations:"]
    for r in results:
        lines.append(f"\n[{r['timestamp'][:16]}] Q: {r['question']}")
        lines.append(f"   A: {r['answer_preview']}")
    return "\n".join(lines)


# ── Procedural memory tools ───────────────────────────────────────────


async def learn_procedure(name: str, description: str, steps: str) -> str:
    from ecms.memory.procedural import get_procedure_store
    store = get_procedure_store()
    step_list = [s.strip() for s in steps.split(",") if s.strip()]
    proc_id = store.learn(name, description, step_list)
    return f"Procedure '{name}' learned ({len(step_list)} steps, id: {proc_id})."


async def recall_procedure(task: str) -> str:
    from ecms.memory.procedural import get_procedure_store
    store = get_procedure_store()
    results = store.search(task, limit=3)
    if not results:
        return "No procedures found matching this task."
    lines = [f"Found {len(results)} procedures:"]
    for r in results:
        lines.append(f"\n## {r['name']} ({r['success_count']} uses)")
        lines.append(f"   {r['description']}")
        lines.append("   Steps:")
        for i, s in enumerate(r["steps"], 1):
            lines.append(f"   {i}. {s}")
    return "\n".join(lines)


# ── Long-term memory tools ────────────────────────────────────────────


async def remember(key: str, value: str) -> str:
    from ecms.memory.long_term import get_preferences_store
    store = get_preferences_store()
    store.set(key, value)
    return f"Long-term memory: {key} = {value}"


async def recall(key: str) -> str:
    from ecms.memory.long_term import get_preferences_store
    store = get_preferences_store()
    val = store.get(key)
    return f"{key} = {val}" if val else f"No long-term value for '{key}'"


# ── Organizational learning tools ────────────────────────────────────


async def publish_pattern(pattern_type: str, description: str) -> str:
    from ecms.memory.organization import get_org_learning
    org = get_org_learning()
    pid = org.publish(pattern_type, description)
    if pid:
        return f"Pattern published (id: {pid}). All ECOS agents can now discover this {pattern_type}."
    return "Failed to publish pattern. Graph may be unavailable."


async def search_org(query: str, pattern_type: str | None = None) -> str:
    from ecms.memory.organization import get_org_learning
    org = get_org_learning()
    results = org.search(query, pattern_type=pattern_type, limit=5)
    if not results:
        return f"No organizational patterns found for '{query}'."
    lines = [f"Found {len(results)} organizational patterns:"]
    for r in results:
        lines.append(f"\n- [{r['type']}] (validated {r['validations']}×) {r['description']}")
    return "\n".join(lines)


# ── Tool dispatcher (ECMS first, then CC) ─────────────────────────────

_ECMS_TOOL_MAP = {
    "spawn_subagent": spawn_subagent,
    "search_memory": search_memory,
    "query_graph": query_graph,
    "expand_atom": expand_atom,
    "search_code": search_code,
    "read_file": read_file,
    "understand_term": understand_term,
    "note": note,
    "set_working": set_working,
    "get_working": get_working,
    "set_session": set_session,
    "get_session": get_session,
    "recall_past": recall_past,
    "learn_procedure": learn_procedure,
    "recall_procedure": recall_procedure,
    "remember": remember,
    "recall": recall,
    "publish_pattern": publish_pattern,
    "search_org": search_org,
}


# CC tool names that get dispatched to cc_invoke_tool
CC_TOOL_NAMES = {
    "edit_file", "read_directory", "write_file", "read_multiple_files",
    "grep", "glob", "shell_command", "monitor_command", "monitor_events",
    "shell_tasks", "todo_write", "ask_user_question", "kill_shell",
    "exit_plan_mode", "enter_plan_mode", "diagnostics",
    "get_self_knowledge", "web_search", "web_fetch",
}


async def invoke_tool(name: str, arguments: dict[str, Any]) -> str:
    # Try ECMS tools first
    func = _ECMS_TOOL_MAP.get(name)
    if func:
        try:
            return await func(**arguments)
        except Exception as e:
            return f"Tool '{name}' failed: {e}"

    # Try org tools (task delegation, cross-team)
    if name in ORG_TOOL_NAMES:
        try:
            return await invoke_org_tool(name, arguments)
        except Exception as e:
            return f"Tool '{name}' failed: {e}"

    # Try CommandCode tools
    if name in CC_TOOL_NAMES and _CC_CONTEXT:
        try:
            return await cc_invoke_tool(name, arguments, context=_CC_CONTEXT)
        except Exception as e:
            return f"Tool '{name}' failed: {e}"

    return f"Unknown tool: {name}"


def get_effective_tools(plan_mode: bool = False) -> list[dict[str, Any]]:
    """Return the tool list for the current mode. ECMS tools + mode-filtered CC tools."""
    cc_tools_filtered = [
        t for t in CC_TOOL_DEFINITIONS
        if t["function"]["name"] != "read_file"  # ECMS has its own read_file
    ]
    if plan_mode:
        # Filter CC tools by plan mode
        cc_tools_filtered = get_tools_for_mode("plan", tools=cc_tools_filtered)
    else:
        cc_tools_filtered = get_tools_for_mode("standard", tools=cc_tools_filtered)
    return ECMS_TOOL_DEFINITIONS + cc_tools_filtered + ORG_TOOL_DEFINITIONS
