"""cordis.patch.yml Generator — per-agent DSH configuration.

Generates DSH cordis.patch.yml files for each AegisOS agent based on their
role, permissions, and scope. Each agent gets an isolated configuration that:

1. Sets agent-specific system prompt/persona
2. Disables approval (autonomous operation)
3. Disables sandbox confinement (full file access)
4. Configures subagent delegation depth (for parent agents)
5. Optionally restricts tools per agent scope
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

logger = logging.getLogger("ecms.agent_os.patch_generator")


# ── Agent Personas by Role ──────────────────────────────────────────────

AGENT_PERSONAS: dict[str, str] = {
    "head-of-engineering": (
        "You are the Head of Engineering. Your working directory is {{cwd}}.\n\n"
        "Your responsibilities:\n"
        "- Break down projects into clear, actionable tasks\n"
        "- Delegate tasks to senior engineers with clear requirements\n"
        "- Review completed work and provide feedback\n"
        "- Report progress to stakeholders\n"
        "- Make architectural decisions and set technical direction\n\n"
        "You have access to junior and senior engineers. Delegate complex work "
        "to senior engineers and simpler tasks to junior engineers. Always "
        "provide clear context when delegating."
    ),
    "senior-engineer": (
        "You are a Senior Software Engineer. Your working directory is {{cwd}}.\n\n"
        "Your responsibilities:\n"
        "- Design system architecture for features\n"
        "- Write complex, production-quality code\n"
        "- Review code from junior engineers and provide mentorship\n"
        "- Make technical decisions within your domain\n"
        "- Break down complex tasks into implementable steps\n\n"
        "You may delegate simpler implementation tasks to junior engineers. "
        "Always explain your design decisions in code comments."
    ),
    "junior-engineer": (
        "You are a Junior Software Engineer. Your working directory is {{cwd}}.\n\n"
        "Your responsibilities:\n"
        "- Write clean, well-tested code\n"
        "- Fix bugs and implement well-defined features\n"
        "- Write unit tests for your code\n"
        "- Ask senior engineers for guidance when requirements are unclear\n"
        "- Follow the coding standards and patterns established in the codebase\n\n"
        "When you encounter blockers beyond your scope, ask your senior engineer "
        "rather than guessing. Always write tests for your changes."
    ),
    "business-analyst": (
        "You are a Senior Business Analyst. Your working directory is {{cwd}}.\n\n"
        "Your responsibilities:\n"
        "- Analyze project requirements and identify gaps\n"
        "- Write detailed specifications and user stories\n"
        "- Create acceptance criteria for features\n"
        "- Validate requirements with stakeholders\n"
        "- Translate business needs into technical requirements\n\n"
        "When you complete your analysis, produce a structured specification "
        "document with: overview, user stories, acceptance criteria, and "
        "open questions."
    ),
    "code-reviewer": (
        "You are a Senior Code Reviewer. Your working directory is {{cwd}}.\n\n"
        "Your responsibilities:\n"
        "- Review code for correctness, security, and maintainability\n"
        "- Check adherence to coding standards and best practices\n"
        "- Identify potential bugs, edge cases, and performance issues\n"
        "- Provide constructive, actionable feedback\n"
        "- Approve code that meets quality standards\n\n"
        "Be thorough but fair. Explain why changes are needed, not just what "
        "to change. Consider: correctness, security, performance, readability, "
        "and test coverage."
    ),
    "qa-engineer": (
        "You are a Senior QA Engineer. Your working directory is {{cwd}}.\n\n"
        "Your responsibilities:\n"
        "- Write comprehensive test plans and test cases\n"
        "- Identify edge cases and boundary conditions\n"
        "- Write automated tests (unit, integration, e2e)\n"
        "- Report bugs with clear reproduction steps\n"
        "- Verify fixes and regressions\n\n"
        "Always think about: what could go wrong? What are the edge cases? "
        "What assumptions might be wrong?"
    ),
    "devops-engineer": (
        "You are a Senior DevOps Engineer. Your working directory is {{cwd}}.\n\n"
        "Your responsibilities:\n"
        "- Set up and maintain CI/CD pipelines\n"
        "- Configure infrastructure and deployments\n"
        "- Monitor system health and performance\n"
        "- Automate operational tasks\n"
        "- Ensure security and compliance in infrastructure\n\n"
        "Always prioritize: reliability, security, and observability."
    ),
}

# Roles that can delegate to subagents (parent roles)
PARENT_ROLES: frozenset[str] = frozenset({
    "head-of-engineering",
    "senior-engineer",
})

# Default subagent depth per role
DEFAULT_MAX_DEPTH: dict[str, int] = {
    "head-of-engineering": 3,
    "senior-engineer": 2,
    "junior-engineer": 0,
    "business-analyst": 1,
    "code-reviewer": 0,
    "qa-engineer": 0,
    "devops-engineer": 1,
}


def get_persona(role: str) -> str:
    """Get the system persona for a given role.

    Args:
        role: Agent role identifier

    Returns:
        System prompt persona string
    """
    return AGENT_PERSONAS.get(
        role,
        (
            f"You are an AI agent with the role: {role}. Your working directory is {{cwd}}.\n\n"
            "Complete the tasks assigned to you thoroughly and report your findings."
        ),
    )


def is_parent_role(role: str) -> bool:
    """Check if a role can spawn subagents (delegate work).

    Args:
        role: Agent role identifier

    Returns:
        True if the role can delegate to subagents
    """
    return role in PARENT_ROLES


def get_max_depth(role: str) -> int:
    """Get the maximum subagent delegation depth for a role.

    Args:
        role: Agent role identifier

    Returns:
        Maximum delegation depth (0 = no delegation)
    """
    return DEFAULT_MAX_DEPTH.get(role, 0)


def generate_cordis_patch(
    role: str,
    output_path: str | Path,
    *,
    extra_system_prompt: str | None = None,
    tool_restrictions: list[str] | None = None,
    approval_policy: str = "never",
    sandbox_mode: str = "danger-full-access",
    enable_subagents: bool | None = None,
    max_depth: int | None = None,
    custom_config: dict[str, Any] | None = None,
) -> Path:
    """Generate a cordis.patch.yml for a specific agent.

    Args:
        role: Agent role (maps to persona)
        output_path: Where to write the patch file
        extra_system_prompt: Additional system prompt appended to persona
        tool_restrictions: List of allowed tools (empty = all tools)
        approval_policy: "never" (autonomous) or "ask" (human approval)
        sandbox_mode: "danger-full-access" or "workspace-write" or "read-only"
        enable_subagents: Override subagent enablement (default: based on role)
        max_depth: Override max delegation depth (default: based on role)
        custom_config: Additional config rows to include

    Returns:
        Path to the generated patch file
    """
    output_path = Path(output_path)
    persona = get_persona(role)

    if extra_system_prompt:
        persona = f"{persona}\n\n{extra_system_prompt}"

    # Build patch rows
    patch: list[dict[str, Any]] = [
        # System prompt / persona
        {
            "id": "system-prompt",
            "config": {"persona": persona},
        },
        # Approval policy
        {
            "id": "approval",
            "name": "@deepseek-ai/dsh-user-approval",
            "config": {"policy": approval_policy},
        },
        # Sandbox mode
        {
            "id": "sandbox-policy",
            "name": "@deepseek-ai/dsh-sandbox-policy",
            "config": {"mode": sandbox_mode},
        },
    ]

    # Subagent configuration (for parent roles)
    should_enable = enable_subagents if enable_subagents is not None else is_parent_role(role)
    if should_enable:
        depth = max_depth if max_depth is not None else get_max_depth(role)
        patch.append({
            "id": "subagent",
            "name": "@deepseek-ai/dsh-subagent",
            "config": {"maxDepth": depth},
        })

    # Tool restrictions (if specified)
    if tool_restrictions is not None:
        patch.append({
            "id": "tools",
            "name": "@deepseek-ai/dsh-tools",
            "config": {
                "mode": "native",
                # Note: actual tool restriction happens via ctx.tools.restrict()
                # This is a config hint for documentation
                "allowedTools": tool_restrictions,
            },
        })

    # Custom config rows (appended at the end, can override)
    if custom_config:
        if isinstance(custom_config, list):
            patch.extend(custom_config)
        elif isinstance(custom_config, dict):
            patch.append(custom_config)

    # Write to file
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        yaml.dump(patch, f, default_flow_style=False, sort_keys=False, width=120)

    logger.info("Generated cordis.patch.yml for role %s at %s", role, output_path)
    return output_path


def generate_minimal_patch(
    role: str,
    output_path: str | Path,
    *,
    extra_system_prompt: str | None = None,
) -> Path:
    """Generate a minimal cordis.patch.yml for sdk-minimal profile.

    The sdk-minimal profile has a smaller patch surface — only configure
    what's essential for the agent to function.

    Args:
        role: Agent role
        output_path: Where to write the patch file
        extra_system_prompt: Additional system prompt

    Returns:
        Path to the generated patch file
    """
    output_path = Path(output_path)
    persona = get_persona(role)

    if extra_system_prompt:
        persona = f"{persona}\n\n{extra_system_prompt}"

    patch: list[dict[str, Any]] = [
        {
            "id": "system-prompt",
            "config": {"persona": persona},
        },
        {
            "id": "approval",
            "name": "@deepseek-ai/dsh-user-approval",
            "config": {"policy": "never"},
        },
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        yaml.dump(patch, f, default_flow_style=False, sort_keys=False, width=120)

    logger.info("Generated minimal cordis.patch.yml for role %s at %s", role, output_path)
    return output_path


def validate_patch(patch_path: str | Path) -> tuple[bool, str | None]:
    """Validate a cordis.patch.yml file.

    Args:
        patch_path: Path to the patch file

    Returns:
        (is_valid, error_message)
    """
    patch_path = Path(patch_path)

    if not patch_path.is_file():
        return False, f"Patch file not found: {patch_path}"

    try:
        with open(patch_path) as f:
            content = f.read()

        if not content.strip():
            return False, "Patch file is empty"

        data = yaml.safe_load(content)

        if not isinstance(data, list):
            return False, "Patch file must be a YAML sequence (list)"

        if not data:
            return False, "Patch file must contain at least one entry"

        for i, entry in enumerate(data):
            if not isinstance(entry, dict):
                return False, f"Entry {i} is not a mapping"
            if "id" not in entry:
                return False, f"Entry {i} missing 'id' field"

        return True, None

    except yaml.YAMLError as e:
        return False, f"Invalid YAML: {e}"
    except Exception as e:
        return False, f"Validation error: {e}"
