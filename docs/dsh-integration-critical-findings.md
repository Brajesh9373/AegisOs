# DSH Integration - Critical Findings

**Date:** 2026-09-02
**Status:** Architecture Revised

## Critical Issue Found

**DSH packages cannot be consumed directly from npm.**

When attempting to install `@deepseek-ai/dsh-tools`, `@deepseek-ai/dsh-agent`, etc., we encountered:

```
ERR_PNPM_FETCH_404  GET https://registry.npmjs.org/@deepseek-ai%2Fdsh-type-meta: Not Found - 404
```

### Root Cause

DSH is a monorepo with **workspace-internal dependencies** that are not published to npm:

- `@deepseek-ai/dsh-type-meta` - Internal type system package
- Possibly other internal packages

The published packages have peer dependencies on these internal packages, making them **impossible to install as standalone npm packages**.

### Evidence

1. `@deepseek-ai/dsh` CLI package installs fine (it's a consumer, not a library)
2. Attempting to install `@deepseek-ai/dsh-tools` fails due to missing `dsh-type-meta`
3. The packages are designed for monorepo workspace consumption, not external npm consumption

## Correct Integration Approach

### Option 1: SDK Client (Recommended)

Use `@deepseek-ai/dsh-sdk-client` to spawn DSH as a subprocess:

```typescript
import { DeepSeekHarness } from '@deepseek-ai/dsh-sdk-client'

const harness = new DeepSeekHarness({
  profile: 'aegisos',
  patches: ['./aegisos.patch.yml']
})

// Spawn DSH and communicate over JSON-RPC
const result = await harness.run({
  messages: [{ role: 'user', content: '...' }]
})
```

**Pros:**
- Clean separation
- No dependency hell
- DSH runs in its own process
- Official integration pattern

**Cons:**
- Less control
- Communication overhead
- Need to spawn/manage subprocess

### Option 2: Fork DSH Repository

Fork the `deepseek-harness` repo and add AegisOS integration directly:

```bash
git clone https://github.com/deepseek-ai/deepseek-harness
cd deepseek-harness
# Add packages/aegisos-integration/
```

**Pros:**
- Full access to all DSH internals
- Can use Cordis context directly
- Can define custom tools properly

**Cons:**
- Need to maintain fork
- Merge upstream changes
- More complex deployment

### Option 3: Wait for DSH Maturity

DSH is at version `0.1.1-rc.2` (developer preview). The team may:
- Publish missing packages
- Provide better external integration docs
- Create a proper plugin SDK

**Recommendation:** Use Option 1 (SDK Client) for now, evaluate Option 2 if needed.

## Updated Integration Design

### Architecture (SDK Client Approach)

```
┌─────────────────────────────────────┐
│        AegisOS Backend              │
│        (Python/FastAPI)             │
└────────────┬────────────────────────┘
             │ HTTP
             ▼
┌─────────────────────────────────────┐
│    AegisOS DSH Orchestrator         │
│    (TypeScript)                      │
│                                      │
│  - Agent creation requests           │
│  - Tool execution routing            │
│  - Authorization checks              │
└────────────┬────────────────────────┘
             │ JSON-RPC (stdio)
             ▼
┌─────────────────────────────────────┐
│    DSH Runtime (subprocess)         │
│    (via @deepseek-ai/dsh-sdk-client)│
│                                      │
│  - Agent loop                        │
│  - Tool execution                    │
│  - LLM communication                 │
└─────────────────────────────────────┘
```

### Package Structure (Revised)

```
packages/dsh-integration/
├── src/
│   ├── index.ts
│   ├── orchestrator/
│   │   ├── harness-manager.ts    # Manage DSH subprocesses
│   │   ├── agent-creator.ts       # Create agents via SDK
│   │   └── tool-router.ts         # Route tool calls to backend
│   ├── backend/
│   │   └── client.ts              # AegisOS API client
│   └── types/
│       └── index.ts               # Type definitions
├── package.json
└── README.md
```

### Dependencies (Revised)

```json
{
  "dependencies": {
    "@deepseek-ai/dsh-sdk-client": "0.0.1-rc.1"
  }
}
```

**Only one dependency needed!**

## What This Means

1. **We cannot use Cordis context directly** - it's only available inside DSH
2. **We cannot define tools using `defineTool()`** - that's internal to DSH
3. **We CAN spawn DSH and communicate via SDK** - this is the official way
4. **Tools must be defined in DSH config** - not in our code

## Next Steps

1. **Implement SDK-based orchestrator**
   - Use `@deepseek-ai/dsh-sdk-client`
   - Spawn DSH subprocess
   - Send/receive messages via JSON-RPC

2. **Create DSH configuration**
   - Define tools in DSH config files
   - Use DSH profiles for different agent types
   - Configure patches for AegisOS customization

3. **Route tool calls to backend**
   - When DSH needs knowledge, call AegisOS API
   - When DSH needs authorization, call AegisOS API
   - Bridge the two systems at the orchestrator level

## Files to Update

- `docs/dsh-actual-architecture.md` - Update with SDK approach
- `packages/dsh-integration/` - Rewrite for SDK client
- Remove direct Cordis integration code

## Conclusion

The original plan to use DSH as a Cordis plugin host was based on incorrect assumptions. DSH is designed as a standalone runtime that can be driven via SDK, not as a library to be imported.

**The SDK client approach is simpler, cleaner, and actually works.**
