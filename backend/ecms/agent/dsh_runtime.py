"""Run deployment-owned Agent OS profiles through the pinned DSH CLI.

Python owns the host security boundary: it validates an installed profile artifact,
synchronizes its immutable bytes, passes a minimal child environment, enforces
bounded argv/output handling, and runs a pinned executable. DSH orchestrates
only the model invocation; it receives no ambient host tools or authority.
"""

from __future__ import annotations

import asyncio
import contextlib
import fcntl
import hashlib
import json
import logging
import os
import re
import shutil
import signal
import tempfile
import time
import uuid
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Final

import yaml
from yaml.nodes import SequenceNode

from ecms.agent_os.profiles.contracts import (
    DSHProfileSpec,
    RuntimeReadiness,
)

logger = logging.getLogger("ecms.agent.dsh_runtime")

__all__ = [
    "DSHExecutionError",
    "DSHExecutionResult",
    "DSHOutputLimitError",
    "DSHProfileNotFoundError",
    "DSHRuntime",
    "ba_clarify",
    "ba_design_team",
    "ba_finalize",
    "ba_understand",
]

_CHILD_ENV_KEYS: Final[frozenset[str]] = frozenset(
    {
        "ANTHROPIC_AUTH_TOKEN",
        "ANTHROPIC_BASE_URL",
        "CLAUDE_CODE_SESSION_ID",
        "HOME",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "PATH",
        "TEMP",
        "TMP",
        "TMPDIR",
        "TZ",
    }
)
_PASSTHROUGH_ENV_KEYS: Final[frozenset[str]] = frozenset(
    {
        "ANTHROPIC_AUTH_TOKEN",
        "ANTHROPIC_BASE_URL",
        "CLAUDE_CODE_SESSION_ID",
        "LANG",
        "LC_ALL",
        "LC_CTYPE",
        "PATH",
        "TZ",
    }
)
_EXPLICIT_ENV_KEYS: Final[frozenset[str]] = _CHILD_ENV_KEYS - {
    "HOME",
    "PATH",
    "TEMP",
    "TMP",
    "TMPDIR",
}
_PROFILE_ENV_KEYS: Final[frozenset[str]] = frozenset(
    {
        "ANTHROPIC_AUTH_TOKEN",
        "ANTHROPIC_BASE_URL",
        "CLAUDE_CODE_SESSION_ID",
    }
)
_GENERATED_PROFILE_ENV_KEYS: Final[frozenset[str]] = frozenset({"CLAUDE_CODE_SESSION_ID"})
_SECRET_MARKERS: Final[tuple[str, ...]] = (
    "TOKEN",
    "API_KEY",
    "PASSWORD",
    "SECRET",
    "SESSION_ID",
    "BASE_URL",
)
_PROFILE_NAME_RE: Final[re.Pattern[str]] = re.compile(r"[a-z0-9][a-z0-9-]{0,63}\Z")
_STREAM_CHUNK_BYTES: Final[int] = 64 * 1024
_AUDIT_METADATA_MAX_BYTES: Final[int] = 256


class DSHExecutionError(Exception):
    """Raised when DSH cannot execute a task successfully."""


class DSHOutputLimitError(DSHExecutionError):
    """Raised when DSH emits more output than the configured execution budget."""


class DSHProfileNotFoundError(DSHExecutionError):
    """Raised when a selected DSH profile artifact is unavailable or malformed."""


@dataclass(frozen=True, slots=True)
class DSHExecutionResult:
    """Non-secret result returned by one real DSH CLI invocation."""

    output: str
    error: str | None = None
    return_code: int = 0
    duration_seconds: float = 0.0
    metadata: Mapping[str, str] = field(default_factory=dict)


class DSHRuntime:
    """Synchronize and invoke a host-selected DSH profile deterministically.

    The process boundary deliberately receives neither the parent process
    environment nor arbitrary caller metadata. Profile assets are copied into a
    content-addressed DSH state root, so a concurrent artifact update cannot alter
    an in-flight execution. The state-root lock protects first-time creation only;
    generated DSH assets remain scoped to the immutable profile fingerprint.
    """

    def __init__(
        self,
        profile: str | None = None,
        timeout: float | None = None,
        dsh_home: Path | None = None,
        env: Mapping[str, str] | None = None,
        dsh_executable: Path | str | None = None,
        profile_source: Path | None = None,
        *,
        profile_spec: DSHProfileSpec | None = None,
        max_task_bytes: int | None = None,
        max_command_bytes: int | None = None,
        max_stdout_bytes: int | None = None,
        max_stderr_bytes: int | None = None,
        shutdown_grace_seconds: float | None = None,
        profile_lock_timeout_seconds: float | None = None,
    ) -> None:
        """Initialize the constrained DSH subprocess boundary.

        ``profile_spec`` is required and identifies the deployment-owned
        artifact. ``profile`` and ``profile_source`` only verify compatibility for
        migrating call sites; they never resolve an artifact or select shared state.
        """
        self._repo_root = Path(__file__).resolve().parents[3]
        self._integration_root = self._repo_root / "packages" / "dsh-integration"
        if profile_spec is None:
            raise ValueError("DSHRuntime requires a deployment-owned DSHProfileSpec")
        if profile is not None and profile != profile_spec.profile_id:
            raise ValueError(
                "profile and profile_spec.profile_id must match when both are supplied"
            )
        if profile_source is not None and profile_source != profile_spec.asset_root:
            raise ValueError("profile_source must be declared by profile_spec.asset_root")
        self.profile_spec = profile_spec
        self.profile = self.profile_spec.profile_id
        self._profile_source = self.profile_spec.asset_root
        self._validate_profile_environment_contract()

        budget = self.profile_spec.execution_budget
        self.timeout = _positive_float("timeout", timeout, budget.timeout_seconds)
        self.max_task_bytes = _positive_int("max_task_bytes", max_task_bytes, budget.max_task_bytes)
        self.max_command_bytes = _positive_int(
            "max_command_bytes", max_command_bytes, budget.max_command_bytes
        )
        self.max_stdout_bytes = _positive_int(
            "max_stdout_bytes", max_stdout_bytes, budget.max_stdout_bytes
        )
        self.max_stderr_bytes = _positive_int(
            "max_stderr_bytes", max_stderr_bytes, budget.max_stderr_bytes
        )
        self.shutdown_grace_seconds = _positive_float(
            "shutdown_grace_seconds", shutdown_grace_seconds, budget.shutdown_grace_seconds
        )
        self.profile_lock_timeout_seconds = _positive_float(
            "profile_lock_timeout_seconds",
            profile_lock_timeout_seconds,
            budget.profile_lock_timeout_seconds,
        )
        if self.max_command_bytes < self.max_task_bytes:
            raise ValueError("max_command_bytes must be at least max_task_bytes")

        supplied_env = dict(env or {})
        unsupported = sorted(set(supplied_env) - _EXPLICIT_ENV_KEYS)
        if unsupported:
            raise ValueError("DSH environment contains unsupported keys: " + ", ".join(unsupported))
        if any(
            not isinstance(key, str) or not isinstance(value, str)
            for key, value in supplied_env.items()
        ):
            raise ValueError("DSH environment keys and values must be strings")

        self.dsh_home = (dsh_home or Path.home() / ".dsh").expanduser()
        self.env = supplied_env
        self._active_profile_fingerprint: str | None = None
        self.dsh_executable = self._resolve_dsh_executable(dsh_executable)

    def _validate_profile_environment_contract(self) -> None:
        """Allow only application-approved child environment names in profile specs."""
        requested = set(self.profile_spec.required_environment).union(
            self.profile_spec.generated_environment
        )
        unsupported = requested.difference(_PROFILE_ENV_KEYS)
        if unsupported:
            raise ValueError(
                "DSH profile requests unsupported environment names: "
                + ", ".join(sorted(unsupported))
            )
        generated_unsupported = set(self.profile_spec.generated_environment).difference(
            _GENERATED_PROFILE_ENV_KEYS
        )
        if generated_unsupported:
            raise ValueError(
                "DSH profile requests unsupported generated environment names: "
                + ", ".join(sorted(generated_unsupported))
            )

    def _resolve_dsh_executable(self, explicit: Path | str | None) -> Path:
        """Resolve a direct CLI executable, never PATH lookup or package download."""
        repository_candidate = self._integration_root / "node_modules" / ".bin" / "dsh"
        candidate = Path(explicit).expanduser() if explicit is not None else repository_candidate
        if explicit is not None and not candidate.is_absolute():
            raise DSHExecutionError("deployment-pinned DSH executable override must be absolute")
        resolved = candidate.resolve(strict=False)
        if not resolved.is_file() or not os.access(resolved, os.X_OK):
            raise DSHExecutionError(
                "DSH CLI not found. Install the pinned integration dependency with "
                f"pnpm install in {self._integration_root}; expected {repository_candidate}."
            )
        if explicit is None and not _path_is_within(resolved, self._integration_root.resolve()):
            raise DSHExecutionError(
                "repository-managed DSH executable resolves outside the pinned "
                "integration dependency"
            )
        return resolved

    @property
    def _profile_state_parent(self) -> Path:
        """Return the root holding immutable state homes for this profile identity."""
        identity = self.profile_spec.identity.encode("utf-8")
        identity_digest = hashlib.sha256(identity).hexdigest()[:16]
        return self.dsh_home / "aegisos-profile-states" / self.profile / identity_digest

    @property
    def _profile_lock_path(self) -> Path:
        """Return the inter-process synchronization lock for profile-state creation."""
        return self._profile_state_parent / ".aegisos.lock"

    def _execution_home(self, fingerprint: str) -> Path:
        """Return the DSH_HOME that contains one immutable profile artifact version."""
        return self._profile_state_parent / fingerprint

    def _profile_dir_for(self, fingerprint: str) -> Path:
        """Return DSH's profile directory inside one versioned execution home."""
        return self._execution_home(fingerprint) / "profiles" / self.profile

    @property
    def _profile_dir(self) -> Path:
        """Return the active profile directory, or the current authored version path."""
        fingerprint = self._active_profile_fingerprint or self.profile_fingerprint
        return self._profile_dir_for(fingerprint)

    def _authored_profile_snapshot(self) -> tuple[str, dict[str, bytes]]:
        """Read and validate the exact authored bytes defining one execution version."""
        source = self._profile_source.resolve(strict=False)
        if not source.exists():
            raise DSHProfileNotFoundError(
                f"DSH profile source does not exist for {self.profile_spec.identity}: {source}"
            )
        if not source.is_dir():
            raise DSHProfileNotFoundError(f"DSH profile source is not a directory: {source}")

        assets: dict[str, bytes] = {}
        missing: list[str] = []
        for asset in self.profile_spec.required_assets:
            path = source / asset
            resolved = path.resolve(strict=False)
            if not _path_is_within(resolved, source) or not resolved.is_file():
                missing.append(asset)
                continue
            try:
                assets[asset] = resolved.read_bytes()
            except OSError as error:
                raise DSHProfileNotFoundError(
                    f"DSH profile asset is unreadable for {self.profile_spec.identity}: {asset}"
                ) from error
        if missing:
            raise DSHProfileNotFoundError(
                f"DSH profile source '{self.profile_spec.identity}' is missing required assets: "
                f"{', '.join(missing)}"
            )

        self._validate_profile_asset_content(assets)
        digest = hashlib.sha256()
        digest.update(b"aegisos-dsh-profile-v2\0")
        digest.update(self.profile_spec.fingerprint_payload())
        digest.update(b"\0")
        for asset in self.profile_spec.required_assets:
            digest.update(asset.encode("utf-8"))
            digest.update(b"\0")
            digest.update(assets[asset])
            digest.update(b"\0")
        return digest.hexdigest(), assets

    def _validate_profile_asset_content(self, assets: Mapping[str, bytes]) -> None:
        """Validate the DSH manifest and Cordis patch before a process can launch."""
        try:
            manifest = json.loads(assets["package.json"].decode("utf-8"))
        except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as error:
            raise DSHProfileNotFoundError(
                f"DSH profile {self.profile_spec.identity} has an invalid package.json"
            ) from error
        try:
            bundles = manifest["dsh"]["profile"]["bundles"]
        except (KeyError, TypeError) as error:
            raise DSHProfileNotFoundError(
                f"DSH profile {self.profile_spec.identity} package.json must "
                "declare dsh.profile.bundles"
            ) from error
        if (
            not isinstance(bundles, list)
            or not bundles
            or any(not isinstance(bundle, str) or not bundle.strip() for bundle in bundles)
        ):
            raise DSHProfileNotFoundError(
                f"DSH profile {self.profile_spec.identity} dsh.profile.bundles must be non-empty"
            )
        absent_bundles = set(self.profile_spec.required_bundles).difference(bundles)
        if absent_bundles:
            raise DSHProfileNotFoundError(
                f"DSH profile {self.profile_spec.identity} is missing required bundles: "
                + ", ".join(sorted(absent_bundles))
            )
        try:
            patch_document = yaml.compose(assets["cordis.patch.yml"].decode("utf-8"))
        except (KeyError, UnicodeDecodeError, yaml.YAMLError) as error:
            raise DSHProfileNotFoundError(
                f"DSH profile {self.profile_spec.identity} has an invalid cordis.patch.yml"
            ) from error
        if not isinstance(patch_document, SequenceNode):
            raise DSHProfileNotFoundError(
                f"DSH profile {self.profile_spec.identity} cordis.patch.yml must be a YAML sequence"
            )

    @property
    def profile_fingerprint(self) -> str:
        """Return the digest of the selected profile artifact and declared contract."""
        fingerprint, _ = self._authored_profile_snapshot()
        return fingerprint

    def preflight(self) -> RuntimeReadiness:
        """Perform side-effect-free, non-secret runtime readiness validation.

        This checks executable availability, profile artifact integrity, and declared
        environment values without creating profile homes, touching DSH state, or
        invoking a model.
        """
        try:
            if not self.dsh_executable.is_file() or not os.access(self.dsh_executable, os.X_OK):
                return RuntimeReadiness(
                    ready=False,
                    profile_identity=self.profile_spec.identity,
                    reason_code="dsh_executable_unavailable",
                )
            fingerprint, _ = self._authored_profile_snapshot()
            self._child_environment_values()
        except DSHProfileNotFoundError:
            return RuntimeReadiness(
                ready=False,
                profile_identity=self.profile_spec.identity,
                reason_code="profile_artifact_invalid",
            )
        except DSHExecutionError:
            return RuntimeReadiness(
                ready=False,
                profile_identity=self.profile_spec.identity,
                reason_code="profile_environment_invalid",
            )
        except OSError:
            return RuntimeReadiness(
                ready=False,
                profile_identity=self.profile_spec.identity,
                reason_code="dsh_dependency_unavailable",
            )
        return RuntimeReadiness(
            ready=True,
            profile_identity=self.profile_spec.identity,
            profile_fingerprint=fingerprint,
        )

    def require_ready(self) -> RuntimeReadiness:
        """Return readiness or fail closed before a request can execute DSH work."""
        readiness = self.preflight()
        if not readiness.ready:
            raise DSHExecutionError(
                f"DSH profile {self.profile_spec.identity} is unavailable: {readiness.reason_code}"
            )
        return readiness

    @contextmanager
    def _profile_lock(self) -> Iterator[None]:
        """Hold an inter-process lock while publishing an immutable profile state."""
        self._profile_lock_path.parent.mkdir(parents=True, exist_ok=True)
        with self._profile_lock_path.open("a+", encoding="utf-8") as lock_file:
            deadline = time.monotonic() + self.profile_lock_timeout_seconds
            while True:
                try:
                    fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() >= deadline:
                        raise DSHExecutionError(
                            f"timed out waiting for DSH profile lock: {self._profile_lock_path}"
                        ) from None
                    time.sleep(0.05)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    @staticmethod
    def _write_synced_asset(target: Path, content: bytes) -> None:
        """Durably write one authored profile asset into an unpublished state home."""
        with target.open("wb") as output:
            output.write(content)
            output.flush()
            os.fsync(output.fileno())

    def _validate_profile_assets(self, profile_dir: Path, assets: Mapping[str, bytes]) -> None:
        """Verify a published state equals its content-addressed profile artifact."""
        for asset, expected in assets.items():
            target = profile_dir / asset
            if not target.is_file() or target.read_bytes() != expected:
                raise DSHProfileNotFoundError(
                    f"DSH profile state is inconsistent for '{self.profile_spec.identity}': {asset}"
                )
        self._validate_profile_asset_content(assets)

    def _synchronize_profile(self) -> str:
        """Atomically publish validated assets to one fingerprinted DSH state root."""
        with self._profile_lock():
            fingerprint, assets = self._authored_profile_snapshot()
            target_home = self._execution_home(fingerprint)
            target_profile = self._profile_dir_for(fingerprint)
            if target_home.exists():
                self._validate_profile_assets(target_profile, assets)
            else:
                temporary_home = Path(
                    tempfile.mkdtemp(
                        prefix=f".{fingerprint}.",
                        dir=self._profile_state_parent,
                    )
                )
                try:
                    temporary_profile = temporary_home / "profiles" / self.profile
                    temporary_profile.mkdir(parents=True)
                    for asset in self.profile_spec.required_assets:
                        self._write_synced_asset(temporary_profile / asset, assets[asset])
                    _fsync_directory(temporary_profile)
                    _fsync_directory(temporary_profile.parent)
                    _fsync_directory(temporary_home)
                    temporary_home.replace(target_home)
                    _fsync_directory(target_home.parent)
                except BaseException:
                    shutil.rmtree(temporary_home, ignore_errors=True)
                    raise

            self._active_profile_fingerprint = fingerprint
            return fingerprint

    def _validate_profile_exists(self, fingerprint: str | None = None) -> None:
        """Verify a synchronized profile state contains validated required assets."""
        selected = fingerprint or self._active_profile_fingerprint
        if selected is None:
            raise DSHProfileNotFoundError(
                "DSH profile state is unavailable until the selected artifact is synchronized"
            )
        profile_dir = self._profile_dir_for(selected)
        assets: dict[str, bytes] = {}
        for asset in self.profile_spec.required_assets:
            target = profile_dir / asset
            if not target.is_file():
                raise DSHProfileNotFoundError(
                    f"DSH profile '{self.profile_spec.identity}' is not installed at {profile_dir}."
                )
            assets[asset] = target.read_bytes()
        self._validate_profile_assets(profile_dir, assets)

    def _child_environment_values(self) -> dict[str, str]:
        """Build and validate profile-requested values without creating directories."""
        environment = {
            key: value for key, value in os.environ.items() if key in _PASSTHROUGH_ENV_KEYS
        }
        environment.update(self.env)
        for name in self.profile_spec.required_environment:
            value = environment.get(name, "").strip()
            if not value:
                raise DSHExecutionError(
                    f"{name} is required for DSH profile {self.profile_spec.identity}"
                )
            environment[name] = value
        for name in self.profile_spec.generated_environment:
            existing = environment.get(name, "").strip()
            environment[name] = existing or _generated_profile_environment_value(name)
        return environment

    def _build_env(self, *, execution_home: Path | None = None) -> dict[str, str]:
        """Build the explicit child environment after profile synchronization."""
        environment = self._child_environment_values()
        if execution_home is None:
            fingerprint = self._active_profile_fingerprint or self.profile_fingerprint
            execution_home = self._execution_home(fingerprint)
        execution_home.mkdir(parents=True, exist_ok=True)
        temporary_home = execution_home / "tmp"
        temporary_home.mkdir(exist_ok=True)
        environment["DSH_HOME"] = str(execution_home)
        environment["HOME"] = str(execution_home)
        environment["TMPDIR"] = str(temporary_home)
        environment["TMP"] = str(temporary_home)
        environment["TEMP"] = str(temporary_home)
        return environment

    @staticmethod
    def _redact(message: str, environment: Mapping[str, str]) -> str:
        """Prevent configured credentials and session identifiers from crossing logs."""
        redacted = message
        secret_values = {
            value
            for key, value in environment.items()
            if value and any(marker in key.upper() for marker in _SECRET_MARKERS)
        }
        for secret in sorted(secret_values, key=len, reverse=True):
            redacted = redacted.replace(secret, "[REDACTED]")
        return redacted

    def _validate_command_budget(self, command: list[str], task: str) -> None:
        """Reject a task that cannot safely travel through DSH's argv interface."""
        task_size = len(task.encode("utf-8"))
        command_size = sum(len(argument.encode("utf-8")) + 1 for argument in command)
        if task_size > self.max_task_bytes:
            raise DSHExecutionError(
                f"DSH task is {task_size} bytes and exceeds {self.max_task_bytes}-byte task budget"
            )
        if command_size > self.max_command_bytes:
            raise DSHExecutionError(
                "DSH command is "
                f"{command_size} bytes and exceeds {self.max_command_bytes}-byte argv budget"
            )

    async def _read_bounded(
        self,
        stream: asyncio.StreamReader,
        *,
        limit: int,
        stream_name: str,
    ) -> bytes:
        """Read one process stream while enforcing a strict captured-byte maximum."""
        chunks: list[bytes] = []
        total = 0
        while chunk := await stream.read(_STREAM_CHUNK_BYTES):
            total += len(chunk)
            if total > limit:
                raise DSHOutputLimitError(
                    f"DSH {stream_name} exceeded the {limit}-byte output budget"
                )
            chunks.append(chunk)
        return b"".join(chunks)

    async def _terminate_process_group(self, process: asyncio.subprocess.Process) -> None:
        """Terminate all DSH descendants, escalating from SIGTERM to SIGKILL."""
        if os.name == "posix":
            with contextlib.suppress(ProcessLookupError):
                os.killpg(process.pid, signal.SIGTERM)
            deadline = time.monotonic() + self.shutdown_grace_seconds
            # Process groups provide no awaitable exit notification; bounded polling
            # confirms descendant reaping before we escalate or return control.
            while (  # noqa: ASYNC110
                _process_group_exists(process.pid) and time.monotonic() < deadline
            ):
                await asyncio.sleep(0.05)
            if _process_group_exists(process.pid):
                with contextlib.suppress(ProcessLookupError):
                    os.killpg(process.pid, signal.SIGKILL)
                kill_deadline = time.monotonic() + self.shutdown_grace_seconds
                while (  # noqa: ASYNC110
                    _process_group_exists(process.pid) and time.monotonic() < kill_deadline
                ):
                    await asyncio.sleep(0.05)
        elif process.returncode is None:  # pragma: no cover - Windows is not deployment target.
            with contextlib.suppress(ProcessLookupError):
                process.terminate()
            try:
                await asyncio.wait_for(process.wait(), timeout=self.shutdown_grace_seconds)
            except TimeoutError:
                with contextlib.suppress(ProcessLookupError):
                    process.kill()

        if process.returncode is None:
            await process.wait()

    async def _execute_bounded_process(
        self,
        command: list[str],
        environment: Mapping[str, str],
    ) -> tuple[bytes, bytes, int]:
        """Run the DSH process and collect bounded output with cancellation safety."""
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=dict(environment),
                start_new_session=os.name == "posix",
            )
        except FileNotFoundError as exc:
            raise DSHExecutionError(f"DSH CLI not found: {self.dsh_executable}") from exc

        if process.stdout is None or process.stderr is None:
            await self._terminate_process_group(process)
            raise DSHExecutionError("DSH process did not expose required output streams")
        stdout_task = asyncio.create_task(
            self._read_bounded(process.stdout, limit=self.max_stdout_bytes, stream_name="stdout")
        )
        stderr_task = asyncio.create_task(
            self._read_bounded(process.stderr, limit=self.max_stderr_bytes, stream_name="stderr")
        )
        process_task = asyncio.create_task(process.wait())
        operation = asyncio.gather(stdout_task, stderr_task, process_task)
        try:
            stdout, stderr, return_code = await asyncio.wait_for(
                asyncio.shield(operation), timeout=self.timeout
            )
            return stdout, stderr, return_code
        except TimeoutError as exc:
            await self._terminate_process_group(process)
            raise DSHExecutionError(f"DSH execution timed out after {self.timeout}s") from exc
        except DSHOutputLimitError:
            await self._terminate_process_group(process)
            raise
        except asyncio.CancelledError:
            cleanup = asyncio.create_task(self._terminate_process_group(process))
            while not cleanup.done():
                try:
                    await asyncio.shield(cleanup)
                except asyncio.CancelledError:
                    continue
            await cleanup
            raise
        finally:
            if not operation.done():
                operation.cancel()
            await asyncio.gather(operation, return_exceptions=True)

    @staticmethod
    def _audit_metadata(metadata: Mapping[str, str] | None) -> dict[str, str]:
        """Return digested, bounded caller metadata without retaining raw values."""
        if metadata is None:
            return {}
        digests: dict[str, str] = {}
        for key, value in metadata.items():
            if (
                not isinstance(key, str)
                or not key.isidentifier()
                or any(marker in key.upper() for marker in _SECRET_MARKERS)
            ):
                raise ValueError(f"DSH metadata key is not permitted: {key!r}")
            if not isinstance(value, str):
                raise ValueError(f"DSH metadata value for {key!r} must be a string")
            if len(value.encode("utf-8")) > _AUDIT_METADATA_MAX_BYTES:
                raise ValueError(
                    f"DSH metadata value for {key!r} exceeds the "
                    f"{_AUDIT_METADATA_MAX_BYTES}-byte limit"
                )
            digests[f"context_{key}_sha256"] = hashlib.sha256(value.encode("utf-8")).hexdigest()
        return digests

    async def run_agent_task(
        self,
        task: str,
        agent_id: str | None = None,
        project_id: str | None = None,
        metadata: Mapping[str, str] | None = None,
    ) -> DSHExecutionResult:
        """Execute one bounded task through the direct pinned DSH CLI."""
        if not isinstance(task, str) or not task.strip():
            raise ValueError("task must not be empty")

        profile_fingerprint = await asyncio.to_thread(self._synchronize_profile)
        await asyncio.to_thread(self._validate_profile_exists, profile_fingerprint)
        execution_home = self._execution_home(profile_fingerprint)
        environment = self._build_env(execution_home=execution_home)
        command = [str(self.dsh_executable), "--profile", self.profile, task]
        self._validate_command_budget(command, task)
        audit_metadata = self._audit_metadata(metadata)
        logger.info("[DSH] Running bounded task with profile '%s'", self.profile_spec.identity)
        started = time.monotonic()
        try:
            stdout, stderr, return_code = await self._execute_bounded_process(command, environment)
        except DSHOutputLimitError as exc:
            raise DSHExecutionError(self._redact(str(exc), environment)) from exc

        duration = time.monotonic() - started
        output = stdout.decode("utf-8", errors="replace").strip()
        error_output = stderr.decode("utf-8", errors="replace").strip()
        if return_code != 0:
            detail = self._redact(error_output or output or "no diagnostic output", environment)
            logger.error("[DSH] Execution failed with code %s", return_code)
            raise DSHExecutionError(f"DSH execution failed (code {return_code}): {detail}")

        safe_metadata = {
            "profile": self.profile,
            "profile_identity": self.profile_spec.identity,
            "profile_fingerprint": profile_fingerprint,
            "dsh_executable": str(self.dsh_executable),
            "run_id": uuid.uuid4().hex,
            **audit_metadata,
        }
        if agent_id:
            safe_metadata["agent_ref"] = hashlib.sha256(agent_id.encode("utf-8")).hexdigest()
        if project_id:
            safe_metadata["project_ref"] = hashlib.sha256(project_id.encode("utf-8")).hexdigest()

        logger.info("[DSH] Execution completed in %.2fs", duration)
        return DSHExecutionResult(
            output=output,
            error=self._redact(error_output, environment) if error_output else None,
            return_code=return_code,
            duration_seconds=duration,
            metadata=safe_metadata,
        )

    async def run_with_context(
        self,
        task: str,
        knowledge_context: str,
        conversation: list[dict[str, Any]] | None = None,
        **kwargs: Any,
    ) -> DSHExecutionResult:
        """Run legacy caller-assembled context; production uses profile renderers."""
        sections = [task]
        if knowledge_context:
            sections.append(f"## Relevant Knowledge\n\n{knowledge_context}")
        if conversation:
            history = "\n".join(
                f"{message.get('role', 'user')}: {message.get('content', '')}"
                for message in conversation
            )
            sections.append(f"## Conversation History\n\n{history}")
        return await self.run_agent_task("\n\n".join(sections), **kwargs)

    def to_dict(self) -> dict[str, Any]:
        """Serialize non-secret runtime configuration for diagnostics."""
        return {
            "profile": self.profile,
            "profile_identity": self.profile_spec.identity,
            "profile_fingerprint": self.profile_fingerprint,
            "timeout": self.timeout,
            "dsh_home": str(self.dsh_home),
            "dsh_executable": str(self.dsh_executable),
            "max_task_bytes": self.max_task_bytes,
            "max_command_bytes": self.max_command_bytes,
            "max_stdout_bytes": self.max_stdout_bytes,
            "max_stderr_bytes": self.max_stderr_bytes,
            "env_keys": sorted(self.env),
        }


def _positive_int(name: str, value: int | None, default: int) -> int:
    """Resolve an optional positive integer override."""
    selected = default if value is None else value
    if not isinstance(selected, int) or isinstance(selected, bool) or selected <= 0:
        raise ValueError(f"{name} must be positive")
    return selected


def _positive_float(name: str, value: float | None, default: float) -> float:
    """Resolve an optional positive numeric override."""
    selected = default if value is None else value
    if not isinstance(selected, (int, float)) or isinstance(selected, bool) or selected <= 0:
        raise ValueError(f"{name} must be positive")
    return float(selected)


def _generated_profile_environment_value(name: str) -> str:
    """Generate the tiny allowlisted set of non-secret per-run child variables."""
    if name == "CLAUDE_CODE_SESSION_ID":
        return str(uuid.uuid4())
    raise DSHExecutionError(f"unsupported generated DSH environment variable: {name}")


def _path_is_within(path: Path, parent: Path) -> bool:
    """Return whether a resolved path remains within a resolved parent directory."""
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _fsync_directory(directory: Path) -> None:
    """Best-effort directory durability for a newly published profile state."""
    try:
        descriptor = os.open(directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    except OSError:  # pragma: no cover - filesystem-specific capability.
        return
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _process_group_exists(process_group_id: int) -> bool:
    """Return whether a POSIX DSH process group still contains any process."""
    try:
        os.killpg(process_group_id, 0)
    except ProcessLookupError:
        return False
    return True


# Compatibility imports preserve old import paths while BA behavior lives in its
# own module. They intentionally resolve lazily to avoid a runtime/BA import cycle.
def _json_object(stage: str, output: str) -> dict[str, Any]:
    """Compatibility alias for BA-only JSON stage validation."""
    from ecms.agent.ba.dsh_compat import _json_object as implementation

    return implementation(stage, output)


async def ba_understand(source_text: str, **kwargs: Any) -> str:
    """Compatibility alias for the BA-only DSH understand helper."""
    from ecms.agent.ba.dsh_compat import ba_understand as implementation

    return await implementation(source_text, **kwargs)


async def _run_structured_stage(
    stage: str,
    task: str,
    validator: Any,
    **kwargs: Any,
) -> Any:
    """Compatibility alias for BA-only structured-stage validation."""
    from ecms.agent.ba.dsh_compat import _run_structured_stage as implementation

    return await implementation(stage, task, validator, **kwargs)


async def ba_clarify(source_text: str, **kwargs: Any) -> dict[str, str]:
    """Compatibility alias for the BA-only DSH clarify helper."""
    from ecms.agent.ba.dsh_compat import ba_clarify as implementation

    return await implementation(source_text, **kwargs)


async def ba_finalize(
    source_text: str,
    conversation: list[dict[str, Any]],
    **kwargs: Any,
) -> dict[str, Any]:
    """Compatibility alias for the BA-only DSH finalize helper."""
    from ecms.agent.ba.dsh_compat import ba_finalize as implementation

    return await implementation(source_text, conversation, **kwargs)


async def ba_design_team(
    requirements: dict[str, Any],
    model_ids: list[str],
    tool_names: list[str],
    org_member_ids: list[str] | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """Compatibility alias for the BA-only DSH team-design helper."""
    from ecms.agent.ba.dsh_compat import ba_design_team as implementation

    return await implementation(
        requirements,
        model_ids,
        tool_names,
        org_member_ids,
        **kwargs,
    )
