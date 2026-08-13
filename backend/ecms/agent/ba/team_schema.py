"""BA team-design — output schema and structural (grammar) validators.

After finalize, the BA designs the professional software-services positions
required for the project. The team is emitted as a FLAT list; the tree is
expressed via `reports_to` referencing each position's stable `key`.

Design freedom is deliberate. The BA decides the ROLES, TITLES, DEPARTMENTS, and
the DEPTH/BREADTH of the org entirely from the project's needs — nothing about the
vocabulary is fixed. The validators enforce only what must hold for the result to
persist as project agent positions and render as a tree:

  - at least one agent, unique keys;
  - exactly one root (reports_to is None);
  - every non-null reports_to references an existing key;
  - no cycles;
  - model and every tool come from the live catalogs (so the team is wireable).

"Who may manage whom" is NOT constrained: any agent that has reports is, by
definition, a manager. No title is privileged.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field, model_validator

__all__ = [
    "TeamAgent",
    "OrgMapping",
    "AgentTeam",
]


# ── Models ──────────────────────────────────────────────────────────────────

class TeamAgent(BaseModel):
    """One agent in the designed org chart. Role/designation/department are free
    text — the BA invents whatever titles the project actually needs."""

    key: str = Field(..., description="Stable slug, unique within the team; reports_to targets it.")
    name: str
    designation: str = ""
    role: str = ""
    department: str = ""
    reports_to: Optional[str] = None
    goal: str = ""
    instructions: str = ""
    skills: list[str] = Field(default_factory=list)
    model: str = ""
    tools: list[str] = Field(default_factory=list)


class PhaseUpdate(BaseModel):
    """Revised phase dates decided by the agent after designing the team."""

    name: str
    startDate: str = Field(..., description="YYYY-MM-DD")
    endDate: str = Field(..., description="YYYY-MM-DD")
    meetingFrequency: str = "weekly"


class OrgMapping(BaseModel):
    """Legacy mapping of a project position to a permanent organization member."""

    project_agent_key: str = Field(..., description="The key of the project agent (references a TeamAgent.key).")
    org_member_id: str = Field(..., description="The id of the permanent org member who oversees this agent.")
    responsibility: str = Field("primary_owner", description="primary_owner | monitor | approver")


class AgentTeam(BaseModel):
    """The complete per-project required-position org chart (flat; tree via reports_to)."""

    agents: list[TeamAgent] = Field(default_factory=list)
    revised_phases: list[PhaseUpdate] = Field(default_factory=list)
    org_mappings: list[OrgMapping] = Field(default_factory=list)

    @classmethod
    def validate_payload(
        cls,
        data: dict,
        allowed_models: tuple[str, ...] = (),
        allowed_tools: tuple[str, ...] = (),
        allowed_org_member_ids: tuple[str, ...] = (),
    ) -> "AgentTeam":
        """Validate an emitted payload against the tree grammar + catalogs.

        Catalog membership is only enforced when the corresponding catalog is
        non-empty, so tests can exercise the structural rules in isolation.
        """
        team = cls.model_validate(data)
        team._check_catalogs(allowed_models, allowed_tools)
        team._check_org_mapping_coverage(allowed_org_member_ids)
        return team

    @model_validator(mode="after")
    def _check_structure(self) -> "AgentTeam":
        agents = self.agents
        if not agents:
            raise ValueError("team must contain at least one agent")

        keys = [a.key for a in agents]
        if len(keys) != len(set(keys)):
            raise ValueError("agent keys must be unique within the team")
        key_set = set(keys)
        by_key = {a.key: a for a in agents}

        # exactly one root (the org's top node)
        roots = [a for a in agents if a.reports_to is None]
        if len(roots) != 1:
            raise ValueError(
                f"team must have exactly one root (reports_to=None); found {len(roots)}"
            )

        # reports_to integrity (no self-reports, targets must exist)
        for a in agents:
            if a.reports_to is None:
                continue
            if a.reports_to == a.key:
                raise ValueError(f"agent '{a.key}' cannot report to itself")
            if a.reports_to not in key_set:
                raise ValueError(
                    f"agent '{a.key}' reports_to unknown key '{a.reports_to}'"
                )

        # no cycles — walk each agent's parent chain to the root
        for a in agents:
            seen = {a.key}
            cur = a.reports_to
            while cur is not None:
                if cur in seen:
                    raise ValueError(f"reporting cycle detected involving '{a.key}'")
                seen.add(cur)
                cur = by_key[cur].reports_to

        # org_mappings must reference valid agent keys and valid responsibility types
        valid_responsibilities = {"primary_owner", "monitor", "approver"}
        for m in self.org_mappings:
            if m.project_agent_key not in key_set:
                raise ValueError(
                    f"org_mapping references unknown agent key '{m.project_agent_key}'"
                )
            if m.responsibility not in valid_responsibilities:
                raise ValueError(
                    f"org_mapping has invalid responsibility '{m.responsibility}'"
                )

        return self

    def _check_catalogs(self, allowed_models: tuple[str, ...], allowed_tools: tuple[str, ...]) -> None:
        """Catalog-membership checks — the one place constraint earns its keep:
        model/tools MUST be real so the designed team is instantiable later."""
        if allowed_models:
            allowed_m = set(allowed_models)
            for a in self.agents:
                if a.model and a.model not in allowed_m:
                    raise ValueError(
                        f"agent '{a.key}' uses model '{a.model}' not in the catalog"
                    )
        if allowed_tools:
            allowed_t = set(allowed_tools)
            for a in self.agents:
                bad = [t for t in a.tools if t not in allowed_t]
                if bad:
                    raise ValueError(f"agent '{a.key}' uses unknown tools: {bad}")

    def _check_org_mapping_coverage(self, allowed_org_member_ids: tuple[str, ...]) -> None:
        """Validate legacy org mappings only when a roster is supplied."""
        if not allowed_org_member_ids:
            return

        agent_keys = {agent.key for agent in self.agents}
        mapped_keys = {mapping.project_agent_key for mapping in self.org_mappings}
        missing = sorted(agent_keys - mapped_keys)
        if missing:
            raise ValueError(
                f"every agent must have an organization employee assignment; missing: {missing}"
            )

        allowed_members = set(allowed_org_member_ids)
        unknown_members = sorted({
            mapping.org_member_id
            for mapping in self.org_mappings
            if mapping.org_member_id not in allowed_members
        })
        if unknown_members:
            raise ValueError(
                "org_mappings reference inactive or unknown organization members: "
                f"{unknown_members}"
            )

    def is_manager(self, key: str) -> bool:
        """A manager is any agent that has at least one direct report."""
        return any(a.reports_to == key for a in self.agents)

    def to_rows(self, project_id: str) -> list[dict]:
        """Map to project-position rows for a project.

        Keys are namespaced by project to keep ids unique and scoped, and
        reports_to keys are resolved to the same namespaced ids.
        """
        def _id(key: str) -> str:
            return f"{project_id}:{key}"

        rows: list[dict] = []
        default_automation = {"autoRetry": True, "maxRetries": 3, "retryDelaySeconds": 30, "escalateOnFailure": True, "heartbeatIntervalSeconds": 60}
        default_features = {"memoryRetentionDays": 30, "dataQueryAccess": "read", "maxConcurrentTasks": 5, "rateLimitPerMinute": 60, "streamingEnabled": True, "auditLogging": True, "piiMasking": False}
        for a in self.agents:
            rows.append({
                "id": _id(a.key),
                "project_id": project_id,
                "name": a.name,
                "role": a.role,
                "designation": a.designation,
                "role_description": a.goal,
                "skills": a.skills,
                "department": a.department,
                "reports_to": _id(a.reports_to) if a.reports_to else None,
                "model": a.model,
                "tool_policy": {"allowed_tools": a.tools, "blocked_tools": []},
                "system_prompt_addon": a.instructions,
                "automation": default_automation,
                "features": default_features,
                "status": "active",
            })
        return rows
