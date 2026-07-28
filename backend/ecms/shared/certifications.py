"""Role-aware certification defaults for digital agents."""

from __future__ import annotations

from typing import Any

__all__ = ["default_certificates_for_agent"]


_CERTIFICATION_RULES: tuple[tuple[tuple[str, ...], tuple[dict[str, str], ...]], ...] = (
    (
        ("security", "compliance", "privacy", "risk"),
        (
            {
                "name": "ISC2 Certified in Cybersecurity (CC)",
                "issuer": "ISC2",
                "url": "https://www.isc2.org/certifications/cc",
            },
            {
                "name": "CompTIA Security+",
                "issuer": "CompTIA",
                "url": "https://www.comptia.org/certifications/security",
            },
            {
                "name": "AWS Certified Security – Specialty",
                "issuer": "Amazon Web Services",
                "url": "https://aws.amazon.com/certification/certified-security-specialty/",
            },
        ),
    ),
    (
        ("qa", "quality", "test", "uat", "acceptance"),
        (
            {
                "name": "ISTQB Certified Tester Foundation Level (CTFL)",
                "issuer": "ISTQB",
                "url": "https://www.istqb.org/certifications/certified-tester-foundation-level",
            },
            {
                "name": "ISTQB Agile Tester (CTFL-AT)",
                "issuer": "ISTQB",
                "url": "https://www.istqb.org/certifications/certified-tester-foundation-level-agile-tester",
            },
            {
                "name": "ISTQB Test Automation Engineering (CTAL-TAE)",
                "issuer": "ISTQB",
                "url": "https://www.istqb.org/certifications/test-automation-engineer",
            },
        ),
    ),
    (
        ("devops", "sre", "reliability", "infrastructure", "kubernetes", "platform"),
        (
            {
                "name": "Certified Kubernetes Administrator (CKA)",
                "issuer": "Cloud Native Computing Foundation",
                "url": "https://www.cncf.io/training/certification/cka/",
            },
            {
                "name": "Certified Kubernetes Application Developer (CKAD)",
                "issuer": "Cloud Native Computing Foundation",
                "url": "https://www.cncf.io/training/certification/ckad/",
            },
            {
                "name": "HashiCorp Certified: Terraform Associate",
                "issuer": "HashiCorp",
                "url": "https://developer.hashicorp.com/certifications/infrastructure-automation",
            },
        ),
    ),
    (
        ("business analyst", "business_analysis", "requirements", "discovery"),
        (
            {
                "name": "Entry Certificate in Business Analysis (ECBA)",
                "issuer": "IIBA",
                "url": "https://www.iiba.org/business-analysis-certifications/ecba/",
            },
            {
                "name": "Certification of Capability in Business Analysis (CCBA)",
                "issuer": "IIBA",
                "url": "https://www.iiba.org/business-analysis-certifications/ccba/",
            },
            {
                "name": "PMI Professional in Business Analysis (PMI-PBA)",
                "issuer": "Project Management Institute",
                "url": "https://www.pmi.org/certifications/business-analysis-pba",
            },
        ),
    ),
    (
        ("architect", "architecture", "solution design", "integration"),
        (
            {
                "name": "TOGAF Enterprise Architecture Foundation",
                "issuer": "The Open Group",
                "url": "https://www.opengroup.org/certifications/togaf-certification-portfolio",
            },
            {
                "name": "AWS Certified Solutions Architect – Associate",
                "issuer": "Amazon Web Services",
                "url": "https://aws.amazon.com/certification/certified-solutions-architect-associate/",
            },
            {
                "name": "Microsoft Certified: Azure Solutions Architect Expert",
                "issuer": "Microsoft",
                "url": "https://learn.microsoft.com/en-us/credentials/certifications/azure-solutions-architect/",
            },
        ),
    ),
    (
        ("data", "migration", "etl", "database", "mysql"),
        (
            {
                "name": "Databricks Certified Data Engineer Associate",
                "issuer": "Databricks",
                "url": "https://www.databricks.com/learn/certification/data-engineer-associate",
            },
            {
                "name": "Google Cloud Professional Data Engineer",
                "issuer": "Google Cloud",
                "url": "https://cloud.google.com/learn/certification/data-engineer",
            },
            {
                "name": "AWS Certified Data Engineer – Associate",
                "issuer": "Amazon Web Services",
                "url": "https://aws.amazon.com/certification/certified-data-engineer-associate/",
            },
        ),
    ),
    (
        ("frappe", "erpnext", "configuration", "python", "engineer", "developer"),
        (
            {
                "name": "PCEP – Certified Entry-Level Python Programmer",
                "issuer": "Python Institute",
                "url": "https://pythoninstitute.org/pcep",
            },
            {
                "name": "PCAP – Certified Associate Python Programmer",
                "issuer": "Python Institute",
                "url": "https://pythoninstitute.org/pcap",
            },
            {
                "name": "GitHub Foundations",
                "issuer": "GitHub",
                "url": "https://learn.microsoft.com/en-us/credentials/certifications/github-foundations/",
            },
        ),
    ),
    (
        ("delivery", "project manager", "program manager", "lead", "manager"),
        (
            {
                "name": "Project Management Professional (PMP)",
                "issuer": "Project Management Institute",
                "url": "https://www.pmi.org/certifications/project-management-pmp",
            },
            {
                "name": "PMI Agile Certified Practitioner (PMI-ACP)",
                "issuer": "Project Management Institute",
                "url": "https://www.pmi.org/certifications/agile-acp",
            },
            {
                "name": "Professional Scrum Master I (PSM I)",
                "issuer": "Scrum.org",
                "url": "https://www.scrum.org/professional-scrum-master-certification",
            },
        ),
    ),
)

_FALLBACK_CERTIFICATES = (
    {
        "name": "GitHub Foundations",
        "issuer": "GitHub",
        "url": "https://learn.microsoft.com/en-us/credentials/certifications/github-foundations/",
    },
    {
        "name": "PCEP – Certified Entry-Level Python Programmer",
        "issuer": "Python Institute",
        "url": "https://pythoninstitute.org/pcep",
    },
)


def default_certificates_for_agent(agent: dict[str, Any]) -> list[dict[str, str]]:
    """Return at least one certification relevant to an agent's role."""
    identity_values = (
        agent.get("name"),
        agent.get("role"),
        agent.get("designation"),
        agent.get("department"),
    )
    context_values = (
        *identity_values,
        agent.get("role_description"),
        *(agent.get("skills") or []),
    )
    identity = " ".join(str(value) for value in identity_values if value).lower()
    context = " ".join(str(value) for value in context_values if value).lower()

    # Role identity wins over incidental words in a long description. For
    # example, a Solution Architect may review testing output but is not a QA
    # worker and should therefore receive an architecture certification.
    for profile in (identity, context):
        for keywords, certificates in _CERTIFICATION_RULES:
            if any(keyword in profile for keyword in keywords):
                return [dict(certificate) for certificate in certificates]

    return [dict(certificate) for certificate in _FALLBACK_CERTIFICATES]
