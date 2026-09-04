"""Business Analyst's deployment-owned DSH profile contract."""

from __future__ import annotations

from pathlib import Path

from ecms.agent_os.profiles.contracts import DSHProfileSpec, StageSpec

__all__ = ["business_analyst_dsh_profile_spec"]


def business_analyst_dsh_profile_spec() -> DSHProfileSpec:
    """Return the BA profile's static artifact and gateway requirements.

    The shared DSH runtime treats this object as opaque host-owned configuration;
    BA alone owns its stage vocabulary and model-gateway environment needs.
    """
    repository_root = Path(__file__).resolve().parents[4]
    return DSHProfileSpec(
        profile_id="business-analyst",
        version="1.0.0",
        asset_root=repository_root
        / "packages"
        / "dsh-integration"
        / "profiles"
        / "business-analyst",
        required_environment=("ANTHROPIC_BASE_URL", "ANTHROPIC_AUTH_TOKEN"),
        generated_environment=("CLAUDE_CODE_SESSION_ID",),
        stages=(
            StageSpec(
                stage_id="understand",
                request_schema_ref="schemas/understand-request.json",
                terminal_schema_ref="schemas/understand-result.json",
                max_repair_attempts=1,
            ),
            StageSpec(
                stage_id="clarify",
                request_schema_ref="schemas/clarify-request.json",
                terminal_schema_ref="schemas/clarify-result.json",
                max_repair_attempts=1,
            ),
            StageSpec(
                stage_id="finalize",
                request_schema_ref="schemas/finalize-request.json",
                terminal_schema_ref="schemas/finalize-result.json",
                max_repair_attempts=1,
            ),
            StageSpec(
                stage_id="design-team",
                request_schema_ref="schemas/design-team-request.json",
                terminal_schema_ref="schemas/design-team-result.json",
                max_repair_attempts=1,
            ),
        ),
    )
