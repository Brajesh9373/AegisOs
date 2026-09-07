"""Unit tests for the agent memory layers and bridge (no LLM, no DSH)."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import pytest

import ecms.persistence.database.rest_session as rest_session
from ecms.agent_os.runtime.agent_memory import AgentMemoryBridge, redact_secrets


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path, monkeypatch):
    """Point the persistence layer at a throwaway sqlite file per test."""
    db_url = f"sqlite+aiosqlite:///{tmp_path}/test_memory.db"
    monkeypatch.setenv("ECMS_DATABASE_URL", db_url)
    rest_session._engine = None
    rest_session._session_factory = None
    yield
    rest_session._engine = None
    rest_session._session_factory = None
    assert "ECMS_DATABASE_URL" in os.environ


@dataclass
class FakeUCO:
    display_name: str = "Episode"
    description: str = "Q: hi\nA: hello"
    uco_id: str = "uco-test-1"


class FakeMemory:
    def __init__(self, results: list[Any] | None = None) -> None:
        self.results = results if results is not None else [FakeUCO()]
        self.queries: list[str] = []

    async def retrieve(self, query: str, *, limit: int = 10) -> list[Any]:
        self.queries.append(query)
        return self.results[:limit]


class FakeRepo:
    def __init__(self) -> None:
        self.added: list[Any] = []

    async def add(self, uco: Any) -> None:
        self.added.append(uco)


def _bridge(results: list[Any] | None = None) -> AgentMemoryBridge:
    return AgentMemoryBridge(memory=FakeMemory(results), repository=FakeRepo())


# ── redaction ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize(
    ("raw", "expected_fragments", "absent"),
    [
        ("key sk-ant-abc123XYZ456 here", ["[REDACTED]"], ["sk-ant-abc123XYZ456"]),
        ("api_key = secret-token-999", ["[REDACTED]"], ["secret-token-999"]),
        ("Bearer mytoken123", ["[REDACTED]"], ["mytoken123"]),
        ("-----BEGIN RSA PRIVATE KEY-----", ["[REDACTED]"], ["PRIVATE KEY"]),
        ("normal text passes through", ["normal text passes through"], []),
    ],
)
def test_redact_secrets(raw: str, expected_fragments: list[str], absent: list[str]) -> None:
    redacted = redact_secrets(raw)
    for fragment in expected_fragments:
        assert fragment in redacted
    for missing in absent:
        assert missing not in redacted


# ── keyword matching ──────────────────────────────────────────────────────

def test_keywords_and_ranking() -> None:
    from ecms.memory.keywords import keywords, rank_by_overlap

    assert keywords("Deploy the REVIEW app!") == {"deploy", "review"}
    assert keywords("a an the") == set()
    ranked = rank_by_overlap(
        "deploy review app",
        [("build and deploy a review app", "proc-1"), ("unrelated cooking", "other")],
    )
    assert ranked == ["proc-1"]


# ── bridge scope gating ───────────────────────────────────────────────────

async def test_recall_denied_without_read_flag() -> None:
    bridge = _bridge()
    assert await bridge.recall("anything", {"read": False}, agent_id="a-1") == ""


async def test_record_skipped_without_write_flag() -> None:
    bridge = _bridge()
    await bridge.record_exchange("a-1", "q", "r", {"write": False})
    assert bridge.episodes._repository.added == []


async def test_recall_aggregates_layers() -> None:
    bridge = _bridge()
    await bridge.procedures.learn("Deploy app", "deploy things", ["step one"], "tester")
    await bridge.preferences.remember("style", "ruff", "a-1")
    await bridge.patterns.publish("best_practice", "run deploy checks", "tester")

    context = await bridge.recall(
        "how do I deploy the app", {"read": True, "write": True}, agent_id="a-1"
    )
    assert "Past episodes" in context
    assert "Deploy app" in context
    assert "style: ruff" in context
    assert "run deploy checks" in context


# ── recency ordering ────────────────────────────────────────────────────

def test_recent_episodes_come_first() -> None:
    import datetime

    from ecms.agent_os.runtime.agent_memory import _recent_first

    @dataclass
    class Episode:
        ontology_type: str = "agent_episode"
        display_name: str = "Episode"
        description: str = "x"
        created_at: Any = None

    @dataclass
    class Knowledge:
        ontology_type: str = "concept"
        display_name: str = "Concept"
        description: str = "y"

    old = Episode(created_at=datetime.datetime(2026, 1, 1))
    new = Episode(created_at=datetime.datetime(2026, 9, 7))
    knowledge = Knowledge()
    assert _recent_first([old, knowledge, new]) == [new, old, knowledge]


# ── store round-trips ─────────────────────────────────────────────────────

async def test_procedure_learn_and_search() -> None:
    from ecms.memory.procedural.store import ProceduralStore

    store = ProceduralStore()
    record = await store.learn("Onboard service", "onboard a new service", ["scaffold", "test"], "be-1")
    assert record["name"] == "Onboard service"
    found = await store.search("how to onboard a service")
    assert [r["id"] for r in found] == [record["id"]]
    assert await store.search("unrelated zebra xylophone") == []


async def test_preferences_overlay_agent_over_shared() -> None:
    from ecms.memory.long_term.store import PreferenceStore

    store = PreferenceStore()
    await store.remember("theme", "dark", "a-1", shared=True)
    await store.remember("theme", "light", "a-1")
    await store.remember("editor", "vim", "a-2")
    prefs = await store.recall("a-1")
    assert prefs == {"theme": "light"}
    assert await store.recall("a-2") == {"theme": "dark", "editor": "vim"}


async def test_patterns_publish_search_and_validation() -> None:
    from ecms.memory.organization.store import PatternStore

    store = PatternStore()
    record = await store.publish("known_bug", "flaky deploy pipeline retries", "be-1")
    assert record["pattern_type"] == "known_bug"
    found = await store.search("deploy pipeline flaky")
    assert [r["id"] for r in found] == [record["id"]]
    with pytest.raises(ValueError):
        await store.publish("not_a_type", "whatever", "be-1")


async def test_episodic_save_and_backfill() -> None:
    from ecms.memory.episodic.store import EpisodicStore
    from ecms.shared.models import UniversalCognitiveObject

    repo = FakeRepo()
    store = EpisodicStore(repo, UniversalCognitiveObject)
    uco_id = await store.save("a-1", "what is the codename", "BlueFalcon")
    assert uco_id is not None
    assert len(repo.added) == 1

    # Fresh store, empty index: backfill must restore from the database.
    restored = await EpisodicStore(FakeRepo(), UniversalCognitiveObject).backfill()
    assert restored == 1


async def test_bridge_record_and_backfill_round_trip() -> None:
    from ecms.shared.models import UniversalCognitiveObject

    bridge = AgentMemoryBridge(
        memory=FakeMemory([]),
        repository=FakeRepo(),
        uco_factory=UniversalCognitiveObject,
    )
    scope = {"read": True, "write": True}
    await bridge.record_exchange("a-9", "remember Redwood", "stored", scope)

    fresh = AgentMemoryBridge(
        memory=FakeMemory([]),
        repository=FakeRepo(),
        uco_factory=UniversalCognitiveObject,
    )
    assert await fresh.backfill_from_db() == 1
    assert len(fresh.episodes._repository.added) == 1
