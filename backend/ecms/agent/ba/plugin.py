"""Business Analyst profile plugin for Agent OS.

This plugin reuses the existing BA cognition layer (contracts, provider, renderer,
executor, durable_writer) without rewriting it. It owns BA stage catalog/contracts/
validators, model identifiers, candidate extraction, finalization projection policy,
and profile-specific response mapping.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ecms.agent.ba.dsh_profile import business_analyst_dsh_profile_spec
from ecms.agent_os.profiles.contracts import (
    DSHProfileSpec,
    RuntimeReadiness,
    StageSpec,
    TerminalResult,
)
from ecms.agent_os.profiles.plugin import AgentProfilePlugin, ProfileContractError
from ecms.plugins.domain.manifest import PluginManifest

__all__ = ["BusinessAnalystProfilePlugin"]


class BusinessAnalystProfilePlugin(AgentProfilePlugin):
    """Business Analyst profile plugin for Agent OS.

    This profile implements the BA stages: understand, clarify, finalize, design_team.
    It reuses the existing BA cognition infrastructure and produces BA-specific
    terminal results (requirements, clarification questions, team designs).
    """

    @property
    def manifest(self) -> PluginManifest:
        """Return lifecycle metadata for the BA profile implementation."""
        return PluginManifest(
            name="agent-profile.business-analyst",
            version=self.profile_spec.version,
        )

    @property
    def profile_spec(self) -> DSHProfileSpec:
        """Return the static deployment-owned BA profile specification."""
        return business_analyst_dsh_profile_spec()

    def validate_request(self, stage: StageSpec, request: Mapping[str, Any]) -> None:
        """Validate the bounded host-rendered BA request for the given stage."""
        valid_stages = {"understand", "clarify", "finalize", "design_team"}
        if stage.stage_id not in valid_stages:
            raise ProfileContractError(f"unsupported BA stage {stage.stage_id!r}")

        if not isinstance(request, Mapping):
            raise ProfileContractError("BA request must be an object")

        # Stage-specific validation
        if stage.stage_id == "understand":
            source_text = request.get("source_text")
            if not isinstance(source_text, str) or not source_text.strip():
                raise ProfileContractError("understand requires non-empty source_text")
            if len(source_text.encode("utf-8")) > self.profile_spec.execution_budget.max_task_bytes:
                raise ProfileContractError("understand source_text exceeds task budget")

        elif stage.stage_id == "clarify":
            source_text = request.get("source_text")
            conversation = request.get("conversation", [])
            if not isinstance(source_text, str) or not source_text.strip():
                raise ProfileContractError("clarify requires non-empty source_text")
            if not isinstance(conversation, list):
                raise ProfileContractError("clarify conversation must be a list")

        elif stage.stage_id == "finalize":
            source_text = request.get("source_text")
            conversation = request.get("conversation", [])
            if not isinstance(source_text, str) or not source_text.strip():
                raise ProfileContractError("finalize requires non-empty source_text")
            if not isinstance(conversation, list):
                raise ProfileContractError("finalize conversation must be a list")

        elif stage.stage_id == "design_team":
            requirements = request.get("requirements")
            if not isinstance(requirements, dict):
                raise ProfileContractError("design_team requires requirements object")

    def render_prompt(self, stage: StageSpec, request: Mapping[str, Any]) -> str:
        """Render a bounded prompt for the BA stage.

        This delegates to the existing BA cognition layer for prompt construction.
        """
        self.validate_request(stage, request)

        if stage.stage_id == "understand":
            return self._render_understand_prompt(request)
        elif stage.stage_id == "clarify":
            return self._render_clarify_prompt(request)
        elif stage.stage_id == "finalize":
            return self._render_finalize_prompt(request)
        elif stage.stage_id == "design_team":
            return self._render_design_team_prompt(request)

        raise ProfileContractError(f"unknown stage: {stage.stage_id}")

    def _render_understand_prompt(self, request: Mapping[str, Any]) -> str:
        """Render the understand stage prompt."""
        from ecms.agent.ba.prompts import build_understand_prompt

        source_text = request["source_text"]
        knowledge_context = request.get("knowledge_context", "")
        return build_understand_prompt(source_text, knowledge_context)

    def _render_clarify_prompt(self, request: Mapping[str, Any]) -> str:
        """Render the clarify stage prompt."""
        from ecms.agent.ba.prompts import build_clarify_prompt

        source_text = request["source_text"]
        conversation = request.get("conversation", [])
        knowledge_context = request.get("knowledge_context", "")
        return build_clarify_prompt(source_text, conversation, knowledge_context)

    def _render_finalize_prompt(self, request: Mapping[str, Any]) -> str:
        """Render the finalize stage prompt."""
        from ecms.agent.ba.prompts import build_finalize_prompt

        source_text = request["source_text"]
        conversation = request.get("conversation", [])
        knowledge_context = request.get("knowledge_context", "")
        return build_finalize_prompt(source_text, conversation, knowledge_context)

    def _render_design_team_prompt(self, request: Mapping[str, Any]) -> str:
        """Render the design_team stage prompt."""
        from ecms.agent.ba.prompts import build_team_design_prompt

        requirements = request["requirements"]
        return build_team_design_prompt(requirements)

    def validate_terminal_result(self, stage: StageSpec, result: TerminalResult) -> dict[str, Any]:
        """Validate and extract the BA-specific terminal result."""
        if result.stage_id != stage.stage_id:
            raise ProfileContractError(
                f"result stage {result.stage_id!r} does not match {stage.stage_id!r}"
            )

        # Validate result based on stage
        if stage.stage_id == "understand":
            return self._validate_understand_result(result)
        elif stage.stage_id == "clarify":
            return self._validate_clarify_result(result)
        elif stage.stage_id == "finalize":
            return self._validate_finalize_result(result)
        elif stage.stage_id == "design_team":
            return self._validate_design_team_result(result)

        raise ProfileContractError(f"unknown stage: {stage.stage_id}")

    def _validate_understand_result(self, result: TerminalResult) -> dict[str, Any]:
        """Validate understand stage result (markdown recap)."""
        if not isinstance(result.result, str):
            raise ProfileContractError("understand result must be markdown string")
        if not result.result.strip():
            raise ProfileContractError("understand result cannot be empty")
        return {"recap": result.result, "stage": "understand"}

    def _validate_clarify_result(self, result: TerminalResult) -> dict[str, Any]:
        """Validate clarify stage result (structured questions)."""
        if not isinstance(result.result, dict):
            raise ProfileContractError("clarify result must be an object")
        if "category" not in result.result:
            raise ProfileContractError("clarify result requires category")
        if "content" not in result.result:
            raise ProfileContractError("clarify result requires content")
        return {"questions": result.result, "stage": "clarify"}

    def _validate_finalize_result(self, result: TerminalResult) -> dict[str, Any]:
        """Validate finalize stage result (requirements package)."""
        if not isinstance(result.result, dict):
            raise ProfileContractError("finalize result must be an object")

        # Check for required fields in requirements package
        required = ["projectName", "objective", "functionalReqs"]
        for field in required:
            if field not in result.result:
                raise ProfileContractError(f"finalize result missing required field: {field}")

        # Ensure arrays are actually arrays
        for field in ["functionalReqs", "risks", "skills", "connectors"]:
            if field in result.result and not isinstance(result.result[field], list):
                raise ProfileContractError(f"finalize result.{field} must be an array")

        return {"requirements": result.result, "stage": "finalize"}

    def _validate_design_team_result(self, result: TerminalResult) -> dict[str, Any]:
        """Validate design_team stage result (team structure)."""
        if not isinstance(result.result, dict):
            raise ProfileContractError("design_team result must be an object")

        # Check for team structure
        if "team" not in result.result:
            raise ProfileContractError("design_team result requires team")
        if not isinstance(result.result["team"], list):
            raise ProfileContractError("design_team result.team must be an array")

        return {"team": result.result["team"], "stage": "design_team"}

    def readiness(self) -> RuntimeReadiness:
        """Report BA profile readiness."""
        spec = self.profile_spec
        return RuntimeReadiness(
            ready=True,
            profile_identity=spec.identity,
            profile_fingerprint=spec.fingerprint_payload().hex()[:16],
        )


# Global catalog instance
_catalog: AgentProfileCatalog | None = None


def get_ba_profile_catalog() -> AgentProfileCatalog:
    """Get the BA profile catalog singleton."""
    global _catalog
    if _catalog is None:
        from ecms.agent_os.profiles.plugin import AgentProfileCatalog

        _catalog = AgentProfileCatalog([BusinessAnalystProfilePlugin()])
    return _catalog
