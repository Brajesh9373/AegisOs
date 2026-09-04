"""Persistence invariants for durable Business Analyst stage outcomes."""

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import func, select

from ecms.agent.ba.cognition.contracts import (
    BAExecutionContext,
    BAExecutionResponse,
    BAStage,
    BAStageResult,
    PromptContextPacket,
)
from ecms.agent.ba.cognition.durable_writer import (
    BACandidatePolicy,
    BAPromotionOutboxRepository,
    BAStageOutcomeRepository,
)
from ecms.persistence import Database
from ecms.persistence.models import ba_stage_outcome  # noqa: F401 - registers tables
from ecms.persistence.models.ba_stage_outcome import BACandidate, BAPromotionOutbox, BAStageReceipt
from ecms.shared.time import utcnow


@pytest.fixture
async def database(tmp_path):
    """Create an isolated database with the durable BA outcome schema."""
    db = Database(f"sqlite+aiosqlite:///{tmp_path.as_posix()}/ba-outcomes.db")
    await db.create_all()
    yield db
    await db.dispose()


def _result(
    *,
    organization_id: str = "org-a",
    discovery_session_id: str = "discovery-a",
    source_revision: str = "source-v1",
    output: dict[str, object] | None = None,
) -> BAStageResult:
    """Build a validated finalization result suitable for durable persistence."""
    context = BAExecutionContext(
        actor_id="actor-a",
        organization_id=organization_id,
        discovery_session_id=discovery_session_id,
        correlation_id="correlation-a",
        source_revision=source_revision,
        conversation_revision="conversation-v1",
        policy_revision="policy-v1",
        classification_ceiling="internal",
        profile_hash="profile-v1",
        template_hash="template-v1",
        schema_hash="schema-v1",
        project_id="project-a",
        scope_ids=("project-a",),
    )
    packet = PromptContextPacket(
        context=context,
        source_text="Build the project",
        conversation=(),
    )
    return BAStageResult(
        stage=BAStage.FINALIZE,
        packet=packet,
        output=output
        or {
            "projectName": "Aegis",
            "objective": "Deliver governed automation",
            "functionalReqs": ["Audit every transition"],
        },
        execution=BAExecutionResponse(
            output="validated by the host",
            duration_seconds=0.123,
            runtime_metadata={"profile": "business-analyst"},
        ),
        validation_attempts=1,
    )


class _ExplodingCandidatePolicy(BACandidatePolicy):
    """Test policy that fails after receipt creation would otherwise occur."""

    def extract(self, result: BAStageResult):  # type: ignore[override]
        raise RuntimeError("candidate policy failure")


async def test_record_rolls_back_the_full_durable_unit_on_policy_failure(
    database: Database,
) -> None:
    """A caught policy error cannot leave an orphaned immutable receipt behind."""
    async with database.session() as session:
        repository = BAStageOutcomeRepository(session)
        with pytest.raises(RuntimeError, match="candidate policy failure"):
            await repository.record(_result(), policy=_ExplodingCandidatePolicy())
        assert await session.scalar(select(func.count()).select_from(BAStageReceipt)) == 0
        assert await session.scalar(select(func.count()).select_from(BACandidate)) == 0
        assert await session.scalar(select(func.count()).select_from(BAPromotionOutbox)) == 0


async def test_records_receipt_and_approval_gated_candidate_atomically(database: Database) -> None:
    """A final result produces a receipt and a candidate, never immediate projection work."""
    async with database.session() as session:
        receipt = await BAStageOutcomeRepository(session).record(
            _result(), policy=BACandidatePolicy()
        )
        assert receipt.stage == "finalize"
        assert receipt.candidate_outcomes == [
            {
                "candidate_id": receipt.candidate_outcomes[0]["candidate_id"],
                "kind": "finalized_requirements",
                "state": "pending_approval",
            }
        ]
        candidate = await session.get(BACandidate, receipt.candidate_outcomes[0]["candidate_id"])
        assert candidate is not None
        assert candidate.organization_id == "org-a"
        assert candidate.state == "pending_approval"
        assert candidate.approval_required is True
        assert (
            await session.scalar(
                BAPromotionOutbox.__table__.select()
                .with_only_columns(BAPromotionOutbox.id)
                .limit(1)
            )
            is None
        )


async def test_duplicate_stage_delivery_returns_same_immutable_receipt(database: Database) -> None:
    """The revision identity prevents duplicate receipts, candidates, and outbox work."""
    async with database.session() as session:
        repository = BAStageOutcomeRepository(session)
        first = await repository.record(_result(), policy=BACandidatePolicy())
        duplicate = await repository.record(_result(), policy=BACandidatePolicy())
        assert duplicate.id == first.id
        assert await session.scalar(select(func.count()).select_from(BAStageReceipt)) == 1

    async with database.session() as session:
        receipts = (await session.execute(BAStageReceipt.__table__.select())).all()
        candidates = (await session.execute(BACandidate.__table__.select())).all()
        assert len(receipts) == 1
        assert len(candidates) == 1


async def test_idempotency_collision_with_different_output_is_rejected(database: Database) -> None:
    """The same stage revision cannot silently overwrite immutable validated output."""
    async with database.session() as session:
        repository = BAStageOutcomeRepository(session)
        await repository.record(_result(), policy=BACandidatePolicy())
        with pytest.raises(ValueError, match="idempotency collision"):
            await repository.record(
                _result(output={"projectName": "Changed", "objective": "Different"}),
                policy=BACandidatePolicy(),
            )


async def test_approval_creates_claimable_outbox_and_tenant_scopes_records(
    database: Database,
) -> None:
    """Approval is explicit and cross-organization lookups cannot see the candidate."""
    async with database.session() as session:
        repository = BAStageOutcomeRepository(session)
        receipt = await repository.record(_result(), policy=BACandidatePolicy())
        candidate_id = receipt.candidate_outcomes[0]["candidate_id"]
        approved = await repository.approve_candidate(candidate_id, organization_id="org-a")
        assert approved is not None
        assert approved.state == "queued_for_projection"
        assert approved.approved_at is not None
        assert await repository.approve_candidate(candidate_id, organization_id="org-b") is None

    async with database.session() as session:
        outbox = await BAPromotionOutboxRepository(session).claim_next(
            worker_id="worker-a", lease_seconds=60
        )
        assert outbox is not None
        assert outbox.organization_id == "org-a"
        assert outbox.state == "leased"
        assert outbox.attempt == 1


async def test_outbox_respects_scheduled_retry_and_recovers_expired_leases(
    database: Database,
) -> None:
    """Workers cannot claim work before availability and can reclaim failed leases."""
    async with database.session() as session:
        outcomes = BAStageOutcomeRepository(session)
        receipt = await outcomes.record(_result(), policy=BACandidatePolicy())
        candidate_id = receipt.candidate_outcomes[0]["candidate_id"]
        await outcomes.approve_candidate(candidate_id, organization_id="org-a")
        outbox_repository = BAPromotionOutboxRepository(session)
        first = await outbox_repository.claim_next(worker_id="worker-a", lease_seconds=1)
        assert first is not None
        retry = await outbox_repository.retry_or_dead_letter(
            first.id,
            worker_id="worker-a",
            error_code="TRANSIENT",
            error_summary="temporary dependency issue",
            available_at=utcnow() + timedelta(minutes=5),
        )
        assert retry is not None
        assert retry.state == "retry"
        assert await outbox_repository.claim_next(worker_id="worker-b", lease_seconds=60) is None
        retry.available_at = utcnow() - timedelta(seconds=1)
        reclaimed = await outbox_repository.claim_next(worker_id="worker-b", lease_seconds=60)
        assert reclaimed is not None
        assert reclaimed.id == first.id
        assert reclaimed.attempt == 2


async def test_expired_final_attempt_is_dead_lettered_without_reclaim(database: Database) -> None:
    """An abandoned final lease is terminal work, never an unbounded reclaim loop."""
    async with database.session() as session:
        outcomes = BAStageOutcomeRepository(session)
        receipt = await outcomes.record(_result(), policy=BACandidatePolicy())
        candidate_id = receipt.candidate_outcomes[0]["candidate_id"]
        await outcomes.approve_candidate(candidate_id, organization_id="org-a")
        outbox_repository = BAPromotionOutboxRepository(session)
        clock = utcnow()
        leased = await outbox_repository.claim_next(
            worker_id="worker-a", lease_seconds=60, now=clock
        )
        assert leased is not None
        leased.max_attempts = 1
        leased.lease_expires_at = clock - timedelta(seconds=1)

        assert (
            await outbox_repository.claim_next(worker_id="worker-b", lease_seconds=60, now=clock)
            is None
        )
        await session.refresh(leased)
        assert leased.state == "dead_letter"
        assert leased.lease_owner is None
        assert leased.lease_expires_at is None
        assert leased.error_code == "LEASE_EXPIRED"


async def test_dead_letter_after_bounded_attempts_and_rejection_revokes_lease(
    database: Database,
) -> None:
    """Exhausted projection work is retained and a rejection prevents stale completion."""
    async with database.session() as session:
        outcomes = BAStageOutcomeRepository(session)
        receipt = await outcomes.record(_result(), policy=BACandidatePolicy())
        candidate_id = receipt.candidate_outcomes[0]["candidate_id"]
        await outcomes.approve_candidate(candidate_id, organization_id="org-a")
        outbox_repository = BAPromotionOutboxRepository(session)
        outbox = await outbox_repository.claim_next(worker_id="worker-a", lease_seconds=60)
        assert outbox is not None
        outbox.max_attempts = 1
        dead = await outbox_repository.retry_or_dead_letter(
            outbox.id,
            worker_id="worker-a",
            error_code="PERMANENT",
            error_summary="projection failed after retries",
        )
        assert dead is not None
        assert dead.state == "dead_letter"

        # A separate candidate shows that an active lease is revoked on rejection.
        receipt_two = await outcomes.record(
            _result(source_revision="source-v2"), policy=BACandidatePolicy()
        )
        candidate_two = receipt_two.candidate_outcomes[0]["candidate_id"]
        await outcomes.approve_candidate(candidate_two, organization_id="org-a")
        leased = await outbox_repository.claim_next(worker_id="worker-b", lease_seconds=60)
        assert leased is not None
        rejected = await outcomes.reject_candidate(candidate_two, organization_id="org-a")
        assert rejected is not None
        assert rejected.state == "rejected"
        assert (
            await outbox_repository.complete(leased.id, worker_id="worker-b", outcome="promoted")
            is None
        )


async def test_terminal_deduplicated_candidate_is_not_requeued(database: Database) -> None:
    """Canonical deduplication is terminal and cannot create a second outbox job."""
    async with database.session() as session:
        outcomes = BAStageOutcomeRepository(session)
        receipt = await outcomes.record(_result(), policy=BACandidatePolicy())
        candidate_id = receipt.candidate_outcomes[0]["candidate_id"]
        await outcomes.approve_candidate(candidate_id, organization_id="org-a")
        outbox_repository = BAPromotionOutboxRepository(session)
        outbox = await outbox_repository.claim_next(worker_id="worker-a", lease_seconds=60)
        assert outbox is not None
        candidate = await outbox_repository.complete(
            outbox.id, worker_id="worker-a", outcome="deduplicated"
        )
        assert candidate is not None
        assert candidate.state == "deduplicated"

        terminal = await outcomes.approve_candidate(candidate_id, organization_id="org-a")
        assert terminal is not None
        assert terminal.state == "deduplicated"
        assert await session.scalar(select(func.count()).select_from(BAPromotionOutbox)) == 1
        assert await outbox_repository.claim_next(worker_id="worker-b", lease_seconds=60) is None
