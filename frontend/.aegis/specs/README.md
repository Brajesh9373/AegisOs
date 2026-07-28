# AegisAI Specifications Index

Welcome to the `.aegis/specs/` directory. While `.aegis/modules/` describes *how* the system works conceptually, the documents in this directory describe *what* physically exists. These are the strict blueprints for the data layer, the API transport layer, the UI presentation layer, and the underlying infrastructure.

## Purpose of Specification Documents

Specifications are the hard contracts between different engineering domains. A Frontend engineer does not need to know the internal logic of the Governance Engine to build the dashboard, but they *do* need to know the exact JSON payload the API will return. 

Any code written that deviates from these specifications—a missing database column, an unhandled API error code, or an extra UI dependency—is considered a bug and will be rejected during Code Review.

---

## The Specifications

### `technology-stack.md`
*   **What it is:** The definitive list of approved frameworks, libraries, and languages (e.g., Next.js, NestJS, PostgreSQL).
*   **Why it matters:** Prevents "resume-driven development" and "framework churn." If a tool is not on this list, you cannot `pnpm install` it without an approved Architectural Decision Record (ADR).

### `database-schema.md`
*   **What it is:** The complete logical entity relationship model. Defines tables, columns, relations, and indexing strategies.
*   **Why it matters:** The database is the single source of truth. Changes to this document require careful migration planning, as they ripple through the entire backend and frontend.

### `api-contracts.md`
*   **What it is:** The RESTful endpoints that connect the Presentation layer to the Application layer. Defines auth requirements, request payloads, and response shapes.
*   **Why it matters:** Allows the Frontend and Backend teams to work in parallel. As long as both teams conform to the contract, integration will succeed.

### `frontend-pages.md`
*   **What it is:** The inventory of every route, dashboard, and builder screen the user can navigate to, including the required RBAC permissions to view them.
*   **Why it matters:** Prevents orphaned pages and ensures that the UI architecture aligns with the platform's logical boundaries.

### `implementation-roadmap.md`
*   **What it is:** The prioritized sequence of development phases (e.g., Phase 1: Identity & Governance -> Phase 2: Runtime -> Phase 3: Builders).
*   **Why it matters:** Prevents engineers from building AI Orchestration features before the underlying Database and Audit layers are complete.

### `docker-architecture.md`
*   **What it is:** The physical deployment topography. Defines how the application is containerized, networked, and scaled.
*   **Why it matters:** Ensures that the code runs identically on a developer's laptop, in the CI/CD pipeline, and on the production enterprise cluster.

### `monorepo-bootstrap.md`
*   **What it is:** The physical folder structure of the Git repository, including Turborepo setup, package boundaries, and local development workflows.
*   **Why it matters:** Enforces the architectural boundaries at the file-system level. Code cannot leak between domains if the physical folder structure prohibits the import.

---

## Read Order

If you are beginning implementation work on a specific feature, you should consume the specifications in the following order:

1.  **`monorepo-bootstrap.md`** -> Know *where* to put your code.
2.  **`technology-stack.md`** -> Know *what tools* you are allowed to use.
3.  **`database-schema.md`** -> Know how the data is stored.
4.  **`api-contracts.md`** -> Know how the data is transported.
5.  **`frontend-pages.md`** -> Know how the data is presented.
6.  **`docker-architecture.md`** -> Know how the code will execute in production.
