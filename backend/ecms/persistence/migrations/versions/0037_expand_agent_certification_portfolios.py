"""Expand generated agent certificates into role-specific portfolios.

Revision ID: 0037
Revises: 0036
"""

from __future__ import annotations

from collections.abc import Sequence

from alembic import op

revision: str = "0037_expand_agent_certification_portfolios"
down_revision: str | None = "0036_refine_agent_certifications"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    identity = "LOWER(CONCAT_WS(' ', name, role, designation, department))"
    context = (
        "LOWER(CONCAT_WS(' ', name, role, designation, department, "
        "role_description, CAST(skills AS TEXT)))"
    )
    generated_names = """
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

    security = """[
      {"name":"ISC2 Certified in Cybersecurity (CC)","issuer":"ISC2","url":"https://www.isc2.org/certifications/cc"},
      {"name":"CompTIA Security+","issuer":"CompTIA","url":"https://www.comptia.org/certifications/security"},
      {"name":"AWS Certified Security – Specialty","issuer":"Amazon Web Services","url":"https://aws.amazon.com/certification/certified-security-specialty/"}
    ]"""
    quality = """[
      {"name":"ISTQB Certified Tester Foundation Level (CTFL)","issuer":"ISTQB","url":"https://www.istqb.org/certifications/certified-tester-foundation-level"},
      {"name":"ISTQB Agile Tester (CTFL-AT)","issuer":"ISTQB","url":"https://www.istqb.org/certifications/certified-tester-foundation-level-agile-tester"},
      {"name":"ISTQB Test Automation Engineering (CTAL-TAE)","issuer":"ISTQB","url":"https://www.istqb.org/certifications/test-automation-engineer"}
    ]"""
    devops = """[
      {"name":"Certified Kubernetes Administrator (CKA)","issuer":"Cloud Native Computing Foundation","url":"https://www.cncf.io/training/certification/cka/"},
      {"name":"Certified Kubernetes Application Developer (CKAD)","issuer":"Cloud Native Computing Foundation","url":"https://www.cncf.io/training/certification/ckad/"},
      {"name":"HashiCorp Certified: Terraform Associate","issuer":"HashiCorp","url":"https://developer.hashicorp.com/certifications/infrastructure-automation"}
    ]"""
    analysis = """[
      {"name":"Entry Certificate in Business Analysis (ECBA)","issuer":"IIBA","url":"https://www.iiba.org/business-analysis-certifications/ecba/"},
      {"name":"Certification of Capability in Business Analysis (CCBA)","issuer":"IIBA","url":"https://www.iiba.org/business-analysis-certifications/ccba/"},
      {"name":"PMI Professional in Business Analysis (PMI-PBA)","issuer":"Project Management Institute","url":"https://www.pmi.org/certifications/business-analysis-pba"}
    ]"""
    architecture = """[
      {"name":"TOGAF Enterprise Architecture Foundation","issuer":"The Open Group","url":"https://www.opengroup.org/certifications/togaf-certification-portfolio"},
      {"name":"AWS Certified Solutions Architect – Associate","issuer":"Amazon Web Services","url":"https://aws.amazon.com/certification/certified-solutions-architect-associate/"},
      {"name":"Microsoft Certified: Azure Solutions Architect Expert","issuer":"Microsoft","url":"https://learn.microsoft.com/en-us/credentials/certifications/azure-solutions-architect/"}
    ]"""
    data = """[
      {"name":"Databricks Certified Data Engineer Associate","issuer":"Databricks","url":"https://www.databricks.com/learn/certification/data-engineer-associate"},
      {"name":"Google Cloud Professional Data Engineer","issuer":"Google Cloud","url":"https://cloud.google.com/learn/certification/data-engineer"},
      {"name":"AWS Certified Data Engineer – Associate","issuer":"Amazon Web Services","url":"https://aws.amazon.com/certification/certified-data-engineer-associate/"}
    ]"""
    engineering = """[
      {"name":"PCEP – Certified Entry-Level Python Programmer","issuer":"Python Institute","url":"https://pythoninstitute.org/pcep"},
      {"name":"PCAP – Certified Associate Python Programmer","issuer":"Python Institute","url":"https://pythoninstitute.org/pcap"},
      {"name":"GitHub Foundations","issuer":"GitHub","url":"https://learn.microsoft.com/en-us/credentials/certifications/github-foundations/"}
    ]"""
    delivery = """[
      {"name":"Project Management Professional (PMP)","issuer":"Project Management Institute","url":"https://www.pmi.org/certifications/project-management-pmp"},
      {"name":"PMI Agile Certified Practitioner (PMI-ACP)","issuer":"Project Management Institute","url":"https://www.pmi.org/certifications/agile-acp"},
      {"name":"Professional Scrum Master I (PSM I)","issuer":"Scrum.org","url":"https://www.scrum.org/professional-scrum-master-certification"}
    ]"""
    fallback = """[
      {"name":"GitHub Foundations","issuer":"GitHub","url":"https://learn.microsoft.com/en-us/credentials/certifications/github-foundations/"},
      {"name":"PCEP – Certified Entry-Level Python Programmer","issuer":"Python Institute","url":"https://pythoninstitute.org/pcep"}
    ]"""

    def cases(profile: str) -> str:
        return f"""
            WHEN {profile} ~ '(security|compliance|privacy|risk)' THEN '{security}'::json
            WHEN {profile} ~ '(qa|quality|test|uat|acceptance)' THEN '{quality}'::json
            WHEN {profile} ~ '(devops|sre|reliability|infrastructure|kubernetes|platform)' THEN '{devops}'::json
            WHEN {profile} ~ '(business analyst|business_analysis|requirements|discovery)' THEN '{analysis}'::json
            WHEN {profile} ~ '(architect|architecture|solution design|integration)' THEN '{architecture}'::json
            WHEN {profile} ~ '(data|migration|etl|database|mysql)' THEN '{data}'::json
            WHEN {profile} ~ '(frappe|erpnext|configuration|python|engineer|developer)' THEN '{engineering}'::json
            WHEN {profile} ~ '(delivery|project manager|program manager|lead|manager)' THEN '{delivery}'::json
        """

    op.execute(
        f"""
        UPDATE agents
        SET certificates = CASE
            {cases(identity)}
            {cases(context)}
            ELSE '{fallback}'::json
        END
        WHERE json_array_length(certificates) = 1
          AND certificates->0->>'name' IN ({generated_names})
        """
    )


def downgrade() -> None:
    pass
