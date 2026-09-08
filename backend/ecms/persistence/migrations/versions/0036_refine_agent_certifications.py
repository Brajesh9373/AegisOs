"""Refine generated certifications using agent role identity.

Revision ID: 0036
Revises: 0035
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0036_refine_agent_certifications"
down_revision: str | None = "0035_backfill_agent_certificates"
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


def _upgrade_sqlite() -> None:
    """Same refinement with LIKE chains and json_extract (no ~, CONCAT_WS, casts)."""
    identity = (
        "LOWER(COALESCE(name,'') || ' ' || COALESCE(role,'') || ' ' || "
        "COALESCE(designation,'') || ' ' || COALESCE(department,''))"
    )
    context = (
        "LOWER(COALESCE(name,'') || ' ' || COALESCE(role,'') || ' ' || "
        "COALESCE(designation,'') || ' ' || COALESCE(department,'') || ' ' || "
        "COALESCE(role_description,'') || ' ' || COALESCE(CAST(skills AS TEXT),''))"
    )
    whens = []
    for subject in (identity, context):
        for alternation, cert in _pairs():
            likes = " OR ".join(f"{subject} LIKE '%{alt}%'" for alt in alternation.split("|"))
            whens.append(f"WHEN {likes} THEN '{cert}'")
    whens.append(f"ELSE '{_FALLBACK}'")
    op.execute(
        "UPDATE agents SET certificates = CASE " + " ".join(whens) + " END "
        "WHERE json_array_length(certificates) = 1 "
        "AND json_extract(certificates, '$[0].name') IN ("
        "'ISC2 Certified in Cybersecurity (CC)',"
        "'ISTQB Certified Tester Foundation Level (CTFL)',"
        "'Certified Kubernetes Administrator (CKA)',"
        "'Entry Certificate in Business Analysis (ECBA)',"
        "'TOGAF Enterprise Architecture Foundation',"
        "'Databricks Certified Data Engineer Associate',"
        "'PCEP – Certified Entry-Level Python Programmer',"
        "'Project Management Professional (PMP)',"
        "'GitHub Foundations')"
    )


def upgrade() -> None:
    if op.get_bind().dialect.name == "sqlite":
        _upgrade_sqlite()
        return
    identity = "LOWER(CONCAT_WS(' ', name, role, designation, department))"
    context = (
        "LOWER(CONCAT_WS(' ', name, role, designation, department, "
        "role_description, CAST(skills AS TEXT)))"
    )
    known_generated_names = """
        'ISC2 Certified in Cybersecurity (CC)',
        'ISTQB Certified Tester Foundation Level (CTFL)',
        'Certified Kubernetes Administrator (CKA)',
        'Entry Certificate in Business Analysis (ECBA)',
        'TOGAF Enterprise Architecture Foundation',
        'Databricks Certified Data Engineer Associate',
        'PCEP – Certified Entry-Level Python Programmer',
        'Project Management Professional (PMP)',
        'GitHub Foundations'
    """
    op.execute(
        f"""
        UPDATE agents
        SET certificates = CASE
            WHEN {identity} ~ '(security|compliance|privacy|risk)'
                THEN '[{{"name":"ISC2 Certified in Cybersecurity (CC)","issuer":"ISC2","url":"https://www.isc2.org/certifications/cc"}}]'::json
            WHEN {identity} ~ '(qa|quality|test|uat|acceptance)'
                THEN '[{{"name":"ISTQB Certified Tester Foundation Level (CTFL)","issuer":"ISTQB","url":"https://www.istqb.org/certifications/certified-tester-foundation-level"}}]'::json
            WHEN {identity} ~ '(devops|sre|reliability|infrastructure|kubernetes|platform)'
                THEN '[{{"name":"Certified Kubernetes Administrator (CKA)","issuer":"Cloud Native Computing Foundation","url":"https://www.cncf.io/training/certification/cka/"}}]'::json
            WHEN {identity} ~ '(business analyst|business_analysis|requirements|discovery)'
                THEN '[{{"name":"Entry Certificate in Business Analysis (ECBA)","issuer":"IIBA","url":"https://www.iiba.org/business-analysis-certifications/ecba/"}}]'::json
            WHEN {identity} ~ '(architect|architecture|solution design|integration)'
                THEN '[{{"name":"TOGAF Enterprise Architecture Foundation","issuer":"The Open Group","url":"https://www.opengroup.org/certifications/togaf-certification-portfolio"}}]'::json
            WHEN {identity} ~ '(data|migration|etl|database|mysql)'
                THEN '[{{"name":"Databricks Certified Data Engineer Associate","issuer":"Databricks","url":"https://www.databricks.com/learn/certification/data-engineer-associate"}}]'::json
            WHEN {identity} ~ '(frappe|erpnext|configuration|python|engineer|developer)'
                THEN '[{{"name":"PCEP – Certified Entry-Level Python Programmer","issuer":"Python Institute","url":"https://pythoninstitute.org/pcep"}}]'::json
            WHEN {identity} ~ '(delivery|project manager|program manager|lead|manager)'
                THEN '[{{"name":"Project Management Professional (PMP)","issuer":"Project Management Institute","url":"https://www.pmi.org/certifications/project-management-pmp"}}]'::json
            WHEN {context} ~ '(security|compliance|privacy|risk)'
                THEN '[{{"name":"ISC2 Certified in Cybersecurity (CC)","issuer":"ISC2","url":"https://www.isc2.org/certifications/cc"}}]'::json
            WHEN {context} ~ '(qa|quality|test|uat|acceptance)'
                THEN '[{{"name":"ISTQB Certified Tester Foundation Level (CTFL)","issuer":"ISTQB","url":"https://www.istqb.org/certifications/certified-tester-foundation-level"}}]'::json
            WHEN {context} ~ '(devops|sre|reliability|infrastructure|kubernetes|platform)'
                THEN '[{{"name":"Certified Kubernetes Administrator (CKA)","issuer":"Cloud Native Computing Foundation","url":"https://www.cncf.io/training/certification/cka/"}}]'::json
            WHEN {context} ~ '(business analyst|business_analysis|requirements|discovery)'
                THEN '[{{"name":"Entry Certificate in Business Analysis (ECBA)","issuer":"IIBA","url":"https://www.iiba.org/business-analysis-certifications/ecba/"}}]'::json
            WHEN {context} ~ '(architect|architecture|solution design|integration)'
                THEN '[{{"name":"TOGAF Enterprise Architecture Foundation","issuer":"The Open Group","url":"https://www.opengroup.org/certifications/togaf-certification-portfolio"}}]'::json
            WHEN {context} ~ '(data|migration|etl|database|mysql)'
                THEN '[{{"name":"Databricks Certified Data Engineer Associate","issuer":"Databricks","url":"https://www.databricks.com/learn/certification/data-engineer-associate"}}]'::json
            WHEN {context} ~ '(frappe|erpnext|configuration|python|engineer|developer)'
                THEN '[{{"name":"PCEP – Certified Entry-Level Python Programmer","issuer":"Python Institute","url":"https://pythoninstitute.org/pcep"}}]'::json
            WHEN {context} ~ '(delivery|project manager|program manager|lead|manager)'
                THEN '[{{"name":"Project Management Professional (PMP)","issuer":"Project Management Institute","url":"https://www.pmi.org/certifications/project-management-pmp"}}]'::json
            ELSE '[{{"name":"GitHub Foundations","issuer":"GitHub","url":"https://learn.microsoft.com/en-us/credentials/certifications/github-foundations/"}}]'::json
        END
        WHERE json_array_length(certificates) = 1
          AND certificates->0->>'name' IN ({known_generated_names})
        """
    )


def downgrade() -> None:
    pass
