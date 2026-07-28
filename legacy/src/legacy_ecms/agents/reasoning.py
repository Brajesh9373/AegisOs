from typing import Any

from legacy_ecms.agents.context_assembler import AssembledContext


class ReasoningEngine:
    """LLM-backed reasoning over assembled context from all memory layers.

    If an OpenAI client is configured, sends the combined context to the LLM.
    Falls back to deterministic summarization when no LLM is available.
    """

    def __init__(self, llm_client: Any = None) -> None:
        self._llm = llm_client

    async def answer(self, context: AssembledContext) -> str:
        if self._llm is not None:
            return await self._llm_answer(context)
        return self._deterministic_answer(context)

    async def _llm_answer(self, context: AssembledContext) -> str:
        prompt = self._build_prompt(context)
        response = self._llm.chat.completions.create(
            model="deepseek/deepseek-v4-flash",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        return response.choices[0].message.content or ""

    def _deterministic_answer(self, context: AssembledContext) -> str:
        sources: list[str] = []
        if context.mem0_results:
            sources.append(f"{len(context.mem0_results)} mem0 episodic memorie(s)")
        if context.memory_notes:
            sources.append(f"{len(context.memory_notes)} GBrain memory note(s)")
        if context.graph_results:
            sources.append(f"{len(context.graph_results)} knowledge graph result(s)")
        if context.session:
            sources.append("session context")
        if context.working:
            sources.append("working memory")

        source_text = ", ".join(sources) if sources else "no retrieved context"
        return f"Question: {context.query}\nContext used: {source_text}"

    def _build_prompt(self, context: AssembledContext) -> str:
        parts: list[str] = []

        if context.graph_results:
            parts.append("Knowledge Graph Results:")
            for item in context.graph_results[:5]:
                parts.append(f"  - {item}")
            parts.append("")

        if context.mem0_results:
            parts.append("Episodic Memories (mem0):")
            for item in context.mem0_results[:5]:
                memory = item.get("memory", str(item))
                score = item.get("score", "?")
                parts.append(f"  - [{score}] {memory}")
            parts.append("")

        if context.memory_notes:
            parts.append("Agent Notes (GBrain):")
            for item in context.memory_notes[:3]:
                content = item.get("content", str(item))[:200]
                parts.append(f"  - {content}")
            parts.append("")

        if context.session:
            parts.append(f"Session Context: {context.session}")
            parts.append("")

        parts.append(f"Question: {context.query}")
        parts.append("Answer using all available context. State which sources you relied on and your confidence level.")

        return "\n".join(parts)
