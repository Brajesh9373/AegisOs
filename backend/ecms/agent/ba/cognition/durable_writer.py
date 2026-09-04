"""Transaction-bound persistence for validated Business Analyst stage results.

This module is deliberately a narrow durability boundary. It records immutable
receipts and policy-scoped candidates in the caller's transaction, then creates
a leaseable outbox record for later canonical promotion. It neither invokes DSH
nor writes directly to knowledge or graph stores.
"""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from hashlib import sha256
from typing import Any, TypeAlias
from uuid import uuid4

from sqlalchemy import and_, or_, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from ecms.agent.ba.cognition.contracts import BAStage, BAStageResult, JSONValue
from ecms.persistence.models.ba_stage_outcome import BACandidate, BAPromotionOutbox, BAStageReceipt
from ecms.shared.time import utcnow

__all__ = [
    "BACandidatePolicy",
    "BAPromotionOutboxRepository",
    "BAStageOutcomeRepository",
    "PersistentDiscoveryMemoryWriter",
]

JSONObject: TypeAlias = dict[str, JSONValue]


@dataclass(frozen=True, slots=True)
class _CandidateDraft:
    """A policy-approved candidate that may be queued for promotion."""

    kind: str
    payload: JSONObject
    approval_required: bool


class BACandidatePolicy:
    """Conservative deterministic policy for candidate extraction.

    Model output is never treated as an enterprise fact by default. Understand,
    clarify, and team-design results receive immutable receipts only. A finalized
    requirements artifact is recorded as a provisional candidate and requires an
    explicit approval transition before the outbox can be claimed.
    """

    def extract(self, result: BAStageResult) -> tuple[_CandidateDraft, ...]:
        """Return candidates that policy permits from an already-validated result."""
        if result.stage is not BAStage.FINALIZE or not isinstance(result.output, dict):
            return ()
        return (
            _CandidateDraft(
                kind="finalized_requirements",
                payload=_json_object(result.output),
                approval_required=True,
            ),
        )


class BAStageOutcomeRepository:
    """Persist and resolve organization-scoped immutable BA receipts."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind this repository to the caller-owned transaction."""
        self._session = session

    async def get_receipt(
        self, receipt_id: str, *, organization_id: str
    ) -> BAStageReceipt | None:
        """Return a receipt only within its owning organization."""
        return await self._session.scalar(
            select(BAStageReceipt).where(
                BAStageReceipt.id == receipt_id,
                BAStageReceipt.organization_id == organization_id,
            )
        )

    async def get_by_idempotency(
        self, *, organization_id: str, idempotency_key: str
    ) -> BAStageReceipt | None:
        """Resolve an already-recorded request without crossing tenant boundaries."""
        return await self._session.scalar(
            select(BAStageReceipt).where(
                BAStageReceipt.organization_id == organization_id,
                BAStageReceipt.idempotency_key == idempotency_key,
            )
        )

    async def record(self, result: BAStageResult, *, policy: BACandidatePolicy) -> BAStageReceipt:
        """Atomically insert a receipt, candidates, and deferred projection work.

        The caller remains responsible for commit/rollback. A duplicate delivery
        returns its original immutable receipt after verifying its snapshot hash,
        rather than producing duplicate candidates or outbox jobs. The complete
        receipt/candidate/outbox unit is contained in one savepoint so a candidate
        policy or persistence failure cannot leave a receipt behind by itself.
        """
        receipt_values = _receipt_values(result)
        existing = await self.get_by_idempotency(
            organization_id=receipt_values["organization_id"],
            idempotency_key=receipt_values["idempotency_key"],
        )
        if existing is not None:
            _assert_same_receipt(existing, receipt_values)
            return existing

        try:
            async with self._session.begin_nested():
                receipt = BAStageReceipt(id=_new_id("ba-receipt"), **receipt_values)
                self._session.add(receipt)
                await self._session.flush()

                outcomes: list[dict[str, Any]] = []
                for draft in policy.extract(result):
                    candidate, created = await self._record_candidate(receipt, draft)
                    outcome = {
                        "candidate_id": candidate.id,
                        "kind": candidate.kind,
                        "state": candidate.state,
                    }
                    if created and candidate.state == "queued_for_projection":
                        outbox = await self._enqueue(candidate)
                        outcome["outbox_id"] = outbox.id
                    outcomes.append(outcome)
                receipt.candidate_outcomes = outcomes
                await self._session.flush()
        except IntegrityError:
            # A concurrent delivery won the organization-scoped idempotency key.
            # A savepoint preserves the outer discovery transaction so its caller
            # can safely load the authoritative immutable result. Other integrity
            # failures are not misreported as duplicate deliveries.
            existing = await self.get_by_idempotency(
                organization_id=receipt_values["organization_id"],
                idempotency_key=receipt_values["idempotency_key"],
            )
            if existing is None:
                raise
            _assert_same_receipt(existing, receipt_values)
            return existing
        return receipt

    async def _record_candidate(
        self, receipt: BAStageReceipt, draft: _CandidateDraft
    ) -> tuple[BACandidate, bool]:
        """Create a candidate or reuse an identical organization-scoped candidate."""
        payload = _json_object(draft.payload)
        payload_checksum = _hash_json(payload)
        candidate_key = _digest(
            {
                "organization_id": receipt.organization_id,
                "project_id": receipt.project_id,
                "discovery_session_id": receipt.discovery_session_id,
                "stage": receipt.stage,
                "source_revision": receipt.source_revision,
                "conversation_revision": receipt.conversation_revision,
                "policy_revision": receipt.policy_revision,
                "profile_hash": receipt.profile_hash,
                "template_hash": receipt.template_hash,
                "schema_hash": receipt.schema_hash,
                "kind": draft.kind,
                "payload_checksum": payload_checksum,
            }
        )
        existing = await self._session.scalar(
            select(BACandidate).where(
                BACandidate.organization_id == receipt.organization_id,
                BACandidate.candidate_key == candidate_key,
            )
        )
        if existing is not None:
            return existing, False

        candidate = BACandidate(
            id=_new_id("ba-candidate"),
            receipt_id=receipt.id,
            organization_id=receipt.organization_id,
            project_id=receipt.project_id,
            discovery_session_id=receipt.discovery_session_id,
            kind=draft.kind,
            candidate_key=candidate_key,
            payload_json=payload,
            payload_checksum=payload_checksum,
            state="pending_approval" if draft.approval_required else "queued_for_projection",
            approval_required=draft.approval_required,
        )
        self._session.add(candidate)
        await self._session.flush()
        return candidate, True

    async def _enqueue(self, candidate: BACandidate) -> BAPromotionOutbox:
        """Create exactly one canonical-promotion work item for an approved candidate."""
        dedupe_key = _digest(
            {
                "organization_id": candidate.organization_id,
                "candidate_id": candidate.id,
                "candidate_key": candidate.candidate_key,
                "event_type": "ba.candidate.promote.v1",
            }
        )
        existing = await self._session.scalar(
            select(BAPromotionOutbox).where(
                BAPromotionOutbox.organization_id == candidate.organization_id,
                BAPromotionOutbox.dedupe_key == dedupe_key,
            )
        )
        if existing is not None:
            return existing
        outbox = BAPromotionOutbox(
            id=_new_id("ba-outbox"),
            organization_id=candidate.organization_id,
            candidate_id=candidate.id,
            event_type="ba.candidate.promote.v1",
            dedupe_key=dedupe_key,
            payload_json={
                "candidate_id": candidate.id,
                "candidate_key": candidate.candidate_key,
                "kind": candidate.kind,
                "payload_checksum": candidate.payload_checksum,
            },
        )
        self._session.add(outbox)
        await self._session.flush()
        return outbox

    async def approve_candidate(
        self, candidate_id: str, *, organization_id: str, approved_at: datetime | None = None
    ) -> BACandidate | None:
        """Approve one pending candidate and atomically enqueue its projection work."""
        candidate = await self._session.scalar(
            select(BACandidate)
            .where(
                BACandidate.id == candidate_id,
                BACandidate.organization_id == organization_id,
            )
            .with_for_update()
        )
        if candidate is None:
            return None
        if candidate.state == "rejected":
            raise ValueError("rejected BA candidates cannot be approved")
        if candidate.state in {"promoted", "deduplicated"}:
            return candidate
        if candidate.state == "pending_approval":
            candidate.state = "queued_for_projection"
            candidate.approved_at = approved_at or utcnow()
            await self._enqueue(candidate)
        await self._session.flush()
        return candidate

    async def reject_candidate(
        self, candidate_id: str, *, organization_id: str, rejected_at: datetime | None = None
    ) -> BACandidate | None:
        """Terminally reject a candidate before it enters canonical promotion."""
        candidate = await self._session.scalar(
            select(BACandidate)
            .where(
                BACandidate.id == candidate_id,
                BACandidate.organization_id == organization_id,
            )
            .with_for_update()
        )
        if candidate is None:
            return None
        if candidate.state in {"promoted", "deduplicated"}:
            raise ValueError("canonical BA candidates cannot be rejected")
        candidate.state = "rejected"
        candidate.rejected_at = rejected_at or utcnow()
        await self._session.execute(
            update(BAPromotionOutbox)
            .where(
                BAPromotionOutbox.candidate_id == candidate.id,
                BAPromotionOutbox.organization_id == organization_id,
                BAPromotionOutbox.state.in_(("pending", "retry", "leased")),
            )
            .values(state="cancelled", lease_owner=None, lease_expires_at=None)
            .execution_options(synchronize_session=False)
        )
        await self._session.flush()
        return candidate


class BAPromotionOutboxRepository:
    """Lease and complete deferred canonical candidate-projection work."""

    def __init__(self, session: AsyncSession) -> None:
        """Bind this repository to the caller-owned transaction."""
        self._session = session

    async def claim_next(
        self,
        *,
        worker_id: str,
        lease_seconds: int,
        now: datetime | None = None,
    ) -> BAPromotionOutbox | None:
        """Atomically claim one eligible outbox record across organizations.

        Worker access is system-internal; the query still joins candidate state so
        cancelled, rejected, or not-yet-approved data can never be projected. An
        expired final lease is made terminal before selection, rather than silently
        becoming one more attempt.
        """
        claimed_at = now or utcnow()
        await self._dead_letter_expired_final_leases(now=claimed_at)
        attempts_remaining = BAPromotionOutbox.attempt < BAPromotionOutbox.max_attempts
        eligible = and_(
            attempts_remaining,
            or_(
                BAPromotionOutbox.state.in_(("pending", "retry")),
                and_(
                    BAPromotionOutbox.state == "leased",
                    BAPromotionOutbox.lease_expires_at.is_not(None),
                    BAPromotionOutbox.lease_expires_at < claimed_at,
                ),
            ),
        )
        candidate_id = await self._session.scalar(
            select(BAPromotionOutbox.id)
            .join(
                BACandidate,
                and_(
                    BACandidate.id == BAPromotionOutbox.candidate_id,
                    BACandidate.organization_id == BAPromotionOutbox.organization_id,
                ),
            )
            .where(
                eligible,
                BAPromotionOutbox.available_at <= claimed_at,
                BACandidate.state == "queued_for_projection",
                or_(
                    BACandidate.approval_required.is_(False),
                    BACandidate.approved_at.is_not(None),
                ),
            )
            .order_by(BAPromotionOutbox.available_at, BAPromotionOutbox.created_at)
            .limit(1)
        )
        if candidate_id is None:
            return None
        claimed = await self._session.execute(
            update(BAPromotionOutbox)
            .where(BAPromotionOutbox.id == candidate_id, eligible)
            .values(
                state="leased",
                lease_owner=worker_id,
                lease_expires_at=claimed_at + timedelta(seconds=max(lease_seconds, 1)),
                attempt=BAPromotionOutbox.attempt + 1,
                error_code=None,
                error_summary=None,
            )
            .execution_options(synchronize_session=False)
        )
        if claimed.rowcount != 1:
            return None
        outbox = await self._session.get(BAPromotionOutbox, candidate_id)
        if outbox is not None:
            await self._session.refresh(outbox)
        return outbox

    async def _dead_letter_expired_final_leases(self, *, now: datetime) -> None:
        """Terminalize abandoned final leases before another worker can select them."""
        await self._session.execute(
            update(BAPromotionOutbox)
            .where(
                BAPromotionOutbox.state == "leased",
                BAPromotionOutbox.lease_expires_at.is_not(None),
                BAPromotionOutbox.lease_expires_at < now,
                BAPromotionOutbox.attempt >= BAPromotionOutbox.max_attempts,
            )
            .values(
                state="dead_letter",
                available_at=now,
                lease_owner=None,
                lease_expires_at=None,
                error_code="LEASE_EXPIRED",
                error_summary="worker lease expired after the final permitted attempt",
            )
            .execution_options(synchronize_session=False)
        )

    async def renew_lease(
        self,
        outbox_id: str,
        *,
        worker_id: str,
        lease_seconds: int,
        now: datetime | None = None,
    ) -> bool:
        """Renew a still-valid lease only for its current worker."""
        renewed_at = now or utcnow()
        result = await self._session.execute(
            update(BAPromotionOutbox)
            .where(
                BAPromotionOutbox.id == outbox_id,
                BAPromotionOutbox.state == "leased",
                BAPromotionOutbox.lease_owner == worker_id,
                BAPromotionOutbox.lease_expires_at >= renewed_at,
            )
            .values(lease_expires_at=renewed_at + timedelta(seconds=max(lease_seconds, 1)))
            .execution_options(synchronize_session=False)
        )
        return result.rowcount == 1

    async def complete(
        self,
        outbox_id: str,
        *,
        worker_id: str,
        outcome: str,
        completed_at: datetime | None = None,
    ) -> BACandidate | None:
        """Atomically record a truthful terminal canonical-projection outcome."""
        if outcome not in {"promoted", "deduplicated", "rejected"}:
            raise ValueError("outcome must be promoted, deduplicated, or rejected")

        # Lock the candidate first, matching rejection's lock ordering. The owned
        # outbox is re-checked under lock below, so this initial lookup cannot let a
        # stale worker complete a candidate after its lease or approval changed.
        observed = await self._session.scalar(
            select(BAPromotionOutbox).where(BAPromotionOutbox.id == outbox_id)
        )
        if observed is None:
            return None
        candidate = await self._session.scalar(
            select(BACandidate)
            .where(
                BACandidate.id == observed.candidate_id,
                BACandidate.organization_id == observed.organization_id,
                BACandidate.state == "queued_for_projection",
            )
            .with_for_update()
        )
        outbox = await self._locked_owned(outbox_id, worker_id)
        if outbox is None:
            return None
        if candidate is None:
            # A concurrent rejection/approval change must never let a stale lease
            # claim a successful projection outcome.
            outbox.state = "cancelled"
            outbox.lease_owner = None
            outbox.lease_expires_at = None
            await self._session.flush()
            return None
        changed_at = completed_at or utcnow()
        outbox.state = "completed"
        outbox.completed_at = changed_at
        outbox.lease_owner = None
        outbox.lease_expires_at = None
        candidate.state = outcome
        if outcome == "promoted":
            candidate.promoted_at = changed_at
        if outcome == "rejected":
            candidate.rejected_at = changed_at
        await self._session.flush()
        return candidate

    async def retry_or_dead_letter(
        self,
        outbox_id: str,
        *,
        worker_id: str,
        error_code: str,
        error_summary: str,
        available_at: datetime | None = None,
    ) -> BAPromotionOutbox | None:
        """Release a recoverable failure or retain a bounded terminal dead letter."""
        outbox = await self._locked_owned(outbox_id, worker_id)
        if outbox is None:
            return None
        exhausted = outbox.attempt >= outbox.max_attempts
        outbox.state = "dead_letter" if exhausted else "retry"
        outbox.available_at = available_at or utcnow()
        outbox.lease_owner = None
        outbox.lease_expires_at = None
        outbox.error_code = error_code[:128]
        outbox.error_summary = _safe_error_summary(error_summary)
        await self._session.flush()
        return outbox

    async def _locked_owned(self, outbox_id: str, worker_id: str) -> BAPromotionOutbox | None:
        """Resolve a live owned lease without accepting stale worker completions."""
        now = utcnow()
        return await self._session.scalar(
            select(BAPromotionOutbox)
            .where(
                BAPromotionOutbox.id == outbox_id,
                BAPromotionOutbox.state == "leased",
                BAPromotionOutbox.lease_owner == worker_id,
                BAPromotionOutbox.lease_expires_at >= now,
            )
            .with_for_update()
        )


class PersistentDiscoveryMemoryWriter:
    """Real ``DiscoveryMemoryWriter`` backed by a caller-supplied transaction.

    A session factory is injected rather than imported from the REST layer so the
    application can compose it with the same transaction as discovery state. The
    writer commits when it owns the session factory; callers needing a larger
    atomic unit should instantiate ``BAStageOutcomeRepository`` directly inside
    their existing transaction.
    """

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        *,
        policy: BACandidatePolicy | None = None,
    ) -> None:
        """Initialize durable write-back with an async-session factory."""
        self._session_factory = session_factory
        self._policy = policy or BACandidatePolicy()

    async def record(self, result: BAStageResult) -> None:
        """Commit one validated result, its receipt, and policy-approved work together."""
        async with self._session_factory() as session:
            repository = BAStageOutcomeRepository(session)
            try:
                await repository.record(result, policy=self._policy)
                await session.commit()
            except Exception:
                await session.rollback()
                raise


def _receipt_values(result: BAStageResult) -> dict[str, Any]:
    """Convert an immutable stage result into bounded non-secret receipt fields."""
    packet = result.packet
    context = packet.context
    output = _json_value(result.output)
    output_checksum = _hash_json(output)
    provenance = {
        "evidence": [
            {
                "citation_id": item.citation.citation_id,
                "source_kind": item.citation.source_kind,
                "source_version": item.citation.source_version,
                "trust_state": item.citation.trust_state,
                "classification": item.classification,
            }
            for item in packet.evidence
        ],
        "graph_snapshot_version": packet.graph.snapshot_version,
        "retrieval_statuses": [
            {
                "source": item.source,
                "state": item.state.value,
                "omitted_count": item.omitted_count,
                "reason_code": item.reason_code,
            }
            for item in packet.retrieval_statuses
        ],
        "omitted_evidence_count": packet.omitted_evidence_count,
    }
    idempotency_key = _digest(
        {
            "organization_id": context.organization_id,
            "project_id": context.project_id,
            "discovery_session_id": context.discovery_session_id,
            "stage": result.stage.value,
            "source_revision": context.source_revision,
            "conversation_revision": context.conversation_revision,
            "policy_revision": context.policy_revision,
            "profile_hash": context.profile_hash,
            "template_hash": context.template_hash,
            "schema_hash": context.schema_hash,
        }
    )
    runtime_metadata = dict(result.execution.runtime_metadata)
    return {
        "organization_id": context.organization_id,
        "project_id": context.project_id,
        "discovery_session_id": context.discovery_session_id,
        "actor_id": context.actor_id,
        "correlation_id": context.correlation_id,
        "stage": result.stage.value,
        "idempotency_key": idempotency_key,
        "context_snapshot_hash": packet.snapshot_hash,
        "scope_partition_hash": context.scope_partition,
        "source_revision": context.source_revision,
        "conversation_revision": context.conversation_revision,
        "policy_revision": context.policy_revision,
        "profile_hash": context.profile_hash,
        "template_hash": context.template_hash,
        "schema_hash": context.schema_hash,
        "classification_ceiling": context.classification_ceiling,
        "retention_policy": context.retention_policy,
        "source_checksum": _digest({"source_text": packet.source_text}),
        "conversation_checksum": _digest(
            [{"role": item.role, "content": item.content} for item in packet.conversation]
        ),
        "evidence_checksum": _digest(provenance["evidence"]),
        "graph_checksum": _digest(
            {
                "snapshot_version": packet.graph.snapshot_version,
                "nodes": [dict(node) for node in packet.graph.nodes],
                "edges": [dict(edge) for edge in packet.graph.edges],
            }
        ),
        "provenance_json": provenance,
        "validated_output": output,
        "output_checksum": output_checksum,
        "runtime_metadata_hash": _digest(runtime_metadata),
        "runtime_metadata_keys": sorted(runtime_metadata),
        "execution_duration_ms": int(round(result.execution.duration_seconds * 1000)),
        "validation_attempts": result.validation_attempts,
    }


def _assert_same_receipt(existing: BAStageReceipt, values: Mapping[str, Any]) -> None:
    """Reject an idempotency collision that represents a different immutable result."""
    comparable = (
        "organization_id",
        "project_id",
        "discovery_session_id",
        "stage",
        "context_snapshot_hash",
        "scope_partition_hash",
        "source_revision",
        "conversation_revision",
        "policy_revision",
        "profile_hash",
        "template_hash",
        "schema_hash",
        "classification_ceiling",
        "retention_policy",
        "source_checksum",
        "conversation_checksum",
        "evidence_checksum",
        "graph_checksum",
        "provenance_json",
        "validated_output",
        "output_checksum",
    )
    if any(getattr(existing, field) != values[field] for field in comparable):
        raise ValueError("BA stage receipt idempotency collision has inconsistent immutable content")


def _json_value(value: JSONValue) -> JSONValue:
    """Round-trip JSON to reject non-serializable subclasses and detach mutable data."""
    return json.loads(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False))


def _json_object(value: Mapping[str, JSONValue]) -> JSONObject:
    """Copy a JSON object into a detached canonical mapping."""
    copied = _json_value(dict(value))
    if not isinstance(copied, dict):  # pragma: no cover - defensive type narrowing
        raise ValueError("candidate payload must be a JSON object")
    return copied


def _hash_json(value: JSONValue | Mapping[str, Any] | Sequence[Any]) -> str:
    """Hash canonical JSON without retaining a second plaintext copy."""
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _digest(value: Any) -> str:
    """Return a canonical SHA-256 digest for non-secret provenance and keys."""
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256(encoded.encode("utf-8")).hexdigest()


def _new_id(prefix: str) -> str:
    """Generate a portable opaque primary key without embedding tenant metadata."""
    return f"{prefix}:{uuid4().hex}"


def _safe_error_summary(value: str) -> str:
    """Bound worker error storage; callers must provide an already-sanitized summary."""
    return value.replace("\x00", "")[:2_000]
