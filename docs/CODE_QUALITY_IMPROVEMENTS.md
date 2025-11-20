# Code Quality Improvement Roadmap

A structured approach to continuously improving code quality beyond the initial setup.

## Current Status

✅ **Tools configured:** Ruff, Mypy, Bandit, Pre-commit
✅ **Auto-fixes applied:** 234 issues resolved
⚠️ **Remaining:** 36 minor issues
⏳ **Test coverage:** Not yet measured
⏳ **Type coverage:** Minimal type hints

## Improvement Phases

### Phase 1: Quick Wins (1-2 hours)

These improvements provide immediate value with minimal effort.

#### 1.1 Fix Remaining Linting Issues

**Current:** 36 remaining issues (mostly low severity)

```bash
# View remaining issues by category
ruff check app/ --statistics

# Fix safe issues with unsafe fixes enabled
ruff check app/ --fix --unsafe-fixes

# Review any remaining manual fixes needed
ruff check app/
```

**Common fixes:**

**Function call in default argument (B008):**
```python
# Before (flagged by ruff)
def get_db(session: Session = Depends(get_session)):
    pass

# This is actually fine for FastAPI - add to ignore list
```

**Exception string formatting (EM101, EM102):**
```python
# Before
raise ValueError(f"Error: {msg}")

# After
error_msg = f"Error: {msg}"
raise ValueError(error_msg)
```

**Import outside top-level (PLC0415):**
```python
# Often intentional for optional dependencies
if TYPE_CHECKING:
    from opentelemetry import trace  # This is fine
```

#### 1.2 Enable Formatting Check in CI

Add to your CI pipeline to enforce formatting:

```bash
# In CI/CD
make format-check  # Fails if code needs formatting
```

#### 1.3 Update .gitignore for Coverage

Ensure coverage reports are ignored:

```bash
echo "*.coverage*" >> .gitignore
echo ".coverage" >> .gitignore
```

---

### Phase 2: Essential Quality Gates (2-4 hours)

Set up automated quality enforcement.

#### 2.1 Measure Test Coverage Baseline

```bash
# Run tests with coverage
pytest --cov=app --cov-report=term --cov-report=html

# View the report
open htmlcov/index.html

# Set a baseline target (e.g., 70%)
```

**Add coverage requirement to pytest:**

```toml
# In pyproject.toml
[tool.coverage.report]
fail_under = 70  # Start with achievable target
```

#### 2.2 Add GitHub Actions CI Pipeline

Create `.github/workflows/quality.yml`:

```yaml
name: Code Quality

on: [push, pull_request]

jobs:
  quality:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-dev.txt

      - name: Lint with Ruff
        run: ruff check app/

      - name: Check formatting
        run: ruff format --check app/

      - name: Type check
        run: mypy app/
        continue-on-error: true  # Don't fail on type errors yet

      - name: Security scan
        run: bandit -c pyproject.toml -r app/

      - name: Run tests
        run: pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

#### 2.3 Add Pre-commit to CI

Ensure pre-commit hooks work in CI:

```yaml
# Add to .github/workflows/quality.yml
- name: Run pre-commit
  run: |
    pip install pre-commit
    pre-commit run --all-files
```

#### 2.4 Configure Branch Protection

On GitHub/GitLab:
- Require "Code Quality" checks to pass before merge
- Require at least one review
- Automatically delete head branches after merge

---

### Phase 3: Type Safety (4-8 hours)

Gradually increase type hint coverage.

#### 3.1 Start with New Code

**Rule:** All new functions must have type hints.

```python
# Good
def process_task(task_id: str, user_id: int) -> dict[str, Any]:
    """Process a task and return results."""
    ...

# Add to code review checklist
```

#### 3.2 Add Types to Critical Paths

Focus on:
1. Public API endpoints
2. Database models
3. Configuration classes
4. Core business logic

```bash
# Check type coverage (requires mypy)
mypy app/ --html-report mypy-report
open mypy-report/index.html
```

#### 3.3 Gradually Increase Mypy Strictness

**Current setting:**
```toml
[tool.mypy]
disallow_untyped_defs = false  # Lenient
```

**Increase gradually:**

```toml
# Step 1: Require types for new modules
[[tool.mypy.overrides]]
module = "app.routers.*"
disallow_untyped_defs = true

# Step 2: Add more modules over time
[[tool.mypy.overrides]]
module = "app.services.*"
disallow_untyped_defs = true

# Step 3: Eventually enable globally
[tool.mypy]
disallow_untyped_defs = true  # All functions need types
```

#### 3.4 Use Type Stubs for Third-Party Libraries

```bash
# Install type stubs
pip install types-requests types-PyYAML

# Add to requirements-dev.txt
```

---

### Phase 4: Testing Excellence (8-16 hours)

Build comprehensive test coverage.

#### 4.1 Increase Test Coverage

**Current gaps** (likely):
- WebSocket connections
- Error handling paths
- Edge cases
- Background worker logic

**Strategy:**

```python
# Add parametrized tests for edge cases
import pytest

@pytest.mark.parametrize("input_data,expected", [
    ({"text": "short"}, "summary"),
    ({"text": ""}, ValueError),
    ({"text": None}, ValueError),
])
def test_summarize_edge_cases(input_data, expected):
    ...
```

#### 4.2 Add Integration Tests

```python
# tests/test_integration.py
import pytest
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_complete_task_flow(client: AsyncClient):
    """Test creating a task, checking status, getting result."""
    # Create task
    response = await client.post("/tasks", json={...})
    task_id = response.json()["id"]

    # Poll until complete
    for _ in range(10):
        status = await client.get(f"/tasks/{task_id}")
        if status.json()["status"] == "done":
            break
        await asyncio.sleep(1)

    assert status.json()["status"] == "done"
```

#### 4.3 Add Performance Tests

```python
# tests/test_performance.py
import pytest
import time

def test_api_response_time(client):
    """Ensure API responds within SLA."""
    start = time.time()
    response = client.get("/health")
    duration = time.time() - start

    assert duration < 0.1  # 100ms SLA
    assert response.status_code == 200
```

#### 4.4 Add Mutation Testing

Install and run mutation testing to find weak tests:

```bash
pip install mutmut

# Run mutation testing
mutmut run

# View results
mutmut results
```

---

### Phase 5: Documentation Quality (4-6 hours)

Ensure code is well-documented.

#### 5.1 Add Docstring Coverage

Install and check docstring coverage:

```bash
pip install interrogate

# Check coverage
interrogate app/ -v

# Add to pyproject.toml
[tool.interrogate]
ignore-init-method = true
ignore-init-module = false
ignore-magic = false
ignore-semiprivate = false
ignore-private = false
ignore-property-decorators = false
ignore-module = false
ignore-nested-functions = false
ignore-nested-classes = true
fail-under = 80
```

#### 5.2 Enforce Docstring Style

Use Ruff to enforce docstring conventions:

```toml
# In pyproject.toml
[tool.ruff.lint]
select = [
    ...existing rules...,
    "D",  # pydocstyle - docstring conventions
]

[tool.ruff.lint.pydocstyle]
convention = "google"  # Or "numpy" or "pep257"
```

#### 5.3 Generate API Documentation

```bash
# Install sphinx
pip install sphinx sphinx-autodoc-typehints

# Initialize
sphinx-quickstart docs/api

# Configure to use autodoc
# Add to docs/api/conf.py:
extensions = ['sphinx.ext.autodoc', 'sphinx_autodoc_typehints']

# Generate docs
cd docs/api
make html
```

---

### Phase 6: Advanced Quality Metrics (8+ hours)

Implement sophisticated quality tracking.

#### 6.1 Code Complexity Monitoring

**Add complexity checks:**

```toml
# In pyproject.toml
[tool.ruff.lint]
select = [
    ...existing...,
    "C90",  # mccabe complexity
]

[tool.ruff.lint.mccabe]
max-complexity = 10  # Flag complex functions
```

**Reduce complexity in flagged functions:**
- Extract helper functions
- Use early returns
- Simplify conditional logic

#### 6.2 Dependency Vulnerability Scanning

**Already configured in pre-commit**, but add continuous monitoring:

```bash
# Install safety
pip install safety

# Check dependencies
safety check --json

# Add to CI
- name: Check dependencies
  run: safety check --continue-on-error
```

#### 6.3 Code Duplication Detection

```bash
# Install vulture for dead code
pip install vulture

# Find dead code
vulture app/

# Install pylint for duplication
pip install pylint

# Check duplication
pylint --disable=all --enable=duplicate-code app/
```

#### 6.4 SonarQube Integration

For enterprise-grade quality tracking:

```yaml
# Add to CI
- name: SonarQube Scan
  uses: sonarsource/sonarqube-scan-action@master
  env:
    SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
```

---

## Continuous Improvement Practices

### Daily Habits

1. **Run before every commit:**
   ```bash
   make validate
   ```

2. **Review coverage changes:**
   ```bash
   pytest --cov=app --cov-report=term-missing
   ```

3. **Keep dependencies updated:**
   ```bash
   pip list --outdated
   ```

### Weekly Practices

1. **Review Ruff/Mypy rule updates:**
   ```bash
   pip install --upgrade ruff mypy
   ```

2. **Check for security advisories:**
   ```bash
   safety check
   ```

3. **Review test coverage trends**

### Monthly Practices

1. **Increase strictness gradually:**
   - Enable one new Ruff rule
   - Add type hints to one module
   - Increase coverage target by 5%

2. **Refactor flagged complexity:**
   - Fix one "too complex" function
   - Reduce code duplication

3. **Update tooling:**
   ```bash
   pip install --upgrade -r requirements-dev.txt
   pre-commit autoupdate
   ```

---

## Quality Metrics Dashboard

Track these metrics over time:

| Metric | Current | Target | Tool |
|--------|---------|--------|------|
| Linting errors | 36 | 0 | Ruff |
| Test coverage | ? | 85% | pytest-cov |
| Type coverage | Low | 80% | mypy |
| Docstring coverage | ? | 80% | interrogate |
| Cyclomatic complexity | ? | <10 avg | Ruff (C90) |
| Security issues | 0 | 0 | Bandit |
| Duplicate code | ? | <5% | Pylint |

---

## Practical Next Steps (Choose Your Path)

### Path A: Quick Wins (Today)
```bash
# 1. Fix remaining linting issues
ruff check app/ --fix --unsafe-fixes

# 2. Install pre-commit hooks
pre-commit install

# 3. Run full validation
make validate
```

### Path B: Quality Gates (This Week)
1. Set up GitHub Actions CI
2. Measure test coverage baseline
3. Add coverage requirement (70%)
4. Enable branch protection

### Path C: Long-term Excellence (This Month)
1. Start adding type hints to new code
2. Write tests for uncovered code
3. Add docstrings to public APIs
4. Enable one new Ruff rule per week

---

## Recommended Reading

- **PEP 8** - Python Style Guide
- **PEP 484** - Type Hints
- **Google Python Style Guide** - Comprehensive best practices
- **Effective Python** (Book) - 90 specific ways to write better Python
- **Clean Code** (Book) - Universal principles

---

## Tools to Consider Later

### Advanced Linting
- **Pylint** - More opinionated linting (slower than Ruff)
- **Flake8-plugins** - Specialized checks

### Performance
- **py-spy** - Profiling
- **memory-profiler** - Memory usage
- **locust** - Load testing

### Documentation
- **Sphinx** - API documentation
- **mkdocs** - User documentation
- **pydoc-markdown** - Markdown API docs

### Security
- **snyk** - Comprehensive vulnerability scanning
- **semgrep** - Pattern-based security analysis

---

## Questions to Guide Decisions

Before adding a new tool, ask:

1. **Does it solve a real problem we have?**
2. **Will it catch bugs we've actually had?**
3. **Can we maintain it long-term?**
4. **Does it overlap with existing tools?**
5. **Will the team actually use it?**

---

## Summary

**Start here:**
1. ✅ Fix remaining Ruff issues
2. ✅ Install pre-commit hooks
3. ✅ Measure test coverage baseline
4. ✅ Set up CI pipeline

**Then gradually:**
- Add type hints to new code
- Increase test coverage to 80%+
- Enable more strict linting rules
- Add documentation standards

**Remember:** Perfect is the enemy of good. Improve incrementally!
