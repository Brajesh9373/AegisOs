"""Capability broker for Agent OS - validates and executes capability requests."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ecms.agent_os.capabilities.contracts import (
    CapabilityExecutionContext,
    CapabilityExecutionResult,
    CapabilityPlugin,
    CapabilitySpec,
)
from ecms.persistence.database.rest_session import db_session

logger = logging.getLogger(__name__)

__all__ = ["CapabilityAuthorization", "CapabilityBroker", "CapabilityDecision"]


@dataclass(frozen=True)
class CapabilityAuthorization:
    """Authorization decision for a capability request."""

    authorized: bool
    reason_code: str | None = None
    capability_spec: CapabilitySpec | None = None


@dataclass(frozen=True)
class CapabilityDecision:
    """Persisted record of a capability authorization decision."""

    capability_id: str
    version: str
    organization_id: str
    run_id: str
    step_id: str
    worker_id: str
    idempotency_key: str
    decision: str  # "approved", "denied", "pending_approval"
    approved_at: datetime | None = None
    executed_at: datetime | None = None
    result_checksum: str | None = None


class CapabilityBroker:
    """Validates capability requests and executes approved capabilities."""

    def __init__(self) -> None:
        self._capabilities: dict[str, CapabilityPlugin] = {}

    def register(self, plugin: CapabilityPlugin) -> None:
        """Register a capability plugin."""
        spec = plugin.capability_spec
        self._capabilities[spec.capability_id] = plugin
        logger.info("Registered capability: %s v%s", spec.capability_id, spec.version)

    async def authorize(
        self,
        capability_id: str,
        version: str,
        organization_id: str,
        run_id: str,
        step_id: str,
        worker_id: str,
        idempotency_key: str,
        arguments: dict[str, Any],
        *,
        profile_capability_ids: tuple[str, ...],
    ) -> CapabilityAuthorization:
        """Validate a capability request against policy."""
        # Check if capability is registered
        capability = self._capabilities.get(capability_id)
        if capability is None:
            return CapabilityAuthorization(
                authorized=False,
                reason_code="capability_not_registered",
            )

        spec = capability.capability_spec

        # Check version matches
        if spec.version != version:
            return CapabilityAuthorization(
                authorized=False,
                reason_code="capability_version_mismatch",
                capability_spec=spec,
            )

        # Check profile is allowed to use this capability
        if capability_id not in profile_capability_ids:
            return CapabilityAuthorization(
                authorized=False,
                reason_code="capability_not_declared_by_profile",
                capability_spec=spec,
            )

        # Check arguments size
        arguments_bytes = len(str(arguments).encode("utf-8"))
        if arguments_bytes > spec.max_arguments_bytes:
            return CapabilityAuthorization(
                authorized=False,
                reason_code="arguments_exceed_limit",
                capability_spec=spec,
            )

        # Check idempotency key present if required
        if spec.requires_idempotency_key and not idempotency_key:
            return CapabilityAuthorization(
                authorized=False,
                reason_code="idempotency_key_required",
                capability_spec=spec,
            )

        # For write/external, check approval status
        if spec.requires_approval:
            async with db_session() as session:
                approved = await self._check_approval(
                    session, capability_id, organization_id, idempotency_key
                )
                if not approved:
                    return CapabilityAuthorization(
                        authorized=False,
                        reason_code="approval_required",
                        capability_spec=spec,
                    )

        return CapabilityAuthorization(
            authorized=True,
            capability_spec=spec,
        )

    async def _check_approval(
        self,
        session: AsyncSession,
        capability_id: str,
        organization_id: str,
        idempotency_key: str,
    ) -> bool:
        """Check if a capability request has been approved."""
        if not idempotency_key:
            return False
        # Check if there's an approval record
        row = (
            await session.execute(
                text(
                    "SELECT 1 FROM agent_capability_approvals "
                    "WHERE capability_id = :cap_id AND organization_id = :org_id "
                    "AND idempotency_key = :key AND approved_at IS NOT NULL "
                    "LIMIT 1"
                ),
                {
                    "cap_id": capability_id,
                    "org_id": organization_id,
                    "key": idempotency_key,
                },
            )
        ).first()
        return row is not None

    async def execute(
        self,
        *,
        capability_id: str,
        context: CapabilityExecutionContext,
        arguments: dict[str, Any],
        idempotency_key: str,
    ) -> CapabilityExecutionResult:
        """Execute an authorized capability request."""
        capability = self._capabilities.get(capability_id)
        if capability is None:
            raise ValueError(f"Capability not registered: {capability_id}")

        # Execute the capability
        result = await capability.execute(
            context=context,
            arguments=arguments,
        )

        # Record the execution
        await self._record_execution(
            organization_id=context.organization_id,
            run_id=context.run_id,
            step_id=context.step_id,
            worker_id=context.worker_id,
            capability_id=capability_id,
            idempotency_key=idempotency_key,
            result=result.result,
        )

        return result

    async def _record_execution(
        self,
        organization_id: str,
        run_id: str,
        step_id: str,
        worker_id: str,
        capability_id: str,
        idempotency_key: str,
        result: dict[str, Any],
    ) -> None:
        """Persist a capability execution record."""
        result_str = str(result)
        result_checksum = hashlib.sha256(result_str.encode("utf-8")).hexdigest()[:16]

        async with db_session() as session:
            await session.execute(
                text(
                    """
                    INSERT INTO agent_capability_invocations
                    (id, organization_id, run_id, step_id, worker_id,
                     capability_id, idempotency_key, result_checksum, executed_at)
                    VALUES (:id, :org_id, :run_id, :step_id, :worker_id,
                            :cap_id, :key, :checksum, :executed)
                    ON CONFLICT (organization_id, idempotency_key)
                    DO UPDATE SET result_checksum = :checksum, executed_at = :executed
                    """
                ),
                {
                    "id": f"cap_{run_id}_{step_id}_{capability_id[:8]}",
                    "org_id": organization_id,
                    "run_id": run_id,
                    "step_id": step_id,
                    "worker_id": worker_id,
                    "cap_id": capability_id,
                    "key": idempotency_key,
                    "checksum": result_checksum,
                    "executed": datetime.now(UTC).isoformat(),
                },
            )
            await session.commit()

    def get_capability_spec(self, capability_id: str) -> CapabilitySpec | None:
        """Get the spec for a registered capability."""
        capability = self._capabilities.get(capability_id)
        return capability.capability_spec if capability else None

    def list_capabilities(self) -> list[CapabilitySpec]:
        """List all registered capability specs."""
        return [c.capability_spec for c in self._capabilities.values()]


# Global broker instance
_broker: CapabilityBroker | None = None


def get_capability_broker() -> CapabilityBroker:
    """Get the global capability broker."""
    global _broker
    if _broker is None:
        _broker = CapabilityBroker()
    return _broker
