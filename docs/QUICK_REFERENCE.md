# Code Quality Quick Reference

## 🚀 Quick Commands

```bash
# Daily use
make validate      # Run all checks before commit
make improve       # Auto-fix everything possible
make assess        # Get quality report + recommendations

# Specific checks
make lint          # Check linting
make format        # Format code
make type-check    # Check types
make security      # Security scan
make coverage      # Measure test coverage

# See all commands
make help
```

## 📋 Pre-Commit Workflow

```bash
# 1. Make changes
vim app/something.py

# 2. Run quality checks
make validate

# 3. Commit (hooks run automatically)
git add .
git commit -m "Add feature"

# If hooks fail:
make improve       # Fix automatically
# Then commit again
```

## 🔧 Common Tasks

### Fix All Issues Automatically
```bash
make improve
```

### Get Quality Assessment
```bash
make assess
```

### Check Test Coverage
```bash
make coverage
open htmlcov/index.html
```

### Find Complex Code
```bash
make complexity
```

## 📊 Quality Metrics to Track

| Metric | Command | Target |
|--------|---------|--------|
| Linting errors | `ruff check app/` | 0 |
| Test coverage | `make coverage` | 80%+ |
| Type coverage | `mypy app/` | Gradual increase |
| Security issues | `make security` | 0 |

## 🎯 Improvement Phases

### Phase 1: Quick Wins (Today)
- ✅ Run `make improve`
- ✅ Install pre-commit: `pre-commit install`
- ✅ Run `make assess`

### Phase 2: CI/CD (This Week)
- ✅ Push `.github/workflows/quality.yml` to GitHub
- ✅ Enable branch protection
- ✅ Measure test coverage baseline

### Phase 3: Gradual Improvement (Ongoing)
- 📝 Add type hints to new code
- 🧪 Increase test coverage by 5% monthly
- 📚 Add docstrings to public APIs
- 🔧 Enable stricter linting rules gradually

## 📚 Documentation

- Complete guide: `docs/CODE_QUALITY.md`
- Improvements roadmap: `docs/CODE_QUALITY_IMPROVEMENTS.md`
- Review checklist: `docs/CODE_REVIEW_CHECKLIST.md`
- Initial report: `docs/CODE_QUALITY_REPORT.md`

## 🛠️ Tools Installed

- **Ruff** - Fast linting + formatting
- **Mypy** - Type checking
- **Bandit** - Security scanning
- **Pre-commit** - Git hooks
- **Pytest** - Testing + coverage

## 💡 Pro Tips

1. **Setup IDE to format on save** (Ruff extension)
2. **Always run `make validate` before pushing**
3. **Review `make assess` output weekly**
4. **Don't skip pre-commit hooks** (use `--no-verify` sparingly)
5. **Improve incrementally** - perfect is the enemy of good

## 🆘 Troubleshooting

**Pre-commit hooks blocking commit?**
```bash
make improve
git commit -m "message"  # Try again
```

**Too many type errors?**
```bash
# Type checking is lenient for now
# Add `# type: ignore` for unavoidable issues
```

**Can't run tests?**
```bash
pip install -r requirements.txt
# Ensure postgres is running: docker-compose up -d postgres
```

## 🎓 Learning Resources

- **Ruff docs:** https://docs.astral.sh/ruff/
- **Mypy docs:** https://mypy.readthedocs.io/
- **Python typing:** https://docs.python.org/3/library/typing.html
- **Pre-commit:** https://pre-commit.com/
