# CommandCode System Prompt Findings

Source inspected:

`C:\Users\braje\AppData\Roaming\npm\node_modules\command-code\dist\cli.mjs`

Package version observed earlier:

`command-code@0.43.1`

## Main Finding

The main interactive CommandCode agent system prompt is not stored as a complete literal in the installed local CLI bundle.

For normal chat, the CLI builds a request body for `POST /alpha/generate` with:

```js
params: {
  model,
  messages,
  tools,
  system: e.system,
  max_tokens,
  stream: true
}
```

But the normal conversation preparation path does not populate `system`. Instead, it sends these context blocks to the CommandCode backend:

- `config`
- `memory`
- `taste`
- `skills`
- `permissionMode`
- `params.messages`
- `params.tools`

That means the main CommandCode identity/system prompt is assembled or injected by the CommandCode API service, not by the local `dist/cli.mjs` package.

The CLI also reads a response header named:

`x-system-prompt-breakdown`

That header is used for token accounting in the `/context` UI. It exposes prompt token categories, not the full prompt text.

## Local Prompt Literals Found

The local bundle does include auxiliary prompt literals:

1. Built-in `explore` subagent system prompt.
2. Built-in `plan` subagent system prompt.
3. Shell-command description prompt.
4. Conversation compaction / handoff prompt.
5. Session title generation prompt.
6. Goal completion verifier prompt.
7. Taste observer / casual observation prompt.

These are local helper prompts, not the main CommandCode interactive agent prompt.

## Exact Extraction

I added an extractor script:

`extract_commandcode_prompts.mjs`

Run it with:

```powershell
node .\extract_commandcode_prompts.mjs "C:\Users\braje\AppData\Roaming\npm\node_modules\command-code\dist\cli.mjs"
```

It prints every literal `systemPrompt:` and `system:` string found in the installed CommandCode bundle, with source character offsets.

## Migration Implication

For the Python migration, we should not claim to have recovered the main CommandCode system prompt from the local package. The faithful migration point is:

- expose a configurable agent/system prompt layer in Python;
- migrate local tool behavior and tool definitions;
- migrate local subagent/helper prompts only as optional compatibility prompts;
- allow the target agent system to inject its own primary system prompt.
