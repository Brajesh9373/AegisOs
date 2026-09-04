"""Compliance Officer Agent OS profile package.

The profile is deployment-owned and intentionally inactive until the durable
Agent OS profile activation control plane is available.
"""

from ecms.agent.compliance_officer.dsh_profile import compliance_officer_dsh_profile_spec
from ecms.agent.compliance_officer.plugin import ComplianceOfficerProfilePlugin

__all__ = ["ComplianceOfficerProfilePlugin", "compliance_officer_dsh_profile_spec"]
