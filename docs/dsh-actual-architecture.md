# DeepSeek Harness - Actual Architecture Analysis

**Date:** 2026-09-02
**Source:** Direct inspection of https://github.com/deepseek-ai/deepseek-harness

## Executive Summary

DeepSeek Harness (DSH) is built on **Cordis**, a plugin framework with a fundamentally different architecture than our initial assumptions. This document corrects our understanding and outlines the proper integration approach.

## Key Findings

### 1. Package Version

- **Actual version:** `0.1.2-alpha.5` (NOT `1.0.0`)
- **Package name:** `@deepseek-ai/dsh-root`
- **Node requirement:** `^22.19.0 || >=24.0.0`
- **Package manager:** `pnpm@11.7.0`

### 2. Architecture Foundation: Cordis

DSH is built on **Cordis** (similar to Koishi), which uses:

- **Context injection** pattern (not plugin classes)
- **Service registration** via `Context` augmentation
- **Scope-based lifecycle** management
- **Event-driven communication**

**There is NO `Plugin`, `PluginContext`, or `ToolContext` interface as we assumed.**

### 3. Actual Tool Registration Pattern

Tools are registered through **Cordis context**, not a plugin class:

```typescript
import { defineTool } from '@deepseek-ai/dsh-tools'

const myTool = defineTool({
  name: 'my_tool',
  description: 'Tool description',
  parameters: {
    param1: { type: 'string', description: 'Parameter 1' }
  },
  output: {
    schema: { type: 'object', properties: { result: { type: 'string' } } },
    render(args, value) {
      return [{ type: 'text', text: value.result }]
    }
  },
  async execute(args, exec) {
    // Tool implementation
    return { result: 'output' }
  }
})

// Registration happens via context
ctx.tools.register(myTool)
```

### 4. Agent Creation Pattern

Agents are created through `AgentRegistry.create()`:

```typescript
interface CreateAgentOptions {
  sessionId: SessionId
  meta?: {
    cwd?: string
    parentSession?: SessionId
    isSeeded?: boolean
    origin?: 'subagent'
    delegationDepth?: number
    agentPreset?: string
  }
  agentOptions?: AgentOptions
  setup?: AgentSetup  // Composition callback
}

interface AgentOptions {
  provider?: string
  model?: string
  reasoningEffort?: ReasoningEffortId
  maxTokens?: number
}
```

### 5. Session Management

DSH uses **event-sourced session logs**:

- Append-only session log
- Session events: `session/created`, `session/disposed`, `session/event`, `session/flush`
- Persistence is a plugin concern
- Session IDs are durable identities

### 6. Scope System

DSH has a sophisticated **scope system** for agent isolation:

- `scopeOf()` for layer selection
- Scope-filtered dispatch
- Agent-scoped listeners
- Scoped tool registration

### 7. SDK Architecture

DSH provides a **JSON-RPC SDK** for external integration:

```
@deepseek-ai/dsh-sdk-protocol  - Wire protocol
@deepseek-ai/dsh-sdk-client    - TypeScript client
@deepseek-ai/dsh-sdk-server    - Runtime server
```

The SDK spawns DSH as a subprocess and communicates over stdio JSON-RPC.

## Corrected Integration Approach

### What We Got Wrong

1. **Plugin Architecture**: We assumed a class-based plugin system with `Plugin`, `PluginContext`, `ToolContext`. DSH uses Cordis context injection.

2. **Tool Registration**: We assumed `this.context.registerTool()`. DSH uses `ctx.tools.register()` with `defineTool()`.

3. **Agent Templates**: We assumed YAML-based template instantiation. DSH uses `AgentRegistry.create()` with programmatic setup callbacks.

4. **Package Versions**: We assumed `@deepseek-ai/dsh@1.0.0`. Actual is `@deepseek-ai/dsh-root@0.1.2-alpha.5`.

### Correct Integration Strategy

#### Option A: Cordis Service Integration (Recommended for deep integration)

1. Create a **Cordis service** that provides AegisOS capabilities
2. Register it on the DSH context
3. Tools and agents access it via dependency injection

```typescript
// aegisos-service.ts
import { Service } from '@deepseek-ai/cordis'

class AegisOSService extends Service {
  constructor(ctx: Context) {
    super(ctx, 'aegisos', true)
  }

  async getKnowledge(query: string, scope: KnowledgeScope) {
    // Call AegisOS backend
  }

  async checkAuthorization(agent: Agent, resource: string, action: string) {
    // Call AegisOS authorization service
  }
}

// Register in DSH context
ctx.plugin(AegisOSService)
```

#### Option B: SDK Client Integration (Recommended for isolation)

1. Run DSH as a subprocess via `DeepSeekHarness`
2. Communicate over JSON-RPC
3. AegisOS backend acts as an orchestrator

```typescript
import { DeepSeekHarness } from '@deepseek-ai/dsh-sdk-client'

const harness = new DeepSeekHarness({
  profile: 'aegisos',
  patches: ['./aegisos-runtime.patch.yml']
})

const session = await harness.run({
  messages: [{ role: 'user', content: '...' }],
  // AegisOS provides tool implementations
})
```

#### Option C: Tool-Level Integration (Minimal integration)

1. Define AegisOS tools using `defineTool()`
2. Tools call AegisOS backend APIs
3. Register tools in agent setup callback

```typescript
const knowledgeTool = defineTool({
  name: 'search_knowledge',
  description: 'Search AegisOS knowledge base',
  parameters: {
    query: { type: 'string', required: true },
    domain: { type: 'string' }
  },
  output: {
    schema: knowledgeSearchResultSchema,
    render: renderKnowledgeResults
  },
  async execute(args, exec) {
    // Call AegisOS backend API
    const response = await fetch('http://aegisos-backend/api/knowledge/search', {
      method: 'POST',
      body: JSON.stringify(args)
    })
    return response.json()
  }
})
```

## Recommended Approach for AegisOS

Given AegisOS's architecture (Python/FastAPI backend, existing authorization, governance, knowledge systems), **Option C (Tool-Level Integration)** is most appropriate:

### Phase 1: Core Tools (2-3 weeks)

1. **Knowledge Tool** - Connects to AegisOS knowledge API
2. **Authorization Tool** - Checks permissions via PolicyAuthorizationService
3. **Governance Tool** - Integrates with approval workflows
4. **Workspace Tool** - Enforces project/workspace boundaries

### Phase 2: Agent Creation Adapter (1-2 weeks)

1. Create a TypeScript adapter that:
   - Reads AegisOS agent templates
   - Generates DSH `CreateAgentOptions` with setup callbacks
   - Registers appropriate tools based on agent configuration
   - Calls AegisOS backend for persistence

### Phase 3: Runtime Integration (2-3 weeks)

1. Deploy DSH as a service alongside AegisOS backend
2. Create a bridge service that:
   - Routes tool calls to AegisOS APIs
   - Enforces authorization at the tool boundary
   - Logs events to AegisOS persistence
   - Syncs agent state with AegisOS database

## Package Structure (Corrected)

```
packages/dsh-integration/
├── tools/
│   ├── knowledge.ts        # Knowledge tool
│   ├── authorization.ts    # Authorization tool
│   ├── governance.ts       # Governance tool
│   └── workspace.ts        # Workspace tool
├── adapters/
│   ├── agent-factory.ts    # Agent creation adapter
│   ├── template-loader.ts  # Load AegisOS templates
│   └── backend-client.ts   # AegisOS API client
├── runtime/
│   ├── dsh.config.ts       # DSH configuration
│   └── preset.ts           # AegisOS preset
└── package.json
```

## Dependencies (Corrected)

```json
{
  "dependencies": {
    "@deepseek-ai/cordis": "0.1.2-alpha.5",
    "@deepseek-ai/dsh-tools": "0.1.2-alpha.5",
    "@deepseek-ai/dsh-agent": "0.1.2-alpha.5",
    "@deepseek-ai/dsh-session": "0.1.2-alpha.5"
  },
  "devDependencies": {
    "typescript": "^6.0.3",
    "@types/node": "^22.20.0"
  }
}
```

## Next Steps

1. **Delete** the incorrectly implemented `packages/dsh-plugins/` code
2. **Create** new `packages/dsh-integration/` with correct structure
3. **Implement** minimal proof of concept with one tool
4. **Validate** against actual DSH runtime
5. **Integrate** with AegisOS backend

## References

- DSH Repository: https://github.com/deepseek-ai/deepseek-harness
- Cordis Framework: https://github.com/koishijs/cordis
- DSH Packages: `packages/core/`, `packages/sdk/`
