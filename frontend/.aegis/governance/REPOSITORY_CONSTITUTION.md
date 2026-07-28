# Repository Constitution

## Purpose

While the AegisAI Platform Blueprint defines _what_ the platform is and its structural architecture, the **Repository Constitution** explicitly defines _how_ the platform is engineered. It establishes the immutable rules of engagement for developers, operations, and AI-assistants operating within this repository. This document serves as the absolute governing law for code integration, package ownership, and pipeline execution.

## Engineering Principles

- **Quality before speed:** Technical excellence supersedes delivery timelines.
- **Verification before commit:** All code must be mathematically and structurally verified before entering the version control ledger.
- **Blueprint before implementation:** No engineering may occur that contradicts or precedes the Constitutional Blueprint.
- **No undocumented architectural changes:** Architecture shifts strictly follow the RFC and ADR processes.
- **AI-assisted but human-verified development:** Machine intelligence accelerates creation; human accountability validates safety.
- **Small incremental changes:** Giant monolithic commits are strictly forbidden. PRs must be scoped and atomic.
- **Reproducible builds:** The repository must be capable of deterministic compilation from zero state in any clean environment.
- **Long-term maintainability:** Code is written to be read and maintained for a decade.

## Repository Structure

- `apps/` - Owned by Product Engineering. Contains end-user and operational frontend applications.
- `packages/` - Owned by Core Platform Engineering. Contains highly cohesive, decoupled architectural packages (`contracts`, `types`, `runtime`, etc.).
- `tools/` - Owned by DevOps. Contains infrastructure scripts, architecture archives, and internal development tooling.
- `scripts/` - Owned by CI/CD Engineering. Contains CI/CD triggers and automation workflows.
- `tests/` - Owned by Quality Assurance. Contains global e2e and integration testing suites outside the package scope.
- `docs/` - Owned by Technical Writing. Contains user-facing integration and onboarding manuals.
- `.aegis/` - Owned by the Chief Architect. The sacrosanct directory containing the Constitutional Blueprint and active Governance records.

## Branch Strategy

- `main` - Production-ready, historically immutable. Only accepts merges from `develop` or critical `hotfix/*`.
- `develop` - The active integration branch. Must remain in a deployable state at all times.
- `feature/*` - Ephemeral branches for atomic implementations. Must branch from `develop`.
- `hotfix/*` - Emergency branches for production vulnerabilities. Must branch from `main`.
- `release/*` - Stabilization branches created from `develop` prior to a `main` merge.
  **Merge Rules:** Fast-forward or squash merges only. No merge commits polluting the primary ledger.

## Commit Standards

- **Format:** Strict conventional commits (e.g., `feat:`, `fix:`, `chore:`, `refactor:`).
- **Atomic Commits:** Each commit must represent a single logical change. Formatting and logic changes must not be mixed.
- **Required Verification:** Pre-commit hooks (Husky) must successfully execute linting and typechecking before a commit is finalized.
- **Forbidden Practices:** "WIP", ambiguous messages, bypassing hooks (`--no-verify`), and committing sensitive credentials.

## Pull Request Standards

- **Checklist:** Every PR must include a description of the change, references to Technical Debt or Feature IDs, and a screenshot/log of local verification.
- **Review Requirements:** Minimum of one human approval. AI approvals are invalid for integration.
- **Verification Requirements:** CI/CD pipeline must pass 100% (Build, Lint, Test, Architecture).
- **Approval Rules:** No self-approvals. Code owners must approve modifications to their respective `packages/`.

## Package Ownership

Every package in the monorepo owns exactly _one_ bounded responsibility.

- No package may absorb responsibilities from another package (e.g., `ui` may not contain database connection logic).
- Cross-package boundary violations will be summarily rejected during architectural review.

## Dependency Rules

- **Allowed:** Downward dependency flow (e.g., `runtime` depends on `contracts`).
- **Forbidden:** Upward dependency flow or lateral coupling that violates the platform boundary model.
- **Circular Dependency Policy:** Absolutely forbidden. Zero tolerance. The build pipeline will immediately fail if `madge` detects a circular graph.

## AI Coding Rules

- AI **may assist** in generating boilerplate, logic, and tests.
- AI **may not bypass** verification steps or pre-commit hooks.
- AI **may not invent APIs** or modules that conflict with the Blueprint.
- AI **may not modify architecture** without passing the formal ADR/RFC governance process.
- AI **may not perform destructive Git operations** (e.g., force pushes, history rewrites, resets) without explicit human supervisory confirmation.

## Verification Pipeline

Every implementation entering the integration stream must deterministically pass:

1. **Format:** Prettier compliance.
2. **Lint:** ESLint strict compliance without warnings.
3. **Typecheck:** Complete `tsc` structural validation.
4. **Tests:** Vitest unit and integration suite execution.
5. **Build:** Turbo topological compilation.
6. **Circular Validation:** Madge circular dependency execution.
7. **Unused Validation:** Knip dead-code execution.
8. **Architecture Compliance:** Semantic adherence to the Blueprint.

## Daily Engineering Reports

- **Daily Report:** A concise ledger of actual work completed, logged in `.aegis/reports/DAILY_ENGINEERING_REPORTS.md`.
- **Phase Report / Completion Certificate:** Generated upon the conclusion of a macro-phase (e.g., Cleanup, Release).
- **Technical Debt Register:** All unresolved structural issues must be logged in `.aegis/engineering/TECHNICAL_DEBT_REGISTER.md`.
- **Decision Log:** Captured sequentially in daily updates or formal ADRs.

## Architecture Change Policy

All architectural structures reference the **AegisAI Platform Blueprint v3.2+**.

- **Minor Change:** Non-breaking optimization within a package boundary. Requires an **ADR** in `.aegis/adr/`.
- **Major Change:** Shifting of structural boundaries or introduction of new core engines. Requires an **RFC**.
- **Blueprint Revision Required:** If an RFC is approved, a new version of the Blueprint must be published and normalized before implementation begins.

## Release Policy

- **Verification Requirements:** Pipeline green, manual smoke test complete, Phase Certificate generated.
- **Tag Strategy:** Semantic versioning explicitly pushed to the origin (e.g., `v1.2.0`).
- **Versioning Strategy:** Changesets manages internal package synchronization and semantic bumping.
- **Rollback Policy:** Remote tags are deleted, and a `git revert` is issued to maintain ledger integrity.
- **Recovery Policy:** Total disaster recovery relies on isolated secure artifact backups (e.g., `.zip` archives off-site).

## Disaster Recovery

- **Backup Strategy:** Weekly binary snapshots of the entire workspace stored in secure off-site cold storage.
- **Repository Recovery:** Out-of-place cloning and exact state overlay (refer to the Phase 1.4 recovery incident).
- **Blueprint Backup:** The Blueprint is replicated across redundant documentation hubs.
- **Release Backup:** Compiled NPM artifacts and Docker images are mirrored across two disparate registries.
- **Verification after recovery:** Mandatory execution of the complete Verification Pipeline before normal operations resume.

## Definition of Done

A development task is officially complete _only_ if:

1. Code is implemented cleanly.
2. Tests are added and passing.
3. The Verification Pipeline passed locally and remotely.
4. Relevant package documentation is updated.
5. The implementation is 100% compliant with the Blueprint.
6. The Daily Engineering Report is updated.
7. Code is Committed atomically.
8. Code is Pushed to the remote repository.

## Repository Laws

1. The Constitutional Blueprint is the single, absolute architectural source of truth.
2. No direct commits to protected branches (`main`, `develop`).
3. No destructive Git commands (`reset`, `push --force`) without explicit human approval.
4. Every development phase must end with strict mathematical verification.
5. Every development phase must end with an official Phase Completion Certificate.
6. Technical Debt cannot be deleted; it can only be resolved and closed.
7. Code that cannot be tested will not be merged.
8. Circular dependencies are considered fatal build errors.
9. Temporary architectural generation scripts belong strictly in historical archives, not active paths.
10. If the repository integrity is uncertain, all development must immediately halt.
11. Security and permissions are opt-in, never opt-out.
12. The repository must remain fundamentally self-hosted and independent of SaaS lock-in.

---

## Implementation Mapping

- **Owner Package:** [To Be Defined]
- **Owner Modules:** [To Be Defined]
- **Related Packages:** [To Be Defined]
- **Required Contracts:** [To Be Defined]
- **Required Types:** [To Be Defined]
- **Required Runtime Components:** [To Be Defined]
- **Required Builder Components:** [To Be Defined]
- **Required APIs:** [To Be Defined]
- **Required Database Models:** [To Be Defined]
- **Required Workflows:** [To Be Defined]
- **Required Skills:** [To Be Defined]
- **Required Tests:** [To Be Defined]
- **Verification Commands:** [To Be Defined]
- **Roadmap Phase:** [To Be Defined]
- **Implementation Status:** [Not Started | In Progress | Completed | Frozen]
