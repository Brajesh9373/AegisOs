# aegisOS Quality Gate

This document defines the mandatory verification checklist that must be satisfied before **ANY** commit is pushed to the repository. No exceptions are permitted.

## 1. Pipeline Verification

Before committing, you must successfully execute the following pipeline commands. All commands must exit with code `0`.

- [ ] **Build:** `pnpm build`
- [ ] **Lint:** `pnpm lint`
- [ ] **Typecheck:** `pnpm typecheck`
- [ ] **Test:** `pnpm test`
- [ ] **Circularity Check:** `npx madge --circular packages`

## 2. Code Quality & Standards

The codebase must adhere to the following structural invariants:

- [ ] **No TODOs introduced**: Do not commit partially implemented thoughts.
- [ ] **No `eslint-disable` added**: The architecture must comply with the rules natively.
- [ ] **No `console.log` in production packages**: Use the structured logging system.
- [ ] **No unused imports**: Keep the dependency graph clean.
- [ ] **No unused variables**: All defined variables must be utilized.
- [ ] **No circular dependencies**: Architectural boundaries are strictly enforced as DAGs.

## 3. Architecture & Delivery

- [ ] **No failing packages**: The entire monorepo must compile cleanly.
- [ ] **No partially implemented packages**: Features must be fully functional and tested before merging.
- [ ] **Documentation updated**: If the architecture, sequence, or dependencies changed, update the relevant reports and blueprint documents.

## 4. Final Review

- [ ] **Status Check**: `git status` shows a clean working directory without unintended file modifications.

**If any box is unchecked, the PR will be rejected. Stop, fix the issue natively, and run the pipeline again.**
