"""AI Scope Analyzer for agent profile permissions.

This module provides an LLM-powered service that analyzes agent profile
configurations and recommends appropriate memory, knowledge, and tool scopes.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from ecms.configuration import get_settings

logger = logging.getLogger(__name__)

# Default scope templates for common roles
DEFAULT_MEMORY_SCOPES: dict[str, dict[str, Any]] = {
    "read_only": {
        "read": True,
        "write": False,
        "categories": [],
        "retention_days": 30,
    },
    "read_write": {
        "read": True,
        "write": True,
        "categories": [],
        "retention_days": 90,
    },
    "ephemeral": {
        "read": True,
        "write": True,
        "categories": [],
        "retention_days": 1,
    },
}

DEFAULT_KNOWLEDGE_SCOPES: dict[str, dict[str, Any]] = {
    "none": {
        "graphs": [],
        "read": False,
        "write": False,
        "node_types": [],
    },
    "read_only": {
        "graphs": ["default"],
        "read": True,
        "write": False,
        "node_types": ["document", "concept", "entity"],
    },
    "read_write": {
        "graphs": ["default"],
        "read": True,
        "write": True,
        "node_types": ["document", "concept", "entity", "relationship"],
    },
}

DEFAULT_TOOL_SCOPES: dict[str, dict[str, Any]] = {
    "minimal": {
        "allowed_tools": [],
        "rate_limit": 10,
        "restrictions": {},
    },
    "standard": {
        "allowed_tools": ["search", "read", "list"],
        "rate_limit": 60,
        "restrictions": {},
    },
    "full": {
        "allowed_tools": ["search", "read", "write", "list", "create", "update", "delete"],
        "rate_limit": 120,
        "restrictions": {},
    },
}


class ScopeAnalyzer:
    """AI-powered scope analyzer for agent profiles.

    This analyzer uses an LLM to understand the agent's purpose and recommend
    appropriate permission scopes for memory, knowledge, and tools.
    """

    def __init__(self, llm_client: Any = None):
        """Initialize the scope analyzer.

        Args:
            llm_client: Optional LLM client. If not provided, uses default.
        """
        self.llm_client = llm_client
        self.settings = get_settings()

    async def analyze(
        self,
        name: str,
        description: str | None,
        system_prompt: str,
        role: str | None,
        parent_profile_id: str | None = None,
    ) -> dict[str, Any]:
        """Analyze profile config and recommend scopes.

        Args:
            name: Profile name
            description: Profile description/purpose
            system_prompt: System prompt defining agent behavior
            role: Agent role designation
            parent_profile_id: Parent profile ID for hierarchy

        Returns:
            Dict with recommended memory_scope, knowledge_scope, tool_scope
        """
        logger.info(
            "scope_analyzer.analyze",
            profile_name=name,
            role=role,
            has_parent=parent_profile_id is not None,
        )

        # Build analysis prompt
        analysis_prompt = self._build_analysis_prompt(
            name=name,
            description=description,
            system_prompt=system_prompt,
            role=role,
            parent_profile_id=parent_profile_id,
        )

        # Try to use LLM for analysis
        if self.llm_client:
            try:
                scope_recommendations = await self._analyze_with_llm(analysis_prompt)
                if scope_recommendations:
                    logger.info("scope_analyzer.llm_success", recommendations=scope_recommendations)
                    return scope_recommendations
            except Exception as e:
                logger.warning("scope_analyzer.llm_failed", error=str(e))

        # Fallback to rule-based analysis
        logger.info("scope_analyzer.using_rule_based")
        return self._rule_based_analysis(name, description, system_prompt, role, parent_profile_id)

    def _build_analysis_prompt(
        self,
        name: str,
        description: str | None,
        system_prompt: str,
        role: str | None,
        parent_profile_id: str | None,
    ) -> str:
        """Build the analysis prompt for the LLM."""
        return f"""You are an AI agent scope analyzer. Analyze the following agent profile
and recommend appropriate permission scopes.

## Agent Profile

**Name:** {name}
**Description:** {description or "Not provided"}
**Role:** {role or "Not specified"}
**Reports to:** {parent_profile_id or "No parent (top-level agent)"}
**System Prompt:**
{system_prompt[:1000]}

## Your Task

Analyze what this agent needs to accomplish based on its name, description, role,
and system prompt. Then recommend appropriate scopes for:

1. **Memory Access:** Does the agent need to read from memory, write to memory,
   or both? Should it access specific categories? How long should memory persist?

2. **Knowledge Graph Access:** Should the agent have read access to knowledge graphs,
   write access, or both? Which node types should it access?

3. **Tool Access:** Which tools should the agent be allowed to use? Consider
   search, read, write, create, update, delete operations.

## Output Format

Respond with a JSON object in this exact format:
{{
  "memory_scope": {{
    "read": true/false,
    "write": true/false,
    "categories": ["category1", "category2"],
    "retention_days": number
  }},
  "knowledge_scope": {{
    "graphs": ["graph1", "graph2"],
    "read": true/false,
    "write": true/false,
    "node_types": ["type1", "type2"]
  }},
  "tool_scope": {{
    "allowed_tools": ["tool1", "tool2"],
    "rate_limit": number,
    "restrictions": {{}}
  }},
  "reasoning": "Brief explanation of why these scopes were recommended"
}}

Consider the principle of least privilege - only grant access that is clearly
needed for the agent's stated purpose.
"""

    async def _analyze_with_llm(self, prompt: str) -> dict[str, Any] | None:
        """Use LLM to analyze and recommend scopes."""
        try:
            response = await self.llm_client.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                model=self.settings.openai_model or "gpt-4o",
                temperature=0.3,
                max_tokens=2000,
            )

            # Parse JSON from response
            content = response.choices[0].message.content
            # Extract JSON from markdown if present
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end]
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                content = content[start:end]

            scopes = json.loads(content.strip())

            # Validate structure
            required_keys = ["memory_scope", "knowledge_scope", "tool_scope"]
            if not all(k in scopes for k in required_keys):
                return None

            return scopes  # type: ignore[return-value]

        except Exception as e:
            logger.error("scope_analyzer.llm_error", error=str(e))
            return None

    def _rule_based_analysis(
        self,
        name: str,
        description: str | None,
        system_prompt: str,
        role: str | None,
        parent_profile_id: str | None,
    ) -> dict[str, Any]:
        """Fallback rule-based scope analysis."""
        name_lower = name.lower()
        desc_lower = (description or "").lower()
        prompt_lower = system_prompt.lower()
        role_lower = (role or "").lower()

        # Combine all text for keyword analysis
        full_text = f"{name_lower} {desc_lower} {prompt_lower} {role_lower}"

        # Analyze memory needs
        memory_scope = self._analyze_memory_scope(full_text, parent_profile_id)

        # Analyze knowledge needs
        knowledge_scope = self._analyze_knowledge_scope(full_text)

        # Analyze tool needs
        tool_scope = self._analyze_tool_scope(full_text)

        return {
            "memory_scope": memory_scope,
            "knowledge_scope": knowledge_scope,
            "tool_scope": tool_scope,
        }

    def _analyze_memory_scope(
        self,
        text: str,
        parent_profile_id: str | None,
    ) -> dict[str, Any]:
        """Analyze memory access needs."""
        # Keywords indicating memory read needs
        read_keywords = ["remember", "context", "history", "previous", "past", "memory"]
        # Keywords indicating memory write needs
        write_keywords = ["save", "store", "remember", "persist", "learn", "update"]

        has_read = any(kw in text for kw in read_keywords)
        has_write = any(kw in text for kw in write_keywords)

        # Child agents typically have less memory autonomy
        retention = 7 if parent_profile_id else 30

        return {
            "read": has_read or True,  # Default to read
            "write": has_write,
            "categories": [],
            "retention_days": retention,
        }

    def _analyze_knowledge_scope(self, text: str) -> dict[str, Any]:
        """Analyze knowledge graph access needs."""
        # Keywords for knowledge access
        read_kw = ["search", "find", "lookup", "query", "knowledge", "information", "research"]
        write_kw = ["create", "update", "add", "knowledge", "graph", "store"]

        has_read = any(kw in text for kw in read_kw)
        has_write = any(kw in text for kw in write_kw)

        return {
            "graphs": ["default"] if has_read else [],
            "read": has_read,
            "write": has_write,
            "node_types": ["document", "concept", "entity"] if has_read else [],
        }

    def _analyze_tool_scope(self, text: str) -> dict[str, Any]:
        """Analyze tool access needs."""
        # Map keywords to tools
        tool_keywords = {
            "search": ["search", "find", "lookup"],
            "read": ["read", "view", "get", "fetch"],
            "write": ["write", "create", "add", "new"],
            "update": ["update", "edit", "modify"],
            "delete": ["delete", "remove"],
            "list": ["list", "enumerate", "show"],
        }

        allowed_tools = []
        for tool, keywords in tool_keywords.items():
            if any(kw in text for kw in keywords):
                allowed_tools.append(tool)

        # Default to standard tools if none found
        if not allowed_tools:
            allowed_tools = ["search", "read", "list"]

        return {
            "allowed_tools": allowed_tools,
            "rate_limit": 60,
            "restrictions": {},
        }


# Singleton instance
_analyzer: ScopeAnalyzer | None = None


def get_scope_analyzer() -> ScopeAnalyzer:
    """Get the singleton scope analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = ScopeAnalyzer()
    return _analyzer


async def analyze_profile_scopes(
    name: str,
    description: str | None,
    system_prompt: str,
    role: str | None = None,
    parent_profile_id: str | None = None,
) -> dict[str, Any]:
    """Convenience function to analyze profile scopes.

    Args:
        name: Profile name
        description: Profile description
        system_prompt: System prompt
        role: Agent role
        parent_profile_id: Parent profile ID

    Returns:
        Dict with memory_scope, knowledge_scope, tool_scope_recommendations
    """
    analyzer = get_scope_analyzer()
    return await analyzer.analyze(name, description, system_prompt, role, parent_profile_id)
