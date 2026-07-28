"""Semantic code-analysis engine (SECTION 109/126).

Code understanding is driven by the source itself, not file names. Python is
analyzed with the standard-library AST; JavaScript/TypeScript use AST via acorn,
and other languages fall back to a language-agnostic import scanner. All produce
the same :class:`CodeAnalysis` shape so downstream knowledge extraction is uniform.
"""

from __future__ import annotations

import ast
import re

from ecms.knowledge.domain.analysis import CodeAnalysis, CodeEntity, CodeRelationship
from ecms.shared.enums import RelationshipType

__all__ = [
    "GenericCodeAnalyzer",
    "PythonCodeAnalyzer",
    "analyze_code",
    "detect_language",
]

_ROUTE_METHODS = {"get", "post", "put", "patch", "delete", "route", "websocket"}
_IMPORT_PATTERN = re.compile(
    r"""^\s*(?:import\s+(?P<a>[\w./-]+)
        |from\s+(?P<b>[\w.]+)\s+import
        |(?:const|let|var)\s+\w+\s*=\s*require\(['"](?P<c>[^'"]+)['"]\)
        |import\s+.*?from\s+['"](?P<d>[^'"]+)['"]
        |\#include\s+[<"](?P<e>[^>"]+)[>"])""",
    re.VERBOSE,
)


def detect_language(content: str, *, hint: str | None = None) -> str:
    """Detect a source language from an explicit hint or the content itself.

    Args:
        content: The source text.
        hint: An optional language or mime hint (for example ``"python"``).

    Returns:
        A lowercase language identifier such as ``"python"`` or ``"generic"``.
    """
    if hint:
        normalized = hint.lower().strip()
        short_map = {
            "py": "python", "pyi": "python",
            "js": "javascript", "mjs": "javascript", "cjs": "javascript",
            "jsx": "javascript",
            "ts": "typescript", "tsx": "typescript", "mts": "typescript",
            "go": "go", "rs": "rust", "rb": "ruby", "java": "java",
            "swift": "swift", "kt": "kotlin", "kts": "kotlin",
            "scala": "scala", "cpp": "cpp", "cc": "cpp", "cxx": "cpp",
            "hpp": "cpp", "c": "c", "h": "c",
            "cs": "csharp", "php": "php",
            "sql": "sql", "sh": "shell", "bash": "shell", "zsh": "shell",
            "yaml": "yaml", "yml": "yaml", "json": "json",
            "xml": "xml", "html": "html", "htm": "html",
            "css": "css", "scss": "scss", "less": "less",
            "md": "markdown", "mdx": "markdown", "toml": "toml",
            "dockerfile": "dockerfile", "makefile": "makefile",
            "cmake": "cmake",
        }
        return short_map.get(normalized, normalized)
    sample = content.lstrip()[:2000]
    if re.search(r"^\s*(def |class |import |from \w)", sample, re.MULTILINE):
        return "python"
    if re.search(r"\b(function|const|=>|export|import\s.*from)\b", sample):
        return "javascript"
    if re.search(r"^\s*(package |func |import \()", sample, re.MULTILINE):
        return "go"
    if re.search(r"^\s*(fn |use |mod |impl |pub )", sample, re.MULTILINE) and re.search(r"->", sample):
        return "rust"
    if re.search(r"<\?php", sample):
        return "php"
    if re.search(r"^\s*(package\s+\w+;|import\s+java\.)", sample, re.MULTILINE):
        return "java"
    if re.search(r"^\s*(using\s+System|namespace\s+\w+)", sample, re.MULTILINE):
        return "csharp"
    if re.search(r"^\s*<!DOCTYPE\s+html|<html\b", sample, re.IGNORECASE):
        return "html"
    return "generic"


class PythonCodeAnalyzer:
    """Analyzes Python source using the standard-library AST (SECTION 126)."""

    language = "python"

    def analyze(self, content: str, *, module_name: str = "module") -> CodeAnalysis:
        """Return the entities and relationships defined by ``content``."""
        entities: list[CodeEntity] = [
            CodeEntity(kind="module", name=module_name, qualified_name=module_name)
        ]
        imports: list[str] = []
        relationships: list[CodeRelationship] = []
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return CodeAnalysis(language=self.language, entities=entities)
        for node in ast.iter_child_nodes(tree):
            self._visit(node, module_name, imports, entities, relationships)
        return CodeAnalysis(
            language=self.language,
            imports=imports,
            entities=entities,
            relationships=relationships,
        )

    def _visit(
        self,
        node: ast.AST,
        module_name: str,
        imports: list[str],
        entities: list[CodeEntity],
        relationships: list[CodeRelationship],
    ) -> None:
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
                relationships.append(self._dependency(module_name, alias.name))
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
            relationships.append(self._dependency(module_name, node.module))
        elif isinstance(node, ast.ClassDef):
            bases = [self._name(base) for base in node.bases]
            class_fqdn = f"{module_name}.{node.name}"
            entities.append(
                CodeEntity(
                    kind="class",
                    name=node.name,
                    qualified_name=class_fqdn,
                    docstring=ast.get_docstring(node),
                    bases=bases,
                    decorators=[self._name(d) for d in node.decorator_list],
                    lineno=node.lineno,
                )
            )
            for base in bases:
                relationships.append(
                    CodeRelationship(
                        source=node.name,
                        target=base,
                        relationship_type=RelationshipType.IMPLEMENTS,
                    )
                )
            # Recurse into class body to find methods
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    qualified_name = f"{class_fqdn}.{child.name}"
                    entities.append(
                        CodeEntity(
                            kind="method",
                            name=child.name,
                            qualified_name=qualified_name,
                            signature=f"({', '.join(a.arg for a in child.args.args)})",
                            docstring=ast.get_docstring(child),
                            lineno=child.lineno,
                        )
                    )
                    relationships.append(
                        CodeRelationship(
                            source=child.name,
                            target=node.name,
                            relationship_type=RelationshipType.BELONGS_TO,
                        )
                    )
        elif isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            decorators = [self._name(d) for d in node.decorator_list]
            kind = "api" if any(self._is_route(d) for d in decorators) else "function"
            arguments = ", ".join(argument.arg for argument in node.args.args)
            entities.append(
                CodeEntity(
                    kind=kind,
                    name=node.name,
                    qualified_name=f"{module_name}.{node.name}",
                    signature=f"({arguments})",
                    docstring=ast.get_docstring(node),
                    decorators=decorators,
                    lineno=node.lineno,
                )
            )

    @staticmethod
    def _dependency(module_name: str, target: str) -> CodeRelationship:
        return CodeRelationship(
            source=module_name,
            target=target.split(".", 1)[0],
            relationship_type=RelationshipType.DEPENDS_ON,
        )

    def _name(self, node: ast.expr) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            return f"{self._name(node.value)}.{node.attr}"
        if isinstance(node, ast.Call):
            return self._name(node.func)
        return ast.unparse(node)

    @staticmethod
    def _is_route(decorator: str) -> bool:
        return decorator.rsplit(".", 1)[-1] in _ROUTE_METHODS


class GenericCodeAnalyzer:
    """Language-agnostic import scanner for non-Python source (SECTION 126)."""

    def analyze(
        self, content: str, *, language: str = "generic", module_name: str = "module"
    ) -> CodeAnalysis:
        """Return a module entity plus any imports detected by pattern matching."""
        imports: list[str] = []
        relationships: list[CodeRelationship] = []
        for line in content.splitlines():
            match = _IMPORT_PATTERN.match(line)
            if match is None:
                continue
            target = next((value for value in match.groupdict().values() if value), None)
            if target is None:
                continue
            imports.append(target)
            relationships.append(
                CodeRelationship(
                    source=module_name,
                    target=target.split("/", 1)[0].split(".", 1)[0],
                    relationship_type=RelationshipType.DEPENDS_ON,
                )
            )
        entities = [CodeEntity(kind="module", name=module_name, qualified_name=module_name)]
        return CodeAnalysis(
            language=language,
            imports=imports,
            entities=entities,
            relationships=relationships,
        )


def analyze_code(
    content: str, *, language: str | None = None, module_name: str = "module"
) -> CodeAnalysis:
    """Analyze source code, dispatching to the best analyzer for its language.

    Args:
        content: The source text to analyze.
        language: An optional language hint; detected from content when omitted.
        module_name: The logical module name used to qualify entities.

    Returns:
        The structured analysis of the source.
    """
    resolved = detect_language(content, hint=language)
    if resolved == "python":
        return PythonCodeAnalyzer().analyze(content, module_name=module_name)
    if resolved in ("javascript", "typescript"):
        try:
            from ecms.knowledge.infrastructure.js_analyzer import JavaScriptAnalyzer, TypeScriptAnalyzer  # type: ignore[import-untyped,unused-ignore]
        except ImportError:
            pass  # fall through to generic
        else:
            if resolved == "typescript":
                return TypeScriptAnalyzer().analyze(content, module_name=module_name)
            return JavaScriptAnalyzer().analyze(content, module_name=module_name)
    return GenericCodeAnalyzer().analyze(content, language=resolved, module_name=module_name)
