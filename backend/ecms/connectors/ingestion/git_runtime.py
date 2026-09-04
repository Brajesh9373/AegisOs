"""Cancellation-aware, bounded Git workspace management."""

from __future__ import annotations

import asyncio
import base64
import contextlib
import os
import re
import signal
import subprocess
from dataclasses import dataclass
from pathlib import Path
from shutil import rmtree
from typing import Any


class GitCommandError(RuntimeError):
    """A Git command failed without leaking credentials in its error."""


class IngestionCancelledError(RuntimeError):
    """The durable job was cancelled."""


@dataclass(frozen=True)
class GitLimits:
    """Operational limits applied to Git network operations."""

    clone_timeout_seconds: int = 600
    fetch_timeout_seconds: int = 300
    clone_depth: int = 50


class GitCommandRunner:
    """Run Git without blocking the API event loop and terminate it on cancellation."""

    async def run(
        self,
        *args: str,
        timeout_seconds: int,
        cancel: asyncio.Event | None = None,
        cwd: Path | None = None,
        env_overrides: dict[str, str] | None = None,
    ) -> str:
        """Execute a command and return stdout."""
        if cancel is not None and cancel.is_set():
            raise IngestionCancelledError("Git operation cancelled")
        process = await asyncio.create_subprocess_exec(
            "git",
            *args,
            cwd=cwd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, **(env_overrides or {})},
            start_new_session=os.name != "nt",
            creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0),
        )
        communicate = asyncio.create_task(process.communicate())
        cancellation = asyncio.create_task(cancel.wait()) if cancel is not None else None
        try:
            waiters: set[asyncio.Task[Any]] = {communicate}
            if cancellation is not None:
                waiters.add(cancellation)
            done, _ = await asyncio.wait(
                waiters,
                timeout=timeout_seconds,
                return_when=asyncio.FIRST_COMPLETED,
            )
            if communicate in done:
                stdout, stderr = communicate.result()
                if process.returncode:
                    detail = _redact_git_error(stderr.decode(errors="replace").strip())[-2_000:]
                    raise GitCommandError(f"git {args[0] if args else 'command'} failed: {detail}")
                return stdout.decode(errors="replace")
            await self._stop(process)
            if cancellation is not None and cancellation in done:
                raise IngestionCancelledError("Git operation cancelled")
            raise TimeoutError(f"git {args[0] if args else 'command'} exceeded {timeout_seconds}s")
        finally:
            communicate.cancel()
            if cancellation is not None:
                cancellation.cancel()
            await asyncio.gather(
                communicate,
                *((cancellation,) if cancellation is not None else ()),
                return_exceptions=True,
            )

    @staticmethod
    async def _stop(process: asyncio.subprocess.Process) -> None:
        if process.returncode is not None:
            return
        if os.name == "nt":
            with contextlib.suppress(ProcessLookupError):
                process.send_signal(signal.CTRL_BREAK_EVENT)
        else:
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGTERM)  # type: ignore[attr-defined]
        with contextlib.suppress(asyncio.TimeoutError):
            await asyncio.wait_for(process.wait(), timeout=5)
        if process.returncode is None:
            if os.name == "nt":
                process.kill()
            else:
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGKILL)  # type: ignore[attr-defined]
            await process.wait()


class GitWorkspace:
    """Create or refresh a shallow, blob-filtered working copy."""

    def __init__(self, runner: GitCommandRunner, limits: GitLimits) -> None:
        """Create a workspace manager using the supplied runner and limits."""
        self._runner = runner
        self._limits = limits

    async def prepare(
        self,
        *,
        repo_url: str,
        branch: str,
        destination: Path,
        cancel: asyncio.Event,
        access_token: str | None = None,
    ) -> Path:
        """Clone or refresh the requested repository."""
        auth_environment = self._authentication_environment(access_token)
        destination.parent.mkdir(parents=True, exist_ok=True)
        if (destination / ".git").is_dir():
            await self._runner.run(
                "fetch",
                "--depth",
                str(self._limits.clone_depth),
                "--filter=blob:none",
                "--prune",
                "origin",
                branch,
                cwd=destination,
                cancel=cancel,
                timeout_seconds=self._limits.fetch_timeout_seconds,
                env_overrides=auth_environment,
            )
            await self._runner.run(
                "reset",
                "--hard",
                "FETCH_HEAD",
                cwd=destination,
                cancel=cancel,
                timeout_seconds=60,
            )
            return destination

        staging = destination.with_name(f"{destination.name}.staging-{os.getpid()}")
        if await asyncio.to_thread(staging.exists):
            await asyncio.to_thread(rmtree, staging)
        try:
            await self._runner.run(
                "clone",
                "--depth",
                str(self._limits.clone_depth),
                "--filter=blob:none",
                "--single-branch",
                "--branch",
                branch,
                "--",
                repo_url,
                str(staging),
                cancel=cancel,
                timeout_seconds=self._limits.clone_timeout_seconds,
                env_overrides=auth_environment,
            )
            if await asyncio.to_thread(destination.exists):
                await asyncio.to_thread(rmtree, destination)
            await asyncio.to_thread(staging.replace, destination)
        except Exception:
            if await asyncio.to_thread(staging.exists):
                await asyncio.to_thread(rmtree, staging)
            raise
        return destination

    async def current_revision(
        self,
        repository: Path,
        *,
        cancel: asyncio.Event,
    ) -> str:
        """Resolve the immutable commit represented by the prepared checkout."""
        revision = await self._runner.run(
            "rev-parse",
            "HEAD",
            cwd=repository,
            cancel=cancel,
            timeout_seconds=60,
        )
        value = revision.strip()
        if not value:
            raise GitCommandError("git rev-parse returned an empty revision")
        return value

    async def checkout_revision(
        self,
        repository: Path,
        revision: str,
        *,
        cancel: asyncio.Event,
        access_token: str | None = None,
    ) -> str:
        """Fetch and detach at an explicitly requested commit/ref safely."""
        value = revision.strip()
        if (
            not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._/-]{0,254}", value)
            or ".." in value
            or "@{" in value
            or value.endswith(("/", "."))
        ):
            raise ValueError("requested Git revision is invalid")
        await self._runner.run(
            "fetch",
            "--depth",
            str(self._limits.clone_depth),
            "--filter=blob:none",
            "origin",
            value,
            cwd=repository,
            cancel=cancel,
            timeout_seconds=self._limits.fetch_timeout_seconds,
            env_overrides=self._authentication_environment(access_token),
        )
        resolved = (
            await self._runner.run(
                "rev-parse",
                "--verify",
                "FETCH_HEAD^{commit}",
                cwd=repository,
                cancel=cancel,
                timeout_seconds=60,
            )
        ).strip()
        if not re.fullmatch(r"[0-9a-fA-F]{40,64}", resolved):
            raise GitCommandError("requested revision did not resolve to a commit")
        await self._runner.run(
            "reset",
            "--hard",
            resolved,
            cwd=repository,
            cancel=cancel,
            timeout_seconds=60,
        )
        return resolved

    @staticmethod
    def _authentication_environment(access_token: str | None) -> dict[str, str]:
        """Supply HTTPS auth through process environment, never URL/argv/error output."""
        if not access_token:
            return {}
        credential = base64.b64encode(f"x-access-token:{access_token}".encode()).decode()
        return {
            "GIT_CONFIG_COUNT": "1",
            "GIT_CONFIG_KEY_0": "http.extraHeader",
            "GIT_CONFIG_VALUE_0": f"Authorization: Basic {credential}",
            "GIT_TERMINAL_PROMPT": "0",
        }


def _redact_git_error(detail: str) -> str:
    """Remove URL credentials and queries from Git diagnostics."""
    return re.sub(
        r"""(https?://)(?:[^/@\s'"]+@)?([^/?#\s'"]+)(?:[/?#][^\s'"]*)?""",
        r"\1\2/[REDACTED]",
        detail,
        flags=re.IGNORECASE,
    )
