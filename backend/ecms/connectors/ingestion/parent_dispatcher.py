"""Single-owner dispatcher for the connector-ingestion parent stream."""

from __future__ import annotations

from ecms.configuration.schemas.settings import AppSettings, get_settings


def selected_runtime(settings: AppSettings) -> str:
    """Return the only parent consumer permitted for this deployment."""
    return (
        "parallel"
        if settings.connector_parallel_ingestion_enabled
        else "legacy"
    )


def main() -> None:
    """Start exactly one parent-stream runtime from the immutable startup flag."""
    runtime = selected_runtime(get_settings())
    if runtime == "parallel":
        from ecms.connectors.ingestion.coordinator_process import main as run
    else:
        from ecms.connectors.ingestion.worker import main as run
    run()


if __name__ == "__main__":
    main()
