from pathlib import Path

import pytest
from fastapi.testclient import TestClient

import ecms.api.graph_context as graph_context
from ecms.core.uko import UKOType
from ecms.providers.git import GitProvider
from ecms.providers.git.provider import RemoteGitRepository
from ecms.main import create_app
from tests.fakes import FakeGraphClient


@pytest.mark.asyncio
async def test_git_provider_discovers_and_syncs_local_repository(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "auth.py").write_text("def authenticate_user(token):\n    return token\n", encoding="utf-8")
    (repo / "README.md").write_text("# Authentication\n", encoding="utf-8")

    provider = GitProvider(roots=[tmp_path])

    assert await provider.validate()
    assert await provider.authenticate({"roots": [str(tmp_path)]})
    assert await provider.discover() == [str(repo.resolve())]

    ukos = [uko async for uko in provider.sync(str(repo))]
    names = {uko.name for uko in ukos}

    assert {"auth.py", "README.md"}.issubset(names)
    assert any(uko.type == UKOType.DOCUMENT for uko in ukos)
    assert any(uko.type == UKOType.FILE for uko in ukos)

    status = await provider.get_status(str(repo))
    assert status.objects_synced == len(ukos)
    assert status.errors == []


@pytest.mark.asyncio
async def test_git_provider_authenticates_github_url_without_storing_token(tmp_path: Path) -> None:
    provider = GitProvider(clone_root=tmp_path)

    assert await provider.authenticate(
        {
            "repo_url": "https://github.com/acme/payments",
            "access_token": "ghp_secret",
        }
    )

    resource_id = (await provider.discover())[0]
    remote = provider.remote_for(resource_id)
    clone_url = provider._clone_url_for_auth(remote)

    assert resource_id == "https://github.com/acme/payments.git"
    assert remote.platform == "github"
    assert remote.username == "x-access-token"
    assert "ghp_secret" not in resource_id
    assert "ghp_secret" not in clone_url
    assert clone_url == "https://x-access-token@github.com/acme/payments.git"


@pytest.mark.asyncio
async def test_git_provider_authenticates_bitbucket_url_without_storing_token(tmp_path: Path) -> None:
    provider = GitProvider(clone_root=tmp_path)

    assert await provider.authenticate(
        {
            "repo_url": "https://bitbucket.org/acme/payments",
            "access_token": "bb_secret",
        }
    )

    resource_id = (await provider.discover())[0]
    remote = provider.remote_for(resource_id)
    clone_url = provider._clone_url_for_auth(remote)

    assert resource_id == "https://bitbucket.org/acme/payments.git"
    assert remote.platform == "bitbucket"
    assert remote.username == "x-token-auth"
    assert "bb_secret" not in resource_id
    assert "bb_secret" not in clone_url
    assert clone_url == "https://x-token-auth@bitbucket.org/acme/payments.git"


@pytest.mark.asyncio
async def test_git_provider_accepts_bitbucket_source_browser_url(tmp_path: Path) -> None:
    provider = GitProvider(clone_root=tmp_path)

    assert await provider.authenticate(
        {
            "repo_url": "http://bitbucket.org/navadhan-acen/catchment/src/master/",
            "access_token": "bb_secret",
        }
    )

    resource_id = (await provider.discover())[0]
    remote = provider.remote_for(resource_id)

    assert resource_id == "https://bitbucket.org/navadhan-acen/catchment.git"
    assert remote.platform == "bitbucket"
    assert remote.branch == "master"
    assert "src/master" not in remote.repo_url
    assert "bb_secret" not in remote.repo_url


@pytest.mark.asyncio
async def test_git_provider_accepts_github_tree_browser_url(tmp_path: Path) -> None:
    provider = GitProvider(clone_root=tmp_path)

    assert await provider.authenticate(
        {
            "repo_url": "https://github.com/acme/payments/tree/main/src",
            "access_token": "ghp_secret",
        }
    )

    resource_id = (await provider.discover())[0]
    remote = provider.remote_for(resource_id)

    assert resource_id == "https://github.com/acme/payments.git"
    assert remote.platform == "github"
    assert remote.branch == "main"


def test_git_sync_api_accepts_github_repo_url_and_token(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "auth.py").write_text("def authenticate_user(token):\n    return token\n", encoding="utf-8")

    def fake_ensure_remote_repo(self: GitProvider, remote: RemoteGitRepository) -> Path:
        return repo

    monkeypatch.setattr(GitProvider, "_ensure_remote_repo", fake_ensure_remote_repo)
    client = TestClient(create_app())

    response = client.post(
        "/providers/git/sync",
        json={
            "repo_url": "https://github.com/acme/payments",
            "access_token": "ghp_secret",
            "branch": "main",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["platform"] == "github"
    assert body["repo_url"] == "https://github.com/acme/payments.git"
    assert body["uko_count"] == 1
    assert body["episode_count"] >= 2
    assert body["persisted"] is False
    assert "ghp_secret" not in response.text


def test_git_sync_api_accepts_public_repo_without_token(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "public.py").write_text("PUBLIC = True\n", encoding="utf-8")

    def fake_ensure_remote_repo(self: GitProvider, remote: RemoteGitRepository) -> Path:
        assert remote.access_token == ""
        return repo

    monkeypatch.setattr(GitProvider, "_ensure_remote_repo", fake_ensure_remote_repo)
    client = TestClient(create_app())

    response = client.post(
        "/providers/git/sync",
        json={"repo_url": "https://github.com/openclaw/openclaw"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["platform"] == "github"
    assert body["repo_url"] == "https://github.com/openclaw/openclaw.git"
    assert body["uko_count"] == 1


def test_git_provider_repo_commands_mark_managed_clone_as_safe(tmp_path: Path) -> None:
    provider = GitProvider(clone_root=tmp_path)
    repo = tmp_path / "repo"

    command = provider._repo_git_command(repo, "status", "--short")

    assert command[:3] == ["git", "-c", f"safe.directory={repo}"]
    assert command[3:] == ["-C", str(repo), "status", "--short"]


def test_git_sync_api_returns_clear_error_for_git_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_sync(self: GitProvider, remote: RemoteGitRepository) -> Path:
        raise RuntimeError("fatal: Authentication failed for https://bitbucket.org/acme/repo.git")

    monkeypatch.setattr(GitProvider, "_ensure_remote_repo", fail_sync)
    client = TestClient(create_app())

    response = client.post(
        "/providers/git/sync",
        json={
            "repo_url": "https://bitbucket.org/acme/repo/src/master/",
            "access_token": "bb_secret",
            "platform": "bitbucket",
        },
    )

    assert response.status_code == 400
    assert "Authentication failed" in response.json()["detail"]
    assert "bb_secret" not in response.text


def test_git_sync_api_persists_when_requested(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    FakeGraphClient.reset()
    monkeypatch.setattr(graph_context, "create_graph_client", lambda: FakeGraphClient())
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "auth.py").write_text("def authenticate_user(token):\n    return token\n", encoding="utf-8")

    def fake_ensure_remote_repo(self: GitProvider, remote: RemoteGitRepository) -> Path:
        return repo

    monkeypatch.setattr(GitProvider, "_ensure_remote_repo", fake_ensure_remote_repo)
    client = TestClient(create_app())

    response = client.post(
        "/providers/git/sync",
        json={
            "repo_url": "https://github.com/acme/payments",
            "access_token": "ghp_secret",
            "persist": True,
        },
    )

    assert response.status_code == 200
    assert response.json()["persisted"] is True
    assert len(FakeGraphClient.instances[0].episodes) == response.json()["episode_count"]
