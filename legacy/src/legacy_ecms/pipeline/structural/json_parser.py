"""Bounded structural extraction for JSON documents."""

import json
from typing import Any

from legacy_ecms.pipeline.structural.models import (
    StructuralArtifact,
    StructuralArtifactType,
    StructuralExtractionResult,
)


class JsonStructuralExtractor:
    """Extract JSON object key paths."""

    def __init__(
        self,
        *,
        max_artifacts: int = 500,
        max_depth: int = 12,
        max_array_items: int = 50,
    ) -> None:
        """Configure hard ceilings for one JSON source file."""
        self._max_artifacts = max_artifacts
        self._max_depth = max_depth
        self._max_array_items = max_array_items

    def extract(self, content: str) -> StructuralExtractionResult:
        """Extract key paths without exceeding configured resource ceilings."""
        try:
            data = json.loads(content)
        except json.JSONDecodeError as exc:
            return StructuralExtractionResult(errors=[str(exc)])

        artifacts: list[StructuralArtifact] = []
        self._walk(data, "$", artifacts, depth=0)
        return StructuralExtractionResult(artifacts=artifacts)

    def _walk(
        self,
        value: Any,
        path: str,
        artifacts: list[StructuralArtifact],
        *,
        depth: int,
    ) -> None:
        if depth >= self._max_depth or len(artifacts) >= self._max_artifacts:
            return
        if isinstance(value, dict):
            for key, child in value.items():
                if len(artifacts) >= self._max_artifacts:
                    return
                child_path = f"{path}.{key}"
                artifacts.append(
                    StructuralArtifact(
                        type=StructuralArtifactType.JSON_KEY,
                        name=child_path,
                        metadata={"value_type": type(child).__name__},
                    )
                )
                self._walk(child, child_path, artifacts, depth=depth + 1)
        elif isinstance(value, list):
            for index, child in enumerate(value[: self._max_array_items]):
                if len(artifacts) >= self._max_artifacts:
                    return
                self._walk(
                    child,
                    f"{path}[{index}]",
                    artifacts,
                    depth=depth + 1,
                )
