"""Parent-stream deployment selection regressions."""

from ecms.configuration.schemas.settings import AppSettings
from ecms.connectors.ingestion.parent_dispatcher import selected_runtime


def test_dispatcher_defaults_to_single_legacy_consumer() -> None:
    assert selected_runtime(AppSettings()) == "legacy"


def test_dispatcher_selects_coordinator_only_with_parallel_flag() -> None:
    settings = AppSettings(connector_parallel_ingestion_enabled=True)
    assert selected_runtime(settings) == "parallel"
