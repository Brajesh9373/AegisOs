from ecms.persistence.models.agent import Agent
from ecms.persistence.models.project_agent_position import ProjectAgentPosition
from ecms.persistence.repositories.project_agent_position import normalize_designation


def test_normalize_designation_matches_titles_across_formatting() -> None:
    assert normalize_designation("Backend/API Engineer") == normalize_designation("backend api engineer")
    assert normalize_designation("Security & Compliance Engineer") == normalize_designation("security compliance engineer")


def test_project_position_serializes_vacant_state() -> None:
    position = ProjectAgentPosition(
        id="project-a:security",
        project_id="project-a",
        position_key="security",
        name="Security Engineer",
        role="security_engineer",
        designation="Security & Compliance Engineer",
        department="security",
        role_description="Review auth and compliance controls.",
        skills=["security review"],
        reports_to=None,
        tool_policy={"allowed_tools": ["search_code"]},
    )

    data = position.to_dict()

    assert data["filled"] is False
    assert data["assigned_agent"] is None
    assert data["designation"] == "Security & Compliance Engineer"


def test_project_position_serializes_assigned_reusable_agent() -> None:
    position = ProjectAgentPosition(
        id="project-a:delivery",
        project_id="project-a",
        position_key="delivery",
        name="Delivery Manager",
        role="delivery_manager",
        designation="Engagement Delivery Manager",
        department="delivery",
        reports_to=None,
        tool_policy={"allowed_tools": []},
    )
    agent = Agent(
        id="agent-delivery",
        name="Delivery Agent",
        role="delivery_manager",
        designation="Engagement Delivery Manager",
        department="delivery",
        project_id=None,
        status="active",
    )

    data = position.to_dict(agent)

    assert data["filled"] is True
    assert data["assigned_agent"]["id"] == "agent-delivery"
    assert data["assigned_agent"]["project_id"] is None
