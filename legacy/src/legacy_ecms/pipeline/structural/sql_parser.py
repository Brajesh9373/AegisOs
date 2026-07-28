import re

from legacy_ecms.pipeline.structural.models import (
    StructuralArtifact,
    StructuralArtifactType,
    StructuralExtractionResult,
    StructuralRelationship,
)

CREATE_TABLE_HEADER_PATTERN = re.compile(
    r"create\s+table\s+(?:if\s+not\s+exists\s+)?[`\"]?(?P<name>[\w.]+)[`\"]?\s*\(",
    re.IGNORECASE,
)
FOREIGN_KEY_PATTERN = re.compile(
    r"foreign\s+key\s*\((?P<columns>[^)]+)\)\s*references\s+[`\"]?(?P<table>[\w.]+)[`\"]?\s*\((?P<target_columns>[^)]+)\)",
    re.IGNORECASE,
)


class SqlStructuralExtractor:
    """Simple DDL extractor for CREATE TABLE statements and foreign keys."""

    def extract(self, content: str) -> StructuralExtractionResult:
        artifacts: list[StructuralArtifact] = []
        relationships: list[StructuralRelationship] = []

        for match, body in self._find_create_table_blocks(content):
            table_name = match.group("name")
            start_line = content[: match.start()].count("\n") + 1
            artifacts.append(
                StructuralArtifact(
                    type=StructuralArtifactType.TABLE,
                    name=table_name,
                    start_line=start_line,
                    metadata={"sql_type": "table"},
                )
            )

            for line in self._split_columns(body):
                stripped = line.strip().strip(",")
                if not stripped or stripped.lower().startswith(("primary key", "foreign key", "constraint")):
                    continue
                column_name = stripped.split()[0].strip("`\"")
                artifacts.append(
                    StructuralArtifact(
                        type=StructuralArtifactType.COLUMN,
                        name=f"{table_name}.{column_name}",
                        start_line=start_line,
                        metadata={"sql_type": "column", "table": table_name, "definition": stripped},
                    )
                )

            for fk in FOREIGN_KEY_PATTERN.finditer(body):
                relationships.append(
                    StructuralRelationship(
                        source_name=table_name,
                        relationship="references",
                        target_name=fk.group("table"),
                        metadata={
                            "columns": self._clean_csv(fk.group("columns")),
                            "target_columns": self._clean_csv(fk.group("target_columns")),
                        },
                    )
                )

        return StructuralExtractionResult(artifacts=artifacts, relationships=relationships)

    def _find_create_table_blocks(self, content: str) -> list[tuple[re.Match[str], str]]:
        blocks: list[tuple[re.Match[str], str]] = []
        for match in CREATE_TABLE_HEADER_PATTERN.finditer(content):
            body_start = match.end()
            depth = 1
            index = body_start
            while index < len(content) and depth > 0:
                char = content[index]
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                index += 1
            if depth == 0:
                blocks.append((match, content[body_start : index - 1]))
        return blocks

    def _split_columns(self, body: str) -> list[str]:
        parts: list[str] = []
        current: list[str] = []
        depth = 0
        for char in body:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
            if char == "," and depth == 0:
                parts.append("".join(current))
                current = []
            else:
                current.append(char)
        if current:
            parts.append("".join(current))
        return parts

    def _clean_csv(self, value: str) -> list[str]:
        return [item.strip().strip("`\"") for item in value.split(",")]
