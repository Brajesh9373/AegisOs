# LLM Provider Configuration

Graphiti requires an LLM client and an embedding client during episode ingestion.

ECMS supports OpenAI-compatible endpoints through environment variables:

```bash
OPENAI_API_KEY=your-compatible-api-key
OPENAI_BASE_URL=https://api.example.com/provider/v1
LLM_MODEL=provider/model-name
LLM_SMALL_MODEL=provider/model-name
GRAPHITI_LLM_CLIENT=openai_compatible_chat
GRAPHITI_RESPONSE_FORMAT=json_object
EMBEDDING_MODEL=provider-embedding-model
EMBEDDING_BASE_URL=https://api.example.com/provider/v1
EMBEDDING_DIM=1024
GRAPHITI_EMBEDDER=openai
```

If `EMBEDDING_BASE_URL` is omitted, ECMS uses `OPENAI_BASE_URL` for embeddings too.

For providers that implement `/chat/completions` but not `/responses`, set:

```bash
GRAPHITI_LLM_CLIENT=openai_compatible_chat
```

If the provider does not expose an embeddings endpoint, use the local deterministic embedder:

```bash
GRAPHITI_EMBEDDER=hash
EMBEDDING_DIM=1024
```

The hash embedder is suitable for local smoke tests and basic persistence. For production semantic search, configure a real embedding endpoint.

Some OpenAI-compatible providers reject the `response_format` parameter. In that case set:

```bash
GRAPHITI_RESPONSE_FORMAT=none
```

Graphiti still injects the required JSON schema into the prompt; ECMS will parse the JSON object from the model's plain text response.

Example for a chat-completions-compatible provider without embeddings:

```bash
OPENAI_API_KEY=your-compatible-api-key
OPENAI_BASE_URL=https://api.commandcode.ai/provider/v1
LLM_MODEL=deepseek/deepseek-v4-flash
LLM_SMALL_MODEL=deepseek/deepseek-v4-flash
GRAPHITI_LLM_CLIENT=openai_compatible_chat
GRAPHITI_RESPONSE_FORMAT=none
GRAPHITI_EMBEDDER=hash
EMBEDDING_DIM=1024
GRAPHITI_TELEMETRY_ENABLED=false
```

## Important

The compatible endpoint must support the OpenAI APIs used by Graphiti:

- structured chat/response generation for entity and edge extraction
- embeddings for semantic search

If the endpoint only supports chat completions and does not expose embeddings, persisted ingestion can still fail during Graphiti embedding calls. In that case, configure `EMBEDDING_BASE_URL`, `EMBEDDING_MODEL`, and `EMBEDDING_DIM` for a provider that supports embeddings.
