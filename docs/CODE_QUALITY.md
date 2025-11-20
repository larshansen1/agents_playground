# Code Quality Setup Guide

This project uses modern Python tooling for linting, formatting, type checking, and security scanning.

## Quick Start

```bash
# 1. Install development dependencies
pip install -r requirements-dev.txt

# 2. Install pre-commit hooks (runs checks automatically on git commit)
pre-commit install

# 3. Run all checks manually
make validate
```

## Tools Overview

### 🚀 Ruff - Fast Linter & Formatter
**Ruff** is a blazing-fast Python linter and formatter that replaces multiple tools:
- ✅ Replaces: flake8, isort, pydocstyle, pyupgrade, autoflake
- ✅ 10-100x faster than traditional tools
- ✅ Auto-fixes most issues

**Commands:**
```bash
# Check for linting issues
ruff check .

# Auto-fix linting issues
ruff check --fix .

# Format code
ruff format .

# Check formatting (CI mode)
ruff format --check .
```

### 🔍 Mypy - Type Checking
**Mypy** performs static type analysis to catch type errors before runtime.

**Commands:**
```bash
# Run type checking
mypy app tests
```

**Tips:**
- Add type hints to function signatures: `def foo(name: str) -> int:`
- Use `# type: ignore` comments sparingly for unavoidable issues
- Start with lenient settings (current) and gradually increase strictness

### 🔒 Bandit - Security Scanner
**Bandit** finds common security issues in Python code.

**Commands:**
```bash
# Scan for security issues
bandit -c pyproject.toml -r app
```

**Common Issues It Catches:**
- Hardcoded passwords
- SQL injection vulnerabilities
- Insecure random number generation
- Shell injection risks

### 🪝 Pre-commit Hooks
**Pre-commit** automatically runs checks before each git commit.

**Commands:**
```bash
# Install hooks (one-time setup)
pre-commit install

# Run manually on all files
pre-commit run --all-files

# Skip hooks for a single commit (use sparingly!)
git commit --no-verify -m "message"
```

## Makefile Commands

We provide a `Makefile` for convenience:

```bash
# Show all available commands
make help

# Install development dependencies
make install-dev

# Run linting
make lint

# Run linting with auto-fix
make lint-fix

# Format code
make format

# Check formatting without changes
make format-check

# Run type checking
make type-check

# Run security scanning
make security

# Run tests
make test

# Run tests with coverage
make test-cov

# Run all validations (recommended before commit)
make validate

# Complete CI/CD pipeline
make all

# Clean generated files
make clean
```

## Workflow

### During Development

1. **Write code** as normal
2. **Format on save** (configure your IDE to run `ruff format` on save)
3. **Run checks** before committing:
   ```bash
   make validate
   ```
4. **Commit** - pre-commit hooks will run automatically
5. **Fix issues** if hooks fail, then commit again

### IDE Integration

#### VS Code
Add to `.vscode/settings.json`:
```json
{
  "[python]": {
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.fixAll": true,
      "source.organizeImports": true
    },
    "editor.defaultFormatter": "charliermarsh.ruff"
  },
  "ruff.lint.args": ["--fix"],
  "mypy-type-checker.args": ["--config-file=pyproject.toml"]
}
```

Install extensions:
- Ruff (charliermarsh.ruff)
- Mypy Type Checker (ms-python.mypy-type-checker)

#### PyCharm
1. Install **Ruff** plugin from marketplace
2. Enable "Run ruff on save" in Settings → Tools → Ruff
3. Configure Mypy as external tool

## Configuration Files

All tool configurations are centralized in `pyproject.toml`:

- **[tool.ruff]** - Linting and formatting rules
- **[tool.mypy]** - Type checking settings
- **[tool.pytest.ini_options]** - Test configuration
- **[tool.coverage]** - Coverage settings
- **[tool.bandit]** - Security scanning rules

## CI/CD Integration

Add this to your CI pipeline (GitHub Actions example):

```yaml
name: Code Quality

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt -r requirements-dev.txt

      - name: Run validation
        run: make validate

      - name: Run tests with coverage
        run: make test-cov
```

## Customization

### Add/Remove Linting Rules

Edit `pyproject.toml`:
```toml
[tool.ruff.lint]
select = ["E", "F", "I"]  # Add rule codes
ignore = ["E501"]          # Ignore specific rules
```

Common rule codes:
- **E/W** - pycodestyle (PEP 8 style)
- **F** - pyflakes (code errors)
- **I** - isort (import sorting)
- **N** - pep8-naming
- **B** - bugbear (common bugs)
- **C4** - comprehensions
- **UP** - pyupgrade (modern Python)

### Adjust Type Checking Strictness

Edit `pyproject.toml`:
```toml
[tool.mypy]
disallow_untyped_defs = true  # Require type hints on all functions
strict = true                 # Enable all strict checks
```

## Troubleshooting

### "Command not found: ruff"
```bash
# Ensure dev dependencies are installed
pip install -r requirements-dev.txt
```

### "pre-commit command not found"
```bash
pip install pre-commit
pre-commit install
```

### "Too many linting errors"
```bash
# Start by auto-fixing what can be fixed
make lint-fix
make format

# Then manually fix remaining issues
```

### Type checking errors
```bash
# Add type: ignore for third-party libraries
import somelib  # type: ignore
```

## Best Practices

1. ✅ **Run `make validate` before every commit**
2. ✅ **Keep pre-commit hooks enabled**
3. ✅ **Format code automatically on save (IDE integration)**
4. ✅ **Add type hints to new functions**
5. ✅ **Don't ignore security warnings from Bandit**
6. ✅ **Keep test coverage above 80%**
7. ⚠️ **Don't use `--no-verify` to skip git hooks**
8. ⚠️ **Don't add `# noqa` or `# type: ignore` without good reason**

## Next Steps

1. Run initial validation:
   ```bash
   make install-dev
   make validate
   ```

2. Fix any issues found

3. Commit the configuration files:
   ```bash
   git add pyproject.toml .pre-commit-config.yaml requirements-dev.txt Makefile
   git commit -m "Add code quality tooling"
   ```

4. Start using the tools in your workflow!
