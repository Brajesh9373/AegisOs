import pytest

from ecms.agent.ba.team_schema import AgentTeam


def _payload() -> dict:
    return {
        "agents": [
            {
                "key": "delivery_manager",
                "name": "Delivery Manager",
                "designation": "Engagement Delivery Manager",
                "role": "Delivery Manager",
                "department": "delivery",
                "reports_to": None,
                "goal": "Own delivery.",
                "instructions": "Coordinate the project.",
                "skills": ["delivery management"],
                "model": "gpt-4o",
                "tools": ["Jira"],
            },
            {
                "key": "backend_engineer",
                "name": "Backend Engineer",
                "designation": "Senior Backend Engineer",
                "role": "Backend Engineer",
                "department": "engineering",
                "reports_to": "delivery_manager",
                "goal": "Build the backend.",
                "instructions": "Implement services.",
                "skills": ["Python"],
                "model": "gpt-4o",
                "tools": ["GitHub"],
            },
        ],
        "revised_phases": [],
        "org_mappings": [
            {
                "project_agent_key": "delivery_manager",
                "org_member_id": "employee-1",
                "responsibility": "primary_owner",
            },
            {
                "project_agent_key": "backend_engineer",
                "org_member_id": "employee-2",
                "responsibility": "primary_owner",
            },
        ],
    }


def test_requires_employee_assignment_for_every_agent() -> None:
    payload = _payload()
    payload["org_mappings"] = payload["org_mappings"][:1]

    with pytest.raises(ValueError, match="backend_engineer"):
        AgentTeam.validate_payload(
            payload,
            allowed_models=("gpt-4o",),
            allowed_tools=("Jira", "GitHub"),
            allowed_org_member_ids=("employee-1", "employee-2"),
        )


def test_employee_assignment_not_required_without_org_roster() -> None:
    payload = _payload()
    payload["org_mappings"] = []

    team = AgentTeam.validate_payload(
        payload,
        allowed_models=("gpt-4o",),
        allowed_tools=("Jira", "GitHub"),
    )

    assert team.org_mappings == []


def test_rejects_unknown_or_inactive_employee_assignment() -> None:
    payload = _payload()
    payload["org_mappings"][1]["org_member_id"] = "inactive-employee"

    with pytest.raises(ValueError, match="inactive-employee"):
        AgentTeam.validate_payload(
            payload,
            allowed_models=("gpt-4o",),
            allowed_tools=("Jira", "GitHub"),
            allowed_org_member_ids=("employee-1", "employee-2"),
        )


def test_accepts_complete_employee_coverage() -> None:
    team = AgentTeam.validate_payload(
        _payload(),
        allowed_models=("gpt-4o",),
        allowed_tools=("Jira", "GitHub"),
        allowed_org_member_ids=("employee-1", "employee-2"),
    )

    assert {mapping.project_agent_key for mapping in team.org_mappings} == {
        "delivery_manager",
        "backend_engineer",
    }
