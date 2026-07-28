# @aegis/config Architecture

## Package Responsibility

The `@aegis/config` package serves as the canonical source of truth for the structural definitions of all configuration payloads across the aegisOS platform. It is strictly limited to defining the shape and contracts of configurations, feature flags, and provider options.

## Configuration Lifecycle

1. **Definition**: The configuration structure is defined here in `@aegis/config`.
2. **Values**: The actual deployment/environment values are owned by the deployment configuration (e.g. Terraform, Kubernetes, or .env in development).
3. **Loading & Mapping**: The runtime layer is entirely responsible for loading environment variables and mapping them into the strict structural forms defined here.
4. **Validation**: The runtime or bootstrap layer validates the loaded variables against schemas matching these structures.
5. **Persistence**: Never handled here.

## Provider Rules

- Provider configurations define structural capability contracts and option structures.
- They **must never** contain SDK initialization logic, hardcoded endpoints, or runtime client abstractions.
- AI, Identity, Notification, and Storage providers all follow these restrictions strictly.
