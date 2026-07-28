# @aegis/shared Architecture

## Package Responsibility

The absolute lowest-level foundation of the aegisOS platform. Provides pure, deterministic, framework-independent, and reusable infrastructure utilities for every other package in the monorepo.

## Dependency Rules

- **No internal imports**: Never imports from other packages within the monorepo.
- **No external imports**: Third-party dependencies are strictly forbidden.
- **Node built-ins**: Allowed only when absolutely necessary (e.g. native crypto for UUID).

## API Stability

- **Stable API**: Everything exposed in `src/index.ts` is stable.
- **Forbidden Patterns**: Business logic, runtime coupling, configuration logic, and side effects are physically prevented from existing in this package.
