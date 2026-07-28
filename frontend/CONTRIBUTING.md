# Contributing to aegisOS

Welcome to the aegisOS project. This document outlines the absolute rules for contributing to the repository. aegisOS is an Enterprise AI Workforce Operating System built on three unshakeable pillars: Control, Governance, and Accountability. Every contribution—whether from a human engineer or an AI assistant—must mathematically uphold these pillars.

## Development Workflow

1.  **Read the Architecture:** Before writing code, you must read the relevant specifications in the `.aegis/` folder.
2.  **Backend First:** Features are built starting from the database, moving to the API, and finally to the UI.
3.  **Governance First:** No tool, endpoint, or feature may be built without integrating it into the `Guardian` module and the `Audit Ledger`.
4.  **Local Testing:** Spin up the local environment (`docker-compose up`) and verify your feature against the local Postgres/Redis instances.

## Branch Strategy

We use Trunk-Based Development.

- **`main`**: The immutable, always-deployable production state. Direct pushes are physically blocked.
- **`feature/*`**: Short-lived branches for new capabilities (e.g., `feature/billing-api`).
- **`fix/*`**: Short-lived branches for bug resolution (e.g., `fix/guardian-regex-bypass`).
- **`chore/*`**: Maintenance tasks (e.g., `chore/update-dependencies`).

## Commit Standards

We strictly enforce Conventional Commits. A CI hook will block malformed commit messages.

- `feat(api): add endpoint for workspace creation`
- `fix(ui): resolve padding issue on agent card`
- `docs(architecture): update database schema for agent transfer`
- `refactor(guardian): optimize regex evaluation loop`

## Pull Request Process

1.  Push your branch and open a PR against `main`.
2.  Fill out the required PR template. You _must_ link to the `.aegis` specification you are implementing.
3.  CI will automatically run Linters, Unit Tests, and E2E Tests. All checks must pass (Green).
4.  Assign at least one Human Reviewer (or AI Reviewer Persona).

## Code Review Process

Reviewers are the final line of defense. The primary question during a code review is NOT "Does this code work?" The primary questions are:

1.  Does this code bypass Governance?
2.  Does this code violate the Architecture boundaries (e.g., UI making a direct DB call)?
3.  Is this action recorded in the Audit Ledger?
    If the answer to 1 or 2 is "Yes", or the answer to 3 is "No", the PR must be rejected immediately, regardless of how elegant the code is.

## Documentation Rules

**Code follows documentation.** If you are adding a new feature, you must update the relevant `.aegis/specs/` or `.aegis/modules/` file in the _same_ PR. If the feature fundamentally alters the system's design, you must submit an ADR first. Undocumented features do not exist.

## Testing Requirements

- **Unit Tests (Jest):** Required for all business logic, particularly the `packages/guardian` and `packages/runtime` folders.
- **Integration Tests (Supertest):** Required for every single REST API endpoint in `apps/api`.
- **E2E Tests (Playwright):** Required for critical UI paths (Login, Agent Creation, Builder Publish).

## ADR Requirements

If you wish to introduce a new database, a new framework, or change the fundamental execution loop, you cannot just open a PR with code. You must first create an Architectural Decision Record in `.aegis/adrs/` and get it approved by the Architecture Board.

## Security Requirements

- Secrets must _never_ be hardcoded. Use environment variables.
- Every API endpoint must validate its input using Zod schemas.
- Every database query must be performed via Prisma to prevent SQL injection.
- Every kinetic action performed by an AI _must_ pass through the `Guardian` module. No exceptions.

## Coding Standards

- **TypeScript:** Strict mode is mandatory. `any` is forbidden. If you use `@ts-ignore`, your PR will be rejected.
- **Formatting:** Prettier runs automatically on commit. Do not argue about formatting.
- **Imports:** No circular dependencies. Respect the package boundaries defined in `monorepo-bootstrap.md`.

## AI Contribution Rules

If you are an AI assistant (Antigravity, Copilot, etc.) generating code for this repository:

1.  You must read `.aegis/core/constitution.md` before generating code.
2.  You must adopt the specific Persona defined in `.aegis/agents/` that matches the user's request.
3.  You are explicitly forbidden from hallucinating new architectures, bypassing Governance, or writing code that contradicts the `.aegis` folder.

## Release Process

Releases are triggered automatically via GitHub Actions when a new semantic version tag (e.g., `v1.2.0`) is pushed to `main`. The CI pipeline builds the Docker images and pushes them to the enterprise registry.

## Do's and Don'ts

**DO:**

- Do write tests before you write code (TDD).
- Do keep PRs small and focused on a single architectural concept.
- Do explicitly log failures in the Audit Ledger.

**DON'T:**

- Don't trust the LLM. Always validate its output via Guardian.
- Don't mix architectural changes with bug fixes in the same PR.
- Don't submit a PR if you haven't run `docker-compose up` locally to verify it.

---

## Contributor Constitution

1. **The Law of Supremacy:** The architecture dictates the code. If the `.aegis` documentation and the source code conflict, the source code is wrong.
2. **The Law of the Ledger:** If an action is not auditable, it is illegal. Every kinetic movement within the platform must be permanently recorded.
3. **The Law of Human Anchor:** We build tools for humans. No AI agent, regardless of its intelligence, is ever granted autonomy without explicit, mathematically enforced human oversight.
