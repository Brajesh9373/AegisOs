# Runtime Generator Rules

This document outlines the mandatory generation policy for the `@aegis/runtime` package and all subsequent platform packages (e.g., storage, monitoring, memory, knowledge, guardian, providers, workflow, agents, api, builder).

## Mandatory Code Generation Policy

1. **Source files are NEVER patched.**
2. **Source files are ALWAYS regenerated** completely from scratch.
3. **No string replacement** (`.replace()`) may be used to alter existing source logic.
4. **No regex replacement** may be used to mutate generated output files.
5. **No escaped newline insertion** (`\\n`); use actual multi-line strings.
6. **No JSON stringification of TypeScript** representations.
7. **Template literals only** for string construction and output assembly.
8. **UTF-8 output only** for all generated artifacts and source files.
9. **Verify generated code before writing** by asserting the output structure.
10. **Run formatter after generation** to guarantee AST syntactical correctness and standard style compliance.
