"""BA agent core — the three staged LLM generations.

Each function is a single structured generation against the resolved BA model
(temperature 0). `finalize` uses function-calling for guaranteed structure plus
a validate/repair loop: if the emitted object fails the fixed-taxonomy schema,
the agent re-asks once with the validation error before giving up.

All LLM calls go through BaLlmClient (timeout, retry, circuit breaker).
"""

from __future__ import annotations

import json
import logging

from pydantic import ValidationError

from ecms.agent.ba.llm_client import get_ba_llm_client
from ecms.agent.ba.prompts import (
    ASSESS_TOOL,
    CLARIFICATION_CATEGORIES,
    CLARIFICATION_TOOL,
    FINALIZE_TOOL,
    build_assess_prompt,
    build_clarify_prompt,
    build_finalize_prompt,
    build_reply_prompt,
    build_system_prompt,
    build_team_prompt,
    build_team_tool,
    build_understand_prompt,
)
from ecms.agent.ba.schema import DetailItem, FinalizedRequirements, Phase
from ecms.agent.ba.team_schema import AgentTeam
from ecms.shared.exceptions import LlmProviderError

logger = logging.getLogger("ecms.ba.agent")


def _is_unconfigured_ba(exc: BaseException) -> bool:
    return isinstance(exc, LlmProviderError) and getattr(exc, "code", "") == "ba_model_not_configured"


def _source_mentions(text: str, *terms: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in terms)


def _project_name_from_source(source_text: str) -> str:
    lowered = source_text.lower()
    if _source_mentions(lowered, "invoice", "vendor", "approval"):
        return "Vendor Invoice Approval Workspace"
    if _source_mentions(lowered, "migration"):
        return "Enterprise Migration Workspace"
    if _source_mentions(lowered, "dashboard", "report"):
        return "Enterprise Reporting Workspace"
    first_line = next((line.strip() for line in source_text.splitlines() if line.strip()), "")
    first_line = first_line.removeprefix("Create ").removeprefix("create ").strip(" .")
    return first_line[:80] or "Project Workspace"


def _conversation_text(conversation: list[dict] | None) -> str:
    return "\n".join(str(m.get("content") or "") for m in (conversation or []) if isinstance(m, dict))


def _fallback_requirements(source_text: str, conversation: list[dict] | None = None) -> FinalizedRequirements:
    """Deterministic requirements package for dev/test when no BA model is configured.

    The fallback is deliberately conservative: it derives content from the source
    and user answers, keeps the fixed frontend schema, and avoids pretending that
    an LLM reviewed the project.
    """
    combined = f"{source_text}\n{_conversation_text(conversation)}"
    project_name = _project_name_from_source(combined)

    connectors = []
    if _source_mentions(combined, "gmail", "outlook", "email", "mailbox"):
        connectors.append("Email mailbox connector")
    if _source_mentions(combined, "postgres", "erp", "database"):
        connectors.append("PostgreSQL ERP connector")
    if _source_mentions(combined, "slack"):
        connectors.append("Slack notifications")
    if _source_mentions(combined, "s3", "storage", "document"):
        connectors.append("S3 document storage")
    if not connectors:
        connectors = ["Application API connector", "Database connector"]

    skills = [
        "Business analysis",
        "Workflow orchestration",
        "Backend API engineering",
        "Data integration",
        "QA automation",
        "Security and compliance",
    ]
    if _source_mentions(combined, "dashboard", "ui", "web", "frontend"):
        skills.append("Frontend engineering")

    functional_reqs = [
        "Ingest source records and documents from the stated project systems.",
        "Validate, normalize, and persist project data with audit history.",
        "Route work through configurable human approval queues when business rules require review.",
        "Synchronize final decisions/status back to connected systems.",
        "Provide dashboards, reports, and operational visibility for administrators.",
    ]
    if _source_mentions(combined, "invoice", "vendor"):
        functional_reqs = [
            "Ingest vendor invoices from mailbox and ERP sources.",
            "Extract invoice fields and match invoices against purchase orders.",
            "Detect duplicate, suspicious, or policy-violating invoices before approval.",
            "Route invoice approvals by amount, department, and compliance rules.",
            "Sync approved/rejected invoice status back to the ERP and retain audit evidence.",
        ]

    return FinalizedRequirements(
        projectName=project_name,
        objective=(
            "Deliver a secure, auditable enterprise workspace that automates the "
            "described business process while preserving human approval for risk "
            "and exception cases."
        ),
        functionalReqs=functional_reqs,
        techStack=["Python/FastAPI", "PostgreSQL", "React", "Docker", "Object storage"],
        skills=skills,
        connectors=connectors,
        risks=[
            "Incorrect business-rule configuration can route approvals to the wrong owner.",
            "Connector outages can delay ingestion or downstream synchronization.",
            "Sensitive financial or operational data requires strict access control and audit logging.",
        ],
        phases=[
            Phase(
                name="Discovery & Requirements Baseline",
                duration="1 week",
                description="Baseline of discovery so far and prerequisites for execution.",
            ),
            Phase(
                name="Integration and Data Model",
                duration="2 weeks",
                description="Depends on Discovery & Requirements Baseline: implement connectors, canonical data model, and persistence.",
            ),
            Phase(
                name="Workflow and Approval Automation",
                duration="2 weeks",
                description="Depends on Integration and Data Model: implement routing rules, human queue, exceptions, and notifications.",
            ),
            Phase(
                name="Reporting, Hardening, and Launch",
                duration="1 week",
                description="Depends on Workflow and Approval Automation: complete dashboards, audit reports, QA, monitoring, and rollout.",
            ),
        ],
        governance=[
            DetailItem(label="Data Privacy", detail="Protect source documents and operational data with least-privilege access and audit logs."),
            DetailItem(label="Access Control", detail="Restrict administration, approval, and reporting actions by role and department."),
            DetailItem(label="Approval Workflow", detail="Enforce approval bands, exception review, and traceable decision history."),
            DetailItem(label="Compliance", detail="Retain evidence for audits and flag policy exceptions for human review."),
            DetailItem(label="Change Management", detail="Version business rules and require approval before production changes."),
        ],
        guardrails=[
            DetailItem(label="Data Validation", detail="Validate extracted fields, required references, and duplicate indicators before routing."),
            DetailItem(label="Rollback Procedure", detail="Allow failed syncs or incorrect decisions to be reversed with audit notes."),
            DetailItem(label="Sync Safety", detail="Use idempotent outbound updates to avoid duplicate ERP writes."),
            DetailItem(label="Rate Limiting", detail="Throttle connector calls and queue retries to protect external systems."),
            DetailItem(label="Monitoring Alerts", detail="Alert on connector failures, stuck approvals, and abnormal exception spikes."),
            DetailItem(label="Cutover Safety", detail="Run pilot validation before enabling full automated routing."),
        ],
        infrastructure=[
            DetailItem(label="Compute", detail="Run backend workers and API services in Docker-managed services."),
            DetailItem(label="Database", detail="Use PostgreSQL for project data, workflow state, and audit metadata."),
            DetailItem(label="Networking", detail="Expose API and connector traffic through controlled service routes."),
            DetailItem(label="Storage", detail="Store documents and derived artifacts in object storage."),
            DetailItem(label="Messaging", detail="Use queue/notification mechanisms for approvals and connector retries."),
            DetailItem(label="Monitoring", detail="Track health, workflow latency, connector errors, and audit events."),
        ],
    )


def _parse_clarification(response) -> dict[str, str]:
    tool_calls = response.choices[0].message.tool_calls or []
    if not tool_calls:
        raise ValueError("BA clarification did not emit a structured turn")
    payload = json.loads(tool_calls[0].function.arguments or "{}")
    category = payload.get("category")
    questions = str(payload.get("questions_markdown") or "").strip()
    if category not in CLARIFICATION_CATEGORIES or not questions:
        raise ValueError("BA clarification emitted an invalid category or empty questions")
    return {
        "category": category,
        "category_label": CLARIFICATION_CATEGORIES[category],
        "content": questions,
    }


async def retrieve_knowledge(source_text: str, conversation: list[dict] | None = None) -> str:
    """Retrieve relevant knowledge for a project. Returns empty string on failure."""
    try:
        from ecms.agent.ba.knowledge.retrieval import retrieve_for_project
        return await retrieve_for_project(source_text, conversation)
    except Exception as exc:
        logger.warning("[ba.agent] knowledge retrieval failed, proceeding without: %s", exc)
        return ""


async def understand(source_text: str, knowledge_context: str = "") -> str:
    """Stage 1 — the 'What I understood' recap message (Markdown)."""
    try:
        llm = await get_ba_llm_client()
    except Exception as exc:
        if not _is_unconfigured_ba(exc):
            raise
        logger.warning("[ba.understand] BA model not configured; using deterministic fallback")
        project_name = _project_name_from_source(source_text)
        return (
            f"## What I understood\n\n"
            f"You want to create **{project_name}** based on the provided project brief. "
            "The workspace should convert the business goal into requirements, documents, "
            "meetings, work items, and a project worker hierarchy.\n\n"
            "I will ask one clarification batch before generating the requirements package."
        )
    resp = await llm.chat(
        messages=[
            {"role": "system", "content": build_system_prompt(knowledge_context)},
            {"role": "user", "content": build_understand_prompt(source_text)},
        ],
        temperature=0.0,
        max_tokens=1600,
    )
    return (resp.choices[0].message.content or "").strip()


async def clarify(source_text: str, knowledge_context: str = "") -> dict[str, str]:
    """Stage 2 — one structured, category-specific question batch."""
    try:
        llm = await get_ba_llm_client()
    except Exception as exc:
        if not _is_unconfigured_ba(exc):
            raise
        logger.warning("[ba.clarify] BA model not configured; using deterministic fallback")
        return {
            "category": "assumptions",
            "category_label": CLARIFICATION_CATEGORIES["assumptions"],
            "content": (
                "Before I generate the requirements package, confirm the main business rules, "
                "approval thresholds, exception handling, meeting cadence, and any required "
                "integrations or compliance constraints."
            ),
        }
    resp = await llm.chat(
        messages=[
            {"role": "system", "content": build_system_prompt(knowledge_context)},
            {"role": "user", "content": build_clarify_prompt(source_text)},
        ],
        tools=[CLARIFICATION_TOOL],
        tool_choice={"type": "function", "function": {"name": "emit_clarification"}},
        temperature=0.0,
        max_tokens=4000,
    )
    return _parse_clarification(resp)


async def assess_coverage(source_text: str, conversation: list[dict], knowledge_context: str = "") -> dict:
    """Score every requirement dimension across the full conversation."""
    llm = await get_ba_llm_client()
    try:
        resp = await llm.chat(
            messages=[
                {"role": "system", "content": build_system_prompt(knowledge_context)},
                {"role": "user", "content": build_assess_prompt(source_text, conversation)},
            ],
            tools=[ASSESS_TOOL],
            tool_choice={"type": "function", "function": {"name": "assess_coverage"}},
            temperature=0.0,
            max_tokens=2000,
        )
    except Exception as exc:
        logger.warning("[ba.assess_coverage] LLM call failed, returning empty coverage: %s", exc)
        return {"dimensions": [], "critical_ready": False, "open_questions": []}
    tool_calls = resp.choices[0].message.tool_calls or []
    if not tool_calls:
        return {"dimensions": [], "critical_ready": False, "open_questions": []}
    try:
        return json.loads(tool_calls[0].function.arguments or "{}")
    except json.JSONDecodeError:
        return {"dimensions": [], "critical_ready": False, "open_questions": []}


async def chat_reply(
    source_text: str,
    conversation: list[dict],
    user_message: str,
    knowledge_context: str = "",
) -> dict[str, str]:
    """Chat turn — a coverage-driven reply."""
    coverage = await assess_coverage(source_text, conversation, knowledge_context)
    llm = await get_ba_llm_client()
    resp = await llm.chat(
        messages=[
            {"role": "system", "content": build_system_prompt(knowledge_context)},
            {"role": "user", "content": build_reply_prompt(source_text, conversation, user_message, coverage)},
        ],
        tools=[CLARIFICATION_TOOL],
        tool_choice={"type": "function", "function": {"name": "emit_clarification"}},
        temperature=0.0,
        max_tokens=2200,
    )
    return _parse_clarification(resp)


async def finalize(source_text: str, conversation: list[dict], knowledge_context: str = "") -> FinalizedRequirements:
    """Stage 3 — the FinalizedRequirements object (validated / repaired)."""
    from ecms.agent.ba.llm_client import LlmCallOpts

    try:
        llm = await get_ba_llm_client(opts=LlmCallOpts.for_finalize())
    except Exception as exc:
        if not _is_unconfigured_ba(exc):
            raise
        logger.warning("[ba.finalize] BA model not configured; using deterministic fallback")
        return _fallback_requirements(source_text, conversation)
    messages = [
        {"role": "system", "content": build_system_prompt(knowledge_context)},
        {"role": "user", "content": build_finalize_prompt(source_text, conversation)},
    ]

    last_error: str | None = None
    for attempt in range(2):
        if last_error:
            messages.append({
                "role": "user",
                "content": (
                    f"Your previous emit_requirements call was invalid: {last_error}. "
                    "Call emit_requirements again with the corrected object. The "
                    "governance/guardrails/infrastructure labels must match exactly, "
                    "and phases must start with Discovery & Requirements Baseline "
                    "followed by descriptions that start with Depends on <previous phase name>:."
                ),
            })
        resp = await llm.chat(
            messages=messages,
            tools=[FINALIZE_TOOL],
            tool_choice={"type": "function", "function": {"name": "emit_requirements"}},
            temperature=0.0,
            max_tokens=6000,
        )
        msg = resp.choices[0].message
        tool_calls = msg.tool_calls or []
        if not tool_calls:
            last_error = "no emit_requirements tool call was made"
            logger.warning("[ba.finalize] attempt %d: no tool call", attempt)
            continue
        raw = tool_calls[0].function.arguments or "{}"
        try:
            data = json.loads(raw)
            return FinalizedRequirements.model_validate(data)
        except (json.JSONDecodeError, ValidationError) as exc:
            last_error = str(exc)
            logger.warning("[ba.finalize] attempt %d validation failed: %s", attempt, exc)
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": tool_calls[0].id,
                    "type": "function",
                    "function": {"name": "emit_requirements", "arguments": raw},
                }],
            })
            messages.append({
                "role": "tool",
                "tool_call_id": tool_calls[0].id,
                "content": f"validation error: {last_error}",
            })

    raise ValueError(f"BA finalize failed after retries: {last_error}")


async def design_team(
    requirements: dict,
    conversation: list[dict],
    model_ids: list[str],
    tool_names: list[str],
    knowledge_context: str = "",
    org_roster: list[dict] | None = None,
) -> AgentTeam:
    """Stage 4 — design the per-project agent org chart (validated / repaired)."""
    llm = await get_ba_llm_client()
    team_tool = build_team_tool(model_ids, tool_names)
    allowed_models = tuple(model_ids)
    allowed_tools = tuple(tool_names)
    allowed_org_member_ids = tuple(
        str(member["id"])
        for member in (org_roster or [])
        if member.get("id")
    )
    messages = [
        {"role": "system", "content": build_system_prompt(knowledge_context)},
        {"role": "user", "content": build_team_prompt(requirements, conversation, org_roster=org_roster)},
    ]

    last_error: str | None = None
    for attempt in range(2):
        if last_error:
            messages.append({
                "role": "user",
                "content": (
                    f"Your previous emit_team call was invalid: {last_error}. "
                    "Call emit_team again with the corrected required-position org "
                    "chart. It must have exactly one root (reports_to=null), every "
                    "reports_to must reference an existing key, and there must be no cycles."
                ),
            })
        resp = await llm.chat(
            messages=messages,
            tools=[team_tool],
            tool_choice={"type": "function", "function": {"name": "emit_team"}},
            temperature=0.0,
            max_tokens=6000,
        )
        msg = resp.choices[0].message
        tool_calls = msg.tool_calls or []
        if not tool_calls:
            last_error = "no emit_team tool call was made"
            logger.warning("[ba.design_team] attempt %d: no tool call", attempt)
            continue
        raw = tool_calls[0].function.arguments or "{}"
        try:
            data = json.loads(raw)
            return AgentTeam.validate_payload(
                data,
                allowed_models,
                allowed_tools,
                allowed_org_member_ids,
            )
        except (json.JSONDecodeError, ValidationError, ValueError) as exc:
            last_error = str(exc)
            logger.warning("[ba.design_team] attempt %d validation failed: %s", attempt, exc)
            messages.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [{
                    "id": tool_calls[0].id,
                    "type": "function",
                    "function": {"name": "emit_team", "arguments": raw},
                }],
            })
            messages.append({
                "role": "tool",
                "tool_call_id": tool_calls[0].id,
                "content": f"validation error: {last_error}",
            })

    raise ValueError(f"BA design_team failed after retries: {last_error}")
