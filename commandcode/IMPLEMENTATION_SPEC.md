# CommandCode → ECMS Agent: Python Migration Specification

## Source

- Package: `command-code@0.43.1`
- Binary: `C:\Users\braje\AppData\Roaming\npm\node_modules\command-code\dist\cli.mjs`
- Exposed tool register: `lu = [pi, xi, Ii, Mi, Ni, Vi, Yi, sl, al, ll, dl, ul, ml, hl, wl, El, oc, hc, Cl, vl]`
- **20 built-in tools confirmed.** `create_file`, `delete_file`, `explore` are referenced internally but NOT in the exposed array.
- MCP tools: loaded dynamically from configured servers (`cu=[]` by default).
- Bundled skills: `agent-browser` + `design` (24 reference docs).

---

## File Map

| File | Action | Scope |
|------|--------|-------|
| `backend/ecms/agent/tools.py` | Rewrite | Add 10 new tool definitions + handlers. Update existing 6 tools for parity. |
| `backend/ecms/agent/loop.py` | Edit | Plan mode guard — before `_build_messages()`, swap in `_get_plan_mode_tools()` |
| `backend/ecms/agent/working_memory.py` | Edit | Add `task_list`, `plan_mode`, `active_skill`, `shell_tasks`, `question_callback` |
| `backend/ecms/memory/system_prompt.py` | Edit | Add skills section, plan mode rules, ask_user_question handling |
| `frontend/features/sessions/components/chat-view.tsx` | Edit | Detect `_type` in assistant messages, render question card |
| `backend/pyproject.toml` | Edit | Add `beautifulsoup4`, `html2text` |
| `commandcode/IMPLEMENTATION_SPEC.md` | Replace | This document |

---

## Phase 1 — Native Core Tools (7 tools)

These map directly to Python stdlib. Zero external dependencies. Under 50 lines each.

### 1. `read_file`

```
Description: Reads a file. Auto-detects text/binary/image. Text files return content (capped); binary/images return metadata. Supports offset+limit for large files.

Parameters:
  absolutePath (string, required): Absolute path inside workspace.
  offset (integer, optional): Start line (0-based).
  limit (integer, optional): Max lines to read.

Behaviour:
  - Validate path is absolute and inside workspace
  - For .png/.jpg/.gif/.bmp/.tiff: return {"type":"image","size":N,"path":"..."}
  - For other binary: return {"type":"binary","size":N,"path":"..."}
  - For text: read_bytes→decode utf-8, apply offset/limit, cap at 4000 chars
  - Large reads return truncation metadata: bytes_shown, total_bytes, line_count_certainty
```

### 2. `edit_file`

```
Description: Precise str_replace in existing files. Never creates files. Creates backups before edits.

Parameters:
  filePath (string, required): Absolute path inside workspace.
  oldValue (string, required): Exact text to find. Case-sensitive, whitespace-sensitive.
  newValue (string, required): Replacement text.
  replaceAll (boolean, optional): Replace all occurrences. Default: false.
  replacementCount (integer, optional): Number to replace when replaceAll=false. Default: 1.

Behaviour:
  - Validate path is absolute and inside workspace
  - Read file → str.replace(oldValue, newValue, count)
  - If oldValue not found → error "Text not found in file"
  - If multiple matches and replaceAll=false and no replacementCount → error "Multiple matches"
  - Create backup: filePath → filePath.bak before writing
  - Return count of replacements made
```

### 3. `read_directory`

```
Description: Lists directory contents — files and subdirectories separated. Respects .gitignore. Supports exclusion glob patterns.

Parameters:
  path (string, required): Absolute directory path inside workspace.
  exclude (array of strings, optional): Glob patterns to exclude. Example: ["*.log","**/node_modules/**"]

Behaviour:
  - Validate path is absolute and inside workspace
  - Use pathlib.Path.iterdir(). Separate files vs directories.
  - Apply .gitignore patterns (read from path/.gitignore and parent dirs)
  - Apply exclude patterns
  - Sort alphabetically
  - Return {"files":[...],"directories":[...],"count":N}
```

### 4. `write_file`

```
Description: Creates or overwrites a file. Creates parent directories. Creates backups before overwriting.

Parameters:
  filePath (string, required): Absolute path inside workspace.
  content (string, required): UTF-8 text content.

Behaviour:
  - Validate path is absolute and inside workspace
  - NEVER write to .commandcode/taste/ paths (protected)
  - Create parent directories: path.parent.mkdir(parents=True, exist_ok=True)
  - If file exists: create backup path.bak before overwriting
  - path.write_text(content, encoding="utf-8")
  - Return {"created":true,"path":"...","size":N}
```

### 5. `read_multiple_files`

```
Description: Reads multiple files by glob patterns. Concatenates contents with clear file headers. Excludes build artifacts by default.

Parameters:
  include (array of strings, required): Glob patterns. Example: ["**/*.ts","src/**/*.py"]
  exclude (array of strings, optional): Exclusion patterns.
  defaultExclude (boolean, optional): Apply default exclusions. Default: true.
  gitIgnore (boolean, optional): Respect .gitignore. Default: true.
  targetDirectory (string, optional): Base directory. Default: cwd.

Behaviour:
  - Default excludes: node_modules, dist, build, .git, coverage, tmp, temp, .DS_Store, *.log, *.tmp, *.cache
  - Glob the include patterns → resolve paths
  - Apply exclude patterns and .gitignore
  - Read each file, apply truncation per-file (4000 char cap)
  - Concatenate with headers: "=== path/to/file ===\\ncontent"
  - Binary files: skip content, note type+size
  - Cap total output at 20000 chars
  - Return aggregated text + metadata
```

### 6. `grep`

```
Description: Recursive regex content search across files. Returns file paths and line numbers.

Parameters:
  pattern (string, required): PCRE regex pattern.
  include (array of strings, optional): File glob filters. Example: ["*.ts","*.tsx"]
  directory (string, optional): Directory to search. Default: cwd.

Behaviour:
  - Use re.compile(pattern) for Python
  - Walk directory tree, respect .gitignore
  - Filter by include globs if provided
  - For each text file: read lines, match pattern, record (file:line_num)
  - Return list of matches: [{"file":"...","line":N,"text":"..."}, ...]
```

### 7. `glob`

```
Description: File discovery by glob pattern. Results sorted by modification time (most recent first).

Parameters:
  pattern (string, required): Glob pattern. Supports *, **, ?, [abc], {js,ts}.
  path (string, optional): Directory to search. Default: cwd.

Behaviour:
  - Use pathlib.Path(path).glob(pattern) for recursive (**) or directory-only (*)
  - Respect .gitignore
  - Sort by Path.stat().st_mtime descending
  - Return list of file paths (capped at 500 results)
```

---

## Phase 2 — Process Tools (5 tools)

Tracked via `WorkingMemory.shell_tasks` dict. Logs written to `/tmp/ecms_shell_{task_id}.log`.

### 8. `shell_command`

```
Description: Executes shell commands. Supports background mode for dev servers/watchers.

Parameters:
  command (string, required): Shell command. "npm install", "pytest", "git status"
  args (array of strings, optional): Arguments (auto-escaped).
  directory (string, optional): Working directory. Default: cwd.
  timeout (integer, optional): Max ms before forced termination. 100-300000. Default: 30000.
  background (boolean, optional): Start in background, return immediately. Default: false.

Behaviour:
  - Validate directory inside workspace
  - If background=true:
    - task_id = str(uuid4())
    - proc = await asyncio.create_subprocess_shell(...)
    - Store in WorkingMemory.shell_tasks[task_id] = {kind:"shell",pid:proc.pid,command,cwd,started_at,status:"running",output_log_path}
    - Start background reader writing stdout+stderr to /tmp/ecms_shell_{task_id}.log
    - Return {"task_id":task_id,"pid":proc.pid,"command":command,"background":true}
  - If background=false:
    - proc = await asyncio.create_subprocess_shell(...)
    - stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout/1000)
    - Return {"stdout":stdout[:5000],"stderr":stderr[:2000],"exit_code":proc.returncode,"duration_ms":N}
```

### 9. `monitor_command`

```
Description: Starts a long-running monitor command. Always background. Output readable via monitor_events.

Parameters:
  command (string, required): Command to start.
  args (array of strings, optional): Arguments.
  directory (string, optional): Working directory.
  description (string, optional): Human description for shell_tasks.
  maxDurationMs (integer, optional): Auto-stop after N ms.
  notify (string, optional): "scheduled" or "never". Default: "scheduled".
  checkAfterMs (integer, optional): Delay before first notification. Default: 45000.

Behaviour:
  - Same as shell_command background mode
  - Persistent log at /tmp/ecms_monitor_{task_id}.log
  - Track stored_offset in WorkingMemory.shell_tasks[task_id]
  - Return {"task_id":...,"pid":...,"cwd":...,"output_log_path":...,"monitoring":true}
```

### 10. `monitor_events`

```
Description: Reads new output from a monitor task since last read.

Parameters:
  taskId (string, required): Monitor task ID.
  fromOffset (integer, optional): Byte offset. Default: stored offset.
  maxBytes (integer, optional): Max bytes. Default: 8192.

Behaviour:
  - Look up shell_tasks[taskId].output_log_path and stored_offset
  - Read from offset → return new content
  - Advance stored_offset
  - Return {"output":"...","bytes_read":N,"eof":bool,"task_id":"..."}
```

### 11. `shell_tasks`

```
Description: Lists tracked shell and monitor tasks.

Parameters:
  includeStopped (boolean, optional): Include completed/failed tasks. Default: true.

Behaviour:
  - Iterate WorkingMemory.shell_tasks
  - Filter by status if includeStopped=false
  - Return {"tasks":[{task_id,kind,status,pid,command,cwd,started_at,output_log_path},...],"count":N}
```

### 12. `kill_shell`

```
Description: Stops tracked tasks by taskId, port, or PID. Graceful first, then force.

Parameters:
  taskId (string, optional): Task ID from shell_command/monitor_command.
  port (integer, optional): Port number to free.
  pid (integer, optional): Process ID to terminate.

Behaviour:
  - Exactly ONE of taskId/port/pid must be provided
  - If taskId: look up shell_tasks[taskId] → os.kill(pid, SIGTERM) → wait 2s → SIGKILL if alive
  - If pid: os.kill(pid, SIGTERM) directly
  - If port: find process by port → kill
  - Update shell_tasks status to "killed"
  - Return {"killed":true,"task_id":"...","pid":N}
```

---

## Phase 3 — Interaction & Planning (4 tools)

### 13. `todo_write`

```
Description: Manages structured task list. Each call replaces the entire list.

Parameters:
  todos (array, required): Array of {id (string), content (string), status (string:"pending"|"in_progress"|"completed")}.

Behaviour:
  - Replace WorkingMemory.task_list entirely
  - Inject into system prompt via WorkingMemory.summary_for_agent()
  - Return "Todo list updated. {N} items: {pending} pending, {in_progress} in progress, {completed} completed"
```

### 14. `ask_user_question`

```
Description: Asks the user structured multiple-choice questions. Use when requirements are ambiguous or user must choose between approaches.

Parameters:
  questions (array, required): Array of {question (string), header (string, ≤20 chars), options (array of {label (string, 1-5 words), description (string, 1 sentence)}), multiSelect (boolean, optional)}.

Behaviour:
  - Handler returns special JSON format:
    {"_type":"ask_user_question","questions":[...]}
  - NO plain text returned
  - Frontend ChatView detects _type and renders interactive question cards
  - User's answer becomes the next user message as {"answers":{"header1":"label1",...}}
  - The agent receives this as its next prompt
```

### 15. `enter_plan_mode`

```
Description: Enter read-only plan mode. Blocked tools become no-ops. Must be called alone — it changes the system mode.

Parameters: None.

Behaviour:
  - Set WorkingMemory.plan_mode = True
  - System prompt adds: "You are now in plan mode. Explore, research, design. No file modifications."
  - Returns "Entered plan mode. Blocked operations: edit_file, shell_command, monitor_command, todo_write, kill_shell."
```

### 16. `exit_plan_mode`

```
Description: Exit plan mode. Asks the user whether to exit and begin implementation. Reads the most recent plan file from ~/.commandcode/plans/ if one exists.

Parameters: None.

Behaviour:
  - Set WorkingMemory.plan_mode = False
  - If plan file exists at ~/.commandcode/plans/: show summary and confirm
  - Returns "Exited plan mode. Write operations are now enabled."
```

---

## Plan Mode Rules

| Tool | Allowed in Plan Mode? |
|------|----------------------|
| read_file | ✓ |
| edit_file | ✗ |
| read_directory | ✓ |
| write_file | ✓ ONLY for `~/.commandcode/plans/<filename>.md` |
| read_multiple_files | ✓ |
| grep | ✓ |
| glob | ✓ |
| shell_command | ✗ |
| monitor_command | ✗ |
| monitor_events | ✓ |
| shell_tasks | ✓ |
| kill_shell | ✗ |
| todo_write | ✗ |
| ask_user_question | ✓ |
| enter_plan_mode | ✗ (already in plan mode) |
| exit_plan_mode | ✓ |
| diagnostics | ✓ |
| get_self_knowledge | ✓ |
| web_search | ✓ |
| web_fetch | ✓ |

### Implementation in loop.py

```python
def _build_messages(self) -> list[dict]:
    tools = TOOL_DEFINITIONS
    if self._working.plan_mode:
        tools = _get_plan_mode_tools()
    ...

def _get_plan_mode_tools() -> list[dict]:
    """Return tool definitions with write/mutate tools marked blocked."""
    blocked = {"edit_file","shell_command","monitor_command","todo_write","kill_shell"}
    result = []
    for tool in TOOL_DEFINITIONS:
        name = tool["function"]["name"]
        if name in blocked:
            blocked_tool = copy.deepcopy(tool)
            blocked_tool["function"]["description"] = (
                "[BLOCKED IN PLAN MODE] " + tool["function"]["description"]
            )
            result.append(blocked_tool)
        elif name == "write_file":
            # Allowed ONLY for plan files
            result.append(tool)  # handler checks path
        elif name == "enter_plan_mode":
            continue  # Don't offer in plan mode
        else:
            result.append(tool)
    return result
```

Tool handlers check `_WORKING_MEMORY.plan_mode` and return appropriate error messages.

---

## Phase 4 — Web & Diagnostics (3 tools)

### 17. `web_search`

```
Description: Searches the web. Uses CommandCode API endpoint /alpha/web-search.

Parameters:
  query (string, required): Search query. Include current year (2026) for recent info.
  numResults (integer, optional): 1-10. Default: 5.

Behaviour:
  - POST to {ECMS_COMMANDCODE_API}/alpha/web-search with {query, numResults}
  - Requires COMMAND_CODE_API_KEY from settings
  - Fallback for offline: DuckDuckGo HTML search via httpx + BeautifulSoup
  - Return {"results":[{"title":"...","url":"...","snippet":"..."}],"query":"..."}
```

### 18. `web_fetch`

```
Description: Fetches a URL and returns clean markdown. Uses CommandCode API endpoint /alpha/web-fetch.

Parameters:
  url (string, required): Must start with http:// or https://. No private/loopback addresses.

Behaviour:
  - POST to {ECMS_COMMANDCODE_API}/alpha/web-fetch with {url}
  - Fallback for offline: httpx.get(url) → BeautifulSoup → html2text → markdown
  - Return {"url":"...","title":"...","content":"..." (5000 char cap),"status_code":N}
```

### 19. `diagnostics`

```
Description: Gets LSP diagnostics from IDE. Requires VS Code extension connection.

Parameters:
  filePaths (array of strings, optional): Specific files to check.

Behaviour (for now):
  - Return "Diagnostics require IDE bridge (VS Code extension). Not available in standalone mode."
  - Placeholder for future IDE integration
```

---

## Phase 5 — Skills & Knowledge (2 systems)

### 20. `get_self_knowledge`

```
Description: Returns CommandCode product documentation from the bundle. Use once per conversation when user asks about CommandCode capabilities.

Parameters: None.

Behaviour:
  - Load from commandcode/README.md or predefined knowledge base
  - Return relevant section as markdown
```

### Skill Loading (not a tool)

Skills load via system prompt instruction, not individual function calls:

```
System prompt addition:

## Skills

Available skill playbooks:
1. design — Frontend design partner: color, typography, layout, motion, review, refinement.
2. agent-browser — Browser automation CLI for web scraping, testing, screenshots.

To use a skill:
1. Read commandcode/skills/{name}/SKILL.md for master instructions
2. Read relevant references as needed
3. Follow the skill's playbook using existing tools

Design references: border, button, checkup, color, create, deslop, finish, interaction, layout, motion, redesign, refine, relayout, responsive, review, shadow, smell, surface, tokenize, typeset, voice, writing, report-html, design-html.

Agent-browser: install with `npm i -g agent-browser && agent-browser install`, then use shell_command to run browser operations.
```

---

## Phase 6 — Host Runtime (deferred)

Not part of the core Python migration. These are UI/runtime features:

- MCP manager (mcp add/list/get/remove)
- Taste learning (taste push/pull/list/lint/learn)
- Session resume/fork/rewind/compact
- Context window tracking (`/context`)
- Model/provider/effort switching (`/model`, `/effort`)
- IDE extension bridge
- Sandbox execution

The ECMS agent already has PostgreSQL-backed sessions, workspace-scoped memory, and model config via settings. These CLI features are not needed for tool parity.

---

## Working Memory Changes

```python
@dataclass
class WorkingMemory:
    # Existing fields...
    active_atom_ids: list[str] = field(default_factory=list)
    active_graph_refs: list[str] = field(default_factory=list)
    tool_results: list[dict] = field(default_factory=list)
    scratchpad: str = ""
    variables: dict[str, Any] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    # New fields
    task_list: list[dict] = field(default_factory=list)        # todo_write items
    plan_mode: bool = False                                     # plan mode state
    active_skill: str | None = None                             # currently loaded skill name
    shell_tasks: dict[str, dict] = field(default_factory=dict) # shell/monitor task registry

    def summary_for_agent(self) -> str:
        # Existing logic + task list + plan mode indicator + shell task count
```

---

## Dependencies

```toml
# backend/pyproject.toml additions:
"beautifulsoup4>=4.12",     # web_fetch HTML parsing (fallback)
"html2text>=2024.0",         # web_fetch HTML → markdown (fallback)
```

---

## Validation Checklist

- [ ] `read_file("src/main.py")` returns content
- [ ] `read_file("image.png")` returns type+size metadata
- [ ] `edit_file("test.txt","old","new")` makes replacement, creates backup
- [ ] `read_directory("/workspace")` returns files + dirs, respects .gitignore
- [ ] `write_file("/tmp/test.txt","hello")` creates file
- [ ] `write_file` to `.commandcode/taste/` → blocked
- [ ] `read_multiple_files(["**/*.py"])` returns concatenated content with headers
- [ ] `grep("def function", include=["*.py"])` returns matches
- [ ] `glob("**/*.py")` returns all Python files sorted by mtime
- [ ] `shell_command("echo hello")` returns stdout
- [ ] `shell_command("sleep 5",timeout=1000)` times out
- [ ] `shell_command("sleep 30",background=True)` returns immediately → `kill_shell(taskId)` kills it
- [ ] `monitor_command("tail -f /var/log/app.log")` starts → `monitor_events(taskId)` reads output
- [ ] `shell_tasks()` lists all tracked tasks
- [ ] `todo_write([{id:"1",content:"Test",status:"pending"}])` updates task list
- [ ] `enter_plan_mode()` → write_file blocks (except plan files)
- [ ] `exit_plan_mode()` → write_file works again
- [ ] `ask_user_question` returns structured JSON → frontend renders question card
- [ ] `web_search("test query")` returns results (API or DuckDuckGo fallback)
- [ ] `web_fetch("https://example.com")` returns markdown
- [ ] `get_self_knowledge()` returns docs
- [ ] All existing 19 ECMS tools still work (search_memory, query_graph, etc.)
