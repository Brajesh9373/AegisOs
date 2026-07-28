# @aegis/config

The canonical source of truth for all structural data shapes defining configuration across the aegisOS platform.

## Principles

- **Structure Only**: This package defines interfaces and types for configuration payload formats. It contains zero bytes of executing behavior.
- **No Validation**: Zod, Joi, or class-validator rules are forbidden here.
- **Runtime Resolution**: It does not read `process.env`. Environment mapping is strictly handled by the runtime layer.
