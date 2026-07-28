"""Tests for observability extensions: diagnostics, alerts, analytics (SECTION 232/233/87)."""

from __future__ import annotations

from ecms.analytics import AnalyticsService
from ecms.graph import GraphEngine
from ecms.infrastructure.reasoning import DeterministicEmbeddingProvider
from ecms.knowledge.infrastructure.repository import InMemoryKnowledgeRepository
from ecms.memory import DefaultMemoryEngine
from ecms.monitoring import AlertEngine, DiagnosticsEngine
from ecms.shared.models import UniversalCognitiveObject


async def test_diagnostics_aggregates_probes() -> None:
    engine = DiagnosticsEngine()
    engine.register("db", lambda: _ok(True))
    engine.register("cache", lambda: _ok(True))
    report = await engine.run()
    assert report["healthy"] is True
    assert report["checks"] == {"db": True, "cache": True}


async def test_diagnostics_reports_failure_without_raising() -> None:
    engine = DiagnosticsEngine()
    engine.register("broker", lambda: _boom())
    report = await engine.run()
    assert report["healthy"] is False
    assert report["checks"]["broker"] is False


def test_alert_engine_evaluates_rules() -> None:
    engine = AlertEngine()
    engine.add_rule("high_errors", "critical", lambda m: m.get("errors", 0) > 10)
    engine.add_rule("no_storage", "warning", lambda m: m.get("free_gb", 100) < 1)
    alerts = engine.evaluate({"errors": 20, "free_gb": 50})
    assert [alert.name for alert in alerts] == ["high_errors"]
    assert alerts[0].severity == "critical"


async def test_analytics_service_summary() -> None:
    graph = GraphEngine()
    repository = InMemoryKnowledgeRepository(DeterministicEmbeddingProvider())
    await graph.upsert_uco(
        UniversalCognitiveObject(
            canonical_name="A", display_name="A", ontology_type="component", description="a"
        )
    )
    memory = DefaultMemoryEngine(repository)
    analytics = AnalyticsService(graph=graph, memory=memory)
    summary = await analytics.summary()
    assert summary["graph"]["node_count"] == 1
    assert "activations" in summary["memory"]


async def _ok(value: bool) -> bool:
    return value


async def _boom() -> bool:
    raise RuntimeError("dependency down")
