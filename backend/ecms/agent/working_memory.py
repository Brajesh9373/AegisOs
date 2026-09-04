"""Working memory — per-task scratchpad for the agent loop.

Each chat creates a WorkingMemory. The agent can read/write to it during
a turn. Cleared after response. Stored in-process (no persistence needed).

Now includes CommandCode plan mode, task list, and shell task tracking.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class WorkingMemory:
    """Ephemeral per-task memory. Lives for one chat turn.

    Agent tools read/write: get_working, set_working, working_snapshot.
    """

    active_atom_ids: list[str] = field(default_factory=list)
    active_graph_refs: list[str] = field(default_factory=list)
    tool_results: list[dict] = field(default_factory=list)
    scratchpad: str = ""
    variables: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    # CommandCode integration
    task_list: list[dict[str, str]] = field(default_factory=list)  # todo_write items
    plan_mode: bool = False  # plan mode state
    active_skill: str | None = None  # currently loaded skill

    def set(self, key: str, value: Any) -> None:
        self.variables[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self.variables.get(key, default)

    def append_tool_result(self, tool: str, result: str) -> None:
        self.tool_results.append({"tool": tool, "result": result[:500]})

    def snapshot(self) -> dict:
        return {
            "active_atoms": len(self.active_atom_ids),
            "active_graph_refs": len(self.active_graph_refs),
            "tool_results_count": len(self.tool_results),
            "scratchpad": self.scratchpad[:300],
            "variables": {k: str(v)[:100] for k, v in self.variables.items()},
            "errors": self.errors,
            "plan_mode": self.plan_mode,
            "task_list_count": len(self.task_list),
        }

    def summary_for_agent(self) -> str:
        parts = []

        # Task list
        if self.task_list:
            statuses = {}
            for item in self.task_list:
                s = item.get("status", "")
                statuses[s] = statuses.get(s, 0) + 1
            parts.append("## Task List")
            counts = ", ".join(f"{v} {k}" for k, v in statuses.items())
            parts.append(f"- {len(self.task_list)} items ({counts})")
            for item in self.task_list:
                icon = {"pending": "○", "in_progress": "●", "completed": "✓"}.get(
                    item["status"], "·"
                )
                parts.append(f"  {icon} {item['content']}")

        # Plan mode indicator
        if self.plan_mode:
            parts.append("- **Plan Mode Active** — files and shell operations are blocked.")

        # Existing memory surfaces
        if self.active_atom_ids:
            parts.append(f"- Active atoms: {', '.join(self.active_atom_ids[:10])}")
        if self.scratchpad:
            parts.append(f"- Notes: {self.scratchpad[:300]}")
        if self.variables:
            for k, v in self.variables.items():
                parts.append(f"- {k}: {str(v)[:150]}")

        return "\n".join(parts) if parts else ""

    def clear(self) -> None:
        self.active_atom_ids.clear()
        self.active_graph_refs.clear()
        self.tool_results.clear()
        self.scratchpad = ""
        self.variables.clear()
        self.errors.clear()
        self.task_list.clear()
