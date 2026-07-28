from fastapi import APIRouter

from legacy_ecms.api.middleware.metrics import metrics

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("")
async def get_metrics() -> dict:
    return metrics.snapshot()
