from __future__ import annotations

import asyncio
from pathlib import Path

import pytest

from ecms.connectors.ingestion.git_runtime import (
    GitCommandRunner,
    GitLimits,
    GitWorkspace,
    IngestionCancelledError,
    _redact_git_error,
)


async def test_git_runner_observes_preexisting_cancellation() -> None:
    cancel = asyncio.Event()
    cancel.set()

    with pytest.raises(IngestionCancelledError):
        await GitCommandRunner().run(
            "--version",
            timeout_seconds=5,
            cancel=cancel,
        )


class RecordingRunner:
    def __init__(self) -> None:
        self.calls = []

    async def run(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if args[0] == "rev-parse":
            return "a" * 40
        return ""


async def test_requested_revision_is_validated_fetched_and_verified() -> None:
    runner = RecordingRunner()
    workspace = GitWorkspace(runner, GitLimits())  # type: ignore[arg-type]

    resolved = await workspace.checkout_revision(
        Path("repo"),
        "refs/tags/v2",
        cancel=asyncio.Event(),
    )

    assert resolved == "a" * 40
    assert runner.calls[0][0][-1] == "refs/tags/v2"
    assert runner.calls[1][0] == (
        "rev-parse",
        "--verify",
        "FETCH_HEAD^{commit}",
    )
    assert runner.calls[2][0] == ("reset", "--hard", "a" * 40)


@pytest.mark.parametrize(
    "revision",
    ["--upload-pack=evil", "../main", "main..evil", "main@{1}", "refs/heads/main/"],
)
async def test_requested_revision_rejects_option_and_revspec_injection(
    revision: str,
) -> None:
    workspace = GitWorkspace(RecordingRunner(), GitLimits())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="invalid"):
        await workspace.checkout_revision(
            Path("repo"), revision, cancel=asyncio.Event()
        )


def test_git_diagnostic_redaction_removes_credentials_and_query_secrets() -> None:
    detail = (
        "fatal: unable to access "
        "'https://user:token@example.test/repo.git?access_token=secret#fragment'"
    )
    redacted = _redact_git_error(detail)
    assert "token" not in redacted
    assert "secret" not in redacted
    assert "user:" not in redacted
    assert redacted == "fatal: unable to access 'https://example.test/[REDACTED]'"
