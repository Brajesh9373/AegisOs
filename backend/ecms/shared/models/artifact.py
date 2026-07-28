"""Cognitive artifact domain model (SECTION 110/296).

Every meaningful output produced during execution becomes an artifact with full
provenance (origin task, session and agent) and links to the evidence, cognitive
objects and files it relates to. Artifacts are searchable through the graph.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import Field

from ecms.shared.ids import new_id
from ecms.shared.models.base import DomainModel
from ecms.shared.time import utcnow

__all__ = ["Artifact"]


def _artifact_id() -> str:
    return new_id("art")


class Artifact(DomainModel):
    """A meaningful output produced during execution, searchable via the graph (SECTION 110).

    The ``artifact_type`` is an open string (for example ``execution_plan``,
    ``generated_code``, ``architecture_decision``) so new kinds may be introduced
    without changing the model.
    """

    artifact_id: str = Field(default_factory=_artifact_id)
    artifact_type: str
    name: str
    description: str | None = None
    content: str | None = None
    uri: str | None = None
    origin_task: str | None = None
    origin_session: str | None = None
    origin_agent: str | None = None
    evidence: list[str] = Field(default_factory=list)
    related_ucos: list[str] = Field(default_factory=list)
    related_files: list[str] = Field(default_factory=list)
    version: int = Field(default=1, ge=1)
    version_history: list[dict[str, Any]] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=utcnow)
