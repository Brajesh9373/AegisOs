# @aegis/types Architecture

## Package Responsibility

The `@aegis/types` package serves as the absolute foundational typing dictionary for the aegisOS platform. Its sole responsibility is to define pure, shared platform type definitions and generic utility types. It acts as the type-level primitive layer that ensures cross-package compilation consistency and type safety.

## Dependency Rules

- **No internal dependencies**: Zero dependencies on other packages in the aegisOS monorepo.
- **No external dependencies**: Zero third-party packages.
- **Node built-ins**: Strictly forbidden.

## Export Rules

- **Explicit Exports Only**: Only named exports permitted (`export type { X }`).
- **No Wildcards**: No `export *` statements.
- **Unified Barrel**: All public definitions strictly route through `src/index.ts`.

## Type System Rules

- **Interfaces over Types**: Prefer `interface` composition over type intersections.
- **Bounded Recursion**: Recursive types must have strict termination logic.
- **No Global Pollution**: `declare global` and `declare module` are universally banned.
