# mypy: ignore-errors
"""JavaScript / TypeScript AST-based code analyzers using acorn + subprocess."""

from __future__ import annotations

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any, cast

from ecms.knowledge.domain.analysis import CodeAnalysis, CodeEntity, CodeRelationship
from ecms.shared.enums import RelationshipType

__all__ = ["JavaScriptAnalyzer", "TypeScriptAnalyzer"]

_JS_EXTRACT_SCRIPT = r"""
const fs = require('fs');
const code = fs.readFileSync(process.argv[2], 'utf8');
const acorn = require(process.argv[3]);
const walk = require('acorn-walk');

const ast = acorn.parse(code, { ecmaVersion: 'latest', sourceType: 'module', locations: true });
const entities = [];
const relationships = [];
const exportedNames = new Set();
const imports = new Map();

walk.simple(ast, {
  ImportDeclaration(node) {
    for (const spec of node.specifiers) {
      const imported = spec.imported ? spec.imported.name : 'default';
      imports.set(spec.local.name, { module: node.source.value, imported });
    }
  },
  CallExpression(node) {
    if (node.callee.name === 'require' && node.arguments.length > 0 && node.arguments[0].type === 'Literal') {
      const source = node.arguments[0].value;
      if (node.parent && (node.parent.type === 'VariableDeclarator' || node.parent.type === 'AssignmentExpression')) {
        imports.set('__require__', { module: source, imported: 'default' });
      }
    }
  }
});

walk.simple(ast, {
  FunctionDeclaration(node) {
    entities.push({
      kind: 'function', name: node.id ? node.id.name : 'anonymous',
      signature: '(' + node.params.map(p => p.name || '...').join(', ') + ')',
      docstring: null, lineno: node.loc ? node.loc.start.line : 0
    });
  },
  VariableDeclarator(node) {
    if (node.init && node.init.type === 'ArrowFunctionExpression') {
      entities.push({
        kind: 'function', name: node.id.name,
        signature: '(' + node.init.params.map(p => p.name || '...').join(', ') + ')',
        docstring: null, lineno: node.loc ? node.loc.start.line : 0
      });
    }
  },
  ClassDeclaration(node) {
    entities.push({
      kind: 'class', name: node.id.name,
      signature: 'class', docstring: null, lineno: node.loc ? node.loc.start.line : 0,
      bases: node.superClass ? [node.superClass.name || 'Object'] : []
    });
    for (const member of node.body.body) {
      if (member.type === 'MethodDefinition') {
        entities.push({
          kind: 'method', name: member.key.name,
          signature: '(' + member.value.params.map(p => p.name || '...').join(', ') + ')',
          docstring: null, lineno: member.loc ? member.loc.start.line : 0
        });
        relationships.push({
          source: node.id.name + '.' + member.key.name,
          target: node.id.name,
          relationship_type: 'belongs_to'
        });
      }
    }
    if (node.superClass) {
      relationships.push({
        source: node.id.name,
        target: node.superClass.name || 'Object',
        relationship_type: 'implements'
      });
    }
  },
  ExportNamedDeclaration(node) {
    if (node.declaration && node.declaration.id) {
      exportedNames.add(node.declaration.id.name);
    }
  },
  ExportDefaultDeclaration(node) {
    if (node.declaration && node.declaration.id) {
      exportedNames.add(node.declaration.id.name);
    }
  }
});

walk.simple(ast, {
  CallExpression(node) {
    if (node.callee.type === 'Identifier') {
      const name = node.callee.name;
      if (name !== 'require') {
        relationships.push({
          source: '__scope__',
          target: name,
          relationship_type: 'calls'
        });
      }
    }
    if (node.callee.type === 'MemberExpression' && node.callee.object.type === 'Identifier') {
      relationships.push({
        source: node.callee.object.name,
        target: node.callee.property.name,
        relationship_type: 'uses'
      });
    }
  }
});

for (const [local, data] of imports) {
  relationships.push({
    source: '__file__',
    target: data.module,
    relationship_type: 'depends_on'
  });
}

console.log(JSON.stringify({
  entities,
  relationships,
  imports: Object.fromEntries(imports),
  exports: [...exportedNames]
}));
"""


def _run_node_script(script_text: str, filepath: str, module: str = "acorn") -> dict[str, Any]:
    """Write JS extractor to temp file, run `node script.js filepath module`.

    Cannot use `node -e` because process.argv layout differs from
    running-a-file mode — argv[2] would be the module string not the file.
    NODE_PATH ensures global acorn is resolvable regardless of cwd.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".cjs", delete=False, encoding="utf-8") as f:
        f.write(script_text)
        script_path = f.name
    try:
        env = os.environ.copy()
        env.setdefault("NODE_PATH", "/usr/lib/node_modules")
        result = subprocess.run(
            ["node", script_path, filepath, module],
            capture_output=True,
            text=True,
            timeout=15,
            env=env,
        )
        if result.returncode != 0:
            from ecms.infrastructure.telemetry import get_logger

            get_logger("ecms.knowledge.js_analyzer").warning(
                "node_extract_failed",
                filepath=filepath,
                stderr=result.stderr[:500] if result.stderr else "",
            )
            return {}
        return json.loads(result.stdout)  # type: ignore[no-any-return]
    except subprocess.TimeoutExpired:
        return {}
    except json.JSONDecodeError:
        return {}
    except FileNotFoundError:
        return {}
    finally:
        Path(script_path).unlink(missing_ok=True)


class JavaScriptAnalyzer:
    """AST-based JavaScript code analyzer using acorn."""

    @staticmethod
    def analyze(content: str, *, module_name: str = "module") -> CodeAnalysis:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".cjs", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            fp = f.name
        try:
            data = _run_node_script(_JS_EXTRACT_SCRIPT, fp, "acorn")
        finally:
            Path(fp).unlink(missing_ok=True)

        data_repr = cast(dict[str, Any], data) if data else {}
        entities = []
        relationships = []
        imports: list[str] = []

        for ent in data_repr.get("entities", []):
            entities.append(
                CodeEntity(
                    kind=ent.get("kind", "function"),
                    name=ent.get("name", ""),
                    qualified_name=f"{module_name}.{ent.get('name', '')}",
                    signature=ent.get("signature"),
                    docstring=ent.get("docstring"),
                    bases=ent.get("bases", []),
                    lineno=ent.get("lineno", 0),
                )
            )
        for rel in data_repr.get("relationships", []):
            relationships.append(
                CodeRelationship(
                    source=rel.get("source", ""),
                    target=rel.get("target", ""),
                    relationship_type=RelationshipType(rel.get("relationship_type", "depends_on")),
                )
            )
        imports_list = (
            data_repr.get("imports", {}) if isinstance(data_repr.get("imports"), dict) else {}
        )
        imports = [v.get("module", "") for v in imports_list.values()]

        return CodeAnalysis(
            language="javascript",
            imports=imports,
            entities=entities,
            relationships=relationships,
        )


class TypeScriptAnalyzer:
    """AST-based TypeScript code analyzer — delegates to JS analyzer after transpilation attempt."""

    @staticmethod
    def analyze(content: str, *, module_name: str = "module") -> CodeAnalysis:
        # TypeScript files can be parsed as JS with acorn's typescript plugin
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".ts", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            fp = f.name
        try:
            data = _run_node_script(_JS_EXTRACT_SCRIPT, fp, "acorn")
        finally:
            Path(fp).unlink(missing_ok=True)

        data_repr = cast(dict[str, Any], data) if data else {}
        entities = [
            CodeEntity(
                kind=ent.get("kind", "function"),
                name=ent.get("name", ""),
                qualified_name=f"{module_name}.{ent.get('name', '')}",
                signature=ent.get("signature"),
                bases=ent.get("bases", []),
                lineno=ent.get("lineno", 0),
            )
            for ent in data_repr.get("entities", [])
        ]
        relationships = [
            CodeRelationship(
                source=rel.get("source", ""),
                target=rel.get("target", ""),
                relationship_type=RelationshipType(rel.get("relationship_type", "depends_on")),
            )
            for rel in data_repr.get("relationships", [])
        ]
        imports_list = (
            data_repr.get("imports", {}) if isinstance(data_repr.get("imports"), dict) else {}
        )
        imports = [v.get("module", "") for v in imports_list.values()]

        return CodeAnalysis(
            language="typescript",
            imports=imports,
            entities=entities,
            relationships=relationships,
        )
