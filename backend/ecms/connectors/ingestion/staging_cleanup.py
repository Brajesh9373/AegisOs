"""Conservative one-shot cleanup for terminal staged ingestion objects."""

from __future__ import annotations

import argparse
import asyncio
import logging
from datetime import timedelta

from sqlalchemy import select

from ecms.configuration.schemas.settings import get_settings
from ecms.infrastructure.storage.factory import create_snapshot_object_store
from ecms.persistence.database.rest_session import db_session
from ecms.persistence.models.connector_ingestion_partition import (
    ConnectorIngestionStageBatch,
)
from ecms.shared.time import utcnow

logger = logging.getLogger(__name__)


async def cleanup(*, execute: bool, limit: int = 1_000) -> int:
    """Delete objects for old committed batches while retaining audit metadata."""
    settings = get_settings()
    cutoff = utcnow() - timedelta(days=settings.connector_ingestion_staged_retention_days)
    async with db_session() as session:
        keys = list(
            await session.scalars(
                select(ConnectorIngestionStageBatch.object_key)
                .where(
                    ConnectorIngestionStageBatch.state == "committed",
                    ConnectorIngestionStageBatch.committed_at.is_not(None),
                    ConnectorIngestionStageBatch.committed_at < cutoff,
                )
                .order_by(ConnectorIngestionStageBatch.committed_at)
                .limit(limit)
            )
        )
    if not execute:
        logger.info("staging cleanup dry run", extra={"eligible_objects": len(keys)})
        return len(keys)
    objects = create_snapshot_object_store(settings)
    for key in keys:
        await objects.delete_object(key)
    logger.info("staging cleanup complete", extra={"deleted_objects": len(keys)})
    return len(keys)


def main() -> None:
    """Run a dry-run by default; require ``--execute`` for deletion."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--limit", type=int, default=1_000)
    arguments = parser.parse_args()
    if arguments.limit < 1:
        parser.error("--limit must be positive")
    logging.basicConfig(level="INFO")
    asyncio.run(cleanup(execute=arguments.execute, limit=arguments.limit))


if __name__ == "__main__":
    main()
