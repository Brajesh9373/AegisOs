# @aegis/contracts

The canonical source of truth for all structural data shapes exchanged across the aegisOS platform.

## Principles

- **Structure Only**: Contains exactly zero bytes of executing behavior.
- **No Validation**: Zod, Joi, or class-validator rules are forbidden.
- **Portability**: Agnostic of serialization mechanisms.
