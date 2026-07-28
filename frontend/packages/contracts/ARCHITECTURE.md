# @aegis/contracts Architecture

## Package Responsibility

The `@aegis/contracts` package serves as the canonical source of truth for all structural data shapes exchanged across the aegisOS platform.

## Folder Structure

- `commands/`: Action-oriented command payload structures
- `events/`: Asynchronous domain and system event contracts
- `messages/`: Internal message bus and queue contracts
- `metadata/`: Standardized telemetry and metadata contracts
- `queries/`: Read-only query parameter and result structures
- `transport/`: Transport-agnostic request and response payload shapes
- `payload/`: Generic structural payload shapes
- `version/`: Versioning constants and namespaces

## Dependency Rules

- **Allowed**: `@aegis/types`
- **Forbidden**: All other packages. Zero external runtime dependencies.
