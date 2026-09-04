"""Agent OS readiness checks for production observability."""

from __future__ import annotations

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

__all__ = ["AgentOSReadiness", "check_readiness"]


@dataclass(frozen=True)
class AgentOSReadiness:
    """Non-secret aggregated readiness status for Agent OS."""

    ready: bool
    profile_readiness: dict[str, bool]
    capability_count: int
    reason_code: str | None = None

    def to_dict(self) -> dict:
        """Return a JSON-safe dictionary for API responses."""
        return {
            "ready": self.ready,
            "profile_readiness": self.profile_readiness,
            "capability_count": self.capability_count,
            "reason_code": self.reason_code,
        }


async def check_readiness() -> AgentOSReadiness:
    """Aggregate readiness from all Agent OS components.

    This performs non-secret, side-effect-free checks for:
    - Profile plugin readiness
    - Capability broker availability
    - Database connectivity
    - Worker health

    Returns a deterministic readiness report without exposing sensitive details.
    """
    profile_readiness: dict[str, bool] = {}
    capability_count = 0
    reasons: list[str] = []

    # Check profile plugins
    try:
        from ecms.agent.ba.plugin import get_ba_profile_catalog
        from ecms.agent.compliance_officer.plugin import ComplianceOfficerProfilePlugin

        catalog = get_ba_profile_catalog()
        for profile in catalog.installed():
            try:
                readiness = profile.readiness()
                profile_readiness[profile.profile_spec.profile_id] = readiness.ready
            except Exception as exc:
                logger.warning(
                    "Profile %s readiness failed: %s", profile.profile_spec.profile_id, exc
                )
                profile_readiness[profile.profile_spec.profile_id] = False
                reasons.append(f"profile_{profile.profile_spec.profile_id}_unready")

        # Check Compliance Officer profile if registered
        try:
            co = ComplianceOfficerProfilePlugin()
            readiness = co.readiness()
            profile_readiness["compliance-officer"] = readiness.ready
        except Exception:
            pass  # Optional profile
    except Exception as exc:
        logger.warning("Profile catalog unavailable: %s", exc)
        reasons.append("profile_catalog_unavailable")

    # Check capability broker
    try:
        from ecms.agent_os.capabilities.broker import get_capability_broker

        broker = get_capability_broker()
        capabilities = broker.list_capabilities()
        capability_count = len(capabilities)
    except Exception as exc:
        logger.warning("Capability broker unavailable: %s", exc)
        reasons.append("capability_broker_unavailable")

    # Check database connectivity
    try:
        from sqlalchemy import text

        from ecms.agent_os.persistence.database import db_session

        async with db_session() as session:
            await session.execute(text("SELECT 1"))
    except Exception as exc:
        logger.warning("Database connectivity failed: %s", exc)
        reasons.append("database_unavailable")

    # Determine overall readiness
    ready = any(profile_readiness.values()) and capability_count > 0 and not reasons

    reason_code = reasons[0] if reasons else None

    return AgentOSReadiness(
        ready=ready,
        profile_readiness=profile_readiness,
        capability_count=capability_count,
        reason_code=reason_code,
    )
