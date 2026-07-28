# CommandCode Python Migration

Standalone Python migration of the confirmed `command-code@0.43.1` built-in agent tools.

This package is intentionally not integrated into any existing agent loop yet. It gives you:

- async Python handlers for the 20 confirmed built-in tools
- OpenAI-style function schemas via `TOOL_DEFINITIONS`
- `invoke_tool(name, arguments)` dispatcher
- workspace boundary checks
- basic `.gitignore`/default exclude handling
- shell and monitor task tracking
- host callbacks for questions, diagnostics, permissions, and web providers

## Confirmed Tools

`read_file`, `edit_file`, `read_directory`, `write_file`, `read_multiple_files`, `grep`, `glob`, `shell_command`, `monitor_command`, `monitor_events`, `shell_tasks`, `todo_write`, `ask_user_question`, `kill_shell`, `exit_plan_mode`, `enter_plan_mode`, `diagnostics`, `get_self_knowledge`, `web_search`, `web_fetch`.

## Quick Use

```python
import asyncio
from pathlib import Path

from commandcode_migration import ToolContext, invoke_tool, set_context

async def main():
    root = Path.cwd()
    set_context(ToolContext(cwd=root, workspace_roots=[root]))
    result = await invoke_tool("glob", {"pattern": "**/*.py"})
    print(result)

asyncio.run(main())
```

## Context

```python
context = ToolContext(
    cwd=Path("/workspace/project"),
    workspace_roots=[Path("/workspace/project")],
    question_callback=my_question_callback,
    diagnostics_provider=my_diagnostics_provider,
    permission_callback=my_permission_callback,
    web_search_provider=my_web_search,
    web_fetch_provider=my_web_fetch,
)
```

If a provider/callback is missing:

- `ask_user_question` returns a structured JSON question-card payload.
- `diagnostics` reports that no provider is configured.
- `web_search` and `web_fetch` use minimal standard-library fallbacks.

## Notes

- `create_file`, `delete_file`, and `explore` are not exposed built-ins in the inspected `command-code@0.43.1` package. Add them later as compatibility aliases only if the host agent needs them.
- Plan mode filtering is available through `get_tools_for_mode(mode)`.
- Tool implementations are host-agnostic; final policy, UI rendering, permissions, and persistence should live in the integrating agent system.
