"""Tool result knowledge capture — extracts atoms from agent tool results.

Runs after every tool call in the ReAct loop. Analyzes the tool name + result
and creates typed MemoryAtoms in the FileMemoryStore so discoveries persist
across sessions.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from legacy_ecms.memory.domain import (
    Evidence,
    EvidenceSource,
    MemoryAtom,
    MemoryScope,
    MemoryStatus,
    MemoryType,
)
from legacy_ecms.memory.stores.file_store import FileMemoryStore

logger = logging.getLogger("ecms.agent.capture")

_store: FileMemoryStore | None = None


def _get_store() -> FileMemoryStore:
    global _store
    if _store is None:
        _store = FileMemoryStore(Path("/app/memory"))
    return _store


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


_KNOWLEDGE_TOOLS = {
    "query_graph", "search_memory", "expand_atom",
    "glob", "grep", "read_file", "read_directory", "read_multiple_files",
    "search_code", "understand_term", "web_search", "web_fetch",
}


def _infer_type_from_tool(name: str, result: str) -> MemoryType:
    """Heuristic type inference based on tool name and content signals."""
    if name == "query_graph":
        return MemoryType.OBSERVATION
    if name in ("glob", "read_directory", "read_multiple_files"):
        return MemoryType.ARCHITECTURE  # file structure = architecture
    if name in ("grep", "search_code"):
        return MemoryType.OBSERVATION
    if name == "read_file":
        if any(k in result.lower() for k in ("class ", "def ", "function", "module")):
            return MemoryType.ARCHITECTURE
    if name == "web_search":
        return MemoryType.FACT
    if name == "web_fetch":
        return MemoryType.FACT
    if name in ("search_memory", "expand_atom", "understand_term"):
        return MemoryType.FACT
    return MemoryType.OBSERVATION


def _truncate(text: str, max_len: int = 300) -> str:
    return text[:max_len] + ("..." if len(text) > max_len else "")


def capture_tool_result(
    tool_name: str,
    tool_args: dict[str, Any],
    result: str,
    session_id: str = "",
) -> None:
    """Parse a tool result and persist findings as memory atoms.

    Called from AgentLoop after every knowledge-producing tool call.
    Fire-and-forget — errors are logged, never raised.
    """
    if tool_name not in _KNOWLEDGE_TOOLS:
        return
    if not result or len(result) < 20:
        return

    try:
        store = _get_store()
        atom_type = _infer_type_from_tool(tool_name, result)

        # Derive topic from tool args
        topic = ""
        if "query" in tool_args:
            topic = str(tool_args["query"])[:80]
        elif "pattern" in tool_args:
            topic = f"grep: {tool_args['pattern']}"[:80]
        elif "path" in tool_args:
            topic = f"file: {tool_args['path']}"[:80]
        elif "absolutePath" in tool_args:
            topic = f"file: {tool_args['absolutePath']}"[:80]
        elif "cypher" in tool_args:
            cypher = str(tool_args["cypher"]).replace("\n", " ")[:60]
            topic = f"graph: {cypher}"
        elif "term" in tool_args:
            topic = f"term: {tool_args['term']}"[:80]
        else:
            topic = f"{tool_name} result"

        summary = _truncate(result, 300)
        atom_id = f"TOOL-{tool_name}-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}-{hash(summary) & 0xFFFF:04x}"

        atom = MemoryAtom(
            id=atom_id,
            type=atom_type,
            topic=topic,
            summary=summary,
            confidence=0.6,
            status=MemoryStatus.DRAFT,
            scope=MemoryScope.WORKSPACE,
            evidence=[
                Evidence(
                    source=session_id or "agent-tool",
                    source_type=EvidenceSource.CONVERSATION,
                    weight=0.5,
                )
            ],
            tags=["tool-captured", tool_name],
        )

        store.upsert_atom(atom)
        store.flush()
        logger.debug("Captured tool result: %s → atom %s", tool_name, atom_id)

    except Exception as e:
        logger.warning("Tool result capture failed (%s): %s", tool_name, e)
