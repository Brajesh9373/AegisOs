"""Agent Profiles API - list and manage DSH agent profiles.

This module provides:
- List/read built-in plugin profiles (BusinessAnalyst, etc.)
- Full CRUD for database-stored AgentProfile configurations
- AI-powered scope analysis for new profiles
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select

from ecms.agent_os.scope_analyzer import analyze_profile_scopes
from ecms.persistence.database.rest_session import db_session
from ecms.persistence.models.agent_profile import AgentProfile

router = APIRouter(prefix="/api/agent-profiles")


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic Models for API
# ─────────────────────────────────────────────────────────────────────────────


class ProfileStageInput(BaseModel):
    stage_id: str
    description: str
    capability_ids: list[str] = []
    max_capability_requests: int = 0


class MemoryScopeInput(BaseModel):
    read: bool = True
    write: bool = False
    categories: list[str] = []
    retention_days: int = 30


class KnowledgeScopeInput(BaseModel):
    graphs: list[str] = ["default"]
    read: bool = True
    write: bool = False
    node_types: list[str] = []


class ToolScopeInput(BaseModel):
    allowed_tools: list[str] = []
    rate_limit: int = 60
    restrictions: dict[str, Any] = {}


class ExecutionBudgetInput(BaseModel):
    timeout_seconds: float = 300
    max_task_bytes: int = 96 * 1024
    max_stdout_bytes: int = 1 * 1024 * 1024


class ScopeRecommendationsInput(BaseModel):
    memory_scope: dict[str, Any]
    knowledge_scope: dict[str, Any]
    tool_scope: dict[str, Any]
    reasoning: str = ""


class ProfileCreateInput(BaseModel):
    """Input schema for creating a new agent profile."""

    profile_id: str = Field(..., description="Unique profile identifier")
    name: str = Field(..., description="Human-readable profile name")
    description: str | None = Field(None, description="Profile purpose")
    version: str = Field("1.0.0", description="Profile version")
    role: str | None = Field(None, description="Agent role designation")
    parent_profile_id: str | None = Field(None, description="Parent profile ID")
    system_prompt: str = Field(..., description="System prompt for the agent")
    user_prompt_template: str | None = Field(None, description="User prompt template")
    stages: list[ProfileStageInput] = Field(default_factory=list, description="Stage definitions")

    # Scope configurations
    memory_scope: dict[str, Any] = Field(default_factory=dict, description="Memory access config")
    knowledge_scope: dict[str, Any] = Field(
        default_factory=dict, description="Knowledge graph config"
    )
    tool_scope: dict[str, Any] = Field(default_factory=dict, description="Tool permissions")

    # AI recommendations (filled by backend)
    scope_recommendations: dict[str, Any] | None = Field(None, description="AI-suggested scopes")

    # LLM configuration
    model_provider: str | None = Field(None, description="LLM provider")
    model_name: str | None = Field(None, description="Model name")
    temperature: float | None = Field(None, ge=0, le=2)
    max_tokens: int | None = Field(None, gt=0)

    # Execution budget
    execution_budget: dict[str, Any] | None = Field(None, description="Execution limits")

    created_by: str | None = Field(None, description="User creating the profile")


class ProfileUpdateInput(BaseModel):
    """Input schema for updating an agent profile."""

    name: str | None = None
    description: str | None = None
    version: str | None = None
    status: str | None = None
    role: str | None = None
    parent_profile_id: str | None = None
    system_prompt: str | None = None
    user_prompt_template: str | None = None
    stages: list[ProfileStageInput] | None = None
    memory_scope: dict[str, Any] | None = None
    knowledge_scope: dict[str, Any] | None = None
    tool_scope: dict[str, Any] | None = None
    scope_recommendations: dict[str, Any] | None = None
    model_provider: str | None = None
    model_name: str | None = None
    temperature: float | None = None
    max_tokens: int | None = None
    execution_budget: dict[str, Any] | None = None


class ProfileOutput(BaseModel):
    """Output schema for agent profile responses."""

    id: str
    profile_id: str
    name: str
    description: str | None
    version: str
    status: str
    role: str | None
    parent_profile_id: str | None
    system_prompt: str | None
    user_prompt_template: str | None
    stages: list[dict[str, Any]] | None
    memory_scope: dict[str, Any]
    knowledge_scope: dict[str, Any]
    tool_scope: dict[str, Any]
    scope_recommendations: dict[str, Any] | None
    model_provider: str | None
    model_name: str | None
    temperature: float | None
    max_tokens: int | None
    execution_budget: dict[str, Any] | None
    created_by: str | None
    createdat: str
    updatedat: str


# ─────────────────────────────────────────────────────────────────────────────
# Helper Functions
# ─────────────────────────────────────────────────────────────────────────────


def _profile_to_output(profile: AgentProfile) -> ProfileOutput:
    """Convert AgentProfile ORM model to API output."""
    return ProfileOutput(
        id=profile.id,
        profile_id=profile.profile_id,
        name=profile.name,
        description=profile.description,
        version=profile.version,
        status=profile.status,
        role=profile.role,
        parent_profile_id=profile.parent_profile_id,
        system_prompt=profile.system_prompt,
        user_prompt_template=profile.user_prompt_template,
        stages=profile.stages,
        memory_scope=profile.memory_scope,
        knowledge_scope=profile.knowledge_scope,
        tool_scope=profile.tool_scope,
        scope_recommendations=profile.scope_recommendations,
        model_provider=profile.model_provider,
        model_name=profile.model_name,
        temperature=profile.temperature,
        max_tokens=profile.max_tokens,
        execution_budget=profile.execution_budget,
        created_by=profile.created_by,
        createdat=profile.createdat.isoformat() if profile.createdat else "",
        updatedat=profile.updatedat.isoformat() if profile.updatedat else "",
    )


def _get_installed_plugin_profiles() -> list[dict[str, Any]]:
    """Get built-in profiles from Python plugins."""
    profiles: list[dict[str, Any]] = []

    # Get BA profile
    try:
        from ecms.agent.ba.plugin import get_ba_profile_catalog

        catalog = get_ba_profile_catalog()
        ba = catalog.resolve("business-analyst")
        spec = ba.profile_spec
        profiles.append(
            {
                "profile_id": spec.profile_id,
                "version": spec.version,
                "name": "Business Analyst",
                "description": "Analyzes requirements, clarifies with stakeholders, and produces structured requirements packages",
                "stages": [{"stage_id": s.stage_id} for s in spec.stages],
                "source": "plugin",
            }
        )
    except Exception:
        pass

    # Get Compliance Officer profile
    try:
        from ecms.agent.compliance_officer import get_compliance_officer_profile_catalog

        catalog = get_compliance_officer_profile_catalog()
        co = catalog.resolve("compliance-officer")
        spec = co.profile_spec
        profiles.append(
            {
                "profile_id": spec.profile_id,
                "version": spec.version,
                "name": "Compliance Officer",
                "description": "Reviews agent actions for policy compliance and generates audit reports",
                "stages": [{"stage_id": s.stage_id} for s in spec.stages],
                "source": "plugin",
            }
        )
    except Exception:
        pass

    return profiles


# ─────────────────────────────────────────────────────────────────────────────
# API Endpoints
# ─────────────────────────────────────────────────────────────────────────────


@router.get("")
async def list_agent_profiles(
    include_plugin_profiles: bool = True,
    status: str | None = None,
) -> dict[str, Any]:
    """List all agent profiles.

    Args:
        include_plugin_profiles: Include built-in plugin profiles
        status: Filter by status (active, deprecated, draft)

    Returns:
        Dict with profiles list and metadata
    """
    all_profiles: list[dict[str, Any]] = []

    # Include plugin profiles if requested
    if include_plugin_profiles:
        all_profiles.extend(_get_installed_plugin_profiles())

    # Get database profiles
    async with db_session() as session:
        query = select(AgentProfile)
        if status:
            query = query.where(AgentProfile.status == status)

        result = await session.execute(query)
        db_profiles = result.scalars().all()

        for p in db_profiles:
            all_profiles.append(_profile_to_output(p).model_dump())

    return {
        "profiles": all_profiles,
        "total": len(all_profiles),
    }


@router.get("/db")
async def list_db_profiles(
    status: str | None = None,
    skip: int = 0,
    limit: int = 50,
) -> dict[str, Any]:
    """List only database-stored profiles (for management UI)."""
    async with db_session() as session:
        query = select(AgentProfile).offset(skip).limit(limit)
        if status:
            query = query.where(AgentProfile.status == status)

        result = await session.execute(query)
        profiles = result.scalars().all()

        return {
            "profiles": [_profile_to_output(p).model_dump() for p in profiles],
            "total": len(profiles),
            "skip": skip,
            "limit": limit,
        }


@router.post("/analyze-scopes")
async def analyze_scopes(
    name: str,
    description: str | None,
    system_prompt: str,
    role: str | None = None,
    parent_profile_id: str | None = None,
) -> dict[str, Any]:
    """Analyze profile and recommend permission scopes.

    This endpoint uses AI to analyze the profile configuration and
    recommend appropriate memory, knowledge, and tool scopes.
    """
    recommendations = await analyze_profile_scopes(
        name=name,
        description=description,
        system_prompt=system_prompt,
        role=role,
        parent_profile_id=parent_profile_id,
    )

    return {
        "recommendations": recommendations,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Agent Instantiation API - must be before POST "" to avoid route conflicts
# ─────────────────────────────────────────────────────────────────────────────


class AgentInstantiateInput(BaseModel):
    """Input for instantiating an agent from a profile."""

    profile_id: str = Field(..., description="Profile ID to instantiate")
    system_prompt_override: str | None = Field(
        None, description="Override the profile's system prompt"
    )
    model_name_override: str | None = Field(
        None, description="Override the profile's model"
    )
    temperature_override: float | None = Field(
        None, ge=0, le=2, description="Override the profile's temperature"
    )
    custom_scopes: dict[str, Any] | None = Field(
        None, description="Override scopes (memory, knowledge, tool)"
    )


class AgentInstanceOutput(BaseModel):
    """Output for an instantiated agent."""

    instance_id: str
    profile_id: str
    name: str
    role: str | None
    system_prompt: str
    stages: list[dict[str, Any]]
    memory_scope: dict[str, Any]
    knowledge_scope: dict[str, Any]
    tool_scope: dict[str, Any]
    llm_config: dict[str, Any]
    execution_budget: dict[str, Any]
    created: bool


# Global factory instance
_agent_factory: "AgentFactory | None" = None


def _get_agent_factory() -> "AgentFactory":
    """Get or create the global agent factory."""
    global _agent_factory
    if _agent_factory is None:
        # Use the shared singleton from runtime
        from ecms.agent_os.runtime import _agent_factory as runtime_factory

        _agent_factory = runtime_factory
    return _agent_factory


@router.post("/instantiate", response_model=AgentInstanceOutput)
async def instantiate_agent(
    data: AgentInstantiateInput,
) -> AgentInstanceOutput:
    """Instantiate an agent from a profile.

    This creates a runtime agent instance with the profile's configured
    scopes, system prompt, stages, and model settings.
    """
    factory = _get_agent_factory()

    overrides = {}
    if data.system_prompt_override:
        overrides["system_prompt"] = data.system_prompt_override
    if data.model_name_override:
        overrides["model_name"] = data.model_name_override
    if data.temperature_override is not None:
        overrides["temperature"] = data.temperature_override
    if data.custom_scopes:
        overrides.update(data.custom_scopes)

    try:
        # Use create_execution_context to enable scope enforcement
        instance = await factory.create_execution_context(data.profile_id, **overrides)
        return AgentInstanceOutput(
            instance_id=instance.instance_id,
            profile_id=instance.profile_id,
            name=instance.name,
            role=instance.role,
            system_prompt=instance.system_prompt,
            stages=instance.stages,
            memory_scope=instance.memory_scope,
            knowledge_scope=instance.knowledge_scope,
            tool_scope=instance.tool_scope,
            llm_config=instance.model_config,
            execution_budget=instance.execution_budget,
            created=True,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/instantiate")
async def list_agent_instances() -> dict[str, Any]:
    """List all active agent instances."""
    factory = _get_agent_factory()
    instances = factory.list_instances()
    return {
        "instances": [
            {
                "instance_id": i.instance_id,
                "profile_id": i.profile_id,
                "name": i.name,
                "role": i.role,
            }
            for i in instances
        ],
        "total": len(instances),
    }


@router.get("/instantiate/{instance_id}", response_model=AgentInstanceOutput)
async def get_agent_instance(instance_id: str) -> AgentInstanceOutput:
    """Get an active agent instance by ID."""
    factory = _get_agent_factory()
    instance = factory.get(instance_id)
    if not instance:
        raise HTTPException(
            status_code=404,
            detail=f"Agent instance '{instance_id}' not found",
        )
    return AgentInstanceOutput(
        instance_id=instance.instance_id,
        profile_id=instance.profile_id,
        name=instance.name,
        role=instance.role,
        system_prompt=instance.system_prompt,
        stages=instance.stages,
        memory_scope=instance.memory_scope,
        knowledge_scope=instance.knowledge_scope,
        tool_scope=instance.tool_scope,
        llm_config=instance.model_config,
        execution_budget=instance.execution_budget,
        created=False,
    )


@router.delete("/instantiate/{instance_id}")
async def destroy_agent_instance(instance_id: str) -> dict[str, Any]:
    """Destroy an agent instance."""
    factory = _get_agent_factory()
    if factory.remove(instance_id):
        return {"message": f"Agent instance '{instance_id}' destroyed", "destroyed": True}
    raise HTTPException(
        status_code=404,
        detail=f"Agent instance '{instance_id}' not found",
    )


@router.post("")
async def create_agent_profile(
    profile_data: ProfileCreateInput,
) -> ProfileOutput:
    """Create a new agent profile.

    This creates a database-stored profile that can be customized
    with specific scopes, system prompts, and configurations.
    """
    # Check for duplicate profile_id
    async with db_session() as session:
        existing = await session.execute(
            select(AgentProfile).where(AgentProfile.profile_id == profile_data.profile_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "PROFILE-ALREADY-EXISTS",
                    "message": f"Profile with ID '{profile_data.profile_id}' already exists",
                },
            )

        # Run scope analysis if no explicit scopes provided
        if not profile_data.memory_scope and not profile_data.knowledge_scope:
            try:
                recommendations = await analyze_profile_scopes(
                    name=profile_data.name,
                    description=profile_data.description,
                    system_prompt=profile_data.system_prompt,
                    role=profile_data.role,
                    parent_profile_id=profile_data.parent_profile_id,
                )
                profile_data.scope_recommendations = recommendations
            except Exception:
                pass  # Continue without recommendations

        # Create new profile
        profile = AgentProfile(
            id=str(uuid.uuid4()),
            profile_id=profile_data.profile_id,
            name=profile_data.name,
            description=profile_data.description,
            version=profile_data.version,
            status="active",
            role=profile_data.role,
            parent_profile_id=profile_data.parent_profile_id,
            system_prompt=profile_data.system_prompt,
            user_prompt_template=profile_data.user_prompt_template,
            stages=[s.model_dump() for s in profile_data.stages] if profile_data.stages else None,
            memory_scope=profile_data.scope_recommendations.get("memory_scope")
            if profile_data.scope_recommendations
            else profile_data.memory_scope,
            knowledge_scope=profile_data.scope_recommendations.get("knowledge_scope")
            if profile_data.scope_recommendations
            else profile_data.knowledge_scope,
            tool_scope=profile_data.scope_recommendations.get("tool_scope")
            if profile_data.scope_recommendations
            else profile_data.tool_scope,
            scope_recommendations=profile_data.scope_recommendations,
            model_provider=profile_data.model_provider,
            model_name=profile_data.model_name,
            temperature=profile_data.temperature,
            max_tokens=profile_data.max_tokens,
            execution_budget=profile_data.execution_budget,
            created_by=profile_data.created_by,
        )

        session.add(profile)
        await session.commit()
        await session.refresh(profile)

        return _profile_to_output(profile)


@router.get("/{profile_id}")
async def get_agent_profile(profile_id: str) -> dict[str, Any]:
    """Get a specific profile by ID.

    First checks plugin profiles, then database profiles.
    """
    # Check plugin profiles first
    plugin_profiles = _get_installed_plugin_profiles()
    for p in plugin_profiles:
        if p["profile_id"] == profile_id:
            return p

    # Check database profiles
    async with db_session() as session:
        result = await session.execute(
            select(AgentProfile).where(AgentProfile.profile_id == profile_id)
        )
        profile = result.scalar_one_or_none()
        if profile:
            return _profile_to_output(profile).model_dump()

    raise HTTPException(
        status_code=404,
        detail={"error": "PROFILE-NOT-FOUND", "message": f"Profile {profile_id} not found"},
    )


@router.get("/db/{profile_id}")
async def get_db_profile(profile_id: str) -> ProfileOutput:
    """Get a specific database-stored profile by profile_id."""
    async with db_session() as session:
        result = await session.execute(
            select(AgentProfile).where(AgentProfile.profile_id == profile_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "PROFILE-NOT-FOUND",
                    "message": f"Database profile {profile_id} not found",
                },
            )

        return _profile_to_output(profile)


@router.put("/{profile_id}")
async def update_agent_profile(
    profile_id: str,
    update_data: ProfileUpdateInput,
) -> ProfileOutput:
    """Update an existing agent profile."""
    async with db_session() as session:
        result = await session.execute(
            select(AgentProfile).where(AgentProfile.profile_id == profile_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(
                status_code=404,
                detail={"error": "PROFILE-NOT-FOUND", "message": f"Profile {profile_id} not found"},
            )

        # Apply updates
        update_dict = update_data.model_dump(exclude_unset=True)
        for key, value in update_dict.items():
            if value is not None:
                setattr(profile, key, value)

        await session.commit()
        await session.refresh(profile)

        return _profile_to_output(profile)


@router.delete("/{profile_id}")
async def delete_agent_profile(profile_id: str) -> dict[str, Any]:
    """Delete an agent profile."""
    async with db_session() as session:
        result = await session.execute(
            select(AgentProfile).where(AgentProfile.profile_id == profile_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(
                status_code=404,
                detail={"error": "PROFILE-NOT-FOUND", "message": f"Profile {profile_id} not found"},
            )

        await session.delete(profile)
        await session.commit()

        return {"message": f"Profile {profile_id} deleted", "deleted": True}


@router.post("/{profile_id}/reanalyze-scopes")
async def reanalyze_scopes(profile_id: str) -> dict[str, Any]:
    """Re-analyze scopes for an existing profile using AI."""
    async with db_session() as session:
        result = await session.execute(
            select(AgentProfile).where(AgentProfile.profile_id == profile_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(
                status_code=404,
                detail={"error": "PROFILE-NOT-FOUND", "message": f"Profile {profile_id} not found"},
            )

        # Get current values
        name = profile.name
        description = profile.description
        system_prompt = profile.system_prompt or ""
        role = profile.role

        # Analyze
        recommendations = await analyze_profile_scopes(
            name=name,
            description=description,
            system_prompt=system_prompt,
            role=role,
            parent_profile_id=profile.parent_profile_id,
        )

        # Update scopes but keep recommendations for review
        profile.scope_recommendations = recommendations
        await session.commit()

        return {
            "current_scopes": {
                "memory_scope": profile.memory_scope,
                "knowledge_scope": profile.knowledge_scope,
                "tool_scope": profile.tool_scope,
            },
            "recommendations": recommendations,
        }


@router.post("/{profile_id}/apply-recommendations")
async def apply_recommendations(profile_id: str) -> ProfileOutput:
    """Apply AI-recommended scopes to a profile."""
    async with db_session() as session:
        result = await session.execute(
            select(AgentProfile).where(AgentProfile.profile_id == profile_id)
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(
                status_code=404,
                detail={"error": "PROFILE-NOT-FOUND", "message": f"Profile {profile_id} not found"},
            )

        if not profile.scope_recommendations:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "NO-RECOMMENDATIONS",
                    "message": "No scope recommendations available. Run analyze first.",
                },
            )

        # Apply recommended scopes
        profile.memory_scope = profile.scope_recommendations.get(
            "memory_scope", profile.memory_scope
        )
        profile.knowledge_scope = profile.scope_recommendations.get(
            "knowledge_scope", profile.knowledge_scope
        )
        profile.tool_scope = profile.scope_recommendations.get("tool_scope", profile.tool_scope)

        await session.commit()
        await session.refresh(profile)

        return _profile_to_output(profile)
