from legacy_ecms.agents.context_assembler import ContextAssembler
from legacy_ecms.agents.reasoning import ReasoningEngine


class BaseAgent:
    def __init__(
        self,
        context_assembler: ContextAssembler | None = None,
        reasoning_engine: ReasoningEngine | None = None,
    ) -> None:
        self.context_assembler = context_assembler or ContextAssembler()
        self.reasoning_engine = reasoning_engine or ReasoningEngine()

    async def ask(self, question: str, session_id: str | None = None) -> str:
        context = await self.context_assembler.assemble(question, session_id=session_id)
        return await self.reasoning_engine.answer(context)
