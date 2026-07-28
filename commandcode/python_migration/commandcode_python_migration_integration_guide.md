# CommandCode Python Tools Integration Guide

This guide explains how to integrate the standalone Python migration of CommandCode tools into a new AI agent system.

Migration artifact:

```text
python_migration/commandcode_python_migration/
```

Main module:

```text
commandcode_migration/tools.py
```

Core exports:

```python
from commandcode_migration import (
    TOOL_DEFINITIONS,
    ToolContext,
    configure_context,
    get_tools_for_mode,
    invoke_tool,
    set_context,
)
```

## What Was Migrated

The package implements the 20 confirmed built-in tools exposed by the inspected `command-code@0.43.1` install:

```text
read_file
edit_file
read_directory
write_file
read_multiple_files
grep
glob
shell_command
monitor_command
monitor_events
shell_tasks
todo_write
ask_user_question
kill_shell
exit_plan_mode
enter_plan_mode
diagnostics
get_self_knowledge
web_search
web_fetch
```

The migration is intentionally host-agnostic. It provides tool behavior, schemas, context, and dispatch. Your agent system remains responsible for model calls, conversation history, permissions UI, session persistence, frontend rendering, and long-term memory.

## Recommended Runtime Shape

A minimal agent loop needs five pieces:

1. Conversation state
2. Tool context
3. Tool schemas
4. Tool dispatch
5. Tool-result messages returned to the model

Example:

```python
from pathlib import Path

from commandcode_migration import ToolContext, get_tools_for_mode, invoke_tool, set_context


workspace = Path("/workspace/my-project").resolve()

context = ToolContext(
    cwd=workspace,
    workspace_roots=[workspace],
)

set_context(context)

tools = get_tools_for_mode("standard")
```

When the model asks for a tool call:

```python
import json


name = tool_call.function.name
arguments = json.loads(tool_call.function.arguments or "{}")

result = await invoke_tool(
    name,
    arguments,
    context=context,
)
```

Then append `result` as a tool-result message in your agent protocol.

## ToolContext

`ToolContext` is the integration boundary between the migrated tools and the host agent runtime.

```python
context = ToolContext(
    cwd=workspace,
    workspace_roots=[workspace],
    tmp_dir=workspace / ".agent_tmp",
    plan_mode=False,
    question_callback=question_callback,
    diagnostics_provider=diagnostics_provider,
    permission_callback=permission_callback,
    web_search_provider=web_search_provider,
    web_fetch_provider=web_fetch_provider,
)
```

Important fields:

- `cwd`: default working directory for relative command/search operations.
- `workspace_roots`: allowed directories for file and shell operations.
- `tmp_dir`: shell logs and backups are stored here.
- `plan_mode`: blocks write/shell tools when enabled.
- `task_list`: current todos from `todo_write`.
- `shell_tasks`: tracked background shell and monitor tasks.
- `question_callback`: host callback for `ask_user_question`.
- `diagnostics_provider`: host callback for IDE/LSP diagnostics.
- `permission_callback`: host callback before risky process actions.
- `web_search_provider`: optional host web search adapter.
- `web_fetch_provider`: optional host web fetch adapter.

## Tool Schemas

Use `TOOL_DEFINITIONS` or `get_tools_for_mode(mode)`.

```python
tools = get_tools_for_mode("standard")
```

Supported modes:

```text
standard
auto-accept
bypass
plan
```

In `plan` mode, the tool list hides write/process tools that should not be available during read-only planning.

Recommended mapping:

```python
mode = "plan" if context.plan_mode else "standard"
tools = get_tools_for_mode(mode)
```

## Dispatch Pattern

A generic OpenAI-style dispatcher looks like this:

```python
import json


async def dispatch_tool_call(tool_call, context):
    name = tool_call.function.name
    try:
        arguments = json.loads(tool_call.function.arguments or "{}")
    except json.JSONDecodeError:
        arguments = {}

    result = await invoke_tool(name, arguments, context=context)
    return {
        "role": "tool",
        "tool_call_id": tool_call.id,
        "name": name,
        "content": result,
    }
```

## Workspace Safety

The migration expects the host to configure workspace roots correctly.

```python
context = ToolContext(
    cwd=project_root,
    workspace_roots=[project_root, shared_package_root],
)
```

Filesystem tools require absolute paths for:

- `read_file.absolutePath`
- `write_file.filePath`
- `edit_file.filePath`
- `read_directory.path`

The tools reject paths outside `workspace_roots`.

`glob`, `grep`, `read_multiple_files`, and shell `directory` can use relative directories, resolved against `cwd`.

## Permissions

The migration exposes a `permission_callback`.

Use it for shell and process termination approvals:

```python
async def permission_callback(tool_name: str, args: dict) -> bool:
    if tool_name == "shell_command":
        return await ui.ask_approval(
            title="Run shell command?",
            body=args.get("command", ""),
        )
    if tool_name == "kill_shell":
        return await ui.ask_approval(
            title="Terminate process?",
            body=str(args),
        )
    return True
```

Then:

```python
context.permission_callback = permission_callback
```

Suggested policy:

- `standard`: ask before shell/process operations and potentially destructive edits.
- `auto-accept`: allow file edits and common commands, still ask for dangerous commands.
- `bypass`: allow all tool operations inside workspace.
- `plan`: block write/process tools.

## Plan Mode

The migrated `enter_plan_mode` and `exit_plan_mode` tools toggle `context.plan_mode`.

Host loop responsibilities:

1. Keep `context.plan_mode` in sync with UI/runtime mode.
2. Rebuild the model tool list after mode changes.
3. Add plan-mode instructions to the system prompt.
4. Decide how plan files are stored or approved.

Example:

```python
if context.plan_mode:
    tools = get_tools_for_mode("plan")
else:
    tools = get_tools_for_mode("standard")
```

Suggested system prompt addition:

```text
In plan mode, use read-only tools to explore and produce a plan.
Do not modify files or run shell commands.
When ready, call exit_plan_mode.
```

## Structured User Questions

`ask_user_question` supports two integration modes.

If no `question_callback` is configured, it returns JSON:

```json
{
  "_type": "ask_user_question",
  "questions": [...]
}
```

Your frontend can detect `_type == "ask_user_question"` and render a question card.

If a callback is configured:

```python
async def question_callback(payload: dict) -> dict:
    return await frontend.ask_questions(payload)


context.question_callback = question_callback
```

Recommended callback return shape:

```json
{
  "answers": [
    {
      "questionIndex": 0,
      "selectedOptions": ["Yes"]
    }
  ]
}
```

## Shell And Monitor Tasks

`shell_command(background=True)` and `monitor_command` create tracked tasks in:

```python
context.shell_tasks
```

Each task has:

- `id`
- `kind`
- `process`
- `command`
- `cwd`
- `output_path`
- `status`
- `output_offset`
- timestamps

Use:

- `shell_tasks` to list tasks
- `monitor_events` to read incremental monitor output
- `kill_shell` to stop tracked tasks

Important runtime requirement:

Background process tasks should live on the same asyncio event loop as the agent runtime. Do not start a monitor in one event loop and read it from another.

## Web Tools

The migration provides standard-library fallback implementations for:

- `web_search`
- `web_fetch`

For production, provide host adapters:

```python
async def web_search_provider(query: str, num_results: int) -> str:
    return await my_search_service.search(query, num_results)


async def web_fetch_provider(url: str) -> str:
    return await my_fetch_service.fetch_markdown(url)


context.web_search_provider = web_search_provider
context.web_fetch_provider = web_fetch_provider
```

Recommended production behavior:

- Reject private, loopback, and link-local URLs.
- Enforce request timeouts.
- Truncate large responses.
- Convert HTML to clean markdown.
- Include source URLs in results.

## Diagnostics Tool

`diagnostics` is an adapter hook. It requires your host to provide IDE/LSP diagnostics.

```python
async def diagnostics_provider(file_paths: list[str] | None) -> str:
    return await ide_bridge.get_diagnostics(file_paths)


context.diagnostics_provider = diagnostics_provider
```

If no provider is configured, the tool returns:

```text
Diagnostics provider not configured.
```

## File Backups

`write_file` and `edit_file` create backups when overwriting/editing existing files.

Backups are written under:

```python
context.tmp_dir / "backups"
```

This is not a full checkpoint system. If your host agent supports rewind/checkpoints, integrate backup creation with that system later.

## Taste Files

The migration protects CommandCode taste files:

```text
.commandcode/taste/**/taste.md
```

Normal `write_file` and `edit_file` calls reject these files.

If a future host system implements taste learning, it should expose a separate controlled API for taste writes.

## Memory And Skills

This migration does not yet implement CommandCode memory or skill loading as executable tools.

Recommended later integration:

### Memory

Load these into the system prompt:

```text
AGENTS.md
.commandcode/AGENTS.md
~/.commandcode/AGENTS.md
```

Support `@file` imports with recursion limits.

### Skills

Load skills as prompt/context assets, not as Python functions.

Potential skill roots:

```text
python_migration/commandcode_python_migration/...
~/.commandcode/skills
~/.agents/skills
.commandcode/skills
.agents/skills
```

When the user invokes a skill, read its `SKILL.md`, read relevant references, and inject the instructions into the model context.

## Minimal Agent Loop Example

```python
import json
from pathlib import Path

from openai import AsyncOpenAI

from commandcode_migration import ToolContext, get_tools_for_mode, invoke_tool


client = AsyncOpenAI()


async def run_agent(prompt: str, workspace: Path) -> str:
    context = ToolContext(cwd=workspace, workspace_roots=[workspace])
    messages = [
        {"role": "system", "content": "You are a coding agent with native Python tools."},
        {"role": "user", "content": prompt},
    ]

    for _ in range(20):
        mode = "plan" if context.plan_mode else "standard"
        response = await client.chat.completions.create(
            model="gpt-5-codex",
            messages=messages,
            tools=get_tools_for_mode(mode),
            tool_choice="auto",
        )

        msg = response.choices[0].message

        if not msg.tool_calls:
            return msg.content or ""

        messages.append(msg)

        for call in msg.tool_calls:
            try:
                args = json.loads(call.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {}

            result = await invoke_tool(call.function.name, args, context=context)
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": call.function.name,
                    "content": result,
                }
            )

    return "Stopped after max tool iterations."
```

## Integration Checklist

- [ ] Add the `commandcode_python_migration` directory to your Python path, or package it.
- [ ] Import from the package inside it: `commandcode_migration`.
- [ ] Create one `ToolContext` per agent session or run.
- [ ] Configure `cwd` and `workspace_roots`.
- [ ] Register `TOOL_DEFINITIONS` or `get_tools_for_mode(mode)` with the model.
- [ ] Dispatch model tool calls through `invoke_tool`.
- [ ] Feed tool results back into the conversation.
- [ ] Rebuild available tools after plan-mode changes.
- [ ] Add a permission callback for shell/process tools.
- [ ] Add a question callback or frontend JSON-card renderer.
- [ ] Add web provider adapters for production.
- [ ] Add diagnostics provider if an IDE/LSP bridge exists.
- [ ] Persist task list, plan mode, and shell tasks if sessions survive process restarts.
- [ ] Decide how backups/checkpoints map to your host undo/rewind system.

## Recommended Next Phases

1. Package this module as an installable internal Python package.
2. Wire it into a small prototype agent loop.
3. Add host callbacks for permissions and user questions.
4. Add production web search/fetch providers.
5. Add memory and skill loading as prompt-context systems.
6. Add MCP and taste learning as separate runtime subsystems.
7. Integrate diagnostics with an IDE bridge.
8. Add session persistence for tasks, monitors, and plan mode.

## Compatibility Note

The inspected CommandCode install exposes 20 built-in tools.

The names `create_file`, `delete_file`, and `explore` appear internally but are not exposed in the built-in tool array. Add them only as optional compatibility aliases if a target agent system explicitly needs them.
