# AegisOS - Enterprise AI Workforce Operating System

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-Available-brightgreen)](https://aegisos.tailb5c137.ts.net/)
[![GitHub Stars](https://img.shields.io/github/stars/Brajesh9373/AegisOS?style=social)](https://github.com/Brajesh9373/AegisOS/stargazers)

> **Enterprise AI Workforce Operating System** – Connect enterprise systems, coordinate AI workers with memory, knowledge graphs, governance, and human approvals.

## 🌟 Why AegisOS?

- **AI Agents with Governance** – Business Analyst, Compliance Officer, and custom agents with memory, knowledge graphs, and human-in-the-loop approvals.
- **Multi‑Source Connectors** – Ingest from Git, GitHub, GitLab, Jira, Confluence, Slack with async parallel extraction.
- **Knowledge‑Graph Powered** – FalkorDB + Apache Arrow snapshots for fast, immutable knowledge.
- **Observability Stack** – Prometheus, Grafana, Loki, Tempo built‑in.
- **Production‑Ready** – Docker‑Compose, Kubernetes, Helm, Terraform assets.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/Brajesh9373/AegisOS
cd AegisOS

# Start the full stack (handles DSH build + Docker automatically)
./scripts/start-aegisos.sh

# Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Requirements
- Docker 24+, ≥8 GB RAM, ≥20 GB disk space  
- Node.js 22+ (for DSH bundle building)  
- pnpm 11+ (for DSH dependency management)  

### Environment Variables
| Variable | Description | Required? |
|----------|-------------|-----------|
| `ANTHROPIC_API_KEY` | Anthropic API key (or compatible proxy) | Yes |
| `ANTHROPIC_BASE_URL` | Anthropic API base URL | Default: `https://api.anthropic.com` |

## 📖 Documentation

- [Architecture](docs/ARCHITECTURE.md)
- [Backend Architecture](docs/backend-architecture.md)
- [Agent System](docs/agent-system.md)
- [Knowledge Graph](docs/knowledge-graph.md)
- [Memory Model](docs/memory.md)
- [Security](docs/security.md)
- [Connector Ingestion Operations](docs/connector-ingestion-operations.md)
- [Knowledge Graph v2 Operations](docs/knowledge-graph-v2-operations.md)
- [Deployment](docs/deployment.md)
- [Testing](docs/testing.md)
- [Integration Guide](docs/integration-guide.md)

## 🛠️ Development

### Backend
```bash
cd backend
uv sync --group dev
uv run uvicorn ecms.main:app --reload
uv run pytest --no-cov
uv run ruff check ecms tests
uv run mypy ecms
```

### Frontend
```bash
cd frontend
pnpm install
pnpm dev
```

## 🤝 Contributing

Contributions are welcome! Please read our [Contributing Guide](CONTRIBUTING.md) for details on setting up the development environment and submitting pull requests.

## 📜 License

This project is licensed under the [Apache License 2.0](LICENSE).

## 🙌 Support

If you find AegisOS useful, please consider:
- Starring the repository ⭐
- Opening issues for bugs or feature requests
- Joining the discussion tab
- Sharing the project with your team and community

---

**Live Demo:** https://aegisos.tailb5c137.ts.net/