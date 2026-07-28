"""Backfill role-relevant certifications for every agent.

Revision ID: 0035
Revises: 0034
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0035"
down_revision: str | None = "0034"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
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


def downgrade() -> None:
    # Existing credentials are useful agent profile data and are intentionally
    # preserved if this schema migration is rolled back.
    pass
