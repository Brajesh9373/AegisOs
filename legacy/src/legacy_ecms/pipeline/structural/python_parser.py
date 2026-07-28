import ast

from legacy_ecms.pipeline.structural.models import (
    StructuralArtifact,
    StructuralArtifactType,
    StructuralExtractionResult,
    StructuralRelationship,
)


class PythonStructuralExtractor:
    """AST-based Python extractor for functions, classes, imports, and calls."""

    def extract(self, content: str) -> StructuralExtractionResult:
        try:
            tree = ast.parse(content)
        except SyntaxError as exc:
            return StructuralExtractionResult(errors=[str(exc)])

        artifacts: list[StructuralArtifact] = []
        relationships: list[StructuralRelationship] = []
        imports_by_root: dict[str, str] = {}

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.asname or alias.name.split(".", 1)[0]
                    imports_by_root[root] = alias.name
                    artifacts.append(
                        StructuralArtifact(
                            type=StructuralArtifactType.IMPORT,
                            name=alias.name,
                            start_line=node.lineno,
                            end_line=getattr(node, "end_lineno", node.lineno),
                            metadata={"asname": alias.asname},
                        )
                    )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                for alias in node.names:
                    name = f"{module}.{alias.name}" if module else alias.name
                    root = alias.asname or alias.name
                    imports_by_root[root] = name
                    artifacts.append(
                        StructuralArtifact(
                            type=StructuralArtifactType.IMPORT,
                            name=name,
                            start_line=node.lineno,
                            end_line=getattr(node, "end_lineno", node.lineno),
                            metadata={"module": module, "asname": alias.asname},
                        )
                    )
            elif isinstance(node, ast.ClassDef):
                artifacts.append(
                    StructuralArtifact(
                        type=StructuralArtifactType.CLASS,
                        name=node.name,
                        start_line=node.lineno,
                        end_line=getattr(node, "end_lineno", node.lineno),
                        docstring=ast.get_docstring(node),
                        metadata={"bases": [self._name_for_expr(base) for base in node.bases]},
                    )
                )
                for base in node.bases:
                    base_name = self._name_for_expr(base)
                    if base_name:
                        relationships.append(
                            StructuralRelationship(
                                source_name=node.name,
                                relationship="extends",
                                target_name=base_name,
                                metadata={"line": node.lineno},
                            )
                        )
                for child in node.body:
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        relationships.append(
                            StructuralRelationship(
                                source_name=node.name,
                                relationship="defines_method",
                                target_name=child.name,
                                metadata={"line": child.lineno},
                            )
                        )
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                parent_class = self._parent_class_for_function(tree, node)
                artifacts.append(
                    StructuralArtifact(
                        type=StructuralArtifactType.FUNCTION,
                        name=node.name,
                        start_line=node.lineno,
                        end_line=getattr(node, "end_lineno", node.lineno),
                        signature=self._signature_for_function(node),
                        docstring=ast.get_docstring(node),
                        metadata={
                            "async": isinstance(node, ast.AsyncFunctionDef),
                            "parent_class": parent_class,
                        },
                    )
                )
                for call in [child for child in ast.walk(node) if isinstance(child, ast.Call)]:
                    call_name = self._name_for_expr(call.func)
                    if call_name:
                        relationships.append(
                            StructuralRelationship(
                                source_name=node.name,
                                relationship="calls",
                                target_name=call_name,
                                metadata={"line": getattr(call, "lineno", None)},
                            )
                        )
                        root = call_name.split(".", 1)[0]
                        if root in imports_by_root:
                            relationships.append(
                                StructuralRelationship(
                                    source_name=node.name,
                                    relationship="uses_import",
                                    target_name=imports_by_root[root],
                                    metadata={"line": getattr(call, "lineno", None)},
                                )
                            )

        return StructuralExtractionResult(artifacts=artifacts, relationships=relationships)

    def _signature_for_function(self, node: ast.FunctionDef | ast.AsyncFunctionDef) -> str:
        args = [arg.arg for arg in node.args.posonlyargs + node.args.args]
        if node.args.vararg:
            args.append(f"*{node.args.vararg.arg}")
        args.extend(arg.arg for arg in node.args.kwonlyargs)
        if node.args.kwarg:
            args.append(f"**{node.args.kwarg.arg}")
        prefix = "async def" if isinstance(node, ast.AsyncFunctionDef) else "def"
        return f"{prefix} {node.name}({', '.join(args)})"

    def _parent_class_for_function(
        self,
        tree: ast.AST,
        function: ast.FunctionDef | ast.AsyncFunctionDef,
    ) -> str | None:
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and function in node.body:
                return node.name
        return None

    def _name_for_expr(self, node: ast.AST) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parent = self._name_for_expr(node.value)
            return f"{parent}.{node.attr}" if parent else node.attr
        if isinstance(node, ast.Call):
            return self._name_for_expr(node.func)
        if isinstance(node, ast.Subscript):
            return self._name_for_expr(node.value)
        return None
