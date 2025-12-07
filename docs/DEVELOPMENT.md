# Development Guide

This guide covers code quality practices, development workflows, and review standards.

## Project Structure

```
agents_playground/
├── app/                        # Application code
│   ├── agents/                 # Agent implementations
│   │   ├── base.py            # Abstract Agent base class
│   │   ├── registry.py        # Agent registry
│   │   ├── registry_init.py   # Global registry singleton
│   │   ├── research_agent.py  # Research agent
│   │   └── assessment_agent.py # Assessment agent
│   ├── tools/                  # Tool implementations
│   │   ├── base.py            # Abstract Tool base class
│   │   ├── registry.py        # Tool registry
│   │   └── registry_init.py   # Global tool registry singleton
│   ├── workflows/              # YAML workflow definitions
│   ├── orchestrator/           # Workflow execution engine
│   │   ├── coordination_strategies.py  # Sequential, iterative, etc.
│   │   └── declarative_orchestrator.py
│   ├── routers/                # FastAPI route handlers
│   │   └── tasks.py           # Task CRUD endpoints
│   ├── middleware/             # FastAPI middleware
│   │   └── mtls.py            # mTLS authentication
│   ├── main.py                 # FastAPI application entry point
│   ├── worker.py               # Worker process entry point
│   ├── worker_state.py         # Worker state machine
│   ├── worker_helpers.py       # Task processing logic
│   ├── worker_lease.py         # Lease management
│   ├── task_state.py           # Task execution state machine
│   ├── tasks.py                # Task execution logic
│   ├── database.py             # Async database connection
│   ├── db_sync.py              # Sync database for worker
│   ├── models.py               # SQLAlchemy ORM models
│   ├── schemas.py              # Pydantic request/response schemas
│   ├── config.py               # Pydantic settings
│   ├── websocket.py            # WebSocket manager
│   ├── tracing.py              # OpenTelemetry setup
│   ├── metrics.py              # Prometheus metrics
│   └── audit.py                # Audit logging
├── config/                     # Configuration files
│   ├── agents.yaml             # Agent definitions (optional)
│   └── tools.yaml              # Tool definitions (optional)
├── docs/                       # Documentation
│   ├── QUICKSTART.md           # Quick start guide
│   ├── ARCHITECTURE.md         # System architecture
│   ├── API_REFERENCE.md        # API documentation
│   ├── MONITORING.md           # Observability guide
│   ├── TROUBLESHOOTING.md      # Common issues
│   ├── WORKFLOWS.md            # Workflow guide
│   ├── AGENT_REGISTRY.md       # Agent registry guide
│   ├── TOOL_REGISTRY.md        # Tool registry guide
│   ├── OPENWEBUI.md            # Open WebUI integration
│   ├── WORKER_SCALING.md       # Scaling guide
│   └── DEVELOPMENT.md          # This file
├── integrations/               # External integrations
│   └── openwebui/              # Open WebUI tools
│       ├── openwebui_tool.py   # @flow command
│       ├── openwebui_agent.py  # @agent command
│       ├── openwebui_tool_tool.py  # @tool command
│       └── openwebui_discover.py   # @discover command
├── monitoring/                 # Observability stack configs
│   ├── grafana/                # Grafana dashboards
│   ├── prometheus/             # Prometheus config
│   └── otel-collector-config.yaml
├── postgres-init/              # Database initialization scripts
│   └── init.sql                # Schema and initial data
├── tests/                      # Test suite
│   ├── test_worker_state.py    # Worker state machine tests
│   ├── test_task_state.py      # Task state machine tests
│   ├── test_agent_registry.py  # Registry tests
│   └── conftest.py             # Pytest fixtures
├── utils/                      # Utility scripts
│   ├── generate_certs.sh       # SSL certificate generation
│   ├── test_api.py             # API testing script
│   └── test_websocket.py       # WebSocket testing script
├── docker-compose.yml          # Service orchestration
├── Dockerfile                  # Task API/Worker container
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Development dependencies
├── pyproject.toml              # Python project config (Ruff, Mypy, etc.)
├── Makefile                    # Development commands
├── .env                        # Environment variables (gitignored)
├── .env.example                # Environment template
├── .gitignore                  # Git ignore rules
└── README.md                   # Project overview
```

## Quick Start

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Run all quality checks
make validate
```

## Daily Commands

```bash
# Before committing
make validate          # Run all checks

# Specific checks
make lint             # Check linting
make lint-fix         # Auto-fix linting issues
make format           # Format code
make type-check       # Check types
make security         # Security scan
make test-cov         # Run tests with coverage

# See all commands
make help
```

## Tools Overview

### Ruff - Linting & Formatting
Fast Python linter and formatter (10-100x faster than traditional tools).

```bash
ruff check .          # Check for issues
ruff check --fix .    # Auto-fix issues
ruff format .         # Format code
```

### Mypy - Type Checking
Static type analysis to catch type errors.

```bash
mypy app tests
```

### Bandit - Security Scanning
Finds common security issues.

```bash
bandit -c pyproject.toml -r app
```

### Pre-commit Hooks
Automatically runs checks before each commit.

```bash
pre-commit install          # One-time setup
pre-commit run --all-files  # Manual run
```

## Workflow

### During Development

1. Write code
2. Format on save (configure IDE)
3. Run `make validate` before committing
4. Commit (pre-commit hooks run automatically)
5. Fix issues if hooks fail

### IDE Integration

#### VS Code
Add to `.vscode/settings.json`:
```json
{
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": true
    },
    "editor.defaultFormatter": "charliermarsh.ruff"
  }
}
```

Install extensions:
- Ruff (charliermarsh.ruff)
- Mypy Type Checker (ms-python.mypy-type-checker)

## Code Review Checklist

Use this checklist for PRs and code reviews.

### Before Committing
- [ ] Run `make validate` and fix all issues
- [ ] Add/update tests for new functionality
- [ ] Check test coverage hasn't decreased
- [ ] Run the application locally

### Code Quality
- [ ] Follows project style (Ruff passes)
- [ ] No unnecessary complexity
- [ ] Functions are reasonably sized (<50 lines)
- [ ] No code duplication
- [ ] Meaningful variable/function names

### Type Safety
- [ ] New functions have type hints
- [ ] Type hints are accurate
- [ ] No `# type: ignore` without good reason

### Testing
- [ ] Tests added for new functionality
- [ ] Tests cover edge cases
- [ ] All tests pass
- [ ] Coverage meets threshold (50%+)

### Security
- [ ] No hardcoded secrets
- [ ] Input validation is present
- [ ] Bandit security scan passes

### Documentation
- [ ] Docstrings for public functions/classes
- [ ] Complex logic has comments
- [ ] README updated if needed

## Configuration

All tool configurations are in `pyproject.toml`:

- **[tool.ruff]** - Linting and formatting rules
- **[tool.mypy]** - Type checking settings
- **[tool.pytest.ini_options]** - Test configuration
- **[tool.bandit]** - Security scanning rules

## Continuous Improvement

### Best Practices

1. ✅ Run `make validate` before every commit
2. ✅ Keep pre-commit hooks enabled
3. ✅ Format code automatically on save
4. ✅ Add type hints to new functions
5. ⚠️ Don't use `--no-verify` to skip git hooks

### Gradual Improvements

As the codebase matures:
- Add type hints to existing code
- Increase test coverage target
- Enable stricter linting rules
- Add docstrings to public APIs

## Troubleshooting

### "Command not found: ruff"
```bash
pip install -r requirements-dev.txt
```

### Pre-commit hooks blocking commit?
```bash
make lint-fix
make format
git commit -m "message"  # Try again
```

### Type checking errors
```bash
# Add type: ignore for third-party libraries
import somelib  # type: ignore
```

## Resources

- **Ruff docs:** https://docs.astral.sh/ruff/
- **Mypy docs:** https://mypy.readthedocs.io/
- **Python typing:** https://docs.python.org/3/library/typing.html
- **Pre-commit:** https://pre-commit.com/
