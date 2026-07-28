# AegisAI Technology Stack Specification

This document defines the permanent, enterprise-grade technology stack for AegisAI. The selection prioritizes strict typing, horizontal scalability, proven stability over hypes, and deep community backing to ensure the platform remains maintainable for years without major rewrites.

---

## 1. Frontend Framework
**Selected:** React (with Next.js App Router)
*   **Why selected:** Industry standard for enterprise SPAs/SSRs. Deep ecosystem, robust developer tooling. Next.js provides necessary server-side rendering for initial load performance and API route integration.
*   **Alternatives considered:** Vue, Svelte, Angular.
*   **Why rejected:** Vue/Svelte lack the sheer volume of enterprise third-party libraries. Angular is overly opinionated and heavier to maintain.
*   **Long-term maintenance:** Backed by Meta and Vercel. Guaranteed long-term support.
*   **Enterprise suitability:** Excellent. Used by Fortune 500s globally.
*   **Community maturity:** The largest ecosystem in frontend web development.
*   **Performance:** Excellent when utilizing Server Components (RSC) to minimize client bundle size.

## 2. UI Component Library
**Selected:** Radix UI Primitives + Tailwind CSS (shadcn/ui approach)
*   **Why selected:** Provides unstyled, accessible primitives. We own the component code, eliminating vendor lock-in to a specific design system's constraints.
*   **Alternatives considered:** Material-UI (MUI), Ant Design, Bootstrap.
*   **Why rejected:** Heavy dependency footprints, difficult to heavily customize without fighting the framework, often look "generic."
*   **Long-term maintenance:** Because we own the implementation code (shadcn/ui model), updates to the underlying primitives don't break our UI.
*   **Enterprise suitability:** Excellent for building bespoke, brand-compliant enterprise dashboards.
*   **Community maturity:** Highly adopted modern standard.
*   **Performance:** Zero runtime overhead compared to CSS-in-JS solutions like MUI.

## 3. Styling Framework
**Selected:** Tailwind CSS
*   **Why selected:** Utility-first CSS allows rapid iteration, enforces a strict design token system, and guarantees tiny production CSS bundles via PurgeCSS.
*   **Alternatives considered:** Styled Components, SCSS/SASS, Vanilla CSS.
*   **Why rejected:** Styled Components adds runtime overhead. SCSS scales poorly in massive teams due to specificity wars.
*   **Long-term maintenance:** Highly stable API, widely understood by modern developers.
*   **Enterprise suitability:** High.
*   **Community maturity:** De facto standard for modern styling.
*   **Performance:** Optimal (compiles to absolute minimum CSS needed).

## 4. Icons
**Selected:** Lucide Icons
*   **Why selected:** Clean, consistent, lightweight SVG icons. Excellent React integration.
*   **Alternatives considered:** FontAwesome, Material Icons.
*   **Why rejected:** FontAwesome is heavy and often requires paid tiers. Material Icons feel dated.
*   **Long-term maintenance:** Active open-source community.
*   **Enterprise suitability:** High.
*   **Community maturity:** High.
*   **Performance:** SVG-based, easily tree-shaken.

## 5. Charts
**Selected:** Recharts
*   **Why selected:** Composable, React-native, declarative charting library built on D3. Highly customizable.
*   **Alternatives considered:** Chart.js, Highcharts.
*   **Why rejected:** Chart.js uses Canvas (harder to style with CSS/Tailwind). Highcharts requires commercial licenses.
*   **Long-term maintenance:** Stable and actively maintained.
*   **Enterprise suitability:** Excellent for dashboard analytics.
*   **Community maturity:** High.
*   **Performance:** Good for standard dataset sizes.

## 6. State Management
**Selected:** Zustand (Global) + React Query (Server State)
*   **Why selected:** React Query handles complex data fetching, caching, and invalidation flawlessly. Zustand is a tiny, unopinionated store for pure UI state (e.g., "is sidebar open").
*   **Alternatives considered:** Redux, MobX, Context API.
*   **Why rejected:** Redux requires massive boilerplate. Context API causes unnecessary re-renders.
*   **Long-term maintenance:** Zustand is minimal and unlikely to break. React Query is heavily backed (TanStack).
*   **Enterprise suitability:** High.
*   **Community maturity:** React Query is the industry standard for server state.
*   **Performance:** Optimal (prevents unnecessary renders).

## 7. Data Fetching
**Selected:** TanStack Query (React Query) + native `fetch`
*   **Why selected:** Handles caching, retries, polling, and deduplication automatically.
*   **Alternatives considered:** Axios, SWR.
*   **Why rejected:** Axios is redundant with modern `fetch`. SWR is good but less feature-rich than TanStack Query for complex enterprise mutations.
*   **Long-term maintenance:** Excellent.
*   **Enterprise suitability:** High.
*   **Community maturity:** Very High.
*   **Performance:** Excellent caching mechanisms.

## 8. Forms
**Selected:** React Hook Form
*   **Why selected:** Uncontrolled inputs by default, leading to massive performance gains in large forms. Tiny bundle size.
*   **Alternatives considered:** Formik, Redux Form.
*   **Why rejected:** Formik triggers re-renders on every keystroke. Redux Form is deprecated.
*   **Long-term maintenance:** Active and stable.
*   **Enterprise suitability:** High.
*   **Community maturity:** Very High.
*   **Performance:** Best-in-class for React forms.

## 9. Validation
**Selected:** Zod
*   **Why selected:** TypeScript-first schema declaration and validation. Can be shared between Frontend and Backend.
*   **Alternatives considered:** Yup, Joi.
*   **Why rejected:** Yup has poorer TS inference. Joi is mostly Node-specific.
*   **Long-term maintenance:** Highly stable.
*   **Enterprise suitability:** High.
*   **Community maturity:** Very High.
*   **Performance:** Fast and lightweight.

## 10. Rich Text Editor
**Selected:** TipTap
*   **Why selected:** Headless, highly customizable, built on ProseMirror. Outputs clean HTML/JSON.
*   **Alternatives considered:** Quill, Draft.js, CKEditor.
*   **Why rejected:** Draft.js is abandoned. Quill is difficult to heavily customize natively in React. CKEditor is heavy.
*   **Long-term maintenance:** Active and commercially backed.
*   **Enterprise suitability:** High.
*   **Community maturity:** High.
*   **Performance:** Excellent.

## 11. Markdown Support
**Selected:** React Markdown + remark/rehype plugins
*   **Why selected:** Safely renders markdown (crucial for LLM outputs). Highly extensible for syntax highlighting and math rendering.
*   **Alternatives considered:** marked.js.
*   **Why rejected:** Less idiomatic React integration.
*   **Long-term maintenance:** Stable ecosystem.
*   **Enterprise suitability:** High.
*   **Community maturity:** High.
*   **Performance:** Fast AST-based parsing.

## 12. Backend Framework
**Selected:** Node.js + NestJS (TypeScript)
*   **Why selected:** NestJS provides an opinionated, Angular-like architecture for Node, enforcing strict Dependency Injection, module separation, and testability. Crucial for large enterprise teams to maintain code consistency.
*   **Alternatives considered:** Express, Fastify, Python/FastAPI, Go.
*   **Why rejected:** Express/Fastify lack structural opinions, leading to spaghetti code. While Python is great for AI data science, TS allows full-stack code sharing (types/schemas). Go is harder to hire for rapidly.
*   **Long-term maintenance:** NestJS is highly stable and heavily adopted.
*   **Enterprise suitability:** Maximum. Built explicitly for enterprise architecture.
*   **Community maturity:** Very High.
*   **Performance:** High (when utilizing the Fastify adapter under the hood).

## 13. API Framework
**Selected:** REST (via NestJS Controllers)
*   **Why selected:** Ubiquitous, cacheable, easily integrated by enterprise third-parties.
*   **Alternatives considered:** GraphQL, gRPC.
*   **Why rejected:** GraphQL introduces massive security and performance overhead (N+1, complex rate limiting) unnecessary for our defined UI. gRPC is reserved for internal microservice communication if needed later, overkill for public API.
*   **Long-term maintenance:** Infinite.
*   **Enterprise suitability:** High.
*   **Community maturity:** Absolute.
*   **Performance:** Excellent with proper caching.

## 14. Authentication Library
**Selected:** Passport.js (within NestJS Auth) + external IdP (e.g., Keycloak/Auth0)
*   **Why selected:** Passport is the Node standard for strategy-based auth (JWT, Local, OAuth2).
*   **Alternatives considered:** NextAuth, custom middleware.
*   **Why rejected:** NextAuth ties auth too closely to the Next.js frontend, violating our API-first separation.
*   **Long-term maintenance:** Highly stable.
*   **Enterprise suitability:** High.
*   **Community maturity:** Very High.
*   **Performance:** Fast.

## 15. Authorization Strategy
**Selected:** Casbin (Node.js port) or bespoke RBAC Middleware
*   **Why selected:** Handles complex RBAC/ABAC models efficiently via memory caching.
*   **Alternatives considered:** Hardcoded checks.
*   **Why rejected:** Hardcoded checks do not scale to dynamic enterprise policies.
*   **Long-term maintenance:** Stable.
*   **Enterprise suitability:** Maximum.
*   **Community maturity:** High.
*   **Performance:** Evaluates in sub-millisecond time.

## 16. ORM
**Selected:** Prisma ORM
*   **Why selected:** Unmatched TypeScript DX. Auto-generated, strictly typed query builder prevents SQL runtime errors.
*   **Alternatives considered:** TypeORM, Sequelize, Knex.
*   **Why rejected:** TypeORM has stagnated. Sequelize has poor TS support.
*   **Long-term maintenance:** Heavily backed by Prisma Data.
*   **Enterprise suitability:** High.
*   **Community maturity:** Very High.
*   **Performance:** Good, with highly optimized Rust engine under the hood.

## 17. Database
**Selected:** PostgreSQL (16+)
*   **Why selected:** The absolute gold standard of open-source relational databases. ACID compliant, supports JSONB, and supports Vector extensions natively.
*   **Alternatives considered:** MySQL, MongoDB.
*   **Why rejected:** MySQL lacks advanced features. MongoDB (NoSQL) cannot guarantee the strict relational integrity required by the architecture.
*   **Long-term maintenance:** Infinite.
*   **Enterprise suitability:** Maximum.
*   **Community maturity:** Absolute.
*   **Performance:** Phenomenal.

## 18. Database Migration Tool
**Selected:** Prisma Migrate
*   **Why selected:** Native to our chosen ORM. Deterministic schema generation.
*   **Alternatives considered:** Flyway, Liquibase.
*   **Why rejected:** Adds unnecessary Java dependencies to a TS stack.
*   **Long-term maintenance:** High.
*   **Enterprise suitability:** High.
*   **Community maturity:** High.
*   **Performance:** Fast execution.

## 19. Cache
**Selected:** Redis (via ioredis)
*   **Why selected:** De facto standard for distributed in-memory caching and session management.
*   **Alternatives considered:** Memcached.
*   **Why rejected:** Lacks advanced data structures (Hashes, Sets) needed for complex caching.
*   **Long-term maintenance:** Infinite.
*   **Enterprise suitability:** Maximum.
*   **Community maturity:** Absolute.
*   **Performance:** Sub-millisecond.

## 20. Queue
**Selected:** RabbitMQ (via AMQP)
*   **Why selected:** Proven, enterprise-grade message broker. Guarantees delivery, supports complex routing.
*   **Alternatives considered:** Redis Pub/Sub, Kafka.
*   **Why rejected:** Redis queues are fragile and can lose data on crash. Kafka is too heavy for task queuing (better for massive event streaming).
*   **Long-term maintenance:** Highly stable.
*   **Enterprise suitability:** Maximum.
*   **Community maturity:** Absolute.
*   **Performance:** Very high.

## 21. Background Workers
**Selected:** BullMQ (backed by Redis)
*   **Why selected:** Robust job queue built specifically for NodeJS. Handles retries, concurrency, and delayed jobs perfectly.
*   **Alternatives considered:** Celery (Python), custom RabbitMQ workers.
*   **Why rejected:** Keeps the worker stack in TypeScript.
*   **Long-term maintenance:** Active.
*   **Enterprise suitability:** High.
*   **Community maturity:** High.
*   **Performance:** Excellent.

## 22. Scheduler
**Selected:** BullMQ Repeatable Jobs / node-cron
*   **Why selected:** Native integration with our worker queue for distributed, persistent cron jobs.
*   **Alternatives considered:** OS-level CRON.
*   **Why rejected:** Does not scale horizontally across multiple containerized nodes.
*   **Long-term maintenance:** High.
*   **Enterprise suitability:** High.

## 23. Event Bus
**Selected:** RabbitMQ
*   **Why selected:** Same infrastructure as the Queue, utilizing Topic/Fanout exchanges for internal domain events.
*   **Alternatives considered:** Kafka.
*   **Why rejected:** Minimizes infrastructure footprint.

## 24. Object Storage
**Selected:** MinIO (S3 Compatible API)
*   **Why selected:** Allows self-hosting on-premise while maintaining perfect compatibility with AWS S3 if deployed to the cloud.
*   **Alternatives considered:** Direct file system, GridFS.
*   **Why rejected:** File system breaks horizontal scalability.
*   **Long-term maintenance:** High.
*   **Enterprise suitability:** Maximum.

## 25. Search Engine
**Selected:** Elasticsearch / OpenSearch
*   **Why selected:** The industry standard for full-text search, essential for the Audit Ledger and exact keyword searches.
*   **Alternatives considered:** Meilisearch, Algolia.
*   **Why rejected:** Algolia is SaaS only (violates self-hosting). Meilisearch lacks deep enterprise features compared to ES.
*   **Long-term maintenance:** High.
*   **Enterprise suitability:** Maximum.

## 26. AI SDK
**Selected:** Vercel AI SDK
*   **Why selected:** Unifies streaming APIs across multiple providers (OpenAI, Anthropic) into a single standard interface for Node/React.
*   **Alternatives considered:** LangChain JS, LlamaIndex JS.
*   **Why rejected:** LangChain is notoriously bloated and overly abstracted, making debugging impossible. Vercel SDK is thin and transparent.
*   **Long-term maintenance:** Heavily backed.
*   **Enterprise suitability:** High.

## 27. Multi Provider AI Support
**Selected:** LiteLLM (Proxy) or native SDK abstractions
*   **Why selected:** Standardizes all API calls to the OpenAI schema format, allowing drop-in replacement of any model.
*   **Alternatives considered:** Hardcoding APIs.
*   **Why rejected:** Vendor lock-in.

## 28. Embedding Provider Strategy
**Selected:** Local (e.g., HuggingFace via Transformers.js or local Python microservice) + API Fallback (OpenAI `text-embedding-3`)
*   **Why selected:** Generating embeddings locally prevents sending massive document chunks to external APIs, saving massive costs and ensuring privacy.

## 29. Vector Database Strategy
**Selected:** pgvector (PostgreSQL extension)
*   **Why selected:** Keeps embeddings in the same database as transactional metadata, massively simplifying architecture and ensuring RBAC joins are atomic.
*   **Alternatives considered:** Pinecone, Milvus, Qdrant.
*   **Why rejected:** Pinecone is SaaS only. Milvus/Qdrant require managing another complex infrastructure piece; `pgvector` scales sufficiently for most enterprise use cases.
*   **Long-term maintenance:** Native to Postgres.
*   **Enterprise suitability:** Maximum.

## 30. File Processing
**Selected:** Multer (Node.js) -> stream to Object Storage
*   **Why selected:** Standard, memory-efficient way to handle multipart/form-data uploads.

## 31. PDF Processing
**Selected:** pdf2json / pdf.js (for extraction)
*   **Why selected:** Open source, robust text extraction for chunking and embedding.
*   **Alternatives considered:** Unstructured.io (heavy Python dependency).

## 32. Excel Processing
**Selected:** SheetJS
*   **Why selected:** De facto standard for parsing spreadsheets in JS.

## 33. Image Processing
**Selected:** Sharp
*   **Why selected:** High-performance Node.js image processing (resizing avatars, compressing).
*   **Alternatives considered:** ImageMagick (OS dependency).

## 34. Email Service
**Selected:** Nodemailer (via SMTP)
*   **Why selected:** Provider agnostic. Connects to enterprise Exchange servers or SendGrid.

## 35. Notification Service
**Selected:** Novu (Open-source notification infrastructure)
*   **Why selected:** Unifies email, in-app, SMS, and Slack notifications under one API. Supports self-hosting.

## 36. WebSocket Strategy
**Selected:** Socket.io
*   **Why selected:** Handles fallbacks to long-polling automatically. Essential for real-time Agent typing indicators.
*   **Alternatives considered:** Native WebSockets, Pusher (SaaS).

## 37. Logging
**Selected:** Winston / Pino
*   **Why selected:** High-performance structured JSON logging. Essential for scraping by Logstash/FluentD.

## 38. Monitoring
**Selected:** Prometheus (Metrics) + Grafana (Dashboards)
*   **Why selected:** The absolute standard for open-source, self-hosted infrastructure monitoring.

## 39. Metrics
**Selected:** Prom-client (Node.js)
*   **Why selected:** Exposes the `/metrics` endpoint for Prometheus to scrape.

## 40. Distributed Tracing
**Selected:** OpenTelemetry (OTel) + Jaeger
*   **Why selected:** Vendor-neutral standard. Traces requests from the React frontend, through the NestJS API, down to the PostgreSQL query.

## 41. Error Tracking
**Selected:** Sentry (Self-hosted or SaaS)
*   **Why selected:** Captures unhandled exceptions and stack traces with full source map support.

## 42. Secret Management
**Selected:** HashiCorp Vault / Doppler
*   **Why selected:** Prevents API keys from living in plaintext `.env` files. Injects secrets directly into containers at runtime.

## 43. Configuration Management
**Selected:** Dotenv + NestJS ConfigModule
*   **Why selected:** Standard 12-factor app compliance.

## 44. Docker Strategy
**Selected:** Multi-stage Dockerfiles + Alpine Node base images
*   **Why selected:** Results in tiny, secure container footprints (<100MB) preventing CVEs in unneeded OS packages.

## 45. Reverse Proxy
**Selected:** NGINX / Traefik
*   **Why selected:** Traefik integrates natively with Docker/Kubernetes for dynamic routing. NGINX is rock solid for static setups.

## 46. SSL Strategy
**Selected:** Let's Encrypt / Certbot (or Enterprise TLS termination at the Load Balancer)

## 47. CI/CD
**Selected:** GitHub Actions / GitLab CI
*   **Why selected:** Native to code hosting. Pipeline as code.

## 48. Unit Testing
**Selected:** Jest
*   **Why selected:** Fast, standard testing framework for Node/React.

## 49. Integration Testing
**Selected:** Supertest (Node) + Testcontainers
*   **Why selected:** Testcontainers spins up real ephemeral Docker databases for true integration testing.

## 50. E2E Testing
**Selected:** Playwright
*   **Why selected:** Faster and more reliable than Cypress. Excellent cross-browser support.

## 51. Code Formatter
**Selected:** Prettier
*   **Why selected:** Ends all debates on code style.

## 52. Linter
**Selected:** ESLint (with typescript-eslint)
*   **Why selected:** Standard static analysis.

## 53. Monorepo Tool
**Selected:** Turborepo
*   **Why selected:** Ultra-fast build system for JS/TS monorepos. Caches builds locally and remotely.
*   **Alternatives considered:** Nx, Lerna (deprecated).

## 54. Package Manager
**Selected:** pnpm
*   **Why selected:** Fastest JS package manager, strict workspace linking, massive disk space savings via hard links.
*   **Alternatives considered:** npm, yarn.

## 55. Git Branch Strategy
**Selected:** Trunk-Based Development
*   **Why selected:** Short-lived feature branches merged into `main`. Requires heavy automated testing. Prevents merge hell.

## 56. Release Strategy
**Selected:** Semantic Versioning (SemVer) + GitHub Releases

## 57. Versioning Strategy
**Selected:** API Versioning via URI (e.g., `/api/v1/`)

## 58. Backup Strategy
**Selected:** pg_dump (cron) + WAL archiving (Barman/pgBackRest) to S3

## 59. Deployment Strategy
**Selected:** Kubernetes (Helm Charts) / Docker Swarm
*   **Why selected:** Kubernetes is required for true horizontal scaling and self-healing. Docker Compose/Swarm supported for smaller single-node deployments.

## 60. Local Development Strategy
**Selected:** Docker Compose
*   **Why selected:** `docker-compose up` spins up Postgres, Redis, RabbitMQ, and MinIO instantly. Developer experience is paramount.

---

## Compatibility Matrix
All selected tools must support Linux/Docker execution, Node 20+, and PostgreSQL 16+. Architecture must remain agnostic to underlying Cloud Providers (AWS/GCP/Azure) to maintain the self-hosting promise.

## Upgrade Strategy
*   Minor/Patch versions: Auto-updated via Dependabot/Renovate, merged if CI passes.
*   Major versions: Reviewed quarterly. Upgraded manually in a dedicated release sprint.

## Dependency Policy
*   No new production dependencies may be added without Architect approval.
*   Dependencies must have >1k GitHub stars, recent commits within 3 months, and an active maintainer team.

## Technology Lifecycle Policy
*   Technologies are evaluated annually. If a technology is officially deprecated by its maintainers, a 6-month migration window is opened to adopt the recommended replacement.

## Replacement Policy
Because the architecture is heavily decoupled via interfaces and NestJS Dependency Injection, swapping a tool (e.g., swapping RabbitMQ for Kafka) requires changing only the specific Adapter module, leaving the core application logic untouched.

---

## Technology Stack Constitution
The permanent Technology principles of AegisAI:
1. **The Principle of Boring Technology**: We do not adopt tools because they are trending; we adopt tools because they have survived the crucible of enterprise production. Boring is stable. Stable is secure.
2. **The Principle of Independence**: The stack must never be locked to a specific cloud provider's proprietary PaaS. The platform must be capable of running in an air-gapped basement data center just as easily as AWS.
3. **The Principle of the Monolingual Monorepo**: By standardizing on TypeScript across the entire stack, a frontend engineer can read the backend, a backend engineer can fix the frontend, and types can be shared flawlessly, destroying silos and maximizing velocity.
