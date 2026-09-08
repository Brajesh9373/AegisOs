"""Backfill role-relevant certifications for every agent.

Revision ID: 0035
Revises: 0034
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0035_backfill_agent_certificates"
down_revision: str | None = "0034_org_tool_assignments"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def _pairs() -> list[tuple[str, str]]:
    """(alternation, certificate JSON) pairs shared by both dialects."""
    return [
        (
            "security|compliance|privacy|risk",
            '[{"name":"ISC2 Certified in Cybersecurity (CC)","issuer":"ISC2","url":"https://www.isc2.org/certifications/cc"}]',
        ),
        (
            "qa|quality|test|uat|acceptance",
            '[{"name":"ISTQB Certified Tester Foundation Level (CTFL)","issuer":"ISTQB","url":"https://www.istqb.org/certifications/certified-tester-foundation-level"}]',
        ),
        (
            "devops|sre|reliability|infrastructure|kubernetes|platform",
            '[{"name":"Certified Kubernetes Administrator (CKA)","issuer":"Cloud Native Computing Foundation","url":"https://www.cncf.io/training/certification/cka/"}]',
        ),
        (
            "business analyst|business_analysis|requirements|discovery",
            '[{"name":"Entry Certificate in Business Analysis (ECBA)","issuer":"IIBA","url":"https://www.iiba.org/business-analysis-certifications/ecba/"}]',
        ),
        (
            "architect|architecture|solution design|integration",
            '[{"name":"TOGAF Enterprise Architecture Foundation","issuer":"The Open Group","url":"https://www.opengroup.org/certifications/togaf-certification-portfolio"}]',
        ),
        (
            "data|migration|etl|database|mysql",
            '[{"name":"Databricks Certified Data Engineer Associate","issuer":"Databricks","url":"https://www.databricks.com/learn/certification/data-engineer-associate"}]',
        ),
        (
            "frappe|erpnext|configuration|python|engineer|developer",
            '[{"name":"PCEP – Certified Entry-Level Python Programmer","issuer":"Python Institute","url":"https://pythoninstitute.org/pcep"}]',
        ),
        (
            "delivery|project manager|program manager|lead|manager",
            '[{"name":"Project Management Professional (PMP)","issuer":"Project Management Institute","url":"https://www.pmi.org/certifications/project-management-pmp"}]',
        ),
    ]


_FALLBACK = '[{"name":"GitHub Foundations","issuer":"GitHub","url":"https://learn.microsoft.com/en-us/credentials/certifications/github-foundations/"}]'


def upgrade() -> None:
    if op.get_bind().dialect.name == "sqlite":
        _upgrade_sqlite()
        return
    profile = (
        "LOWER(CONCAT_WS(' ', name, role, designation, department, "
        "role_description, CAST(skills AS TEXT)))"
    )
    op.execute(
        f"""
        UPDATE agents
        SET certificates = CASE
            WHEN {profile} ~ '(security|compliance|privacy|risk)'
                THEN '[{{"name":"ISC2 Certified in Cybersecurity (CC)","issuer":"ISC2","url":"https://www.isc2.org/certifications/cc"}}]'::json
            WHEN {profile} ~ '(qa|quality|test|uat|acceptance)'
                THEN '[{{"name":"ISTQB Certified Tester Foundation Level (CTFL)","issuer":"ISTQB","url":"https://www.istqb.org/certifications/certified-tester-foundation-level"}}]'::json
            WHEN {profile} ~ '(devops|sre|reliability|infrastructure|kubernetes|platform)'
                THEN '[{{"name":"Certified Kubernetes Administrator (CKA)","issuer":"Cloud Native Computing Foundation","url":"https://www.cncf.io/training/certification/cka/"}}]'::json
            WHEN {profile} ~ '(business analyst|business_analysis|requirements|discovery)'
                THEN '[{{"name":"Entry Certificate in Business Analysis (ECBA)","issuer":"IIBA","url":"https://www.iiba.org/business-analysis-certifications/ecba/"}}]'::json
            WHEN {profile} ~ '(architect|architecture|solution design|integration)'
                THEN '[{{"name":"TOGAF Enterprise Architecture Foundation","issuer":"The Open Group","url":"https://www.opengroup.org/certifications/togaf-certification-portfolio"}}]'::json
            WHEN {profile} ~ '(data|migration|etl|database|mysql)'
                THEN '[{{"name":"Databricks Certified Data Engineer Associate","issuer":"Databricks","url":"https://www.databricks.com/learn/certification/data-engineer-associate"}}]'::json
            WHEN {profile} ~ '(frappe|erpnext|configuration|python|engineer|developer)'
                THEN '[{{"name":"PCEP – Certified Entry-Level Python Programmer","issuer":"Python Institute","url":"https://pythoninstitute.org/pcep"}}]'::json
            WHEN {profile} ~ '(delivery|project manager|program manager|lead|manager)'
                THEN '[{{"name":"Project Management Professional (PMP)","issuer":"Project Management Institute","url":"https://www.pmi.org/certifications/project-management-pmp"}}]'::json
            ELSE '[{{"name":"GitHub Foundations","issuer":"GitHub","url":"https://learn.microsoft.com/en-us/credentials/certifications/github-foundations/"}}]'::json
        END
        WHERE certificates IS NULL
           OR json_array_length(certificates) = 0
        """
    )


def _upgrade_sqlite() -> None:
    """Same backfill with LIKE chains (no ~ regex, CONCAT_WS, or casts)."""
    profile = (
        "LOWER(COALESCE(name,'') || ' ' || COALESCE(role,'') || ' ' || "
        "COALESCE(designation,'') || ' ' || COALESCE(department,'') || ' ' || "
        "COALESCE(role_description,'') || ' ' || COALESCE(CAST(skills AS TEXT),''))"
    )
    whens = []
    for alternation, cert in _pairs():
        likes = " OR ".join(f"{profile} LIKE '%{alt}%'" for alt in alternation.split("|"))
        whens.append(f"WHEN {likes} THEN '{cert}'")
    whens.append(f"ELSE '{_FALLBACK}'")
    op.execute(
        "UPDATE agents SET certificates = CASE " + " ".join(whens) + " END "
        "WHERE certificates IS NULL OR json_array_length(certificates) = 0"
    )


def downgrade() -> None:
    # Existing credentials are useful agent profile data and are intentionally
    # preserved if this schema migration is rolled back.
    pass
