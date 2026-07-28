"""Business Analyst agent — output schema and fixed taxonomy.

The approved frontend mock (NewProject.tsx) defines the exact output envelope
the BA agent must reproduce byte-for-byte. Content is derived from real project
input; the *structure* is fixed. The three detail sections (Governance,
Guardrails, Infrastructure) use a fixed label taxonomy — the LLM writes only the
`detail` string per fixed label, guaranteeing every project renders identically.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, field_validator

__all__ = [
    "GOVERNANCE_LABELS",
    "GUARDRAIL_LABELS",
    "INFRASTRUCTURE_LABELS",
    "DetailItem",
    "Phase",
    "FinalizedRequirements",
]

# ── Fixed taxonomy (order matters — panels render in this order) ────────────

GOVERNANCE_LABELS: tuple[str, ...] = (
    "Data Privacy",
    "Access Control",
    "Approval Workflow",
    "Compliance",
    "Change Management",
)

GUARDRAIL_LABELS: tuple[str, ...] = (
    "Data Validation",
    "Rollback Procedure",
    "Sync Safety",
    "Rate Limiting",
    "Monitoring Alerts",
    "Cutover Safety",
)

INFRASTRUCTURE_LABELS: tuple[str, ...] = (
    "Compute",
    "Database",
    "Networking",
    "Storage",
    "Messaging",
    "Monitoring",
)


# ── Models ──────────────────────────────────────────────────────────────────

class DetailItem(BaseModel):
    """A labeled detail entry (Governance / Guardrails / Infrastructure)."""

    label: str
    detail: str


class Phase(BaseModel):
    """A migration/delivery phase."""

    name: str
    duration: str
    description: str


class FinalizedRequirements(BaseModel):
    """The finalized requirements object — matches NewProject.tsx exactly."""

    project_name: str = Field(..., alias="projectName")
    objective: str
    functional_reqs: list[str] = Field(default_factory=list, alias="functionalReqs")
    tech_stack: list[str] = Field(default_factory=list, alias="techStack")
    skills: list[str] = Field(default_factory=list)
    connectors: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    phases: list[Phase] = Field(default_factory=list)
    governance: list[DetailItem] = Field(default_factory=list)
    guardrails: list[DetailItem] = Field(default_factory=list)
    infrastructure: list[DetailItem] = Field(default_factory=list)

    model_config = {"populate_by_name": True}

    @field_validator("governance")
    @classmethod
    def _check_governance(cls, v: list[DetailItem]) -> list[DetailItem]:
        _require_labels(v, GOVERNANCE_LABELS, "governance")
        return _reorder(v, GOVERNANCE_LABELS)

    @field_validator("guardrails")
    @classmethod
    def _check_guardrails(cls, v: list[DetailItem]) -> list[DetailItem]:
        _require_labels(v, GUARDRAIL_LABELS, "guardrails")
        return _reorder(v, GUARDRAIL_LABELS)

    @field_validator("infrastructure")
    @classmethod
    def _check_infrastructure(cls, v: list[DetailItem]) -> list[DetailItem]:
        _require_labels(v, INFRASTRUCTURE_LABELS, "infrastructure")
        return _reorder(v, INFRASTRUCTURE_LABELS)

    @field_validator("phases")
    @classmethod
    def _check_phases(cls, v: list[Phase]) -> list[Phase]:
        if not v:
            raise ValueError("phases must include Discovery & Requirements Baseline")
        first = v[0]
        if first.name.strip() != "Discovery & Requirements Baseline":
            raise ValueError('phases[0].name must be "Discovery & Requirements Baseline"')
        if not first.description.strip():
            raise ValueError("phases[0].description must capture the discovery baseline and prerequisites")

        previous_name = first.name.strip()
        for idx, phase in enumerate(v[1:], start=1):
            expected_prefix = f"Depends on {previous_name}:"
            if not phase.description.strip().startswith(expected_prefix):
                raise ValueError(
                    f"phases[{idx}].description must start with {expected_prefix!r}"
                )
            previous_name = phase.name.strip()
        return v

    def to_frontend(self) -> dict:
        """Serialize to the exact camelCase shape NewProject.tsx consumes."""
        return {
            "projectName": self.project_name,
            "objective": self.objective,
            "functionalReqs": self.functional_reqs,
            "techStack": self.tech_stack,
            "skills": self.skills,
            "connectors": self.connectors,
            "risks": self.risks,
            "phases": [p.model_dump() for p in self.phases],
            "governance": [d.model_dump() for d in self.governance],
            "guardrails": [d.model_dump() for d in self.guardrails],
            "infrastructure": [d.model_dump() for d in self.infrastructure],
        }


# ── Validation helpers ────────────────────────────────────────────────────

def _require_labels(items: list[DetailItem], expected: tuple[str, ...], section: str) -> None:
    got = {i.label for i in items}
    missing = [lbl for lbl in expected if lbl not in got]
    if missing:
        raise ValueError(f"{section} missing required labels: {missing}")


def _reorder(items: list[DetailItem], order: tuple[str, ...]) -> list[DetailItem]:
    """Return items in the fixed taxonomy order, dropping any extras."""
    by_label = {i.label: i for i in items}
    return [by_label[lbl] for lbl in order]
