# Contributing to AegisOS

Thank you for your interest in contributing to AegisOS! This guide will help you get started.

## Code of Conduct

By participating in this project, you agree to follow our [Code of Conduct](CODE_OF_CONDUCT.md).

## How Can I Contribute?

### 🐛 Report Bugs

Before creating a bug report:
1. Check if the issue already exists
2. Use a clear title and description
3. Include steps to reproduce, expected vs actual behavior

```bash
# Example bug report format
**Bug**: Brief description
**Steps to Reproduce**:
1. Go to '...'
2. Click on '....'
3. See error

**Expected**: What should happen
**Actual**: What actually happened
```

### 💡 Suggest Features

Open an issue with:
- Clear use case description
- Potential implementation approach
- Any relevant docs or examples

### 🛠️ Pull Requests

1. **Fork** the repository
2. **Clone** your fork: `git clone https://github.com/YOUR_USERNAME/AegisOs.git`
3. **Create** a feature branch: `git checkout -b feature/amazing-feature`
4. **Make** your changes
5. **Test** your changes
6. **Commit** with descriptive messages
7. **Push** to your fork
8. **Open** a Pull Request

## Development Setup

### Prerequisites

- Python 3.12+
- Node.js 20+
- pnpm 8+
- Docker 24+
- PostgreSQL 16 (optional, can use Docker)

### Backend Setup

```bash
cd backend

# Create virtual environment
uv venv
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate on Windows

# Install dependencies
uv sync --group dev

# Run tests
uv run pytest

# Start development server
uv run uvicorn ecms.main:app --reload
```

### Frontend Setup

```bash
cd frontend
pnpm install
pnpm dev
```

### Full Stack (Docker)

```bash
docker compose -f docker/docker-compose.yml up -d
```

## Coding Standards

### Python

- Follow **PEP 8** style guide
- Use **type hints** where possible
- Run linting: `ruff check ecms`
- Run type checking: `mypy ecms`

```python
# Good example
def process_user_request(user_id: str, request: str) -> dict[str, Any]:
    """Process a user request and return the result."""
    result = {"user_id": user_id, "status": "completed"}
    return result
```

### TypeScript/React

- Follow ESLint and Prettier configurations
- Use functional components with hooks
- Prefer TypeScript types over `any`

```typescript
// Good example
interface UserProfile {
  id: string;
  name: string;
  email: string;
}

const UserCard: React.FC<{ user: UserProfile }> = ({ user }) => {
  return <div>{user.name}</div>;
};
```

## Testing

### Run All Tests

```bash
# Backend
cd backend
uv run pytest

# Frontend
cd frontend
pnpm test
```

### Run Specific Tests

```bash
uv run pytest tests/test_ba_agent.py -v
```

## Commit Messages

Use clear, descriptive commit messages:

```
feat: Add AI Scope Analyzer for agent profiles
fix: Resolve migration chain error for revision 0022
docs: Update API documentation
refactor: Simplify knowledge graph query builder
test: Add unit tests for memory layer
```

## Review Process

1. All PRs require at least one review
2. Ensure CI/CD checks pass
3. Update documentation if needed
4. Squash commits before merging

## Resources

- [Documentation](docs/)
- [API Docs](http://localhost:8000/docs)
- [Architecture Overview](docs/ARCHITECTURE.md)

## Questions?

- Open a [Discussion](https://github.com/Brajesh9373/AegisOs/discussions)
- Join our community

---

⭐ Thanks for contributing to AegisOS!