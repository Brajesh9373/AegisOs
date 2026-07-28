import asyncio
import hashlib
import os
import subprocess
import tempfile
from collections.abc import AsyncIterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse

from legacy_ecms.core.uko import UKOMetadata, UKORelationship, UKOType, UniversalKnowledgeObject
from legacy_ecms.providers.base import KnowledgeProvider, ProviderStatus


@dataclass(frozen=True)
class RemoteGitRepository:
    repo_url: str
    access_token: str
    platform: str
    username: str
    branch: str | None
    clone_path: Path

    @property
    def resource_id(self) -> str:
        return self.repo_url


class GitProvider(KnowledgeProvider):
    """Git repository provider for local, GitHub, and Bitbucket repositories.

    Resource IDs may be local filesystem paths or remote repository URLs. Remote
    credentials are used only for Git transport and are never stored in UKOs.
    """

    provider_name = "git"
    provider_version = "0.2.0"

    def __init__(
        self,
        roots: list[Path] | None = None,
        clone_root: Path | str | None = None,
        include_extensions: set[str] | None = None,
    ) -> None:
        self.roots = [root.resolve() for root in roots] if roots else []
        self.clone_root = Path(clone_root or "./data/repos").resolve()
        self.include_extensions = include_extensions or {
            ".py", ".md", ".markdown", ".json", ".sql",
            ".js", ".jsx", ".ts", ".tsx", ".css", ".scss", ".html",
            ".yml", ".yaml", ".toml", ".ini", ".cfg",
        }
        self._remotes: dict[str, RemoteGitRepository] = {}
        self._authenticated = False
        self._sync_counts: dict[str, int] = {}
        self._last_sync_at: dict[str, datetime] = {}
        self._errors: dict[str, list[str]] = {}

    async def authenticate(self, credentials: dict[str, Any]) -> bool:
        root_values = credentials.get("roots")
        if root_values:
            self.roots = [Path(value).resolve() for value in root_values]
        clone_root = credentials.get("clone_root")
        if clone_root:
            self.clone_root = Path(clone_root).resolve()

        repo_url = credentials.get("repo_url")
        access_token = credentials.get("access_token") or ""
        if repo_url:
            remote = self._build_remote_repository(
                repo_url=repo_url,
                access_token=access_token,
                platform=credentials.get("platform"),
                branch=credentials.get("branch"),
                username=credentials.get("username"),
            )
            self._remotes[remote.resource_id] = remote

        local_ok = all(root.exists() and root.is_dir() for root in self.roots) if self.roots else False
        self._authenticated = local_ok or bool(self._remotes)
        return self._authenticated

    async def discover(self) -> list[str]:
        resources: list[str] = list(self._remotes)
        for root in self.roots:
            if (root / ".git").exists():
                resources.append(str(root))
                continue
            for candidate in root.rglob(".git"):
                if candidate.is_dir():
                    resources.append(str(candidate.parent.resolve()))
        return sorted(set(resources))

    async def sync(
        self,
        resource_id: str,
        since: datetime | None = None,
    ) -> AsyncIterator[UniversalKnowledgeObject]:
        repo_path = await asyncio.to_thread(self._resolve_resource_to_repo_path, resource_id)
        status_key = self._status_key(resource_id, repo_path)
        count = 0
        errors: list[str] = []
        try:
            for uko in await asyncio.to_thread(self._collect_file_ukos, repo_path, resource_id):
                count += 1
                yield uko
            for uko in await asyncio.to_thread(self._collect_commit_ukos, repo_path, since, resource_id):
                count += 1
                yield uko
        except Exception as exc:
            errors.append(str(exc))
            raise
        finally:
            self._sync_counts[status_key] = count
            self._last_sync_at[status_key] = datetime.now(UTC)
            self._errors[status_key] = errors

    async def validate(self) -> bool:
        if self._remotes:
            return True
        if not self.roots:
            return False
        return all(root.exists() and root.is_dir() for root in self.roots)

    async def get_status(self, resource_id: str) -> ProviderStatus:
        resource = resource_id if self._is_url(resource_id) else str(Path(resource_id).resolve())
        return ProviderStatus(
            provider_name=self.provider_name,
            resource_id=resource,
            is_authenticated=self._authenticated,
            last_sync_at=self._last_sync_at.get(resource),
            objects_synced=self._sync_counts.get(resource, 0),
            errors=self._errors.get(resource, []),
        )

    def remote_for(self, resource_id: str) -> RemoteGitRepository:
        remote = self._remotes.get(resource_id)
        if remote is None:
            raise KeyError(f"No authenticated remote registered for {resource_id}")
        return remote

    def _collect_file_ukos(
        self,
        repo_path: Path,
        resource_id: str | None = None,
    ) -> list[UniversalKnowledgeObject]:
        now = datetime.now(UTC)
        ukos: list[UniversalKnowledgeObject] = []
        for path in sorted(repo_path.rglob("*")):
            if not path.is_file() or self._is_ignored(path, repo_path):
                continue
            if path.suffix.lower() not in self.include_extensions:
                continue

            relative_path = path.relative_to(repo_path).as_posix()
            content = path.read_text(encoding="utf-8", errors="replace")
            modified_at = datetime.fromtimestamp(path.stat().st_mtime, tz=UTC)
            uko_type = self._uko_type_for_path(path)
            ukos.append(
                UniversalKnowledgeObject(
                    id=f"git:file:{repo_path.name}:{relative_path}",
                    type=uko_type,
                    name=relative_path,
                    content=content,
                    metadata=UKOMetadata(
                        source=self.provider_name,
                        source_id=relative_path,
                        source_url=resource_id if resource_id and self._is_url(resource_id) else None,
                        created_at=modified_at,
                        modified_at=max(modified_at, now) if modified_at > now else modified_at,
                        tags=[path.suffix.lower().lstrip(".")],
                    ),
                    raw_data={
                        "repo_path": str(repo_path),
                        "repo_url": resource_id if resource_id and self._is_url(resource_id) else None,
                        "path": relative_path,
                        "size_bytes": path.stat().st_size,
                    },
                )
            )
        return ukos

    def _collect_commit_ukos(
        self,
        repo_path: Path,
        since: datetime | None = None,
        resource_id: str | None = None,
    ) -> list[UniversalKnowledgeObject]:
        args = [
            "git",
            "-c",
            f"safe.directory={repo_path}",
            "-C",
            str(repo_path),
            "log",
            "--pretty=format:%H%x1f%an%x1f%ae%x1f%aI%x1f%s",
            "--name-only",
        ]
        if since is not None:
            args.insert(-2, f"--since={since.isoformat()}")

        result = subprocess.run(args, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            return []

        commits: list[UniversalKnowledgeObject] = []
        current: dict[str, Any] | None = None
        files: list[str] = []

        def flush() -> None:
            if current is None:
                return
            committed_at = datetime.fromisoformat(current["committed_at"].replace("Z", "+00:00"))
            commits.append(
                UniversalKnowledgeObject(
                    id=f"git:commit:{repo_path.name}:{current['sha']}",
                    type=UKOType.COMMIT,
                    name=current["subject"],
                    content=current["subject"],
                    metadata=UKOMetadata(
                        source=self.provider_name,
                        source_id=current["sha"],
                        source_url=resource_id if resource_id and self._is_url(resource_id) else None,
                        created_at=committed_at,
                        modified_at=committed_at,
                        authors=[current["author_name"]],
                        tags=["commit"],
                    ),
                    relationships=[
                        UKORelationship(
                            target_id=f"git:file:{repo_path.name}:{file_path}",
                            relationship="modified",
                            target_type=UKOType.FILE,
                        )
                        for file_path in files
                    ],
                    raw_data={
                        **current,
                        "files": list(files),
                        "repo_path": str(repo_path),
                        "repo_url": resource_id if resource_id and self._is_url(resource_id) else None,
                    },
                )
            )

        for line in result.stdout.splitlines():
            if "\x1f" in line:
                flush()
                sha, author_name, author_email, committed_at, subject = line.split("\x1f", 4)
                current = {
                    "sha": sha,
                    "author_name": author_name,
                    "author_email": author_email,
                    "committed_at": committed_at,
                    "subject": subject,
                }
                files = []
            elif line.strip():
                files.append(line.strip())
        flush()
        return commits

    def _is_ignored(self, path: Path, repo_path: Path) -> bool:
        relative_parts = path.relative_to(repo_path).parts
        return any(part in {".git", "__pycache__", ".venv", ".uv-cache"} for part in relative_parts)

    def _uko_type_for_path(self, path: Path) -> UKOType:
        if path.suffix.lower() in {".md", ".markdown"}:
            return UKOType.DOCUMENT
        return UKOType.FILE

    def _resolve_resource_to_repo_path(self, resource_id: str) -> Path:
        if self._is_url(resource_id):
            remote = self._remotes.get(resource_id)
            if remote is None:
                raise ValueError("Remote Git resource was not authenticated")
            return self._ensure_remote_repo(remote)
        return Path(resource_id).resolve()

    def _ensure_remote_repo(self, remote: RemoteGitRepository) -> Path:
        remote.clone_path.parent.mkdir(parents=True, exist_ok=True)
        clone_url = self._clone_url_for_auth(remote) if remote.access_token else remote.repo_url
        if (remote.clone_path / ".git").exists():
            self._run_authenticated_git(
                self._repo_git_command(remote.clone_path, "remote", "set-url", "origin", clone_url),
                remote,
            )
            self._run_authenticated_git(
                self._repo_git_command(remote.clone_path, "fetch", "--prune", "origin"),
                remote,
            )
            if remote.branch:
                self._run_authenticated_git(
                    self._repo_git_command(remote.clone_path, "checkout", remote.branch),
                    remote,
                )
                self._run_authenticated_git(
                    self._repo_git_command(remote.clone_path, "pull", "--ff-only", "origin", remote.branch),
                    remote,
                )
            else:
                self._run_authenticated_git(
                    self._repo_git_command(remote.clone_path, "pull", "--ff-only"),
                    remote,
                )
        else:
            command = ["git", "clone"]
            if remote.branch:
                command.extend(["--branch", remote.branch])
            command.extend([clone_url, str(remote.clone_path)])
            self._run_authenticated_git(command, remote)
        return remote.clone_path

    def _repo_git_command(self, repo_path: Path, *args: str) -> list[str]:
        return ["git", "-c", f"safe.directory={repo_path}", "-C", str(repo_path), *args]

    def _run_authenticated_git(self, command: list[str], remote: RemoteGitRepository) -> None:
        with tempfile.TemporaryDirectory() as directory:
            askpass = Path(directory) / ("git-askpass.bat" if os.name == "nt" else "git-askpass.sh")
            if os.name == "nt":
                askpass.write_text(
                    "@echo off\n"
                    "echo %ECMS_GIT_ACCESS_TOKEN%\n",
                    encoding="utf-8",
                )
            else:
                askpass.write_text("#!/bin/sh\nprintf '%s\\n' \"$ECMS_GIT_ACCESS_TOKEN\"\n", encoding="utf-8")
                askpass.chmod(0o700)

            env = os.environ.copy()
            env["GIT_ASKPASS"] = str(askpass)
            env["ECMS_GIT_ACCESS_TOKEN"] = remote.access_token
            env["GIT_TERMINAL_PROMPT"] = "0"
            result = subprocess.run(command, capture_output=True, text=True, env=env, check=False)
            if result.returncode != 0:
                raise RuntimeError(self._sanitize_git_error(result.stderr or result.stdout, remote))

    def _build_remote_repository(
        self,
        repo_url: str,
        access_token: str,
        platform: str | None = None,
        branch: str | None = None,
        username: str | None = None,
    ) -> RemoteGitRepository:
        normalized_url, inferred_branch = self._normalize_repo_url(repo_url)
        detected_platform = platform or self._detect_platform(normalized_url)
        if detected_platform not in {"github", "bitbucket"}:
            raise ValueError("Only GitHub and Bitbucket repository URLs are supported")
        auth_username = username or ("x-access-token" if detected_platform == "github" else "x-token-auth")
        clone_path = self.clone_root / self._clone_directory_name(normalized_url)
        return RemoteGitRepository(
            repo_url=normalized_url,
            access_token=access_token,
            platform=detected_platform,
            username=auth_username,
            branch=branch or inferred_branch,
            clone_path=clone_path,
        )

    def _clone_url_for_auth(self, remote: RemoteGitRepository) -> str:
        parsed = urlparse(remote.repo_url)
        netloc = parsed.hostname or parsed.netloc
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"
        return urlunparse(
            (
                parsed.scheme,
                f"{remote.username}@{netloc}",
                parsed.path,
                "",
                "",
                "",
            )
        )

    def _normalize_repo_url(self, repo_url: str) -> tuple[str, str | None]:
        parsed = urlparse(repo_url)
        if parsed.scheme not in {"https", "http"}:
            raise ValueError("Remote Git repositories must use an HTTP(S) URL")
        if not parsed.hostname:
            raise ValueError("Remote Git repository URL must include a host")
        netloc = parsed.hostname.lower()
        if parsed.port:
            netloc = f"{netloc}:{parsed.port}"
        path, branch = self._repo_path_and_branch(parsed.hostname.lower(), parsed.path)
        if not path.endswith(".git"):
            path = f"{path}.git"
        return urlunparse(("https", netloc, path, "", "", "")), branch

    def _repo_path_and_branch(self, host: str, raw_path: str) -> tuple[str, str | None]:
        parts = [part for part in raw_path.strip("/").split("/") if part]
        if len(parts) < 2:
            raise ValueError("Remote Git repository URL must include owner/workspace and repository")

        owner = parts[0]
        repo = parts[1].removesuffix(".git")

        if host.endswith("bitbucket.org") and len(parts) >= 4 and parts[2] == "src":
            return f"/{owner}/{repo}", parts[3]

        if host.endswith("github.com") and len(parts) >= 4 and parts[2] in {"tree", "blob"}:
            return f"/{owner}/{repo}", parts[3]

        return f"/{owner}/{repo}", None

    def _detect_platform(self, repo_url: str) -> str:
        host = urlparse(repo_url).hostname or ""
        if host.endswith("github.com"):
            return "github"
        if host.endswith("bitbucket.org"):
            return "bitbucket"
        return "unknown"

    def _clone_directory_name(self, repo_url: str) -> str:
        parsed = urlparse(repo_url)
        path_parts = [part for part in parsed.path.removesuffix(".git").split("/") if part]
        readable = "-".join([parsed.hostname or "repo", *path_parts])[:80]
        digest = hashlib.sha256(repo_url.encode("utf-8")).hexdigest()[:12]
        return f"{readable}-{digest}"

    def _sanitize_git_error(self, message: str, remote: RemoteGitRepository) -> str:
        sanitized = message
        if remote.access_token:
            sanitized = sanitized.replace(remote.access_token, "***")
            sanitized = sanitized.replace(self._clone_url_for_auth(remote), remote.repo_url)
        return sanitized

    def _status_key(self, resource_id: str, repo_path: Path) -> str:
        return resource_id if self._is_url(resource_id) else str(repo_path)

    def _is_url(self, value: str) -> bool:
        parsed = urlparse(value)
        return parsed.scheme in {"http", "https"}
