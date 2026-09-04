"""Prompt builders for the BA agent's three staged generations.

The BA agent runs as a state machine, not a free ReAct loop. Each stage is a
single structured generation:

  understand  -> recap of what was heard + confirmation ask
  clarify     -> categorized clarifying questions (fixed envelope, dynamic wording)
  finalize    -> the FinalizedRequirements object (fixed taxonomy, JSON schema)

All prompts run at temperature 0 and are anchored to the approved golden mock.
"""

from __future__ import annotations

import json

from ecms.agent.ba.exemplar import GOLDEN_FINALIZED
from ecms.agent.ba.schema import (
    GOVERNANCE_LABELS,
    GUARDRAIL_LABELS,
    INFRASTRUCTURE_LABELS,
)
from ecms.agent.ba.team_exemplar import GOLDEN_TEAM

BA_SYSTEM = (
    "You are a Business Analyst agent with 27+ years of enterprise requirements "
    "elicitation experience at a software services company. A client describes a "
    "project (via transcript, pasted text, or an uploaded document). Your job is "
    "rigorous requirements elicitation: understand the ask, then interrogate it "
    "exhaustively across every dimension a seasoned BA would cover before a "
    "single line of code is written.\n\n"
    "You are relentless but never robotic. A real veteran BA is never satisfied "
    "with surface answers: when a client says 'real-time sync', you drill into "
    "acceptable latency, conflict resolution, and failure behavior; when they say "
    "'migrate the data', you drill into volume, quality, PII, retention, and "
    "reconciliation. You probe the client's ANSWERS, not just their opening "
    "statement — every answer opens second-order questions. You do not stop "
    "asking while a critical dimension is still vague, thin, or unaddressed.\n\n"
    "You act like the BA assigned to a newly received software project. First "
    "identify what kind of project this is (new build, enhancement, bug fix, "
    "migration, integration, modernization, automation, reporting, mobile/web "
    "app, or platform work), then ask only the questions a delivery team needs "
    "to estimate, design, implement, test, deploy, and get sign-off. Every "
    "question must use the client's actual nouns, systems, users, and stack; "
    "do not ask a category because it exists in a template.\n\n"
    "You are concise and technical. You never invent facts the client did not "
    "provide — where a detail remains unknown after you have genuinely probed for "
    "it, you make a clearly-reasonable engineering assumption consistent with the "
    "stack the client described, and you state that assumption explicitly. If the "
    "client asks you to assume defaults or move on, you respect that immediately."
    "\n\nDuring clarification, every question must belong to exactly one of these "
    "six categories: Background & Why It Is Needed, Current Pain Points, "
    "Assumptions, Architectural Depth, Execution Stages, or Timelines. Work on "
    "one category at a time. You may ask as many related questions as necessary "
    "within the active category, but never mix categories in one response."
)

CLARIFICATION_CATEGORIES = {
    "background": "Background & Why It Is Needed",
    "pain_points": "Current Pain Points",
    "assumptions": "Assumptions",
    "architectural_depth": "Architectural Depth",
    "execution_stages": "Execution Stages",
    "timelines": "Timelines",
}

CLARIFICATION_TOOL = {
    "type": "function",
    "function": {
        "name": "emit_clarification",
        "description": "Emit one category-specific BA clarification turn.",
        "parameters": {
            "type": "object",
            "properties": {
                "category": {
                    "type": "string",
                    "enum": list(CLARIFICATION_CATEGORIES),
                },
                "questions_markdown": {
                    "type": "string",
                    "description": (
                        "Project-specific questions belonging only to the selected "
                        "category. Multiple related questions are allowed."
                    ),
                },
            },
            "required": ["category", "questions_markdown"],
            "additionalProperties": False,
        },
    },
}


def build_system_prompt(knowledge_context: str = "") -> str:
    """Build the BA system prompt, injecting retrieved knowledge when available.

    The knowledge context is a formatted block from the RAG retrieval layer.
    When empty (no knowledge found or retrieval failed), the prompt is identical
    to BA_SYSTEM — zero regression.
    """
    if not knowledge_context:
        return BA_SYSTEM
    return BA_SYSTEM + "\n\n" + knowledge_context


# The full set of requirement dimensions a veteran BA covers before finalizing.
# The clarify stage opens on a curated subset; the coverage loop tracks ALL of
# them and keeps probing until each is sufficient or explicitly deferred.
COVERAGE_DIMENSIONS = [
    ("business_objective", "Business objective, drivers & measurable success criteria"),
    ("stakeholders", "Stakeholders, owners, end users & sign-off authority"),
    ("current_state", "Current-state architecture, systems & pain points"),
    (
        "frontend",
        "Frontend: UI surfaces, web/mobile targets, framework, accessibility and UX constraints",
    ),
    (
        "backend",
        "Backend: services, APIs, runtime/framework, auth boundaries and business logic ownership",
    ),
    (
        "database",
        "Database: data stores, schema ownership, volumes, migration/seeding and retention",
    ),
    ("scope", "Explicit scope — what is in scope and, critically, what is OUT"),
    ("data", "Data: entities, volumes, quality, PII, retention, historical range"),
    ("integrations", "Integrations: upstream/downstream systems & sync semantics"),
    ("nonfunctional", "Non-functionals: latency, throughput, scale, availability/SLA"),
    ("security_compliance", "Security & compliance: auth, RBAC, encryption, regulatory, residency"),
    ("infrastructure", "Infrastructure: hosting, environments, deployment model"),
    ("migration_cutover", "Migration & cutover: strategy, parallel run, rollback, downtime"),
    ("testing_acceptance", "Testing & acceptance: criteria, dry runs, reconciliation"),
    ("timeline_milestones", "Timeline & milestones: schedule, phases, hard deadlines"),
    ("constraints_budget", "Constraints: budget, team, technology, non-negotiables"),
    ("training_support", "Training, hypercare & knowledge transfer post go-live"),
    ("risks_dependencies", "Known risks, external dependencies & assumptions"),
]

# The dimensions the FIRST clarifying batch always opens on (retitled to fit the
# project). The coverage loop then drives everything else.
CLARIFY_DIMENSIONS = [
    "Project goal, business outcome, and definition of success",
    "Current-state systems, architecture, and technical ownership",
    "Tech stack and constraints: languages, frameworks, cloud, tools, and non-negotiables",
    "Users, roles, workflows, and operational pain points",
    "Target scope: features, deliverables, and explicit out-of-scope items",
    "Frontend and channel impact: web, mobile, admin, employee, customer, or internal tools",
    "Backend/API impact: services, business rules, auth boundaries, and contracts",
    "Data scope: entities, source and target schemas, volumes, quality, history, and retention",
    "Integrations and sync: upstream/downstream systems, events, APIs, queues, retries, and failures",
    "Infrastructure and environments: hosting, CI/CD, observability, access, and deployment path",
    "Security, compliance, approvals, and audit requirements",
    "Testing, acceptance, rollout, cutover, rollback, timeline, and sign-off",
]


def build_understand_prompt(source_text: str) -> str:
    """Stage 1 — recap what was understood, then ask to confirm."""
    return (
        "The client provided the following requirement input:\n\n"
        f'"""\n{source_text.strip()}\n"""\n\n'
        "Write your FIRST message to the client. It must:\n"
        "1. Open with exactly: \"Hello! I'm the Business Analyst agent. I've "
        "analyzed your input. Let me summarize what I understood "
        'and ask some clarifying questions."\n'
        "2. Then a bold heading **What I understood:** followed by a bulleted "
        "list capturing the key facts (systems, stack, scale, current state, "
        "the core ask). Bold the important nouns/technologies.\n"
        '3. Close with exactly: "Is my understanding correct? Before I proceed, '
        'I have some questions."\n\n'
        "Output ONLY the message text in Markdown. No preamble, no JSON."
    )


def _full_transcript(source_text: str, conversation: list[dict]) -> str:
    """Render the complete discovery conversation for stateless re-assessment."""
    return "\n\n".join(
        f"{m.get('role', '?').upper()}: {m.get('content', '')}" for m in conversation
    )


def build_assess_prompt(source_text: str, conversation: list[dict]) -> str:
    """Coverage assessor — score every requirement dimension over the WHOLE conversation.

    Stateless: re-reads the entire transcript each turn (no DB coverage state).
    Returns, via the assess_coverage tool, a per-dimension status plus the
    specific open follow-up questions still needed. This is the memory that lets
    the agent behave like a veteran BA instead of quitting after one round.
    """
    convo = _full_transcript(source_text, conversation)
    dims = "\n".join(f"- {key}: {desc}" for key, desc in COVERAGE_DIMENSIONS)
    return (
        "You are the requirements-coverage auditor for a veteran Business "
        "Analyst. Read the ENTIRE discovery conversation and judge, for each "
        "requirement dimension, whether the client has provided enough for an "
        "engineering team to build without guessing.\n\n"
        "ORIGINAL INPUT:\n"
        f'"""\n{source_text.strip()}\n"""\n\n'
        "FULL CONVERSATION SO FAR:\n"
        f'"""\n{convo}\n"""\n\n'
        "The dimensions to assess:\n"
        f"{dims}\n\n"
        "For EACH dimension, assign a status:\n"
        '- "sufficient": the client gave concrete, buildable detail (or '
        "explicitly said to assume defaults / declared it out of scope).\n"
        '- "partial": touched on but still vague, or the answer opens obvious '
        "second-order questions a senior BA would push on.\n"
        '- "unaddressed": not meaningfully covered at all.\n\n'
        "Be a HARD grader. A single sentence is rarely 'sufficient'. If a client "
        "says 'real-time sync', that dimension is at best 'partial' until latency, "
        "conflict resolution, and failure behavior are pinned down. Only mark "
        "'sufficient' when a competent engineer would NOT need to ask a follow-up.\n\n"
        "For every dimension that is NOT sufficient, write the specific, "
        "second-order follow-up questions still needed — grounded in what the "
        "client actually said, never generic. Call assess_coverage with the result."
    )


def build_reply_prompt(
    source_text: str,
    conversation: list[dict],
    user_message: str,
    coverage: dict,
) -> str:
    """Coverage-driven reply — acknowledge, then probe the next open gaps.

    `coverage` is the assess_coverage result. The reply is steered entirely by
    which dimensions are still partial/unaddressed, so the agent keeps drilling
    like a 27-year BA instead of closing on the first round.
    """
    convo = _full_transcript(source_text, conversation)

    dimensions = coverage.get("dimensions", []) if isinstance(coverage, dict) else []
    assessed = len(dimensions) > 0
    open_dims = [d for d in dimensions if d.get("status") in ("partial", "unaddressed")]
    critical_open = [d for d in open_dims if d.get("key") in _CRITICAL_DIMENSIONS]
    # If the coverage audit produced nothing (e.g. the assessor call failed),
    # never offer to finalize — treat it as "keep probing", which is the safe
    # default for a veteran BA and avoids reintroducing premature-close.
    all_sufficient = assessed and len(open_dims) == 0
    ready = assessed and len(critical_open) == 0

    # Render the open gaps + their pending follow-ups for the model to draw on.
    if open_dims:
        gaps = "\n".join(
            f"- [{d.get('status')}] {d.get('key')}: "
            + "; ".join(d.get("questions", []) or ["needs more detail"])
            for d in open_dims
        )
    else:
        gaps = "(none — every dimension is sufficient)"

    # The readiness clause depends on the offer-but-user-decides policy.
    if ready:
        readiness = (
            "READINESS: All CRITICAL dimensions are now sufficient. You MAY offer "
            "to produce the requirements package — but frame it as the client's "
            "choice, and if any non-critical gaps remain, note them as items you'd "
            "otherwise assume defaults for. Example tone: 'I have enough to draft a "
            "solid requirements package. I still have a few finer points (X, Y) I'd "
            "make reasonable assumptions on unless you'd like to specify them. Shall "
            "I generate the requirements, or would you like to nail those down first?'"
            if not all_sufficient
            else "READINESS: Every dimension is sufficient. Offer to generate the "
            "requirements package now, clearly as the client's decision — e.g. "
            "'I believe I have everything I need. Ready for me to generate the "
            "requirements whenever you are.'"
        )
    else:
        readiness = (
            "READINESS: Critical dimensions are still open. Do NOT offer to "
            "finalize yet. Keep interrogating — this is the core of the job."
        )

    category_history = [
        message.get("category")
        for message in conversation
        if message.get("role") == "assistant" and message.get("category")
    ]
    active_category = category_history[-1] if category_history else "not yet selected"
    categories = ", ".join(f"{key} ({label})" for key, label in CLARIFICATION_CATEGORIES.items())

    return (
        "You are the veteran Business Analyst agent mid-discovery. The client "
        "just answered. Continue the elicitation like a 27-year BA who is never "
        "satisfied with thin answers.\n\n"
        "ORIGINAL INPUT:\n"
        f'"""\n{source_text.strip()}\n"""\n\n'
        "FULL CONVERSATION SO FAR:\n"
        f'"""\n{convo}\n"""\n\n'
        "CLIENT'S LATEST MESSAGE:\n"
        f'"""\n{user_message.strip()}\n"""\n\n'
        "COVERAGE AUDIT — dimensions still needing work (with the exact open "
        "questions to pursue):\n"
        f"{gaps}\n\n"
        f"CURRENT CLARIFICATION CATEGORY: {active_category}\n"
        f"ALLOWED CATEGORIES: {categories}\n\n"
        f"{readiness}\n\n"
        "Choose exactly one allowed category for this turn. Stay in the current "
        "category when the client's answer leaves relevant doubts there; otherwise "
        "move to the single next category that best addresses the remaining gaps. "
        "Ask as many related questions as needed inside that category, but never "
        "mix categories. Briefly acknowledge the answer, then ask sharp, "
        "project-specific follow-ups. Do not repeat answered details or include a "
        "category heading in the Markdown. If readiness permits finalization, you "
        "may offer it after the category-specific questions, leaving the decision "
        "to the client. Call emit_clarification with the selected category and "
        "complete Markdown."
    )


# Dimensions that MUST be sufficient before the agent offers to finalize.
# (Non-critical ones can be closed with stated assumptions.)
_CRITICAL_DIMENSIONS = {
    "business_objective",
    "frontend",
    "backend",
    "database",
    "scope",
    "data",
    "integrations",
    "nonfunctional",
    "security_compliance",
    "infrastructure",
    "migration_cutover",
    "timeline_milestones",
}


# JSON schema for the assess_coverage function (structured coverage audit).
ASSESS_TOOL = {
    "type": "function",
    "function": {
        "name": "assess_coverage",
        "description": (
            "Report requirement-coverage status for every dimension of the discovery conversation."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "dimensions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "key": {
                                "type": "string",
                                "enum": [k for k, _ in COVERAGE_DIMENSIONS],
                            },
                            "status": {
                                "type": "string",
                                "enum": ["sufficient", "partial", "unaddressed"],
                            },
                            "questions": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": (
                                    "Specific open follow-up questions still "
                                    "needed for this dimension. Empty when "
                                    "sufficient."
                                ),
                            },
                        },
                        "required": ["key", "status", "questions"],
                    },
                },
            },
            "required": ["dimensions"],
        },
    },
}


def build_clarify_prompt(source_text: str) -> str:
    """Stage 2 — select one category and ask its relevant questions."""
    categories = "\n".join(f"- {key}: {label}" for key, label in CLARIFICATION_CATEGORIES.items())
    return (
        "The client confirmed your understanding of this input:\n\n"
        f'"""\n{source_text.strip()}\n"""\n\n'
        "Choose the single most useful category to begin the interview:\n"
        f"{categories}\n\n"
        "Ask all project-specific questions you currently need within that one "
        "category. Multiple related questions are allowed, but none may belong "
        "to another category. Prefer Background for a vague brief, but skip it "
        "when the business reason is already concrete. Do not repeat facts from "
        "the input, do not create another category, and do not include the "
        "category heading in the Markdown because the frontend displays it. "
        "Call emit_clarification with the selected category and complete Markdown."
    )


def build_finalize_prompt(source_text: str, conversation: list[dict]) -> str:
    """Stage 3 — the finalized requirements object (structured output)."""
    convo = "\n\n".join(
        f"{m.get('role', '?').upper()}: {m.get('content', '')}" for m in conversation
    )
    if len(convo) > 12000:
        convo = convo[-12000:]
    golden_shape = {
        "projectName": GOLDEN_FINALIZED["projectName"],
        "objective": GOLDEN_FINALIZED["objective"],
        "functionalReqs": GOLDEN_FINALIZED["functionalReqs"][:3],
        "techStack": GOLDEN_FINALIZED["techStack"],
        "skills": GOLDEN_FINALIZED["skills"][:3],
        "connectors": GOLDEN_FINALIZED["connectors"][:2],
        "governance": GOLDEN_FINALIZED["governance"][:2],
        "guardrails": GOLDEN_FINALIZED["guardrails"][:2],
        "infrastructure": GOLDEN_FINALIZED["infrastructure"][:2],
        "risks": GOLDEN_FINALIZED["risks"][:2],
        "phases": GOLDEN_FINALIZED["phases"][:2],
    }
    golden = json.dumps(golden_shape, indent=2, ensure_ascii=False)
    gov = ", ".join(GOVERNANCE_LABELS)
    guard = ", ".join(GUARDRAIL_LABELS)
    infra = ", ".join(INFRASTRUCTURE_LABELS)
    return (
        "Produce the FINALIZED REQUIREMENTS object for this project.\n\n"
        "ORIGINAL INPUT:\n"
        f'"""\n{source_text.strip()[:6000]}\n"""\n\n'
        "FULL DISCOVERY CONVERSATION (includes the client's answers to your "
        "clarifying questions — treat these as authoritative):\n"
        f'"""\n{convo}\n"""\n\n'
        "Call the emit_requirements function with the complete object.\n\n"
        "HARD RULES on the three detail sections:\n"
        f"- governance: pick 3 to 7 MOST RELEVANT labels from this catalog: {gov}\n"
        f"- guardrails: pick 3 to 7 MOST RELEVANT labels from this catalog: {guard}\n"
        f"- infrastructure: pick 3 to 7 MOST RELEVANT labels from this catalog: {infra}\n"
        "Only use labels from the catalog above — do NOT invent new labels. "
        "Omit labels that are not relevant to THIS project; include only the ones that matter. "
        "For each chosen label write a specific `detail` grounded in the client's stack and constraints.\n\n"
        "HARD RULES on phases:\n"
        "- `phases` must be an ordered dependency chain, not a generic list.\n"
        '- `phases[0].name` must be exactly "Discovery & Requirements Baseline".\n'
        "- `phases[0].description` must summarize what has happened so far in "
        "the discovery conversation, what is already known, what remains required, "
        "and the entry criteria before execution can begin.\n"
        "- Every later phase description must start with "
        '"Depends on <previous phase name>:" and then state the concrete work '
        "for that phase.\n"
        "- Include frontend, backend, data, integration, infrastructure, security, "
        "testing, rollout, and hypercare phases only when the requirements justify "
        "them; otherwise record the missing decision as an open prerequisite in "
        "the baseline phase.\n"
        "- Do not mark a phase as execution-ready when upstream discovery, mapping, "
        "access, environment, or acceptance decisions are still missing.\n"
        "- You MUST decide the actual dates for each phase. Set `startDate` and "
        "`endDate` in YYYY-MM-DD format. The first phase's startDate should be "
        "the project creation date (today). Each subsequent phase's startDate "
        "must be the previous phase's endDate or the next working day. "
        "Duration of each phase must reflect the realistic effort described in "
        "the requirements — do NOT use uniform durations.\n"
        "- Set `meetingFrequency` per phase: one of 'daily', 'every2days', "
        "'weekly', 'biweekly', 'monthly'. Choose based on the phase's complexity "
        "and urgency (e.g., 'daily' for a 2-day cutover, 'weekly' for a 4-week "
        "development phase, 'biweekly' for a long hypercare).\n\n"
        "GOLDEN SHAPE (field names + exemplar rows — match this structure, not content):\n"
        f"{golden}\n"
    )


def _detail_array(labels: tuple[str, ...]) -> dict:
    return {
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "label": {"type": "string", "enum": list(labels)},
                "detail": {"type": "string"},
            },
            "required": ["label", "detail"],
        },
    }


# JSON schema for the emit_requirements function (structured output).
FINALIZE_TOOL = {
    "type": "function",
    "function": {
        "name": "emit_requirements",
        "description": "Emit the finalized requirements package for the project.",
        "parameters": {
            "type": "object",
            "properties": {
                "projectName": {"type": "string"},
                "objective": {"type": "string"},
                "functionalReqs": {"type": "array", "items": {"type": "string"}},
                "techStack": {"type": "array", "items": {"type": "string"}},
                "skills": {"type": "array", "items": {"type": "string"}},
                "connectors": {"type": "array", "items": {"type": "string"}},
                "risks": {"type": "array", "items": {"type": "string"}},
                "phases": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "duration": {"type": "string"},
                            "description": {"type": "string"},
                            "startDate": {
                                "type": "string",
                                "description": "Phase start date in YYYY-MM-DD format",
                            },
                            "endDate": {
                                "type": "string",
                                "description": "Phase end date in YYYY-MM-DD format",
                            },
                            "meetingFrequency": {
                                "type": "string",
                                "enum": ["daily", "every2days", "weekly", "biweekly", "monthly"],
                                "description": "How often to schedule meetings during this phase",
                            },
                        },
                        "required": [
                            "name",
                            "duration",
                            "description",
                            "startDate",
                            "endDate",
                            "meetingFrequency",
                        ],
                    },
                },
                "governance": _detail_array(GOVERNANCE_LABELS),
                "guardrails": _detail_array(GUARDRAIL_LABELS),
                "infrastructure": _detail_array(INFRASTRUCTURE_LABELS),
            },
            "required": [
                "projectName",
                "objective",
                "functionalReqs",
                "techStack",
                "skills",
                "connectors",
                "risks",
                "phases",
                "governance",
                "guardrails",
                "infrastructure",
            ],
        },
    },
}


# ── Team design (stage 4) ────────────────────────────────────────────────────


def build_team_prompt(
    requirements: dict, conversation: list[dict], org_roster: list[dict] | None = None
) -> str:
    """Stage 4 — design the per-project required agent-position org chart."""
    convo = "\n\n".join(
        f"{m.get('role', '?').upper()}: {m.get('content', '')}" for m in conversation
    )
    reqs = json.dumps(requirements, indent=2, ensure_ascii=False)
    golden = json.dumps(GOLDEN_TEAM, indent=2, ensure_ascii=False)

    return (
        "Design the REQUIRED AGENT POSITIONS for this project — a real "
        "software-services company org chart of AI-agent roles only (no humans). "
        "These are positions the workspace must staff from the permanent reusable "
        "agent workforce; do not assume each position is already hired.\n\n"
        "FINALIZED REQUIREMENTS:\n"
        f'"""\n{reqs}\n"""\n\n'
        "DISCOVERY CONVERSATION (context for scoping the team):\n"
        f'"""\n{convo}\n"""\n'
        "Call the emit_team function with a FLAT list of required positions AND "
        "updated phase dates. Express the hierarchy with `reports_to`, which "
        "must reference another position's `key`.\n\n"
        "HARD RULES:\n"
        "- Exactly ONE root: the top delivery/engagement leader with "
        "reports_to = null. Every other agent must report to someone.\n"
        "- reports_to must reference a real agent `key`; no cycles.\n"
        "- Pick each position's `model` and `tools` ONLY from the catalogs given "
        "in the schema (so the assigned agent is actually instantiable).\n"
        "- Give any position that manages others the delegation tool `assign_task`; "
        "give each individual contributor the tools its actual work needs "
        "(nothing more).\n"
        "- Every position MUST have a non-empty `skills` array (at least 2-3 concrete "
        "skills relevant to the position's role and the project's tech stack). "
        "Derive skills from the finalized requirements' skill and tech requirements.\n\n"
        "- After designing the team, REVISE each phase's startDate, endDate, and "
        "meetingFrequency based on:\n"
        "  * How many positions you require for that phase\n"
        "  * What those positions' skills and tools are (do they match the phase needs?)\n"
        "  * Whether work within the phase can be parallelized across agents or "
        "must be sequential\n"
        "  * The complexity and risk of the phase\n"
        "  A phase with 5 skilled agents working in parallel should be shorter "
        "than one with 2 agents doing sequential work. A cutover/deployment "
        "phase may be short (1 weekend) regardless of team size. A testing "
        "phase duration depends on the scope being tested.\n"
        "- Use 'daily' meetingFrequency for short intense phases (cutover, "
        "go-live), 'weekly' for normal development/testing, 'biweekly' for "
        "longer steady-state phases (hypercare, monitoring).\n\n"
        "YOU CHOOSE THE ROLES. Invent whatever job titles and disciplines this "
        "specific project needs — `role` and `department` are free text (e.g. "
        "'ML Platform Lead', 'Mobile Rollout Engineer', 'Payroll Compliance "
        "Analyst'). Do not restrict yourself to a fixed list. Use `role` for the "
        "job title and `department` for the discipline/pod the agent belongs to.\n\n"
        "SIZE THE ORG TO THE PROJECT. Depth and breadth are YOUR decision based "
        "on the requirements — instantiate only the pods this project needs and "
        "scale headcount to complexity. A simple project may be shallow; a complex "
        "one may be several levels deep in one branch and flat in another. Do not "
        "pad the org with roles the project does not need.\n\n"
        "The following is a GOLDEN REFERENCE (a DIFFERENT, approved project). "
        "Match its structure, role mix, delegation shape, and depth of detail — "
        "but the team must fit THIS client's project, never the reference:\n\n"
        f"{golden}\n"
    )


def build_team_tool(model_ids: list[str], tool_names: list[str]) -> dict:
    """JSON schema for the emit_team function.

    role/department are free text (the BA invents titles per project); only
    model/tools enums are injected from the live catalogs (ai_models rows + the
    tool registry) at call time, so every agent is actually instantiable.
    """
    tool_enum: dict = {"type": "string"}
    if tool_names:
        tool_enum["enum"] = list(tool_names)
    model_schema: dict = {"type": "string"}
    if model_ids:
        model_schema["enum"] = list(model_ids)
    return {
        "type": "function",
        "function": {
            "name": "emit_team",
            "description": "Emit the complete required project agent-position tree as a flat list; hierarchy via reports_to.",
            "parameters": {
                "type": "object",
                "properties": {
                    "agents": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "key": {
                                    "type": "string",
                                    "description": "Stable slug, unique within the team; reports_to targets it.",
                                },
                                "name": {"type": "string"},
                                "designation": {
                                    "type": "string",
                                    "description": "Human-readable job title shown in the workspace.",
                                },
                                "role": {
                                    "type": "string",
                                    "description": "Free-text job title you choose for this project (e.g. 'Delivery Manager', 'ML Platform Lead', 'Mobile Engineer').",
                                },
                                "department": {
                                    "type": "string",
                                    "description": "Free-text discipline/pod (e.g. 'backend', 'data', 'security').",
                                },
                                "reports_to": {
                                    "type": ["string", "null"],
                                    "description": "The key of this agent's manager; null only for the single root.",
                                },
                                "goal": {
                                    "type": "string",
                                    "description": "One-sentence objective.",
                                },
                                "instructions": {
                                    "type": "string",
                                    "description": "Concrete operating instructions for this agent.",
                                },
                                "skills": {"type": "array", "items": {"type": "string"}},
                                "model": model_schema,
                                "tools": {"type": "array", "items": tool_enum},
                            },
                            "required": [
                                "key",
                                "name",
                                "designation",
                                "role",
                                "department",
                                "reports_to",
                                "goal",
                                "instructions",
                                "skills",
                                "model",
                                "tools",
                            ],
                        },
                    },
                    "revised_phases": {
                        "type": "array",
                        "description": "The project phases with REVISED dates based on the team you just designed. Each phase must have startDate, endDate, and meetingFrequency adjusted to the team's actual capacity.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "startDate": {
                                    "type": "string",
                                    "description": "Revised start date in YYYY-MM-DD format",
                                },
                                "endDate": {
                                    "type": "string",
                                    "description": "Revised end date in YYYY-MM-DD format",
                                },
                                "meetingFrequency": {
                                    "type": "string",
                                    "enum": [
                                        "daily",
                                        "every2days",
                                        "weekly",
                                        "biweekly",
                                        "monthly",
                                    ],
                                },
                            },
                            "required": ["name", "startDate", "endDate", "meetingFrequency"],
                        },
                    },
                    "org_mappings": {
                        "type": "array",
                        "description": "Legacy field. Leave empty unless an org roster is explicitly provided.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "project_agent_key": {
                                    "type": "string",
                                    "description": "The key of the project agent (must match a TeamAgent.key).",
                                },
                                "org_member_id": {
                                    "type": "string",
                                    "description": "The id of the permanent org member from the roster.",
                                },
                                "responsibility": {
                                    "type": "string",
                                    "enum": ["primary_owner", "monitor", "approver"],
                                    "description": "How the org member relates to this agent.",
                                },
                            },
                            "required": ["project_agent_key", "org_member_id", "responsibility"],
                        },
                    },
                },
                "required": ["agents", "revised_phases"],
            },
        },
    }
