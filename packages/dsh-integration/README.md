# DSH Integration - Final Approach

**Status:** Validated
**Date:** 2026-09-02

## What Actually Works

After extensive testing, here's what works and what doesn't:

### What DOESN'T Work

1. **Direct package imports** - Cannot import `@deepseek-ai/dsh-tools`, `@deepseek-ai/dsh-agent`, etc. because they have unpublished internal dependencies (`@deepseek-ai/dsh-type-meta`)

2. **SDK Client** - `@deepseek-ai/dsh-sdk-client` also has peer dependencies on the same unpublished packages

3. **Cordis integration** - The Cordis context is only available inside DSH runtime, not from external code

### What DOES Work

**DSH as a subprocess via CLI** - The `dsh` command can be invoked as a subprocess:

```bash
# Run a headless session
dsh --profile headless "analyze the requirements"

# Run with custom profile
dsh --profile aegisos "your task here"
```

## Integration Architecture

```
┌─────────────────────────────────────┐
│        AegisOS Backend              │
│        (Python/FastAPI)             │
└────────────┬────────────────────────┘
             │ HTTP REST API
             ▼
┌─────────────────────────────────────┐
│    AegisOS Agent Orchestrator       │
│    (Python or TypeScript)           │
│                                      │
│  1. Receive agent creation request   │
│  2. Generate DSH profile/config      │
│  3. Spawn DSH subprocess             │
│  4. Capture output                   │
│  5. Persist results                  │
└────────────┬────────────────────────┘
             │ subprocess
             ▼
┌─────────────────────────────────────┐
│    DSH CLI (subprocess)             │
│                                      │
│  dsh --profile headless "task"      │
└─────────────────────────────────────┘
```

## Implementation Steps

### 1. Install DSH CLI

```bash
# Global install
pnpm add -g @deepseek-ai/dsh

# Or as a dependency
pnpm add @deepseek-ai/dsh
```

### 2. Create DSH Profile for AegisOS

Create `~/.dsh/profiles/aegisos/`:

```yaml
# dsh.profile
name: aegisos
bundles:
  - @deepseek-ai/dsh-base
  - @deepseek-ai/dsh-headless
```

```yaml
# cordis.patch.yml
# Custom configuration for AegisOS tools
```

### 3. Invoke DSH from Python

```python
import subprocess
import json

def create_agent_and_run(template_id: str, task: str) -> str:
    """Create an agent and run a task using DSH"""

    # Run DSH as subprocess
    result = subprocess.run(
        ["dsh", "--profile", "aegisos", task],
        capture_output=True,
        text=True,
        timeout=300
    )

    return result.stdout
```

### 4. Or Invoke from TypeScript

```typescript
import { spawn } from 'child_process'

async function runAgent(task: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const proc = spawn('dsh', ['--profile', 'headless', task])

    let output = ''
    proc.stdout.on('data', (data) => output += data)
    proc.stderr.on('data', (data) => console.error(data))

    proc.on('close', (code) => {
      if (code === 0) resolve(output)
      else reject(new Error(`DSH exited with code ${code}`))
    })
  })
}
```

## Tool Configuration

Tools are configured via DSH profile patches, not in our code:

```yaml
# cordis.patch.yml
tools:
  knowledge:
    enabled: true
    config:
      backendUrl: "http://localhost:8000/api/knowledge"
  governance:
    enabled: true
    config:
      backendUrl: "http://localhost:8000/api/governance"
```

## What We Lose

1. **Direct tool definitions** - Cannot use `defineTool()` in our code
2. **Cordis context access** - Cannot register services
3. **Type safety** - No TypeScript types for tool execution
4. **Tight integration** - DSH is a black box subprocess

## What We Gain

1. **Simplicity** - Just spawn a process
2. **Stability** - DSH updates don't break our integration
3. **Isolation** - DSH crashes don't affect our backend
4. **Language agnostic** - Can call from Python, TypeScript, anything

## Recommendation

**Keep the current Python backend architecture.** Instead of deep DSH integration:

1. Use DSH as an **optional** agent runtime
2. Configure DSH profiles for different agent types
3. Spawn DSH when an agent needs to run
4. Keep all business logic in Python

This is simpler, more maintainable, and actually works.

## Files to Keep

- `docs/dsh-actual-architecture.md` - Correct architecture analysis
- `docs/dsh-integration-critical-findings.md` - What we learned

## Files to Remove

- `packages/dsh-integration/src/tools/*` - Cordis tools (don't work)
- `packages/dsh-integration/src/adapters/*` - Direct integration (doesn't work)
- `packages/dsh-integration/examples/minimal-poc.ts` - Misleading example

## Conclusion

DSH is not designed to be used as a library. It's a standalone runtime that should be invoked as a subprocess. The integration is simpler than we thought - just call the CLI.
