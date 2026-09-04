"""Safety defaults for partitioned connector ingestion."""

import pytest
from pydantic import ValidationError

from ecms.configuration.schemas.settings import AppSettings


def test_parallel_ingestion_is_disabled_with_bounded_defaults() -> None:
    settings = AppSettings()

    assert settings.connector_parallel_ingestion_enabled is False
    assert settings.connector_extraction_worker_count == 4
    assert settings.connector_graph_writer_concurrency == 1
    assert settings.connector_ingestion_partition_target_files == 100
    assert settings.connector_ingestion_max_active_partitions_per_org == 8
    assert settings.connector_ingestion_max_staged_bytes_per_org == 10 * 1024**3
    assert settings.connector_ingestion_max_batch_encoded_bytes == 4 * 1024**2


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("connector_extraction_worker_count", 0),
        ("connector_graph_writer_concurrency", 0),
        ("connector_ingestion_partition_target_files", 0),
        ("connector_ingestion_max_active_partitions_per_org", 0),
        ("connector_ingestion_max_staged_bytes_per_org", 0),
        ("connector_ingestion_max_batch_encoded_bytes", 0),
    ],
)
def test_parallel_ingestion_rejects_unbounded_zero_values(field: str, value: int) -> None:
    with pytest.raises(ValidationError):
        AppSettings(**{field: value})
