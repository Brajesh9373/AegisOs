# CommandCode Python Migration Inventory

Source inspected:

- `C:\Users\braje\AppData\Roaming\npm\node_modules\command-code`
- Package: `command-code@0.43.1`
- Runtime bundle: `dist/cli.mjs`
- Entrypoints: `cmd`, `cmdc`, `command-code`, `commandcode`

This inventory focuses on capabilities worth migrating or adapting into a Python agent system. It does not inspect or assume any target repo integration.

## Exposed Built-In Agent Tools

The installed bundle exposes 20 built-in client tools via:

```js
lu = [pi, xi, Ii, Mi, Ni, Vi, Yi, sl, al, ll, dl, ul, ml, hl, wl, El, oc, hc, Cl, vl]
cu = []
```

`cu=[]` means no bundled server-side tools are registered locally in this install; MCP tools are loaded dynamically from configured MCP servers.

### Filesystem Tools

1. `read_file`
   - Reads absolute file paths inside the workspace.
   - Handles text, image, and binary files.
   - Supports `offset` and `limit` for large text files.
   - Large reads return bounded previews with truncation metadata.

2. `edit_file`
   - Exact string replacement in an existing text file.
   - Parameters: `filePath`, `oldValue`, `newValue`, `replaceAll`, `replacementCount`.
   - Fails safely when target text is absent or replacement count is invalid.
   - Creates backups before edits.

3. `read_directory`
   - Lists files and directories separately.
   - Requires absolute directory path inside workspace.
   - Supports `exclude` glob patterns.
   - Respects `.gitignore` by default.

4. `write_file`
   - Creates or overwrites UTF-8 text files.
   - Requires absolute `filePath`.
   - Creates parent directories automatically.
   - Creates backups before overwriting existing files.

5. `read_multiple_files`
   - Reads multiple files by include/exclude glob patterns.
   - Parameters include `include`, `exclude`, `defaultExclude`, `gitIgnore`, `targetDirectory`.
   - Excludes common generated/build folders by default.
   - Handles text and binary files differently.
   - Aggregates output with per-file headers and truncation metadata.

6. `grep`
   - Recursive regex content search.
   - Parameters: `pattern`, optional `include`, optional `directory`.
   - Supports file filtering via glob patterns.
   - Returns file paths and line numbers.

7. `glob`
   - File discovery by glob pattern.
   - Parameters: `pattern`, optional `path`.
   - Results are sorted by modification time.
   - Respects workspace boundaries.

### Shell And Process Tools

8. `shell_command`
   - Executes shell commands with stdout/stderr capture.
   - Parameters: `command`, `args`, `directory`, `timeout`, `background`.
   - Supports background mode for dev servers/watchers.
   - Tracked background tasks get `taskId`, PID, cwd, status, and output log path.
   - Uses permission callbacks for risky execution modes.

9. `monitor_command`
   - Starts a long-running tracked monitor command.
   - Parameters: `command`, `args`, `directory`, `description`, `maxDurationMs`, `notify`, `checkAfterMs`.
   - Always backgrounded.
   - Intended for log tails, watch commands, health streams, server logs.
   - Can schedule hidden wakeups after a delay or on exit.

10. `monitor_events`
    - Reads new output from a monitor task.
    - Parameters: `taskId`, `fromOffset`, `maxBytes`.
    - Advances stored output offset unless `fromOffset` is supplied.
    - Defangs output as untrusted process data.

11. `shell_tasks`
    - Lists tracked shell and monitor tasks.
    - Parameter: `includeStopped`.
    - Shows task id, kind, status, PID, command, cwd, timestamps, and output log path.

12. `kill_shell`
    - Stops tracked shell/monitor tasks by `taskId`, or processes by `pid` or `port`.
    - Exactly one of `taskId`, `pid`, or `port` must be supplied.
    - Attempts graceful termination before force-kill.
    - Has a permission callback.

### Planning And Interaction Tools

13. `todo_write`
    - Manages structured task lists.
    - Parameter: `todos`, array of `{ id, content, status }`.
    - Status values: `pending`, `in_progress`, `completed`.
    - The installed CLI implementation mostly formats/returns the todo list; persistence is handled by the runtime UI/context layer.

14. `ask_user_question`
    - Asks structured multiple-choice questions.
    - Parameters: `questions`, each with `question`, `header`, `options`, and optional `multiSelect`.
    - Validates 2-4 options.
    - Truncates headers longer than 20 chars.
    - Uses an `onQuestionRequest` callback supplied by the host runtime.
    - Supports hidden custom/free-text input in the UI.

15. `exit_plan_mode`
    - Asks the user whether to exit plan mode and begin implementation.
    - Reads the most recent plan file from `~/.commandcode/plans`.
    - Possible outcomes include standard mode, auto-accept mode, or staying in plan mode.

16. `enter_plan_mode`
    - Asks the user whether to enter read-only plan mode.
    - Intended for explicit planning requests, architectural work, multi-file work, or uncertain approaches.
    - Must be called alone because it changes mode/system prompt.

### IDE, Product Knowledge, Web

17. `diagnostics`
    - Gets LSP diagnostics from the IDE.
    - Parameter: optional `filePaths` array.
    - Requires IDE connection through Command Code extension.
    - Useful integration candidate if the target agent has an IDE bridge.

18. `get_self_knowledge`
    - Returns Command Code product/help documentation from the bundle.
    - Covers features, shortcuts, commands, taste, FAQ, troubleshooting, pricing, privacy.
    - Intended to be called once per conversation when the user asks about Command Code.

19. `web_search`
    - Calls Command Code API endpoint `/alpha/web-search`.
    - Parameters: `query`, optional `numResults`.
    - The tool description instructs agents to include the current year for recent/current queries.

20. `web_fetch`
    - Calls Command Code API endpoint `/alpha/web-fetch`.
    - Parameter: `url`.
    - Returns URL, status, and cleaned markdown content.
    - Rejects private, loopback, and link-local addresses at the API/service layer.

## Referenced But Not Exposed As Built-In Tools

These names appear in the bundle but are not present in the exposed built-in tool array for this install:

- `create_file`
- `delete_file`
- `explore`

They appear in display/permission/block lists, so they may be legacy, remote, planned, or mode-specific concepts. For Python migration, treat them as optional compatibility aliases rather than confirmed CommandCode 0.43.1 built-ins.

## Permission And Mode Rules Worth Porting

CommandCode has a permission mode filter:

- `standard`, `auto-accept`, `bypass`: most tools available.
- `plan`: read-only mode.

Plan mode blocks:

- `edit_file`
- `delete_file`
- `shell_command`
- `monitor_command`
- `todo_write`
- `kill_shell`

Plan mode also hides `enter_plan_mode`, while standard-like modes hide `exit_plan_mode`.

Special exception:

- `write_file` is allowed in plan mode only for plan files under `~/.commandcode/plans/<filename>.md`.

Migration recommendation:

- Implement mode filtering separately from tool implementations.
- Keep each tool pure and have a host policy layer decide whether it may run.

## Workspace And Safety Rules

Important reusable safety behavior:

- File paths are expected to be absolute for read/write/edit/directory operations.
- Paths must stay inside the current workspace or additional allowed directories.
- `.commandcode/taste/` files are protected from normal `write_file` and `edit_file`.
- Sensitive basenames are ignored by some discovery logic, including `.env`, PEM/key files, SSH keys, credentials, `.npmrc`, `.pypirc`, and `.netrc`.
- Shell commands validate cwd inside workspace.
- Long shell output is capped/truncated.
- Monitor output is wrapped as untrusted data.
- File edits/writes create backups through the file history/checkpoint system.

## Bundled Skills

The package includes two bundled skills:

1. `agent-browser`
   - File: `skills/agent-browser/SKILL.md`
   - A discovery stub for the separate `agent-browser` CLI.
   - Instructs agents to run:
     - `agent-browser skills get core`
     - `agent-browser skills get core --full`
     - specialized skills: `electron`, `slack`, `dogfood`
   - Integration value: browser automation workflow, but it depends on another CLI unless reimplemented.

2. `design`
   - File: `skills/design/SKILL.md`
   - Large frontend design playbook.
   - References 24 design docs:
     - `border.md`
     - `button.md`
     - `checkup.md`
     - `color.md`
     - `create.md`
     - `design-html.md`
     - `deslop.md`
     - `finish.md`
     - `interaction.md`
     - `layout.md`
     - `motion.md`
     - `redesign.md`
     - `refine.md`
     - `relayout.md`
     - `report-html.md`
     - `responsive.md`
     - `review.md`
     - `setup.md`
     - `shadow.md`
     - `smell.md`
     - `surface.md`
     - `tokenize.md`
     - `typeset.md`
     - `voice.md`
     - `writing.md`
   - Integration value: can be migrated almost directly as prompt/context assets, not executable code.

## CLI Command Surface

Top-level CLI commands detected:

- `login`
- `logout`
- `status`
- `whoami`
- `info`
- `help`
- `update`
- `feedback`
- `mcp`
- `taste`
- `learn`
- `skills`
- `sandbox`

MCP subcommands:

- `mcp add`
- `mcp add-json`
- `mcp list`
- `mcp get`
- `mcp remove`
- `mcp auth`

Skills subcommands:

- `skills add`
- `skills remove`
- `skills list`

Taste subcommands:

- `taste push`
- `taste pull`
- `taste list`
- `taste lint`
- `taste open`
- `taste learn` when experimental mode is enabled.

## Interactive Slash Commands

The help table exposes these interactive commands:

- `/init`
- `/goal [<objective>|clear|status]`
- `/memory`
- `/resume`
- `/fork [name]`
- `/rename [name]`
- `/rewind`
- `/clear`
- `/share`
- `/unshare`
- `/taste`
- `/learn-taste`
- `/skills`
- `/agents`
- `/mcp`
- `/model`
- `/configure-models`
- `/effort`
- `/provider`
- `/compact`
- `/compact-mode`
- `/context`
- `/ide`
- `/login`
- `/logout`
- `/courses`
- `/feedback [title]`
- `/trace`
- `/session-file`
- `/plan [task]`
- `/review [pr]`
- `/pr-comments`
- `/add-dir`
- `/status`
- `/usage`
- `/update`
- `/reload`
- `/help`
- `/exit`

Integration value:

- These are not all Python tools.
- They are UI/runtime commands that can inspire host-agent features.
- Highest-value candidates for another agent system are `/memory`, `/mcp`, `/skills`, `/agents`, `/model`, `/effort`, `/compact`, `/context`, `/ide`, `/plan`, `/review`, `/pr-comments`, `/add-dir`, `/session-file`.

## Other Reusable Systems

### Memory

CommandCode loads memory from:

- Enterprise memory: `~/.commandcode/AGENTS.md`
- User memory: likely user-level `AGENTS.md`
- Project memory:
  - `AGENTS.md`
  - `.commandcode/AGENTS.md`

It supports `@file` imports inside memory files, with recursion depth limiting.

### Skills

Skills can be loaded from:

- Bundled package skills.
- Global skills under `~/.commandcode/skills`.
- Compatibility global skills under `~/.agents/skills`.
- Project skills under `.commandcode/skills`.
- Compatibility project skills under `.agents/skills`.

Skill install/remove/list supports GitHub repositories and validates `SKILL.md` frontmatter.

### MCP

MCP config scopes:

- User: `~/.commandcode/mcp.json`
- Project: `.mcp.json`
- Local per-project: `~/.commandcode/projects/<slug>/mcp.json`

Transport/config support includes command-based servers and HTTP/OAuth flows.

### Taste Learning

Taste is a major CommandCode-specific subsystem:

- Learns coding style from repos/sessions.
- Stores local project and global taste packages.
- Supports push/pull/list/lint/open.
- Protects `.commandcode/taste/` from ordinary file tools.

Migration value:

- Not part of the core tool layer.
- Worth treating as a later memory/preference subsystem.

### Session Management

Useful features:

- Resume sessions.
- Fork sessions.
- Rename sessions.
- Rewind to checkpoints.
- Show session file.
- Share/unshare conversations.
- Compact conversation history.
- Track trace IDs.

Migration value:

- Host runtime concerns, not tool primitives.

### IDE Bridge

CommandCode ships a VSIX:

- `vsix/commandcode-vscode.vsix`

IDE-linked features include:

- Diagnostics tool.
- Open file and selected-line context.
- `/ide` setup.

Migration value:

- Keep as a separate integration layer.
- Python tool can define a diagnostics interface, but real diagnostics require an editor/LSP bridge.

### Sandbox

Experimental command:

- `sandbox`

It uses CommandCode API sandbox endpoints:

- `/alpha/sandbox/start`
- `/alpha/sandbox/stream`
- `/alpha/sandbox/status`
- `/alpha/sandbox/stop`
- `/alpha/sandbox/sessions`

Migration value:

- Later remote-execution feature, not core local Python migration.

## Recommended Python Migration Order

### Phase 1: Native Core Tools

Implement and test:

- `read_file`
- `read_directory`
- `glob`
- `grep`
- `read_multiple_files`
- `write_file`
- `edit_file`

Include:

- workspace boundary checks
- `.gitignore` support
- binary/image metadata handling
- truncation metadata
- default excludes
- backup hooks as optional host callbacks

### Phase 2: Process Tools

Implement:

- `shell_command`
- `monitor_command`
- `monitor_events`
- `shell_tasks`
- `kill_shell`

Include:

- tracked task registry
- output log files
- task IDs
- timeout handling
- graceful then forceful termination
- untrusted monitor-output wrapping

### Phase 3: Interaction And Planning

Implement:

- `todo_write`
- `ask_user_question`
- `enter_plan_mode`
- `exit_plan_mode`

Keep callbacks host-supplied:

- question rendering
- permission prompts
- mode switching
- todo persistence

### Phase 4: Web And Diagnostics

Implement:

- `web_search`
- `web_fetch`
- `diagnostics`

For portability:

- Use provider interfaces, not CommandCode API calls directly.
- Provide default implementations with `httpx`/HTML parsing for web.
- Leave diagnostics as an adapter interface until an IDE bridge exists.

### Phase 5: Context Assets

Migrate:

- bundled `design` skill and references
- `agent-browser` stub as integration documentation
- self-knowledge docs
- memory file loading
- skills discovery/loading

### Phase 6: Host Runtime Integrations

Later system-level work:

- MCP manager
- taste learning
- session resume/fork/rewind
- compact/context accounting
- model/provider/effort settings
- IDE extension bridge
- sandbox execution

## Key Difference From The Existing Spec

The earlier migration spec mentions 23 tools, including `create_file` and `delete_file`.

The installed `command-code@0.43.1` package exposes 20 built-in tools. `create_file`, `delete_file`, and `explore` are referenced internally but are not in the actual exposed built-in tool array.

Recommendation:

- Implement the 20 confirmed tools first.
- Add `create_file` and `delete_file` only as compatibility conveniences if the target agent needs them.
- Do not treat `explore` as a real executable tool unless another CommandCode version exposes it.
