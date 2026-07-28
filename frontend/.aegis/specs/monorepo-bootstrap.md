# AegisAI Monorepo Bootstrap Specification

This document defines the exact structural layout, dependency boundaries, and workflow procedures for the AegisAI monorepo. It establishes the physical repository state *before* any implementation begins, ensuring architectural constraints are enforced by the file system itself.

---

## 1. Bootstrap Philosophy
A codebase is a physical reflection of the organization's architecture (Conway's Law). A chaotic repository structure guarantees a chaotic architecture. The AegisAI monorepo enforces the separation of concerns via strict folder structures, package boundaries, and unidirectional dependency graphs. If Guardian cannot import the API, the repository is working as intended.

## 2. Objectives
*   Establish a unified repository for all AegisAI source code to maximize code sharing and developer velocity.
*   Enforce hard boundaries between the Frontend (Presentation), API (Transport), Runtime (Execution), and Guardian (Governance).
*   Standardize the tooling (Turborepo, pnpm) across all packages.
*   Define clear procedures for expanding the repository.

---

## Repository Structure

## 3. Root Directory Layout
The repository is split into distinct top-level directories:
```text
/
├── .aegis/          (Architecture Specifications & ADRs)
├── .github/         (CI/CD Workflows & PR Templates)
├── apps/            (Deployable Applications)
├── packages/        (Internal Shared Libraries)
├── docker/          (Container manifests & Compose files)
├── scripts/         (Developer tooling and CI scripts)
├── docs/            (End-user documentation site)
├── package.json     (Root workspace configuration)
└── turbo.json       (Monorepo build orchestration)
```

## 4. `apps` Responsibilities
Contains the final, deployable artifacts. Applications consume `packages` but *never* consume other `apps`.
*   `/apps/web`: The Next.js frontend application.
*   `/apps/api`: The NestJS REST API server.
*   `/apps/worker`: The background job processing daemon.

## 5. `packages` Responsibilities
Contains highly cohesive, loosely coupled internal libraries. These are the building blocks of the applications.

## 6. `shared` Package Responsibilities
`/packages/shared`: The foundational library. Contains TypeScript interfaces, generic utilities, and cross-platform Zod schemas. It depends on *nothing*. Everything depends on it.

## 7. `sdk` Responsibilities
`/packages/sdk`: The TypeScript API Client. Auto-generated from the API's OpenAPI specification. Used by `/apps/web` and external integrators.

## 8. `runtime` Package Responsibilities
`/packages/runtime`: The core AI orchestration engine. Handles provider routing, prompt building, and tool execution. Depends on `database` and `guardian`.

## 9. `guardian` Package Responsibilities
`/packages/guardian`: The policy evaluation engine. A pure, isolated library. It accepts a payload and a policy, and returns `ALLOW` or `DENY`. Depends only on `shared`.

## 10. `database` Package Responsibilities
`/packages/database`: The single source of truth for database interaction. Contains the Prisma schema, generated client, and migration files. Only `/apps/api` and `/apps/worker` may import this directly.

## 11. `ui` Package Responsibilities
`/packages/ui`: The shared React component library (shadcn/ui primitives, Tailwind config). Used exclusively by `/apps/web` and `/docs`.

## 12. `worker` Package Responsibilities
(Migrated to `/apps/worker` as it is a deployable artifact).

## 13. `scripts` Responsibilities
Contains Node.js and Bash scripts for local development bootstrapping, database seeding, and CI/CD utility tasks.

## 14. `docker` Responsibilities
Contains `docker-compose.yml`, local development overrides, and the production `Dockerfile` definitions.

## 15. `docs` Responsibilities
Contains the source code for the public-facing documentation website (e.g., Nextra or Docusaurus).

## 16. `tests` Responsibilities
Unit tests live alongside the code (e.g., `user.service.spec.ts`). Global End-to-End (E2E) tests live in a dedicated root `/tests/e2e` folder to test the fully integrated system.

## 17. `.aegis` Responsibilities
The immutable architectural record. Contains all `.md` files detailing the system's design and Architectural Decision Records (ADRs).

---

## Build & Dependency Management

## 18. Build Strategy
The monorepo uses Turborepo. Building `/apps/web` will automatically build `/packages/ui` and `/packages/sdk` first. Builds are heavily cached both locally and remotely to ensure fast CI times.

## 19. Dependency Strategy
`pnpm` workspaces are used exclusively. Dependencies are hoisted to the root `node_modules` where possible to save disk space.

## 20. Package Dependency Rules
*   **Unidirectional Flow**: `apps` depend on `packages`. `packages` *never* depend on `apps`.
*   **The Shared Base**: All `packages` may depend on `@aegis/shared`.
*   **The Governance Ceiling**: `@aegis/runtime` must depend on `@aegis/guardian`. `@aegis/guardian` must *never* depend on `@aegis/runtime`.

## 21. Shared Code Strategy
Code needed by both the API and the Web frontend (e.g., validation schemas, standard types) must be extracted to `@aegis/shared`. Do not duplicate types.

## 22. Import Rules
Packages must explicitly export their public API via `index.ts`. Deep imports into another package's internal file structure (e.g., `import { X } from '@aegis/database/src/internal/utils'`) are strictly forbidden and enforced via ESLint boundaries.

## 23. Environment Strategy
Environment variables are injected at deployment time. The monorepo provides a `.env.example` at the root, which developers copy to `.env.local` for `docker-compose` to consume.

---

## Workflows

## 24. Local Development Workflow
1.  Clone repo.
2.  `pnpm install`.
3.  `cp .env.example .env.local`.
4.  `pnpm run db:up` (Starts Postgres/Redis via Docker).
5.  `pnpm run dev` (Starts Turborepo watching all apps/packages).

## 25. Build Workflow
`pnpm build` triggers `turbo run build`. Turbo analyzes the dependency graph and builds packages in topological order.

## 26. Release Workflow
Releases are triggered via GitHub Actions upon tagging the `main` branch. The CI builds the production Docker images and pushes them to the Container Registry.

## 27. Versioning Workflow
The entire monorepo is versioned together (e.g., AegisAI v1.4.0). Independent package versioning (e.g., `@aegis/ui` v2.1 while `@aegis/api` is v1.4) is disabled to prevent internal version skew.

## 28. Branch Strategy
*   `main`: Always deployable. Protected.
*   `feature/XYZ`: Branched from `main`.
*   `fix/XYZ`: Branched from `main`.

## 29. Commit Standards
Conventional Commits are mandatory (e.g., `feat(api): add workspace creation endpoint`, `fix(ui): resolve button padding`). Enforced via Husky and commitlint.

## 30. Repository Protection Rules
*   Direct pushes to `main` are blocked.
*   PRs require 1 Approval.
*   PRs require CI (Lint, Test, Build) to pass.

## 31. Code Review Workflow
Reviewers must verify architectural alignment. Does this PR place business logic in the UI? Does it bypass Guardian? If so, reject immediately.

## 32. CI/CD Entry Points
Defined in `.github/workflows/`.
*   `pr.yml`: Runs tests/linting on PRs.
*   `deploy.yml`: Builds and pushes Docker images on tag.

## 33. Testing Entry Points
*   `pnpm test`: Runs all unit tests.
*   `pnpm test:e2e`: Runs Playwright integration tests.

## 34. Documentation Workflow
Any PR adding a new feature *must* include an update to the relevant `/docs` folder. Undocumented features do not exist.

## 35. Module Creation Workflow
When adding a new major feature (e.g., "Billing"):
1.  Define the API contracts.
2.  Define the Database schema updates.
3.  Implement in `@aegis/database`.
4.  Implement in `/apps/api`.
5.  Update `@aegis/sdk`.
6.  Implement in `/apps/web`.

## 36. Feature Development Workflow
Features must be developed "Backend First." The database schema and API must be reviewed and merged before frontend integration begins.

## 37. Bug Fix Workflow
1.  Write a failing test reproducing the bug.
2.  Fix the code so the test passes.
3.  Submit PR.

## 38. Refactoring Workflow
Refactoring should be isolated from feature additions. Do not mix a 50-file refactor with a new API endpoint in the same PR.

## 39. Architecture Change Workflow
Any change that violates `.aegis/specs/` requires an Architectural Decision Record (ADR).

## 40. ADR Workflow
1.  Create `.aegis/adrs/XXXX-proposed-change.md`.
2.  Detail Context, Decision, and Consequences.
3.  PR is reviewed by the Architect.
4.  If approved, the codebase is updated.

## 41. Release Workflow
See section 26.

## 42. Migration Workflow
Database migrations are strictly forward-only. If a migration is flawed, a new migration must be written to fix it. Never alter a previously committed migration file.

## 43. Future Expansion
The monorepo structure supports the seamless addition of new apps (e.g., `/apps/desktop` for an Electron wrapper, or `/apps/cli` for a terminal tool) that reuse the exact same `@aegis/runtime` and `@aegis/sdk`.

## 44. Permanent Constraints
*   Every module owns its responsibility.
*   No circular dependencies.
*   No duplicate packages.
*   No shared business logic outside the shared package.
*   Runtime is isolated.
*   Guardian is isolated.
*   UI never accesses the database directly.
*   Business logic never exists inside UI.
*   New modules require architecture approval.
*   Architecture changes require an ADR.
*   Every package must have tests.
*   Every package must have documentation.

---

## Examples

### Adding a new package
Need a new package for PDF processing?
1.  `mkdir packages/pdf-parser`
2.  `pnpm init`
3.  Update `package.json` name to `@aegis/pdf-parser`.
4.  Add `@aegis/shared` as a dependency.

### Adding a new application
Need an internal Admin dashboard?
1.  `mkdir apps/admin-panel`
2.  Initialize Next.js.
3.  Depend on `@aegis/ui` and `@aegis/sdk`.

### Deprecating a package
1.  Add `[DEPRECATED]` to the package's `README.md`.
2.  Open issues to migrate all consumers.
3.  Once zero consumers exist, delete the folder.

---

## Monorepo Constitution
The permanent Repository principles of AegisAI:
1. **The Principle of Physical Boundaries**: Code structure enforces architecture. If two things should not communicate directly, they must not live in the same package.
2. **The Principle of Unidirectional Truth**: Information flows up. The Database does not know about the API. The API does not know about the UI. The UI knows about everything below it.
3. **The Principle of Shared Language**: If a concept, type, or schema is used by more than one entity, it must be elevated to a shared library. Duplication is the enemy of truth.
