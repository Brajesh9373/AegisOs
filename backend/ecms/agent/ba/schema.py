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
    "FinalizedRequirements",
    "Phase",
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
        v = _normalize_labels(v)
        _check_flexible(v, GOVERNANCE_LABELS, "governance")
        return _reorder(v, GOVERNANCE_LABELS)

    @field_validator("guardrails")
    @classmethod
    def _check_guardrails(cls, v: list[DetailItem]) -> list[DetailItem]:
        v = _normalize_labels(v)
        _check_flexible(v, GUARDRAIL_LABELS, "guardrails")
        return _reorder(v, GUARDRAIL_LABELS)

    @field_validator("infrastructure")
    @classmethod
    def _check_infrastructure(cls, v: list[DetailItem]) -> list[DetailItem]:
        v = _normalize_labels(v)
        _check_flexible(v, INFRASTRUCTURE_LABELS, "infrastructure")
        return _reorder(v, INFRASTRUCTURE_LABELS)

    @field_validator("phases", mode="before")
    @classmethod
    def _coerce_phases(cls, v):
        if not isinstance(v, list) or not v:
            return v
        first = (
            v[0]
            if isinstance(v[0], dict)
            else {
                "name": getattr(v[0], "name", ""),
                "description": getattr(v[0], "description", ""),
            }
        )
        name = (
            (first.get("name") or "").strip()
            if isinstance(first, dict)
            else str(first.get("name", "")).strip()
        )
        if name.lower() not in (
            "discovery & requirements baseline",
            "discovery & requirements baseline ",
            "discovery and requirements baseline",
        ):
            if isinstance(v[0], dict):
                v[0]["name"] = "Discovery & Requirements Baseline"
            else:
                try:
                    v[0].name = "Discovery & Requirements Baseline"
                except Exception:
                    pass
        if isinstance(v[0], dict) and not (v[0].get("description") or "").strip():
            v[0]["description"] = "Baseline of discovery so far and prerequisites for execution."
        for idx in range(1, len(v)):
            item = v[idx]
            desc = (
                (item.get("description") or "")
                if isinstance(item, dict)
                else getattr(item, "description", "")
            )
            prev_name = (
                (v[idx - 1].get("name") or "")
                if isinstance(v[idx - 1], dict)
                else getattr(v[idx - 1], "name", "")
            )
            prefix = f"Depends on {prev_name.strip()}:"
            if not desc.strip().startswith(prefix):
                fixed = f"{prefix} {desc.strip()}" if desc.strip() else prefix
                if isinstance(item, dict):
                    item["description"] = fixed
                else:
                    try:
                        item.description = fixed
                    except Exception:
                        pass
        return v

    @field_validator("phases")
    @classmethod
    def _check_phases(cls, v: list[Phase]) -> list[Phase]:
        if not v:
            raise ValueError("phases must include Discovery & Requirements Baseline")
        first = v[0]
        if first.name.strip() != "Discovery & Requirements Baseline":
            raise ValueError('phases[0].name must be "Discovery & Requirements Baseline"')
        if not first.description.strip():
            raise ValueError(
                "phases[0].description must capture the discovery baseline and prerequisites"
            )
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


def _normalize_labels(items: list[DetailItem]) -> list[DetailItem]:
    norm_map = {
        lbl.lower().strip(): lbl
        for lbl in GOVERNANCE_LABELS + GUARDRAIL_LABELS + INFRASTRUCTURE_LABELS
    }
    for it in items:
        key = it.label.strip().lower()
        if key in norm_map:
            it.label = norm_map[key]
    return items


def _require_labels(items: list[DetailItem], expected: tuple[str, ...], section: str) -> None:
    got = {i.label for i in items}
    missing = [lbl for lbl in expected if lbl not in got]
    if missing:
        raise ValueError(f"{section} missing required labels: {missing}")


def _check_flexible(items: list[DetailItem], allowed: tuple[str, ...], section: str) -> None:
    """Flexible count (3-7), fixed catalog — not 5/6/6."""
    allowed_set = set(allowed)
    for it in items:
        if it.label not in allowed_set:
            raise ValueError(f"{section} label {it.label!r} not in allowed catalog {allowed}")
    labels = [it.label for it in items]
    if len(labels) != len(set(labels)):
        raise ValueError(f"{section} has duplicate labels: {labels}")
    if len(items) < 3:
        raise ValueError(f"{section} needs at least 3 items, got {len(items)}")
    if len(items) > 7:
        raise ValueError(f"{section} needs at most 7 items, got {len(items)}")


def _reorder(items: list[DetailItem], order: tuple[str, ...]) -> list[DetailItem]:
    """Return items in the fixed taxonomy order, dropping any extras."""
    by_label = {i.label: i for i in items}
    return [by_label[lbl] for lbl in order if lbl in by_label]
