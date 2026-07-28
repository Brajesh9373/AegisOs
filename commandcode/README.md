# CommandCode Integration

## What Is CommandCode?

CommandCode v0.43.1 is the coding agent CLI that powers ECMS's LLM backend.
It runs in two channels:

| Channel | Path | Mechanism |
|---------|------|-----------|
| **LLM Backend** | `api.commandcode.ai/provider/v1` | OpenAI-compatible API — all ReAct agent LLM calls |
| **Terminal CLI** | `/usr/bin/command-code` | PTY-bridged via WebSocket `/ws/terminal` |

The Dockerfile installs it globally: `npm install -g command-code`.

---

## Built-in Skills (2 skills, 26 references)

Skills are structured YAML + Markdown playbooks. Each skill defines a name,
description, allowed tools, and step-by-step references. The agent loads these
as tool definitions.

### 1. agent-browser

**File:** `commandcode/skills/agent-browser/SKILL.md`
**Allowed tools:** `Bash(agent-browser:*)`, `Bash(npx agent-browser:*)`

Browser automation for AI agents:
- Navigate web pages, fill forms, click buttons
- Take screenshots, extract structured data
- Test web apps, automate UI interactions
- Control Electron desktop apps (VS Code, Slack, Discord, Figma, Notion, Spotify)
- Check Slack messages, send Slack messages, search conversations

**Install:** `npm install -g agent-browser && agent-browser install`

### 2. design

**File:** `commandcode/skills/design/SKILL.md`

Design partner for frontend interfaces. One command per visual discipline
with 24 reference documents:

| Reference | Purpose |
|-----------|---------|
| `create.md` | New feature/page/component from scratch |
| `redesign.md` | Rework existing UI while preserving function |
| `relayout.md` | Reorganize layout, spacing, hierarchy |
| `recolor.md` | Color palette adjustments |
| `typeset.md` | Typography, font sizing, readability |
| `deslop.md` | Fix AI-generated visual slop |
| `color.md` | Color system guidelines |
| `layout.md` | Layout principles and patterns |
| `shadow.md` | Shadow/elevation system |
| `border.md` | Border and divider rules |
| `surface.md` | Surface/card/panel treatment |
| `button.md` | Button styles and states |
| `motion.md` | Animation and transition guidelines |
| `interaction.md` | Click, hover, focus, keyboard states |
| `responsive.md` | Responsive breakpoint system |
| `voice.md` | Writing tone and microcopy |
| `writing.md` | Content writing guidelines |
| `tokenize.md` | Generate design tokens (CSS vars) |
| `setup.md` | Initialize design brief for a project |
| `finish.md` | Final polish pass before shipping |
| `checkup.md` | Visual QA checklist |
| `smell.md` | Anti-pattern detection |
| `review.md` | Design review against spec |
| `refine.md` | Iterative improvement pass |
| `report-html.md` | HTML report template |
| `design-html.md` | HTML design reference |

---

## MCP (Model Context Protocol)

CommandCode supports MCP servers for external tool integration. Commands:

| Command | Purpose |
|---------|---------|
| `mcp add <name> [url]` | Add an MCP server |
| `mcp list` | List configured servers |
| `mcp get <name>` | Show server details |
| `mcp remove <name>` | Remove a server |
| `mcp add-json <name> <json>` | Add from JSON config |
| `mcp auth [server]` | Manage OAuth authentication |

**No MCP servers are installed yet.** The infrastructure exists — servers get
configured via CLI or `.commandcode/config.json`.

---

## Taste Learning

CommandCode learns coding preferences from repositories:

| Command | Purpose |
|---------|---------|
| `taste learn <source>` | Learn taste from local repo or GitHub URL |
| `taste push [package]` | Push taste to remote or global |
| `taste pull [package]` | Pull taste into current project |
| `taste list` | List available packages |
| `taste lint [package]` | Validate taste package format |

Taste files live in `.commandcode/taste/` and capture code style preferences
(what patterns to use, naming conventions, technology choices). ECMS's agent
can load these preferences to align its output with project conventions.

---

## Conversation Management (CLI-only)

The CLI has session management that the API agent doesn't:

| Command | Purpose |
|---------|---------|
| `/resume [name]` | Resume a past conversation by name/ID |
| `/fork [name]` | Fork into new session (original left untouched) |
| `/compact` | Compact conversation history to free context |
| `/rewind` | Restore to previous checkpoint |
| `/clear` | Clear conversation history |
| `/session-file` | Show current session file path |
| `/context` | Show context window usage and breakdown |

---

## Built-in Operations (CLI-only)

Operations the CLI agent performs natively that the API agent must implement:

| Operation | CLI Command | What It Does |
|-----------|------------|--------------|
| **Plan mode** | `--plan` or `/plan [task]` | Structured planning before execution |
| **Code review** | `/review [pr]` | Review a pull request |
| **PR comments** | `/pr-comments` | Fetch all PR comments for current branch |
| **Multi-model** | `/model`, `--model`, `/configure-models` | Switch models or route tasks to specific models |
| **Reasoning effort** | `/effort` | Set reasoning effort for current model |
| **IDE integration** | `/ide`, `--ide-setup` | Connect IDE to share open file and selections |
| **Task routing** | Built-in | Different models for different built-in tasks |

---

## Files and Directories

| Path | Content |
|------|---------|
| `/usr/lib/node_modules/command-code/` | Global npm install — binary, skills, vsix |
| `/usr/lib/node_modules/command-code/skills/` | Built-in skills (agent-browser, design) |
| `/usr/lib/node_modules/command-code/dist/index.mjs` | Main entry point |
| `/home/ecms/.commandcode/` | User's CommandCode data directory |
| `/home/ecms/.commandcode/config.json` | User config |
| `/home/ecms/.commandcode/projects/` | Per-project session storage |
| `/home/ecms/.commandcode/taste/` | Taste learning data (if initialized) |
| `/workspace/.commandcode/` | Project-level CommandCode config (if initialized) |

---

## Integration Strategy

The agent loop already uses CommandCode's API as its LLM backend. To gain
the CLI's native capabilities without subprocess overhead:

1. **Skills as tools** — Register each skill's capabilities as agent tool definitions.
   The agent calls `use_skill("design", {"mode": "recolor"})` and the handler
   loads the relevant reference document.

2. **MCP as direct connections** — Connect to MCP servers directly from the
   agent loop using the Python MCP SDK (`mcp` package). No CLI intermediary needed.

3. **Taste as system prompt context** — If `.commandcode/taste/taste.md` exists,
   load it into the system prompt so the agent follows project conventions.

4. **Session management** — The agent already has PostgreSQL-backed sessions
   via `session_chat.py`. Conversation history replays on page load via
   `GET /sessions/{id}/messages`. 

5. **Plan mode** — Add a `planning` mode to the system prompt that the agent
   detects from user intent ("plan this feature", "design first").

6. **Code review** — Add a `review_code` tool that uses the agent's existing
   `read_file` + `query_graph` tools to emulate `/review`.
