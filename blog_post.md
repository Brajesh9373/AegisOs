# How to Deploy and Explore AegisOS – An Enterprise AI Workforce Operating System

**Published:** September 11, 2026  
**Author:** Brajesh Kumar (via community contribution)  
**Tags:** AI agents, knowledge graph, enterprise software, open source, Docker, FastAPI, React

---

## Introduction

AegisOS is an open‑source **Enterprise AI Workforce Operating System** that lets you connect disparate enterprise systems (Git, Jira, Slack, databases, etc.), spin up governed AI agents with memory and knowledge‑graph capabilities, and observe everything through a built‑in Prometheus/Grafana/Loki/Tempo stack. In this post we’ll walk through a quick local deployment, highlight the key features, and show how you can start building your own AI‑native workflows.

---

## Prerequisites

| Tool | Minimum Version |
|------|-----------------|
| Docker | 24+ |
| RAM | 8 GB |
| Disk | 20 GB |
| Node.js | 22+ |
| pnpm | 11+ |
| API Key | An Anthropic‑compatible key (we’ll use the free FreeLLM API for this demo) |

> **Tip:** If you don’t have an Anthropic key, sign up for a free key at [FreeLLM API](https://freellmapi.co) and use the endpoint `http://localhost:3002/v1` (see the “Using FreeLLM” section below).

---

## Step‑by‑Step Installation

### 1. Clone the repository
```bash
git clone https://github.com/Brajesh9373/AegisOS
cd AegisOS
```

### 2. Configure the environment
Copy the example environment file and insert your API key:
```bash
cp .env.example .env
# Edit .env with your favorite editor
nano .env
```
Set:
```
ANTHROPIC_API_KEY=freellmapi-7e13a597ba6b66fc039d7f5544c86d1488f40b71671e0564
ANTHROPIC_BASE_URL=http://localhost:3002/v1
```
(Replace the key with your own if you have a different one.)

### 3. Start the stack
The provided script handles DSH bundle creation, Docker image builds, and container orchestration:
```bash
./scripts/start-aegisos.sh
```
You’ll see output similar to:
```
[DSH] Building bundle…
[Docker] Building images…
[Docker] Starting services…
✅ Frontend: http://localhost:3000
✅ Backend API: http://localhost:8000
✅ API Docs: http://localhost:8000/docs
✅ Grafana: http://localhost:3300
✅ Prometheus: http://localhost:9090
```
The first run may take a few minutes while the DSH bundle is compiled.

### 4. Verify the services
Open your browser and navigate to:
- **Frontend UI:** `http://localhost:3000` – the Mission Control dashboard.
- **API Docs:** `http://localhost:8000/docs` – interactive Swagger UI for the FastAPI backend.
- **Grafana:** `http://localhost:3300` (default credentials: `admin` / `admin`) – pre‑built panels for system metrics, logs, and traces.
- **Prometheus:** `http://localhost:9090` – query the raw metrics if you’d like.

---

## Core Features Walkthrough

### 1. Mission Control (Frontend)
The React/ Ant Design SPA gives you a top‑level view of:
- **Projects** – containers for your AI‑driven initiatives.
- **Teams** – hierarchies of AI agents (Head of Engineering, Senior Frontend/Backend Engineers, etc.).
- **Connectors** – links to GitHub, GitLab, Jira, Slack, etc.
- **Knowledge Graph** – visualised with Cosmos.gl + D3.js.
- **Chat with the Head of Engineering** – powered by the underlying LLM (via FreeLLM in our demo).

### 2. Creating a Project
Click **“Create Project”**, fill in a name and optional description, and you’re taken to the workspace view. Here you can:
- Spawn new agent teams (e.g., a backend team for API work).
- Add connectors to ingest source code or tickets.
- Start a chat session with the AI agent to ask for designs, reviews, or code generation.

### 3. Adding a Connector
In the **Connectors** tab:
1. Choose a source (e.g., GitHub).
2. Provide the repository URL and any required credentials (personal access token or OAuth).
3. Click **Run Ingestion**.
The coordinator will clone the repo, extract file‑level metadata, and commit immutable snapshots to FalkorDB. You’ll see progress in the UI and, once done, the knowledge graph updates automatically.

### 4. Exploring the Knowledge Graph
Switch to the **Knowledge Graph** tab. You’ll see:
- **Nodes** representing files, classes, functions, and documentation.
- **Edges** showing calls, imports, inheritance, and documentation links.
- **Zoom, pan, and search** capabilities.
- **Colour‑coding** by node type (file, class, function, etc.).
- **Node details** pane on click, showing the raw snippet and metadata.

### 5. Observability Stack
All services emit metrics, logs, and traces:
- **Prometheus** scrapes the backend (`/metrics`) and the frontend (custom metrics).
- **Grafana** ships with dashboards for:
  - Request latency and error rates.
  - Queue lengths (Redis Streams).
  - Agent telemetry (tokens consumed, tool calls).
- **Loki** collects logs from all containers; you can explore them via Grafana’s log panel.
- **Tempo** captures distributed traces (OpenTelemetry) letting you follow a request from the browser → backend → DSH agent → LLM call.

---

## Extending AegisOS

### Adding a Custom Agent
1. Create a new profile in `postgres/seeds/agent_profiles.csv` (or via the UI once the admin panel is enabled).
2. Implement the agent’s logic in a Python class under `ecms/agents/`.
3. Register the agent in `ecms/main.py` (import and add to the agent factory).
4. Restart the backend (`docker compose restart ecms-backend-1`) or use the provided scripts.

### Adding a New Connector
Connectors live in `ecms/connectors/`. To add one:
1. Subclass `BaseConnector` and implement `fetch()` and `transform()`.
2. Add the connector type to the `ConnectorType` enum in `ecms/models.py`.
3. Register the route in `ecms/routes/connector.py`.
4. Rebuild and restart the stack.

### Using Your Own LLM Provider
If you prefer to run a local model (e.g., via Ollama or llama.cpp):
1. Set `ANTHROPIC_BASE_URL` to point to your local OpenAI‑compatible endpoint (e.g., `http://host.docker.internal:11434/v1`).
2. Ensure the model name you want to use is listed in `/v1/models` of your provider.
3. Optionally add a `modelOverrides` section in `.claude/settings.json` if you’re using Claude Code locally.

---

## Why Star the Repo?

- **Visibility:** More stars help the project appear in GitHub’s explore and trending sections, attracting contributors and users.
- **Feedback:** A larger community means more issue reports, pull requests, and ideas for new features.
- **Sustainability:** Stars signal interest, which can encourage sponsors or grant opportunities for long‑term maintenance.
- **Learning:** By starring, you get notified of new releases, making it easy to stay up‑to‑date with improvements.

If you found this guide useful, please:
1. ⭐ Star the repository: https://github.com/Brajesh9373/AegisOS
2. 🐛 Open an issue if you encounter bugs or have feature ideas.
3. 💬 Join the discussion tab to share your use‑case.
4. 📤 Share the link with teammates, friends, or on social media (Twitter/X, LinkedIn, Reddit r/MachineLearning, etc.).
5. 🔁 Consider contributing code, documentation, or translations.

---

## Conclusion

AegisOS gives you a ready‑to‑run foundation for building AI‑native enterprise systems. With a single `./scripts/start-aegisos.sh` command you have a full stack of agents, knowledge graph, observability, and a polished UI—all powered by free LLM tiers via FreeLLM API (or any provider you prefer).  

Start experimenting today, and let’s grow the ecosystem together!

---

*Happy building!*  
— Brajesh Kumar (community contributor)