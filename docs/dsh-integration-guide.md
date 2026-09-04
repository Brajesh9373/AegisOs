# DSH Integration - Final Implementation Guide

**Status:** Validated and Working
**Date:** 2026-09-02

## Executive Summary

After extensive investigation, the **correct integration approach** is:

**Invoke DSH as a subprocess via its CLI.**

```bash
dsh --profile headless "your task here"
```

This works. Everything else (direct package imports, SDK client, Cordis integration) fails due to unpublished internal dependencies.

## What Was Tested

| Approach | Result | Reason |
|----------|--------|--------|
| Direct package imports (`@deepseek-ai/dsh-tools`) | ❌ FAIL | Missing `@deepseek-ai/dsh-type-meta` package |
| SDK Client (`@deepseek-ai/dsh-sdk-client`) | ❌ FAIL | Same missing dependencies |
| CLI subprocess (`dsh --profile headless`) | ✅ WORKS | Self-contained runtime |

## Integration Architecture

```
┌─────────────────────────────────────┐
│        AegisOS Backend              │
│        (Python/FastAPI)             │
│                                     │
│  - Agent templates                  │
│  - Knowledge API                    │
│  - Authorization                    │
│  - Governance                       │
└────────────┬────────────────────────┘
             │
             │ spawn subprocess
             ▼
┌─────────────────────────────────────┐
│    DSH CLI                          │
│    (Node.js process)                │
│                                     │
│  dsh --profile headless "task"      │
└─────────────────────────────────────┘
```

## Implementation Steps

### Step 1: Install DSH

```bash
# As a dependency in your project
pnpm add @deepseek-ai/dsh

# Or globally
pnpm add -g @deepseek-ai/dsh
```

### Step 2: Configure API Keys

```bash
# Set DeepSeek API key
export DEEPSEEK_API_KEY="your-key-here"

# Or via DSH credentials (if using web profile)
# Use the Models page in the DSH web UI
```

### Step 3: Create Agent Profile (Optional)

Create custom profiles for different agent types:

```bash
# Create profile directory
mkdir -p ~/.dsh/profiles/aegisos-compliance
cd ~/.dsh/profiles/aegisos-compliance

# Create profile manifest
cat > dsh.profile <<EOF
name: aegisos-compliance
bundles:
  - @deepseek-ai/dsh-base
  - @deepseek-ai/dsh-headless
EOF

# Create configuration patch
cat > cordis.patch.yml <<EOF
# Custom system prompt for compliance agent
systemPrompt:
  sections:
    agent-purpose:
      priority: 100
      content: |
        You are a compliance officer for AegisOS.
        Your role is to ensure GDPR, HIPAA, and SOC2 compliance.
EOF
```

### Step 4: Integrate with Python Backend

```python
# backend/ecms/agent/dsh_runtime.py

import subprocess
import asyncio
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class DSHRuntime:
    """Manages DSH subprocess execution for AegisOS agents"""

    def __init__(self, profile: str = "headless", timeout: int = 300):
        self.profile = profile
        self.timeout = timeout

    async def run_agent_task(
        self,
        task: str,
        agent_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> str:
        """
        Run a task using DSH and return the result.

        Args:
            task: The task/prompt for the agent
            agent_id: Optional agent identifier for context
            project_id: Optional project identifier for scope

        Returns:
            The agent's response
        """
        try:
            # Run DSH as subprocess
            proc = await asyncio.create_subprocess_exec(
                "npx", "dsh", "--profile", self.profile, task,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )

            # Wait with timeout
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(),
                timeout=self.timeout
            )

            if proc.returncode != 0:
                error_msg = stderr.decode() if stderr else "Unknown error"
                logger.error(f"DSH failed: {error_msg}")
                raise RuntimeError(f"DSH execution failed: {error_msg}")

            return stdout.decode()

        except asyncio.TimeoutError:
            proc.kill()
            raise RuntimeError(f"DSH execution timed out after {self.timeout}s")

# Usage in agent endpoint
async def create_and_run_agent(template_id: str, task: str) -> str:
    runtime = DSHRuntime(profile="aegisos-" + template_id)
    return await runtime.run_agent_task(task)
```

### Step 5: Connect to AegisOS APIs

Create custom DSH plugins that call AegisOS APIs:

```yaml
# ~/.dsh/profiles/aegisos/cordis.patch.yml

# This is conceptual - DSH plugin development is separate
plugins:
  aegisos-knowledge:
    config:
      baseUrl: "http://localhost:8000/api"
      # This would need actual DSH plugin code
```

**Note:** Custom DSH plugins require forking DSH or using their plugin system, which is beyond the scope of this integration.

## What This Means for AegisOS

### Keep the Python Backend

The Python backend remains the core:

- Agent templates stored in database
- Knowledge retrieval via `/api/knowledge/search`
- Authorization via `PolicyAuthorizationService`
- Governance via approval workflows
- Agent execution spawns DSH subprocess

### DSH as Agent Runtime

DSH becomes an optional component:

- Install DSH on servers that run agents
- Configure profiles for different agent types
- Spawn DSH when an agent task needs execution
- Capture and persist results

### No TypeScript Integration Layer

We don't need `packages/dsh-integration/` with Cordis tools. Just:

1. Install `@deepseek-ai/dsh` as a dependency
2. Call it as a subprocess from Python
3. Configure profiles as needed

## Simplified Package Structure

```
packages/dsh-integration/
├── README.md                    # This file
├── package.json                 # Just depends on @deepseek-ai/dsh
└── profiles/                    # DSH profile configurations
    ├── compliance-officer.yml
    ├── business-analyst.yml
    └── developer.yml
```

## Dependencies

```json
{
  "dependencies": {
    "@deepseek-ai/dsh": "0.1.1-rc.2"
  }
}
```

That's it. No other packages needed.

## Conclusion

The integration is **much simpler** than initially planned:

1. Install DSH CLI
2. Configure profiles
3. Spawn as subprocess from Python
4. Capture output

No complex TypeScript integration, no Cordis context manipulation, no unpublished package issues.

**This is the production-ready approach.**
