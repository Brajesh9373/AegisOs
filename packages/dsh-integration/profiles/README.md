# AegisOS DSH Profiles

The `business-analyst` directory is a real package profile for the pinned DeepSeek Harness (DSH) CLI. It is not a loose configuration template: DSH loads its bundle manifest from `package.json`, then composes the top-level patch list in `cordis.patch.yml`.

## Supported profile

`business-analyst` is the only profile in this directory currently prepared for the pinned DSH runtime. It uses `@deepseek-ai/dsh-base` and `@deepseek-ai/dsh-headless`, and defines the `glm-gateway` provider route through DSH's `@deepseek-ai/dsh-llm-pi-ai` integration.

The other directories are legacy templates. Do not treat them as runnable DSH package profiles until they are converted to the same manifest-and-patch format.

## Run through AegisOS

Use the backend wrapper. It synchronizes only the authored package assets into the selected DSH home, invokes the repository-pinned CLI directly, and leaves generated `cordis.yml` plus profile dependency links under DSH control.

```bash
export ANTHROPIC_BASE_URL="https://your-anthropic-compatible-gateway"
export ANTHROPIC_AUTH_TOKEN="<gateway-bearer-token>"
export CLAUDE_CODE_SESSION_ID="<non-empty-session-id>"

cd backend
PYTHONPATH=. ../backend/venv/bin/python -c '
import asyncio
from ecms.agent.dsh_runtime import ba_understand
print(asyncio.run(ba_understand("Describe the project brief here.")))
'
```

`DSHRuntime` uses `packages/dsh-integration/node_modules/.bin/dsh`, pinned by `packages/dsh-integration/package.json`. Install or refresh it from that directory with `pnpm install --frozen-lockfile`; do not use `npx` or a global DSH install for the AegisOS runtime path.

## Profile assets

- `package.json`: declares the ordered DSH bundle chain.
- `pnpm-workspace.yaml`: tells DSH how the package profile is laid out.
- `cordis.patch.yml`: DSH patch array for the GLM-5 Anthropic Messages route, default model, and BA prompt.
- `cordis.yml`: generated and maintained by DSH; do not author or commit it.

Credentials are always resolved at runtime from environment variables. Do not put a gateway token in profile assets, documentation, benchmark reports, or source control.
