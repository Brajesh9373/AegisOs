"""Git repository connector — clones remotes, discovers files, feeds into KG pipeline.

Supports: public repos, private repos via HTTPS+token, local paths.
Every file becomes a UKO; the KnowledgeEngine does the rest (AST analysis, UCO
creation, graph population). Commits are also extracted for temporal context.
"""

from __future__ import annotations

import asyncio
import subprocess
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ecms.providers.domain.connector import DiscoveredObject
from ecms.providers.infrastructure.base import BaseConnector

__all__ = ["GitConnector"]

_IGNORED_DIRS = {".git", "node_modules", "__pycache__", ".venv", "dist", "build", ".next", "venv"}
_IGNORED_EXT = {".pyc", ".pyo", ".o", ".so", ".dll", ".exe", ".class", ".jar", ".war",
                ".jpg", ".jpeg", ".png", ".gif", ".ico", ".svg", ".woff", ".woff2",
                ".ttf", ".eot", ".mp3", ".mp4", ".avi", ".mov", ".zip", ".tar", ".gz"}


class GitConnector(BaseConnector):
    """Discovers every text file in a Git repository (local or remote).

    Remote repos are cloned into a temporary workspace. File content is read
    as UTF-8; binary/large files are skipped. Commit history is also extracted
    as commit-type objects.
    """

    name = "git"
    provider = "git"

    def __init__(
        self,
        repo_url: str = "",
        branch: str = "main",
        access_token: str = "",
        local_path: str = "",
        workspace: str = "/workspace/repos",
    ) -> None:
        self._repo_url = repo_url.strip().rstrip("/\\")
        self._branch = branch
        self._access_token = access_token
        self._local_path = local_path
        self._workspace = Path(workspace)
        self._repo_path: Path | None = None
        self._repo_name: str = ""

    async def initialize(self) -> None:
        """Clone remote repo or validate local path."""
        self._workspace.mkdir(parents=True, exist_ok=True)

        if self._local_path:
            self._repo_path = Path(self._local_path).resolve()
            if not self._repo_path.exists():
                raise FileNotFoundError(f"Local path not found: {self._local_path}")
            self._repo_name = self._repo_path.name
            return

        if self._repo_url:
            self._repo_name = self._repo_url.rstrip("/").split("/")[-1].removesuffix(".git")
            dest = self._workspace / self._repo_name
            await asyncio.to_thread(self._clone_or_pull, dest)
            self._repo_path = dest
            return

        raise ValueError("Either repo_url or local_path must be provided")

    async def discover(self) -> list[DiscoveredObject]:
        """Return every text file and every commit as a DiscoveredObject."""
        if self._repo_path is None:
            return []
        return await asyncio.to_thread(self._discover)

    async def collect(self, object_id: str) -> DiscoveredObject | None:
        """Fetch a single file by relative path."""
        if self._repo_path is None:
            return None
        path = self._repo_path / object_id
        if path.is_file():
            return self._describe_file(path)
        return None

    def _clone_or_pull(self, dest: Path) -> None:
        """Clone if missing, otherwise pull latest."""
        url = self._repo_url
        if self._access_token and "github.com" in url:
            # Inject token directly into URL for GitHub — most reliable method
            url = url.replace("https://", f"https://x-access-token:{self._access_token}@")

        if dest.exists():
            subprocess.run(
                ["git", "-C", str(dest), "fetch", "--prune", "origin"],
                check=False, capture_output=True, text=True, timeout=60,
            )
            subprocess.run(
                ["git", "-C", str(dest), "checkout", self._branch],
                check=False, capture_output=True, text=True, timeout=30,
            )
            subprocess.run(
                ["git", "-C", str(dest), "pull", "--ff-only", "origin", self._branch],
                check=False, capture_output=True, text=True, timeout=60,
            )
        else:
            subprocess.run(
                ["git", "clone", "--branch", self._branch, url, str(dest)],
                check=False, capture_output=True, text=True, timeout=120,
            )

    def _discover(self) -> list[DiscoveredObject]:
        objects: list[DiscoveredObject] = []
        assert self._repo_path is not None

        # File objects
        for path in sorted(self._repo_path.rglob("*")):
            if not path.is_file():
                continue
            if any(p in _IGNORED_DIRS for p in path.parts):
                continue
            if path.suffix.lower() in _IGNORED_EXT:
                continue
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            if not content.strip():
                continue
            objects.append(self._describe_file(path))

        # Commit objects (last 100 commits)
        commits = self._collect_commits(limit=100)
        objects.extend(commits)

        return objects

    def _describe_file(self, path: Path) -> DiscoveredObject:
        assert self._repo_path is not None
        rel = path.relative_to(self._repo_path).as_posix()
        try:
            content = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            content = ""
        stat = path.stat()
        return DiscoveredObject(
            object_id=f"{self._repo_name}:{rel}",
            object_type="file",
            title=rel,
            content=content,
            metadata={
                "repo": self._repo_name,
                "path": rel,
                "suffix": path.suffix,
                "size_bytes": stat.st_size,
                "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
            },
        )

    def _collect_commits(self, limit: int = 100) -> list[DiscoveredObject]:
        assert self._repo_path is not None
        result = subprocess.run(
            [
                "git", "-C", str(self._repo_path), "log",
                f"--max-count={limit}",
                "--pretty=format:%H%x1f%an%x1f%aI%x1f%s",
                "--name-only",
            ],
            capture_output=True, text=True, timeout=30, check=False,
        )
        if result.returncode != 0:
            return []

        commits: list[DiscoveredObject] = []
        blocks = result.stdout.strip().split("\n\n")
        for block in blocks:
            lines = block.strip().split("\n")
            if not lines:
                continue
            header = lines[0].split("\x1f")
            if len(header) < 4:
                continue
            sha, author, date, message = header[0], header[1], header[2], header[3]
            files = [f.strip() for f in lines[1:] if f.strip()]
            commits.append(
                DiscoveredObject(
                    object_id=f"{self._repo_name}:commit:{sha[:8]}",
                    object_type="commit",
                    title=message[:120],
                    content=f"Author: {author}\nDate: {date}\nMessage: {message}\nFiles: {', '.join(files[:20])}",
                    metadata={
                        "repo": self._repo_name,
                        "sha": sha,
                        "author": author,
                        "date": date,
                        "files": files,
                    },
                )
            )
        return commits
