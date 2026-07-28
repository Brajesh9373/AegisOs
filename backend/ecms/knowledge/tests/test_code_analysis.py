"""Tests for the semantic code-analysis engine (SECTION 126)."""

from __future__ import annotations

from ecms.knowledge import PythonCodeAnalyzer, analyze_code, detect_language
from ecms.knowledge.infrastructure.code_analysis import GenericCodeAnalyzer
from ecms.shared.enums import RelationshipType

_PYTHON = '''
import os
from fastapi import APIRouter

router = APIRouter()


class AuthService(BaseService):
    """Handles authentication."""

    def login(self, user: str) -> bool:
        return True


@router.get("/health")
async def health() -> dict:
    return {"status": "ok"}
'''


def test_python_analysis_extracts_entities_and_imports() -> None:
    analysis = analyze_code(_PYTHON, language="python", module_name="auth")
    kinds = {entity.kind for entity in analysis.entities}
    assert {"module", "class", "api"} <= kinds
    assert "os" in analysis.imports
    assert "fastapi" in analysis.imports
    api = next(entity for entity in analysis.entities if entity.kind == "api")
    assert api.name == "health"


def test_python_analysis_records_inheritance_and_dependencies() -> None:
    analysis = PythonCodeAnalyzer().analyze(_PYTHON, module_name="auth")
    assert any(
        rel.relationship_type is RelationshipType.IMPLEMENTS and rel.target == "BaseService"
        for rel in analysis.relationships
    )
    assert any(
        rel.relationship_type is RelationshipType.DEPENDS_ON and rel.target == "fastapi"
        for rel in analysis.relationships
    )


def test_python_analysis_survives_syntax_errors() -> None:
    analysis = PythonCodeAnalyzer().analyze("def broken(:\n", module_name="bad")
    assert [entity.kind for entity in analysis.entities] == ["module"]


def test_language_detection() -> None:
    assert detect_language("def f():\n    pass") == "python"
    assert detect_language("const x = () => 1") == "javascript"
    assert detect_language("package main\nfunc main() {}") == "go"
    assert detect_language("plain text", hint="py") == "python"


def test_generic_analyzer_detects_imports() -> None:
    source = "const fs = require('fs')\nimport thing from './thing'"
    analysis = GenericCodeAnalyzer().analyze(source, language="javascript")
    assert "fs" in analysis.imports
