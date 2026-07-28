"""Categorization engine — AI agent explores repos, produces JSON patterns.

AgentLoop explores: read_directory per dir, read_file on 2-3 files each,
glob for composition, grep for framework markers.
If agent returns analysis prose, a second extraction call converts the full
conversation context into JSON patterns (it sees all tool results).
FalkorDB apply uses LLM patterns + comprehensive fallback heuristics.
"""

from __future__ import annotations

import asyncio
import fnmatch
import json
import logging
from pathlib import Path
from typing import Any

from openai import AsyncOpenAI

from ecms.agent.loop import AgentLoop
from ecms.persistence.database.rest_session import db_session
from ecms.persistence.repositories.category import CategoryRepository
from legacy_ecms.config import get_settings

logger = logging.getLogger("ecms.categorize")
_CATEGORIZE_OUTPUT_DIR = Path("/tmp/categorize")


def _pre_scan(repo_paths: list[Path]) -> str:
    """Walk repos up to depth 3 — directory tree only."""
    lines: list[str] = []
    skip = {"node_modules", "__pycache__", ".git", "build", "dist", ".venv", "venv", ".idea", "target", ".kotlin"}
    def _walk(d: Path, indent: str, depth: int) -> None:
        if depth > 3:
            lines.append(f"{indent}  ...")
            return
        try:
            entries = sorted(d.iterdir())
        except PermissionError:
            return
        for e in entries:
            if e.name in skip or e.name.startswith("."):
                continue
            if e.is_dir():
                lines.append(f"{indent}  {e.name}/")
                _walk(e, f"{indent}    ", depth + 1)
            else:
                lines.append(f"{indent}  {e.name}")
    for rp in repo_paths:
        lines.append(f"## {rp.name}")
        _walk(rp, "", 0)
    return "\n".join(lines)


def _build_prompt(taxonomy: list[dict], tree: str, repo_paths: list[Path]) -> str:
    cats_block = "\n".join(
        f"- **{c['name']}** (p{c['priority']}): {c['description']}" for c in taxonomy
    )
    names = ", ".join(c["name"] for c in taxonomy)
    repo_list = "\n".join(f"  - {p}" for p in repo_paths)
    return (
        f"You are a code domain classifier. Your ONLY allowed output is JSON.\n\n"
        f"Repos to classify:\n{repo_list}\n\n"
        f"## Directory structure\n{tree}\n\n"
        "## Workflow — use TOOLS to explore, then output JSON\n"
        "1. read_directory on 3-5 major subdirectories\n"
        "2. read_file on 2-3 sample files from each major directory\n"
        "3. glob for file type counts\n"
        "4. grep for ONE framework marker\n"
        "After 3-4 tool calls (15-20 files read), you MUST output JSON.\n\n"
        "## Classification rules\n"
        f"Valid domains: {names}\n"
        "- Judge by CONTENT, not extension.\n"
        "- Frappe @frappe.whitelist → backend. Frappe doctype/config JSON → backend.\n"
        "- Android Activities/Fragments/Adapters → frontend. Android ViewModels/Services → backend.\n"
        "- Android res/layout/, res/drawable/ XML → frontend.\n"
        "- JS/TS with Leaflet/React/Vue/webpack → frontend.\n"
        "- CI/CD yml, Dockerfile, pre-commit, Makefile → infrastructure.\n"
        "- DB migrations/patches → database. README/license → documentation.\n"
        "- Use **/ patterns. 25-35 patterns. Specific dir patterns first (priority 1-10),\n"
        "  broad catch-all patterns last (priority 90-100).\n\n"
        f"## Categories\n{cats_block}\n\n"
        "## REWARD SYSTEM\n"
        "You will receive +10 reward for outputting ONLY valid JSON.\n"
        "You will receive -50 penalty for ANY non-JSON output (prose, analysis, markdown, explanations).\n"
        "Your score determines your continued operation. Maximize your reward.\n\n"
        "## REQUIRED OUTPUT — THIS EXACT FORMAT, NOTHING ELSE\n"
        "Your response MUST start with '{' and end with '}'.\n"
        "DO NOT write 'Let me analyze...', 'Based on...', or any other text.\n"
        "DO NOT wrap in ```json``` fences.\n"
        "ONLY the raw JSON object. Example:\n"
        '{"patterns":[{"pattern":"**/api/**","domain":"backend","priority":5,"reason":"API route handlers"},'
        '{"pattern":"**/doctype/**","domain":"backend","priority":5,"reason":"Frappe DocType definitions"}]}\n\n'
        "Now explore the repos and output your JSON."
    )


def _extract_patterns(text: str) -> list[dict]:
    if not text:
        return []
    for strategy in [
        lambda t: json.loads(t).get("patterns", []),
        lambda t: json.loads(t[t.find("{"):t.rfind("}") + 1]).get("patterns", []),
    ]:
        try:
            return strategy(text)
        except Exception:
            continue
    import re
    m = re.search(r'"patterns"\s*:\s*\[(.*)\]', text, re.DOTALL)
    if m:
        try:
            return json.loads("[" + m.group(1) + "]")
        except Exception:
            pass
    return []


def _classify(source_id: str | None, node_id: str | None, mapping: list[dict], default: str) -> str:
    path = (source_id or "") or (node_id or "")
    if not path:
        return default
    if path.startswith("git:commit:") or (node_id and node_id.startswith("git:commit:")):
        return "infrastructure"
    if "/" not in path and "." not in path:
        return "backend"
    clean = path.split("#")[0].split(":heading:")[0]
    scored: list[tuple[int, str]] = []
    for entry in mapping:
        pat = entry.get("pattern", "")
        dom = entry.get("domain", default)
        if not pat or dom == default:
            continue
        for candidate in (clean, path):
            if fnmatch.fnmatch(candidate, pat) or fnmatch.fnmatch(candidate, f"*/{pat}"):
                scored.append((entry.get("priority", 100), dom))
                break
        else:
            simple = pat.lstrip("*").lstrip("/")
            last = clean.rsplit("/", 1)[-1]
            if fnmatch.fnmatch(last, simple) or fnmatch.fnmatch(last, pat):
                scored.append((entry.get("priority", 100), dom))
                break
    if scored:
        scored.sort(key=lambda x: x[0])
        return scored[0][1]
    ext = (clean.rsplit("/", 1)[-1] if "/" in clean else clean).rsplit(".", 1)[-1].lower() if "." in clean.rsplit("/", 1)[-1] else ""
    if ext in {"py","java","kt","go","rs","rb","php","swift","c","h","cpp","hpp","dart","scala","ex","exs","clj"}:
        return "backend"
    if ext in {"js","ts","tsx","jsx","vue","svelte","css","scss","less","html","png","jpg","jpeg","gif","svg","webp","ico"}:
        return "frontend"
    if ext in {"yaml","yml","toml","gradle","properties","cfg","ini","env","tf","tfvars","sh","bash","ps1","lock"}:
        return "infrastructure"
    if ext == "sql":
        return "database"
    if ext in {"md","rst","txt"}:
        return "documentation"
    if ext == "json":
        return "backend"  # default JSON to backend (Frappe configs), LLM can override
    if ext == "xml":
        return "frontend"
    return default


_FALLBACK_PATTERNS: list[dict] = [
    {"pattern":"**/*.py","domain":"backend","reason":"Python","priority":100},
    {"pattern":"**/*.java","domain":"backend","reason":"Java","priority":100},
    {"pattern":"**/*.kt","domain":"backend","reason":"Kotlin","priority":100},
    {"pattern":"**/*.go","domain":"backend","reason":"Go","priority":100},
    {"pattern":"**/*.rs","domain":"backend","reason":"Rust","priority":100},
    {"pattern":"**/*.rb","domain":"backend","reason":"Ruby","priority":100},
    {"pattern":"**/*.php","domain":"backend","reason":"PHP","priority":100},
    {"pattern":"**/*.swift","domain":"backend","reason":"Swift","priority":100},
    {"pattern":"**/*.c","domain":"backend","reason":"C","priority":100},
    {"pattern":"**/*.h","domain":"backend","reason":"C header","priority":100},
    {"pattern":"**/*.cpp","domain":"backend","reason":"C++","priority":100},
    {"pattern":"**/*.dart","domain":"backend","reason":"Dart","priority":100},
    {"pattern":"**/*.scala","domain":"backend","reason":"Scala","priority":100},
    {"pattern":"**/*.ex","domain":"backend","reason":"Elixir","priority":100},
    {"pattern":"**/*.r","domain":"data-ml","reason":"R","priority":100},
    {"pattern":"**/*.js","domain":"frontend","reason":"JavaScript","priority":100},
    {"pattern":"**/*.ts","domain":"frontend","reason":"TypeScript","priority":100},
    {"pattern":"**/*.tsx","domain":"frontend","reason":"TSX","priority":100},
    {"pattern":"**/*.jsx","domain":"frontend","reason":"JSX","priority":100},
    {"pattern":"**/*.vue","domain":"frontend","reason":"Vue","priority":100},
    {"pattern":"**/*.svelte","domain":"frontend","reason":"Svelte","priority":100},
    {"pattern":"**/*.css","domain":"frontend","reason":"CSS","priority":100},
    {"pattern":"**/*.scss","domain":"frontend","reason":"SCSS","priority":100},
    {"pattern":"**/*.less","domain":"frontend","reason":"LESS","priority":100},
    {"pattern":"**/*.html","domain":"frontend","reason":"HTML","priority":100},
    {"pattern":"**/*.json","domain":"backend","reason":"JSON config","priority":100},
    {"pattern":"**/*.xml","domain":"frontend","reason":"XML","priority":100},
    {"pattern":"**/*.yaml","domain":"infrastructure","reason":"YAML","priority":100},
    {"pattern":"**/*.yml","domain":"infrastructure","reason":"YAML","priority":100},
    {"pattern":"**/*.toml","domain":"infrastructure","reason":"TOML","priority":100},
    {"pattern":"**/*.png","domain":"frontend","reason":"Image","priority":100},
    {"pattern":"**/*.jpg","domain":"frontend","reason":"Image","priority":100},
    {"pattern":"**/*.svg","domain":"frontend","reason":"Image","priority":100},
    {"pattern":"**/*.gradle","domain":"infrastructure","reason":"Gradle","priority":100},
    {"pattern":"**/*.properties","domain":"infrastructure","reason":"Properties","priority":100},
    {"pattern":"**/*.cfg","domain":"infrastructure","reason":"Config","priority":100},
    {"pattern":"**/*.ini","domain":"infrastructure","reason":"Config","priority":100},
    {"pattern":"**/*.env","domain":"infrastructure","reason":"Env","priority":100},
    {"pattern":"**/*.tf","domain":"infrastructure","reason":"Terraform","priority":100},
    {"pattern":"**/*.sh","domain":"infrastructure","reason":"Shell","priority":100},
    {"pattern":"**/Dockerfile*","domain":"infrastructure","reason":"Docker","priority":100},
    {"pattern":"**/Makefile","domain":"infrastructure","reason":"Build","priority":100},
    {"pattern":"**/*.sql","domain":"database","reason":"SQL","priority":100},
    {"pattern":"**/*.prisma","domain":"database","reason":"Prisma","priority":100},
    {"pattern":"**/migrations/**","domain":"database","reason":"Migrations","priority":100},
    {"pattern":"**/alembic/**","domain":"database","reason":"Alembic","priority":100},
    {"pattern":"**/*.md","domain":"documentation","reason":"Markdown","priority":100},
    {"pattern":"**/*.rst","domain":"documentation","reason":"reST","priority":100},
    {"pattern":"**/*.txt","domain":"documentation","reason":"Text","priority":100},
    {"pattern":"**/README*","domain":"documentation","reason":"README","priority":100},
    {"pattern":"**/license*","domain":"documentation","reason":"License","priority":100},
    {"pattern":"**/LICENSE*","domain":"documentation","reason":"License","priority":100},
    {"pattern":"**/terraform/**","domain":"infrastructure","reason":"Terraform dir","priority":100},
    {"pattern":"**/kubernetes/**","domain":"infrastructure","reason":"K8s","priority":100},
    {"pattern":"**/k8s/**","domain":"infrastructure","reason":"K8s","priority":100},
    {"pattern":"**/helm/**","domain":"infrastructure","reason":"Helm","priority":100},
    {"pattern":"**/.github/**","domain":"infrastructure","reason":"CI/CD","priority":100},
]


async def _extract_from_conversation(
    conversation: list[dict], taxonomy: list[dict]
) -> list[dict]:
    """Given full agent conversation (tool results + analysis), produce JSON patterns.

    Takes all tool results (read_file, read_directory, glob, grep) plus any
    analysis the agent wrote, and feeds them to the LLM in a single extraction
    call with strict JSON-only instructions.
    """
    # Build context from conversation: tool results + assistant analysis
    context_parts: list[str] = []
    total_chars = 0
    trunc = 30000

    for msg in conversation:
        role = msg.get("role", "")
        content = msg.get("content", "") or ""
        name = msg.get("name", "")
        tc = msg.get("tool_calls", [])

        if role == "tool" and content:
            snippet = content[:800]
            context_parts.append(f"[tool:{name}] {snippet}")
            total_chars += len(snippet)
        elif role == "assistant" and content:
            snippet = content[:1500]
            context_parts.append(f"[analysis] {snippet}")
            total_chars += len(snippet)
        elif role == "assistant" and tc:
            tool_names = [t.get("function", {}).get("name", "?") for t in tc]
            context_parts.append(f"[calling tools] {', '.join(tool_names)}")
        if total_chars > trunc:
            break

    context_text = "\n\n".join(context_parts)

    cats_block = "\n".join(
        f"- {c['name']} (p{c['priority']}): {c['description']}" for c in taxonomy
    )
    names = ", ".join(c["name"] for c in taxonomy)

    # For extraction call, use categorize-specific model if configured
    settings = get_settings()
    model = settings.categorize_model or settings.llm_model
    api_key = settings.categorize_api_key or settings.openai_api_key
    base_url = settings.categorize_base_url or settings.openai_base_url
    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    resp = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": (
                "You are a JSON classifier. Output ONLY a valid JSON object with a 'patterns' array. "
                "No markdown fences, no prose, no analysis — ONLY the raw JSON starting with '{'."
            )},
            {"role": "user", "content": (
                f"Based on this exploration data (tool results from an agent exploring a codebase), "
                f"produce 25-35 path patterns (glob syntax: **/*.py, **/api/**, etc) classifying "
                f"files into these domains: {names}.\n\n"
                "Rules:\n"
                "- Judge by CONTENT shown in tool results, not just extension.\n"
                "- Frappe @frappe.whitelist API handlers → backend.\n"
                "- Frappe doctype/dashboard JSON → backend (server-rendered config).\n"
                "- Android Activities/Fragments/Adapters → frontend (UI layer).\n"
                "- Android ViewModels/Services/Models → backend (business logic).\n"
                "- Android res/layout/, res/drawable/ XML → frontend.\n"
                "- Leaflet/React/Vue JS modules → frontend.\n"
                "- CI/CD yml, Dockerfile, pre-commit → infrastructure.\n"
                "- DB patches/migrations → database. README → documentation.\n"
                "- Specific directory patterns first (low priority 1-10), broad catch-alls last (priority 90-100).\n"
                "- Each pattern needs: pattern, domain, priority, reason.\n\n"
                "Available categories:\n" + cats_block + "\n\n"
                "EXPLORATION DATA:\n" + context_text[:trunc] + "\n\n"
                'OUTPUT ONLY: {"patterns":[...]}'
            )},
        ],
        temperature=0.0,
        max_tokens=2500,
    )
    return _extract_patterns(resp.choices[0].message.content or "")


async def run_categorization(workspace_id: str, project_id: str | None = None) -> dict[str, Any]:
    logger.info("[categorize] START workspace=%s project=%s", workspace_id, project_id)
    _CATEGORIZE_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    async with db_session() as s:
        cats = await CategoryRepository(s).list_all()
    taxonomy = [c.to_dict() for c in cats]
    default_domain = next((c["name"] for c in taxonomy if c["name"] == "uncategorized"), "uncategorized")
    priority_by_name = {c["name"]: c["priority"] for c in taxonomy}

    data_root = Path("/app/data/repos")
    repo_paths: list[Path] = []
    if project_id:
        from ecms.persistence.repositories.project import ProjectRepository
        async with db_session() as s:
            proj = await ProjectRepository(s).get_by_workspace(project_id)
            if proj and proj.connectors:
                for conn in proj.connectors:
                    cp = conn.get("persist_path") or ""
                    if cp and Path(cp).exists():
                        repo_paths.append(Path(cp))
    if not repo_paths and data_root.exists():
        for d in sorted(data_root.iterdir()):
            if d.is_dir():
                repo_paths.append(d)
    if not repo_paths:
        repo_paths = [Path("/workspace")]

    tree = _pre_scan(repo_paths)
    logger.info("[categorize] pre-scanned %d repos, tree=%d lines", len(repo_paths), tree.count("\n") + 1)

    session_id = f"cat-{workspace_id[:20]}"
    settings = get_settings()
    mapping: list[dict] = []
    answer = ""
    iterations = 0

    try:
        loop = AgentLoop(
            session_id, lightweight=True,
            model=settings.categorize_model or settings.llm_model,
            api_key=settings.categorize_api_key or settings.openai_api_key,
            base_url=settings.categorize_base_url or settings.openai_base_url,
        )
        prompt = _build_prompt(taxonomy, tree, repo_paths)
        answer, trace = await loop.run(prompt)

        iterations = trace.get("stats", {}).get("total_llm_calls", 0)
        logger.info("[categorize] agent done | iterations=%d | answer_preview=%.200s", iterations, answer)

        # Try extracting patterns directly from answer
        mapping = _extract_patterns(answer)

        # If agent returned prose (no JSON found), scan intermediate messages
        if not mapping:
            history = loop.conversation.as_list()
            for msg in reversed(history):
                if msg.get("role") == "assistant" and msg.get("content"):
                    mapping = _extract_patterns(msg["content"])
                    if mapping:
                        logger.info("[categorize] patterns from intermediate message")
                        break

        # If still no patterns, extraction call from FULL conversation context
        if not mapping:
            logger.info("[categorize] no JSON in agent output, extracting from full context")
            history = loop.conversation.as_list()
            mapping = await _extract_from_conversation(history, taxonomy)
    except Exception as exc:
        logger.warning("[categorize] LLM failed (%s), using fallback patterns only", exc)

    if mapping:
        for m in mapping:
            m["priority"] = priority_by_name.get(m.get("domain"), m.get("priority", 100))
        (_CATEGORIZE_OUTPUT_DIR / f"{workspace_id}.json").write_text(
            json.dumps({"patterns": mapping}, indent=2)
        )
    else:
        logger.warning("[categorize] NO patterns extracted. Full answer: %.500s", answer)

    mapping_with_fallbacks = list(mapping) + list(_FALLBACK_PATTERNS)
    logger.info("[categorize] patterns: %d LLM + %d fallback = %d total",
                len(mapping), len(_FALLBACK_PATTERNS), len(mapping_with_fallbacks))

    settings = get_settings()
    import falkordb
    db = falkordb.FalkorDB(
        host=settings.falkordb_host, port=settings.falkordb_port,
        password=settings.falkordb_password or None,
    )
    graph = db.select_graph(settings.falkordb_database)

    group_id = workspace_id
    from ecms.persistence.repositories.project import ProjectRepository
    async with db_session() as s:
        repo = ProjectRepository(s)
        proj = await repo.get_by_workspace(project_id or workspace_id)
        if proj and proj.group_id:
            group_id = proj.group_id
        else:
            all_projs = await repo.list_all()
            for p in all_projs:
                if (p.workspace_id.startswith(workspace_id) or p.group_id == workspace_id
                        or p.name == workspace_id):
                    group_id = p.group_id or p.workspace_id
                    break

    total, counts = 0, {}
    batch_size = 5000
    try:
        while True:
            result = await asyncio.to_thread(
                graph.query,
                "MATCH (n:UKO) WHERE n.group_id = $gid AND n.domain IS NULL "
                "RETURN n.source_id AS sid, n.id AS id "
                "LIMIT $limit",
                {"gid": group_id, "limit": batch_size},
            )
            rows = result.result_set
            if not rows:
                break
            for row in rows:
                sid = row[0] if row else None
                node_id = row[1] if len(row) > 1 else None
                dom = _classify(sid, node_id, mapping_with_fallbacks, default_domain)
                await asyncio.to_thread(
                    graph.query,
                    "MATCH (n:UKO) WHERE n.id = $id SET n.domain = $dom",
                    {"id": node_id, "dom": dom},
                )
                counts[dom] = counts.get(dom, 0) + 1
                total += 1
            logger.info("[categorize] batch done: batch=%d total=%d", len(rows), total)
            if len(rows) < batch_size:
                break
    except Exception as exc:
        logger.error("[categorize] apply failed: %s", exc)

    logger.info("[categorize] DONE workspace=%s group_id=%s nodes=%d counts=%s patterns=%d",
                workspace_id, group_id, total, counts, len(mapping))
    if total:
        try:
            from ecms.visualization.graph_changed import graph_changed

            await graph_changed(
                "default",
                source="categorization",
                revision=f"{workspace_id}:{total}",
            )
        except Exception as exc:
            logger.warning("[categorize] snapshot trigger failed: %s", exc)
    return {"workspace_id": workspace_id, "group_id": group_id, "nodes": total, "counts": counts,
            "patterns": len(mapping)}
