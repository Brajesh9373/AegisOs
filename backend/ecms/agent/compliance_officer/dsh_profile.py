"""Deployment-owned DSH artifact contract for Compliance Officer."""

from __future__ import annotations

from pathlib import Path

from ecms.agent_os.profiles.contracts import DSHProfileSpec, StageSpec

__all__ = ["compliance_officer_dsh_profile_spec"]


def compliance_officer_dsh_profile_spec() -> DSHProfileSpec:
    """Return the inactive, read-only Compliance Officer profile contract.

    This declaration does not activate the profile for any tenant. Activation,
    capability grants, and invocation remain unavailable until the durable Agent
    OS control plane registers them.
    """
    repository_root = Path(__file__).resolve().parents[4]
    return DSHProfileSpec(
        profile_id="compliance-officer",
        version="1.0.0",
        asset_root=(
            repository_root / "packages" / "dsh-integration" / "profiles" / "compliance-officer"
        ),
        required_environment=("ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN"),
        generated_environment=("CLAUDE_CODE_SESSION_ID",),
        stages=(
            StageSpec(
                stage_id="assess",
                request_schema_ref="schemas/compliance-assess-request.json",
                terminal_schema_ref="schemas/compliance-assess-result.json",
                max_repair_attempts=1,
                max_capability_requests=2,
                capability_ids=("knowledge.search.v1",),
            ),
        ),
    )
