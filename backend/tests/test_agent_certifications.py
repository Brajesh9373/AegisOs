from ecms.shared.certifications import default_certificates_for_agent


def test_solution_architect_receives_togaf_certification() -> None:
    certificates = default_certificates_for_agent(
        {
            "name": "Solution Architect",
            "role": "architect",
            "skills": ["system design", "architecture review"],
            "role_description": "Review performance testing and QA output.",
        }
    )

    assert 2 <= len(certificates) <= 4
    assert certificates[0]["name"] == "TOGAF Enterprise Architecture Foundation"
    assert len({certificate["name"] for certificate in certificates}) == len(certificates)


def test_unknown_agent_receives_fallback_certification() -> None:
    certificates = default_certificates_for_agent({"name": "Specialist"})

    assert 2 <= len(certificates) <= 4
    assert certificates[0]["name"] == "GitHub Foundations"
