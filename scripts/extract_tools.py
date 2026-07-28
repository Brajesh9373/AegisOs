import re, json, sys

data = open('/usr/lib/node_modules/command-code/dist/cli.mjs', 'r', errors='ignore').read()

# Find tool definitions — these have name + description + parameters
# Pattern: name marker followed by description
tools_found = {}

# Look for: function name patterns in the minified JS
# Tools typically appear with: "description" near "name"
# Try to find blocks with both name and description

# Broad scan for quoted strings that could be tool names
candidates = [
    'read_file', 'write_file', 'edit_file', 'create_file', 'delete_file',
    'glob', 'grep', 'read_directory', 'read_multiple_files', 'shell_command',
    'web_search', 'web_fetch', 'read_lints', 'replace_in_file', 'search_file',
    'search_content', 'list_code_definition_names', 'preview_url',
    'run_terminal_cmd', 'execute_command', 'kill_shell', 'monitor_command',
    'monitor_events', 'shell_tasks', 'task', 'todo_write',
    'tasklist', 'ask_user_question', 'web_search', 'web_fetch',
    'search_code', 'run_command', 'bash', 'terminal',
    'browser_navigate', 'browser_click', 'browser_screenshot',
    'browser_fill', 'browser_scrape', 'browser_extract',
    'agent-browser', 'design',
    'get_self_knowledge', 'find_skills', 'plan',
    'enter_plan_mode', 'exit_plan_mode',
    'thinking', 'reasoning',
]

found = []
for c in candidates:
    count = len(re.findall(re.escape(c), data))
    if count > 0:
        found.append((c, count))

found.sort(key=lambda x: x[1], reverse=True)
for name, count in found:
    print(f"{name}: {count}")
