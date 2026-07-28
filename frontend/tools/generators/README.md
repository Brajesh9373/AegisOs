
# aegisOS Generation Framework

## Architecture
The generation framework standardizes how new packages and modules are instantiated across the platform.
It relies on a shared set of utilities in `common/` to guarantee compliance with the platform rules:

- **writer.ts**: Safely writes files to disk, strictly enforcing UTF-8 encoding and directory scaffolding.
- **formatter.ts**: Intercepts source code prior to writing, enforcing Prettier AST alignment.
- **validator.ts**: Pre-flight checks on generated source logic (detecting empty interfaces or backslash-n defects).

## Migration Plan
1. Stop using ad-hoc one-off generators located in `scratch/`.
2. As new packages (like `storage` or `memory`) are tackled, their respective generation orchestration logic will be placed in `tools/generators/<package>/`.
3. The package generators will construct raw source code strictly using multiline template literals and route the output through `writeGeneratedFile()` for validation, formatting, and disk I/O.
