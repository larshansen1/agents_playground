# Code Quality Checklist

Use this checklist for code reviews and before merging PRs.

## Before Committing

- [ ] Run `make validate` and fix all issues
- [ ] Add/update tests for new functionality
- [ ] Add/update docstrings for public functions
- [ ] Check test coverage hasn't decreased
- [ ] Run the application locally to verify changes

## Code Review Checklist

### Functionality
- [ ] Code does what it's supposed to
- [ ] Edge cases are handled
- [ ] Error handling is appropriate
- [ ] No obvious bugs

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
- [ ] Tests are meaningful (not just for coverage)
- [ ] All tests pass
- [ ] Coverage meets threshold (70%+)

### Security
- [ ] No hardcoded secrets
- [ ] Input validation is present
- [ ] SQL injection risks addressed
- [ ] Authentication/authorization appropriate
- [ ] Bandit security scan passes

### Documentation
- [ ] Docstrings for public functions/classes
- [ ] Complex logic has comments
- [ ] README updated if needed
- [ ] API docs updated if needed

### Performance
- [ ] No obvious performance issues
- [ ] Database queries are efficient
- [ ] No N+1 query problems
- [ ] Appropriate use of async/await

### Dependencies
- [ ] New dependencies are justified
- [ ] Dependencies are pinned
- [ ] No known vulnerabilities (safety check)

### Git
- [ ] Commit messages are clear
- [ ] No merge conflicts
- [ ] No unintended file changes
- [ ] .gitignore is appropriate

## Before Releasing

- [ ] All CI checks pass
- [ ] Manual testing complete
- [ ] Performance testing if needed
- [ ] Security review if needed
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] Version bumped appropriately
