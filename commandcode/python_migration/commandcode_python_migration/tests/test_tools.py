from __future__ import annotations

import asyncio
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from commandcode_migration.tools import ToolContext, invoke_tool


class CommandCodeMigrationToolsTest(unittest.TestCase):
    def run_async(self, coro):
        return asyncio.run(coro)

    def make_context(self):
        tmp = tempfile.TemporaryDirectory()
        root = Path(tmp.name).resolve()
        ctx = ToolContext(cwd=root, workspace_roots=[root], tmp_dir=root / ".tmp")
        return tmp, root, ctx

    def test_filesystem_tools(self):
        tmp, root, ctx = self.make_context()
        self.addCleanup(tmp.cleanup)
        file_path = root / "src" / "main.py"

        result = self.run_async(
            invoke_tool(
                "write_file",
                {"filePath": str(file_path), "content": "hello = 'world'\nprint(hello)\n"},
                context=ctx,
            )
        )
        self.assertIn("File written", result)

        result = self.run_async(
            invoke_tool("read_file", {"absolutePath": str(file_path)}, context=ctx)
        )
        self.assertIn("hello = 'world'", result)

        result = self.run_async(
            invoke_tool(
                "edit_file",
                {
                    "filePath": str(file_path),
                    "oldValue": "world",
                    "newValue": "python",
                },
                context=ctx,
            )
        )
        self.assertIn("Edited", result)
        self.assertIn("python", file_path.read_text())

        result = self.run_async(invoke_tool("glob", {"pattern": "**/*.py"}, context=ctx))
        self.assertIn("src/main.py", result.replace("\\", "/"))

        result = self.run_async(
            invoke_tool("grep", {"pattern": "python", "directory": "."}, context=ctx)
        )
        self.assertIn("src/main.py", result.replace("\\", "/"))

        result = self.run_async(
            invoke_tool(
                "read_multiple_files",
                {"include": ["**/*.py"], "targetDirectory": str(root)},
                context=ctx,
            )
        )
        self.assertIn("hello = 'python'", result)

        result = self.run_async(
            invoke_tool("read_directory", {"path": str(root / "src")}, context=ctx)
        )
        self.assertIn("main.py", result)

    def test_shell_and_monitor_tools(self):
        tmp, root, ctx = self.make_context()
        self.addCleanup(tmp.cleanup)

        async def scenario():
            result = await invoke_tool(
                "shell_command",
                {"command": "python", "args": ["-c", "print('hello')"], "directory": str(root)},
                context=ctx,
            )
            self.assertIn("Exit code: 0", result)
            self.assertIn("hello", result)

            result = await invoke_tool(
                "monitor_command",
                {
                    "command": "python",
                    "args": ["-c", "print('tick')"],
                    "directory": str(root),
                    "notify": "never",
                },
                context=ctx,
            )
            self.assertIn("Started monitor command", result)
            task_id = next(iter(ctx.shell_tasks))
            await asyncio.sleep(0.6)
            events = await invoke_tool("monitor_events", {"taskId": task_id}, context=ctx)
            self.assertIn("tick", events)
            tasks = await invoke_tool("shell_tasks", {}, context=ctx)
            self.assertIn(task_id, tasks)

        self.run_async(scenario())

    def test_planning_question_and_diagnostics(self):
        tmp, root, ctx = self.make_context()
        self.addCleanup(tmp.cleanup)

        result = self.run_async(
            invoke_tool(
                "todo_write",
                {
                    "todos": [
                        {"id": "1", "content": "Migrate tools", "status": "in_progress"}
                    ]
                },
                context=ctx,
            )
        )
        self.assertIn("Todo list updated", result)

        result = self.run_async(
            invoke_tool(
                "ask_user_question",
                {
                    "questions": [
                        {
                            "question": "Proceed?",
                            "header": "Proceed",
                            "options": [
                                {"label": "Yes", "description": "Continue."},
                                {"label": "No", "description": "Stop."},
                            ],
                        }
                    ]
                },
                context=ctx,
            )
        )
        self.assertIn('"_type": "ask_user_question"', result)

        self.run_async(invoke_tool("enter_plan_mode", {}, context=ctx))
        blocked = self.run_async(
            invoke_tool(
                "shell_command",
                {"command": "python", "args": ["-c", "print('blocked')"]},
                context=ctx,
            )
        )
        self.assertIn("Plan mode active", blocked)
        self.run_async(invoke_tool("exit_plan_mode", {}, context=ctx))

        diagnostics = self.run_async(invoke_tool("diagnostics", {}, context=ctx))
        self.assertIn("not configured", diagnostics)

    def test_web_fetch_rejects_localhost(self):
        tmp, root, ctx = self.make_context()
        self.addCleanup(tmp.cleanup)

        result = self.run_async(
            invoke_tool("web_fetch", {"url": "http://127.0.0.1:9999"}, context=ctx)
        )
        self.assertIn("rejected", result)


if __name__ == "__main__":
    unittest.main()
