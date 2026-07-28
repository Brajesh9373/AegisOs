# Testing Guide

A practical guide to the AegisOS test infrastructure -- how tests are organized,
how to run them, and how to write new ones.

---

## Philosophy

The test suite follows a few core principles:

1. **Fast feedback.** Unit tests must run in under a second. Integration tests
   use in-memory or lightweight substitutes (SQLite, fakeredis, InMemoryObjectStore)
   so they stay fast without external services.
2. **Contract-driven.** Every port (interface) has a contract test that proves
   each concrete adapter satisfies it. If you add a new adapter, add a contract
   assertion.
3. **Security by default.** Security controls are tested explicitly -- token
   tampering, revocation, default-deny authorization, and sensitive-value
   redaction.
4. **Migration safety.** Every Alembic migration is a real numbered file with
   upgrade and downgrade paths. The CI pipeline validates the full migration
   chain against a disposable SQLite database.

---

## Backend Testing

### Tooling

| Tool              | Purpose                          |
|-------------------|----------------------------------|
| pytest            | Test runner                      |
| pytest-asyncio    | Async test support (`asyncio_mode = "auto"`) |
| pytest-cov        | Coverage reporting               |
| pytest-benchmark  | Performance regression detection |
| aiosqlite         | In-memory SQLite for integration tests |
| fakeredis         | Fake Redis client for cache tests |

All dependencies live in the `[dependency-groups] dev` section of
`backend/pyproject.toml`.

### Configuration

Pytest configuration is in `backend/pyproject.toml` under `[tool.pytest.ini_options]`:

```toml
asyncio_mode = "auto"
addopts = "-q --cov=ecms --cov-report=term-missing --benchmark-disable"
pythonpath = ["."]
testpaths = ["tests", "ecms"]
```

Key points:
- `asyncio_mode = "auto"` means every `async def test_*` function is
  automatically treated as an async test -- no `@pytest.mark.asyncio` decorator
  needed (though some tests still use it explicitly for clarity).
- Benchmarks are disabled by default (`--benchmark-disable`). Pass
  `--benchmark-enable` explicitly to run them.
- Coverage is collected automatically on every test run.

### Directory Structure

```
backend/tests/
  unit/                    # Pure logic, no I/O
    shared/                # Shared kernel: enums, models, validation, etc.
    test_benchmarks.py     # Performance benchmarks
    test_cli.py            # CLI commands
    test_di.py             # Dependency injection container
    test_domain_models.py  # Domain model defaults and constructors
    test_metrics.py        # Prometheus metrics
    test_sdk.py            # Enterprise SDK facade
    ...
  integration/             # Tests that touch persistence, cache, storage, API
    test_api.py            # REST endpoints (FastAPI TestClient)
    test_cache.py          # InMemory + fakeredis cache adapters
    test_cognition_api.py  # Cognition REST routes
    test_cors.py           # CORS middleware
    test_graphql.py        # GraphQL gateway
    test_persistence.py    # SQLAlchemy UnitOfWork, Saga, AuditRepository
    test_storage.py        # InMemoryObjectStore
    test_websocket.py      # WebSocket connections
    ...
  contract/                # Port/adapter conformance
    test_port_contracts.py # isinstance checks for every port
  security/                # Auth, authz, redaction
    test_security_controls.py
  smoke/                   # Package sanity checks
    test_smoke.py
  load/                    # Stress tests
    test_load.py
  api/                     # (reserved for API-specific test helpers)
  infrastructure/          # (reserved for infrastructure tests)
```

### Async Test Patterns

Because `asyncio_mode = "auto"`, writing an async test is as simple as:

```python
async def test_in_memory_cache() -> None:
    cache = InMemoryCache()
    await cache.set("k", "v")
    assert await cache.get("k") == "v"
```

For async fixtures, use `pytest_asyncio.fixture`:

```python
@pytest_asyncio.fixture
async def database(tmp_path: Path) -> AsyncIterator[Database]:
    db = Database(f"sqlite+aiosqlite:///{tmp_path.as_posix()}/test.db")
    await db.create_all()
    yield db
    await db.dispose()
```

### Common Fixtures

The suite relies on a small set of reusable fixtures and helpers:

- **`database(tmp_path)`** -- creates a temporary SQLite database with all
  tables, yields it, and disposes on teardown.
- **`client()`** -- returns a `TestClient(create_app())` for REST and GraphQL
  tests.
- **`tmp_path`** -- pytest built-in; a unique temporary directory per test.

Most tests construct their own fixtures inline to keep dependencies minimal.

---

## Backend Test Types

### Unit Tests (`tests/unit/`)

Fast, isolated tests that exercise pure logic. No network, no database, no
external services. Examples:

- Domain model constructors and default values (`test_domain_models.py`)
- Enum value stability (`shared/test_enums.py`)
- Validation helpers (`shared/test_validation.py`)
- Dependency injection container (`test_di.py`)
- CLI output (`test_cli.py`)
- Prometheus metric rendering (`test_metrics.py`)

### Integration Tests (`tests/integration/`)

Tests that touch real subsystems through lightweight substitutes:

- **Persistence** -- SQLAlchemy with aiosqlite. Tests cover CRUD, tenant
  scoping, soft delete, governed purge, conflict detection, UnitOfWork rollback,
  and Saga compensation.
- **Cache** -- InMemoryCache and RedisCache backed by fakeredis.
- **Object Storage** -- InMemoryObjectStore.
- **REST API** -- FastAPI TestClient. Tests cover health, readiness, versioning,
  CORS headers, correlation IDs, OpenAPI generation, auth enforcement, rate
  limiting, and pagination.
- **GraphQL** -- TestClient posting to `/graphql`. Tests cover version queries,
  system info, and the playground endpoint.

### Contract Tests (`tests/contract/`)

Verify that every concrete adapter implements its port:

```python
def test_cache_contract() -> None:
    assert isinstance(InMemoryCache(), Cache)

def test_token_codec_contract() -> None:
    assert isinstance(JwtTokenCodec(secret=_TEST_SECRET), TokenCodec)
```

If you add a new adapter, add a one-line `isinstance` check here.

### Security Tests (`tests/security/`)

Explicit verification of security controls:

- Tampered JWT tokens are rejected.
- Revoked tokens are rejected.
- Authorization defaults to deny.
- Sensitive values (passwords, tokens) are redacted in mappings.

### Smoke Tests (`tests/smoke/`)

Quick sanity checks that the package is importable and well-formed:

```python
def test_version_is_defined() -> None:
    assert isinstance(ecms.__version__, str)
    assert ecms.__version__
```

### Load Tests (`tests/load/`)

Stress tests for internal subsystems. Example: publishing 1000 events through
the InMemoryEventBus and verifying all are delivered, including under concurrent
publish.

### Benchmark Tests (`tests/unit/test_benchmarks.py`)

Performance regression detection using pytest-benchmark. Benchmarks are disabled
by default and must be opted in:

```bash
uv run pytest tests/unit/test_benchmarks.py --benchmark-enable
```

Each benchmark wraps a hot-path function (e.g., `to_json`) and tracks its
execution time across runs. The CI pipeline runs benchmarks as a separate step.

---

## Migration Qualification

Alembic migrations live in `backend/ecms/persistence/migrations/versions/`.
Each file follows the naming convention `NNNN_description.py` (e.g.,
`0001_initial.py`, `0042_connector_ingestion_integrity.py`).

### Structure

Every migration defines:

```python
revision: str = "0001"
down_revision: str | None = None

def upgrade() -> None:
    """Apply the migration."""
    ...

def downgrade() -> None:
    """Reverse the migration."""
    ...
```

The `env.py` file configures Alembic for async operation using
`create_async_engine` and registers all model modules so metadata is complete.

### Running Migrations Locally

```bash
cd backend

# Apply all migrations
uv run alembic upgrade head

# Revert the last migration
uv run alembic downgrade -1

# Generate SQL without executing (offline mode)
uv run alembic upgrade head --sql

# Check current revision
uv run alembic current
```

The database URL defaults to `sqlite+aiosqlite:///./ecms.db` (from
`alembic.ini`) but can be overridden with the `ECMS_DATABASE_URL` environment
variable.

### Writing a New Migration

1. Create a new file: `backend/ecms/persistence/migrations/versions/0043_your_change.py`
2. Set `revision = "0043"` and `down_revision = "0042"`.
3. Implement `upgrade()` and `downgrade()`.
4. Test locally: `uv run alembic upgrade head` then `uv run alembic downgrade -1`.
5. The CI pipeline validates the full chain automatically.

---

## Frontend Testing

### Tooling

| Tool       | Purpose                  |
|------------|--------------------------|
| Vitest     | Unit and component tests |
| Playwright | End-to-end tests         |
| ESLint     | Linting                  |
| Prettier   | Formatting               |
| TypeScript | Type checking            |
| Turbo      | Monorepo task orchestration |

### Vitest Configuration

The root `frontend/vitest.config.ts`:

```ts
export default defineConfig({
  test: {
    globals: true,
    environment: 'node',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
    },
    passWithNoTests: true,
  },
});
```

The workspace file (`vitest.workspace.ts`) includes all packages and apps:

```ts
export default defineWorkspace(['packages/*', 'apps/*']);
```

### Running Frontend Tests

```bash
cd frontend

# Run all unit tests once
pnpm test

# Run tests in watch mode
pnpm test:watch

# Run tests with coverage
pnpm test:coverage

# Run e2e tests (delegates to Turbo)
pnpm test:e2e

# Type check all packages
pnpm typecheck

# Full verification (format + lint + typecheck + test + build + circular check + exports check)
pnpm verify
```

### Writing Frontend Tests

Frontend tests use Vitest with `describe`/`it`/`expect` and run in a Node
environment by default. Example from `snapshotClient.test.ts`:

```ts
import { describe, expect, it } from 'vitest';

describe('knowledge graph snapshot integrity', () => {
  it('computes the standard SHA-256 digest', async () => {
    const buffer = new TextEncoder().encode('abc').buffer;
    await expect(sha256Hex(buffer)).resolves.toBe(
      'ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad',
    );
  });
});
```

Test files follow the pattern `*.test.ts` or `*.spec.ts` and live alongside the
code they test.

---

## Linting and Formatting

### Backend (Ruff + mypy)

Ruff handles both linting and formatting. Configuration is in
`backend/pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py312"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM", "C4", "PTH", "RUF", "ASYNC", "S", "N", "D"]
```

The selected rule groups cover:
- **E/F** -- pycodestyle errors and pyflakes
- **I** -- isort (import sorting)
- **UP** -- pyupgrade (modern Python idioms)
- **B** -- flake8-bugbear (common bugs)
- **SIM** -- simplification
- **C4** -- comprehensions
- **PTH** -- pathlib usage
- **RUF** -- Ruff-specific rules
- **ASYNC** -- async pitfalls
- **S** -- security (Bandit rules)
- **N** -- naming conventions
- **D** -- docstrings (Google convention)

Test files suppress `S101` (assert), `S105` (hardcoded passwords),
`S106` (hardcoded passwords), and `D` (docstrings).

mypy runs in strict mode:

```toml
[tool.mypy]
python_version = "3.12"
strict = true
packages = ["ecms"]
disallow_untyped_defs = true
warn_return_any = true
exclude = ["ecms/persistence/migrations/"]
```

Migrations are excluded from type checking since they are auto-generated
Alembic boilerplate.

#### Running Locally

```bash
cd backend

# Lint
uv run ruff check .

# Auto-fix lint issues
uv run ruff check --fix .

# Format check
uv run ruff format --check .

# Auto-format
uv run ruff format .

# Type check
uv run mypy ecms
```

### Frontend (ESLint + Prettier + TypeScript)

```bash
cd frontend

# Lint all packages
pnpm lint

# Format check
pnpm format:check

# Auto-format
pnpm format

# Type check
pnpm typecheck
```

---

## Security Scanning

### Ruff Security Rules

The `S` rule group in Ruff applies Bandit-style security checks. Run it
isolated:

```bash
cd backend
uv run ruff check --select S .
```

This catches issues like hardcoded passwords, use of `eval`, insecure random
number generation, and similar patterns.

### Dependency Audit

pip-audit checks all installed packages against known vulnerability databases:

```bash
cd backend
uv run --with pip-audit pip-audit
```

In CI, this step uses `continue-on-error: true` so it reports findings without
blocking the pipeline (vulnerability databases may lag behind releases).

---

## Running Tests Locally

### Full Backend Suite

```bash
cd backend
uv sync                          # install all dependencies (including dev)
uv run pytest                    # lint + type check are separate (see below)
```

This runs all tests with coverage. Output includes a term-missing coverage
report.

### Specific Test Categories

```bash
# Unit tests only
uv run pytest tests/unit/

# Integration tests only
uv run pytest tests/integration/

# A single test file
uv run pytest tests/unit/test_di.py

# A single test function
uv run pytest tests/unit/test_di.py::test_transient_returns_new_instances

# Benchmarks (opt-in)
uv run pytest tests/unit/test_benchmarks.py --benchmark-enable
```

### Full Frontend Suite

```bash
cd frontend
pnpm install --frozen-lockfile   # install dependencies
pnpm verify                      # format + lint + typecheck + test + build
```

### Full Stack (Backend + Frontend)

```bash
# From the repo root
cd backend && uv sync && uv run pytest && cd ..
cd frontend && pnpm install --frozen-lockfile && pnpm verify && cd ..
```

---

## CI Pipeline

The CI pipeline runs on every push to `main` and every pull request. It defines
seven parallel jobs:

### 1. Backend Quality and Tests

```
uv sync -> ruff check -> ruff format --check -> mypy -> pytest -> benchmarks
```

Runs the full backend quality gate: lint, format verification, strict type
checking, all tests with coverage, and performance benchmarks.

### 2. Security and Dependency Scan

```
uv sync -> ruff check --select S -> pip-audit
```

Static security analysis via Ruff's Bandit rules, followed by a dependency
vulnerability scan.

### 3. Frontend Build

```
pnpm install -> typecheck -> build
```

Installs dependencies, runs TypeScript type checking across all packages, and
builds the full monorepo.

### 4. Docker Build

Builds the backend Docker image (`docker/backend.Dockerfile`) without pushing.
Validates that the container image builds successfully.

### 5. Kubernetes and Helm Validation

```
kubeconform (strict) -> helm lint -> helm template | kubeconform
```

Validates raw Kubernetes manifests against schemas, lints the Helm chart, and
validates rendered Helm output.

### 6. Terraform Validation

```
terraform fmt -check -> terraform init -backend=false -> terraform validate
```

Checks formatting, initializes without a backend, and validates the Terraform
configuration.

### 7. Documentation Build

```
mkdocs build --strict
```

Builds the MkDocs documentation site in strict mode (warnings become errors).

---

## Writing New Tests

### Naming Conventions

- Test files: `test_<module>.py` (backend) or `<module>.test.ts` (frontend).
- Test functions: `test_<behavior>` -- describe what is being verified, not how.
- Group related tests in the same file. Separate by concern (unit vs
  integration).

### Where to Put Your Test

| What you are testing                  | Where it goes                         |
|---------------------------------------|---------------------------------------|
| Pure logic, no I/O                    | `tests/unit/`                         |
| Database, cache, storage, API         | `tests/integration/`                  |
| Port/interface conformance            | `tests/contract/`                     |
| Auth, authz, security controls        | `tests/security/`                     |
| Stress or throughput                  | `tests/load/`                         |
| Package sanity                        | `tests/smoke/`                        |
| Performance regression                | `tests/unit/test_benchmarks.py`       |

### Fixture Patterns

Keep fixtures local to the test file unless three or more files need them.
Prefer `tmp_path` over hardcoded paths. For database tests, create a fresh
SQLite database per test:

```python
@pytest_asyncio.fixture
async def database(tmp_path: Path) -> AsyncIterator[Database]:
    db = Database(f"sqlite+aiosqlite:///{tmp_path.as_posix()}/test.db")
    await db.create_all()
    yield db
    await db.dispose()
```

For API tests, use FastAPI's TestClient:

```python
@pytest.fixture
def client() -> TestClient:
    return TestClient(create_app())
```

### Assertion Style

Use plain `assert` statements. The project does not use `unittest.TestCase`.
For expected exceptions:

```python
with pytest.raises(ConflictError):
    await repo.add(duplicate_task)
```

For async mocks:

```python
from unittest.mock import AsyncMock

redis = AsyncMock()
redis.xpending.return_value = {"pending": 7}
```

### Adding a Benchmark

Wrap a hot-path function in `benchmark()`:

```python
def test_to_json_benchmark(benchmark: Any) -> None:
    payload = {"a": 1, "b": [1, 2, 3], "c": {"nested": True}}
    result = benchmark(to_json, payload)
    assert result
```

Benchmarks are skipped by default. Run them with `--benchmark-enable`.

---

## Test Coverage

Coverage is collected automatically on every `pytest` run via pytest-cov. The
configuration in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["ecms"]
branch = true
omit = [
    "ecms/*/tests/*",
    "ecms/*/interfaces/*",
    "ecms/infrastructure/storage/s3.py",
    "ecms/persistence/migrations/*",
]

[tool.coverage.report]
show_missing = true
skip_covered = false
exclude_lines = ["pragma: no cover", "if TYPE_CHECKING:", "raise NotImplementedError"]
```

What is excluded from coverage:
- Test files themselves
- Interface definitions (abstract base classes)
- S3 storage adapter (requires AWS credentials)
- Alembic migrations (auto-generated boilerplate)
- Lines marked `pragma: no cover`, `if TYPE_CHECKING:`, or
  `raise NotImplementedError`

### Checking Coverage

```bash
cd backend

# Terminal report with missing lines (default)
uv run pytest

# HTML report
uv run pytest --cov-report=html
# Opens in: backend/htmlcov/index.html

# JSON report
uv run pytest --cov-report=json
# Output in: backend/coverage.json
```

Frontend coverage uses V8 coverage via Vitest:

```bash
cd frontend
pnpm test:coverage
```

---

## Quick Reference

| Task                          | Command                                          |
|-------------------------------|--------------------------------------------------|
| Run all backend tests         | `cd backend && uv run pytest`                    |
| Run backend unit tests only   | `cd backend && uv run pytest tests/unit/`        |
| Run a single test file        | `cd backend && uv run pytest tests/unit/test_di.py` |
| Run benchmarks                | `cd backend && uv run pytest tests/unit/test_benchmarks.py --benchmark-enable` |
| Backend lint                  | `cd backend && uv run ruff check .`              |
| Backend format check          | `cd backend && uv run ruff format --check .`     |
| Backend type check            | `cd backend && uv run mypy ecms`                 |
| Security scan                 | `cd backend && uv run ruff check --select S .`   |
| Dependency audit              | `cd backend && uv run --with pip-audit pip-audit` |
| Run migrations                | `cd backend && uv run alembic upgrade head`      |
| Revert last migration         | `cd backend && uv run alembic downgrade -1`      |
| Run frontend tests            | `cd frontend && pnpm test`                       |
| Frontend type check           | `cd frontend && pnpm typecheck`                  |
| Full frontend verification    | `cd frontend && pnpm verify`                     |
