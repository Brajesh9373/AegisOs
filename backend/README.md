# ECMS Backend

The Python platform for the Enterprise Cognitive Memory System. Distribution package:
`ecms` (import root under `backend/ecms`).

## Quickstart

```bash
uv venv --python 3.12
uv sync
uv run ruff check .
uv run ruff format --check
uv run mypy ecms
uv run pytest
```

## Layout

See [`../docs/ARCHITECTURE.md`](../docs/ARCHITECTURE.md). DDD service modules use the
hexagonal layout (`domain/application/infrastructure/interfaces/events/schemas/services/
repositories/tests`); cross-cutting packages (`api`, `shared`, `infrastructure`,
`persistence`, `sdk`, `cli`) use fit-for-purpose structures.

## Tooling

- **ruff** — linting + formatting (config in `pyproject.toml`).
- **mypy** — strict static typing.
- **pytest** + **pytest-cov** — tests and coverage.
- Dependencies are declared in `pyproject.toml` and grow per implementation stage.
