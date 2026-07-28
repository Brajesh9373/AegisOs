import re

from legacy_ecms.pipeline.structural.models import (
    StructuralArtifact,
    StructuralArtifactType,
    StructuralExtractionResult,
)

HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+?)\s*$")


class MarkdownStructuralExtractor:
    """Extract Markdown headings as document structure."""

    def extract(self, content: str) -> StructuralExtractionResult:
        artifacts: list[StructuralArtifact] = []
        for line_number, line in enumerate(content.splitlines(), start=1):
            match = HEADING_PATTERN.match(line)
            if not match:
                continue
            artifacts.append(
                StructuralArtifact(
                    type=StructuralArtifactType.HEADING,
                    name=match.group(2),
                    start_line=line_number,
                    end_line=line_number,
                    metadata={"level": len(match.group(1))},
                )
            )
        return StructuralExtractionResult(artifacts=artifacts)
