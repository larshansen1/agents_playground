# Testing Improvement Requirements

**Project:** Agents Playground - Task Orchestration System
**Current State:** 362 tests, 78.18% coverage, 4.81s execution time
**Document Version:** 1.0
**Created:** November 2025

---

## Executive Summary

This document outlines a phased approach to improving test quality for the Agents Playground project. The current test suite provides good foundational coverage but has gaps in critical areas including error handling paths, concurrent operations, and property-based testing. The improvements are organized into four phases, each with clear success criteria and deliverables.

---

## Phase 1: Technical Debt & Coverage Gaps

**Duration:** 1-2 weeks
**Priority:** Critical
**Goal:** Eliminate dead code and achieve baseline coverage on all production modules

### 1.1 Dead Code Elimination

| Item | Action | Rationale |
|------|--------|-----------|
| `app/worker_backup.py` (0% coverage) | Delete or archive | 114 statements with zero tests indicates abandoned code |
| Pydantic v1 `class Config` usage | Migrate to `ConfigDict` | Deprecation warnings will become errors in Pydantic v3 |
| `ast.Num` usage in calculator.py | Replace with `ast.Constant` | Deprecated in Python 3.12, removed in 3.14 |

### 1.2 Critical Coverage Gaps

Target modules requiring immediate attention:

| Module | Current | Target | Missing Lines |
|--------|---------|--------|---------------|
| `app/text_utils.py` | 17.65% | 80% | 9-20, 25-39, 44-53 |
| `app/instance.py` | 40% | 75% | 27-48, 53 |
| `app/db_utils.py` | 54.17% | 80% | 63-92, 146-147, 154-160, 203-222, 241-292, 314-324 |
| `app/main.py` | 51.20% | 65% | 43-47, 54-72, 128-150, 167-211 |

### 1.3 Required Test Additions

```
tests/
├── test_text_utils.py          # NEW: Text processing edge cases
├── test_instance.py            # NEW: Instance lifecycle management
├── test_db_utils_errors.py     # NEW: Database error handling paths
└── test_main_lifecycle.py      # NEW: Application startup/shutdown
```

### Success Criteria - Phase 1

- [ ] `worker_backup.py` removed from codebase or fully tested
- [ ] Zero Pydantic deprecation warnings in test output
- [ ] Zero `ast.Num` deprecation warnings in test output
- [ ] All modules at minimum 50% coverage (current floor)
- [ ] `text_utils.py` coverage ≥ 80%
- [ ] `db_utils.py` coverage ≥ 75%
- [ ] No module with 0% coverage remains in production code

**Verification Command:**
```bash
pytest --cov=app --cov-fail-under=50 -v 2>&1 | grep -E "(PASSED|FAILED|warnings)"
# Expected: 0 deprecation warnings, all tests pass
```

---

## Phase 2: Boundary & Invariant Testing

**Duration:** 2-3 weeks
**Priority:** High
**Goal:** Establish property-based testing and encode critical system invariants

### 2.1 Property-Based Testing Setup

**Dependencies to add:**
```toml
[project.optional-dependencies]
test = [
    # ... existing
    "hypothesis>=6.100.0",
    "hypothesis-jsonschema>=0.23.0",
]
```

### 2.2 Invariants to Encode

#### Task State Machine Invariants

```python
# Allowed state transitions
VALID_TRANSITIONS = {
    "pending": {"running", "failed"},
    "running": {"completed", "failed", "pending"},  # pending = retry
    "completed": set(),  # terminal
    "failed": {"pending"},  # retry allowed
}

# Properties to test:
# 1. No transition to invalid state ever succeeds
# 2. Terminal states cannot transition
# 3. Status timestamp always updates on transition
```

#### Lease System Invariants

```python
# Properties to test:
# 1. lease_timeout > locked_at (always)
# 2. Only one worker can hold a lease at a time
# 3. Expired leases can be claimed by any worker
# 4. try_count monotonically increases per task
# 5. try_count <= max_tries when task is running
```

#### Cost Calculation Invariants

```python
# Properties to test:
# 1. total_cost >= 0 (never negative)
# 2. total_cost = f(input_tokens, output_tokens, model) is deterministic
# 3. Zero tokens → zero cost
# 4. Cost scales linearly with token count
```

#### Workflow Invariants

```python
# Properties to test:
# 1. iteration_count <= max_iterations (always)
# 2. Completed workflow has all subtasks in terminal state
# 3. Parent task cost >= sum(subtask costs)
# 4. Workflow state progression is monotonic (no backward steps)
```

### 2.3 Boundary Test Cases

| Component | Boundary | Test Cases |
|-----------|----------|------------|
| Lease timeout | Exact expiry second | `now == lease_timeout`, `now == lease_timeout + 1ms` |
| Max iterations | Iteration limit | `iteration == max - 1`, `iteration == max`, `iteration == max + 1` |
| Retry count | Max tries | `try_count == max_tries - 1`, `try_count == max_tries` |
| Web search results | Result limits | `max_results == 0`, `max_results == 1`, `max_results == 10`, `max_results == 11` |
| Cost precision | Decimal places | Values requiring >6 decimal places, exactly 6, fewer than 6 |
| Task input size | JSON limits | Empty input `{}`, 1MB input, malformed JSON |

### 2.4 Required Test Files

```
tests/
├── test_invariants/
│   ├── __init__.py
│   ├── test_task_state_machine.py      # State transition properties
│   ├── test_lease_invariants.py        # Lease system properties
│   ├── test_cost_invariants.py         # Cost calculation properties
│   └── test_workflow_invariants.py     # Workflow progression properties
├── test_boundaries/
│   ├── __init__.py
│   ├── test_lease_boundaries.py        # Exact timeout boundaries
│   ├── test_iteration_boundaries.py    # Max iteration edge cases
│   └── test_retry_boundaries.py        # Retry count limits
```

### Success Criteria - Phase 2

- [ ] Hypothesis installed and configured in test suite
- [ ] Minimum 20 property-based tests implemented
- [ ] All state machine transitions have explicit allow/deny tests
- [ ] Lease timeout boundary tests pass with 1-second precision
- [ ] Iteration boundary tests cover `max-1`, `max`, `max+1` cases
- [ ] Cost invariant tests prove non-negativity
- [ ] All boundary tests documented with rationale

**Verification Command:**
```bash
pytest tests/test_invariants tests/test_boundaries -v --hypothesis-show-statistics
# Expected: All properties pass, no counterexamples found
```

---

## Phase 3: Mutation Testing & Fault Injection

**Duration:** 2-3 weeks
**Priority:** Medium-High
**Goal:** Verify test suite catches real bugs through mutation testing and chaos engineering

### 3.1 Mutation Testing Setup

**Dependencies:**
```toml
[project.optional-dependencies]
test = [
    # ... existing
    "mutmut>=2.4.0",
]
```

**Configuration (pyproject.toml):**
```toml
[tool.mutmut]
paths_to_mutate = "app/"
tests_dir = "tests/"
runner = "pytest -x -q"
```

### 3.2 Mutation Testing Targets

Priority modules for mutation testing (high complexity, high risk):

| Module | Reason | Expected Mutation Score |
|--------|--------|-------------------------|
| `app/orchestrator/coordination_strategies.py` | Complex state logic | ≥ 85% |
| `app/worker_lease.py` | Concurrency-critical | ≥ 90% |
| `app/worker.py` | Core business logic | ≥ 80% |
| `app/tools/calculator.py` | Parsing edge cases | ≥ 85% |
| `app/cost_tracking.py` (via tasks.py) | Financial calculations | ≥ 95% |

### 3.3 Known Weak Spots to Strengthen

Based on test structure analysis, likely surviving mutants:

| Location | Mutation Type | Required Test |
|----------|---------------|---------------|
| Error messages | String changes | Assert exact error text |
| Numeric comparisons | `<` → `<=`, `>` → `>=` | Boundary value tests |
| Default values | Value changes | Explicit default verification |
| Boolean conditions | `and` → `or`, negation | Truth table coverage |
| Return values | None → empty, swap returns | Return value assertions |

### 3.4 Fault Injection Tests

#### Database Failures

```python
class TestDatabaseFaultInjection:
    """Test resilience to database failures."""

    async def test_connection_drop_during_task_processing(self):
        """Task should be retryable after connection loss."""

    async def test_transaction_timeout(self):
        """Long-running transactions should not corrupt state."""

    async def test_connection_pool_exhaustion(self):
        """System should degrade gracefully when pool exhausted."""
```

#### Network Failures

```python
class TestNetworkFaultInjection:
    """Test resilience to network failures."""

    async def test_api_timeout_during_agent_call(self):
        """Agent timeout should mark task for retry."""

    async def test_partial_response_handling(self):
        """Incomplete API responses should not corrupt state."""
```

#### Concurrent Operation Failures

```python
class TestConcurrencyFaultInjection:
    """Test resilience to race conditions."""

    async def test_double_claim_same_task(self):
        """Only one worker should succeed in claiming."""

    async def test_lease_renewal_during_expiry(self):
        """Renewal at exact expiry moment should be deterministic."""

    async def test_completion_after_lease_expiry(self):
        """Late completion should not overwrite new owner's work."""
```

### 3.5 Required Test Files

```
tests/
├── test_fault_injection/
│   ├── __init__.py
│   ├── test_database_faults.py
│   ├── test_network_faults.py
│   └── test_concurrency_faults.py
├── mutation_results/          # Generated by mutmut
│   └── .gitkeep
```

### Success Criteria - Phase 3

- [ ] mutmut configured and baseline mutation score recorded
- [ ] `worker_lease.py` mutation score ≥ 90%
- [ ] `coordination_strategies.py` mutation score ≥ 85%
- [ ] Cost calculation mutation score ≥ 95%
- [ ] Overall mutation score ≥ 75%
- [ ] All surviving mutants documented with justification (equivalent mutants, etc.)
- [ ] Database fault injection tests pass
- [ ] Network fault injection tests pass
- [ ] Concurrent fault tests prove deterministic behavior

**Verification Commands:**
```bash
# Run mutation testing
mutmut run --paths-to-mutate=app/worker_lease.py
mutmut results

# Run fault injection
pytest tests/test_fault_injection -v --timeout=30
```

---

## Phase 4: Contract Testing & Integration Hardening

**Duration:** 2-3 weeks
**Priority:** Medium
**Goal:** Establish API contracts and comprehensive integration testing

### 4.1 API Contract Testing

**Dependencies:**
```toml
[project.optional-dependencies]
test = [
    # ... existing
    "schemathesis>=3.25.0",
]
```

#### OpenAPI Schema Validation

```python
# tests/test_api_contracts.py

import schemathesis

schema = schemathesis.from_path("openapi.yaml")

@schema.parametrize()
def test_api_contract(case):
    """All API endpoints conform to OpenAPI spec."""
    response = case.call()
    case.validate_response(response)
```

#### Response Schema Tests

| Endpoint | Contract Assertions |
|----------|---------------------|
| `POST /tasks` | Returns TaskResponse with valid UUID |
| `GET /tasks/{id}` | 404 has standard error schema |
| `PUT /tasks/{id}` | Partial update doesn't null other fields |
| `GET /admin/agents` | List schema matches AgentMetadata[] |
| `GET /costs/summary` | Numeric fields are non-negative |

### 4.2 Integration Test Hardening

#### End-to-End Workflow Tests

```python
class TestCompleteWorkflowE2E:
    """Full workflow execution with real components."""

    async def test_sequential_workflow_happy_path(self):
        """Complete sequential workflow from creation to completion."""

    async def test_iterative_workflow_with_refinement(self):
        """Iterative workflow requiring multiple passes."""

    async def test_workflow_failure_recovery(self):
        """Workflow recovers from transient failures."""

    async def test_workflow_timeout_handling(self):
        """Workflow handles agent timeouts gracefully."""
```

#### Multi-Worker Integration Tests

```python
class TestMultiWorkerIntegration:
    """Tests with multiple concurrent workers."""

    async def test_work_distribution_fairness(self):
        """Tasks distributed roughly evenly across workers."""

    async def test_no_duplicate_processing(self):
        """Same task never processed by multiple workers."""

    async def test_worker_failure_recovery(self):
        """Other workers pick up tasks from failed worker."""
```

### 4.3 Performance Baseline Tests

```python
class TestPerformanceBaselines:
    """Establish and verify performance baselines."""

    @pytest.mark.benchmark
    async def test_task_creation_latency(self, benchmark):
        """Task creation < 50ms p99."""

    @pytest.mark.benchmark
    async def test_task_claim_latency(self, benchmark):
        """Task claim < 100ms p99."""

    @pytest.mark.benchmark
    async def test_registry_lookup_latency(self, benchmark):
        """Registry lookup < 1ms p99."""
```

### 4.4 Required Test Files

```
tests/
├── test_contracts/
│   ├── __init__.py
│   ├── test_api_contracts.py           # OpenAPI conformance
│   ├── test_response_schemas.py        # Response structure validation
│   └── test_error_schemas.py           # Error response consistency
├── test_integration/
│   ├── __init__.py
│   ├── test_workflow_e2e.py            # Full workflow tests
│   ├── test_multi_worker.py            # Concurrent worker tests
│   └── test_performance_baselines.py   # Performance regression tests
├── openapi.yaml                        # API specification (if not exists)
```

### Success Criteria - Phase 4

- [ ] OpenAPI specification exists and is complete
- [ ] All endpoints pass schemathesis validation
- [ ] Error responses have consistent schema across all endpoints
- [ ] E2E workflow tests cover happy path, failure, and timeout scenarios
- [ ] Multi-worker tests prove no duplicate processing
- [ ] Performance baselines established and documented
- [ ] CI pipeline includes contract and performance tests

**Verification Commands:**
```bash
# Contract testing
schemathesis run openapi.yaml --base-url=http://localhost:8000

# Performance baselines
pytest tests/test_integration/test_performance_baselines.py --benchmark-only

# Full integration suite
pytest tests/test_integration tests/test_contracts -v --timeout=120
```

---

## Implementation Tracking

### Phase Summary

| Phase | Duration | Tests Added | Coverage Target | Mutation Target |
|-------|----------|-------------|-----------------|-----------------|
| 1 | 1-2 weeks | ~30 | 80% overall | N/A |
| 2 | 2-3 weeks | ~50 | 82% overall | N/A |
| 3 | 2-3 weeks | ~40 | 85% overall | 75% mutation score |
| 4 | 2-3 weeks | ~30 | 85% overall | 80% mutation score |

### Final Success Metrics

After all phases complete:

| Metric | Current | Target |
|--------|---------|--------|
| Total tests | 362 | ~500+ |
| Line coverage | 78.18% | ≥ 85% |
| Branch coverage | Unknown | ≥ 75% |
| Mutation score | Unknown | ≥ 80% |
| Test execution time | 4.81s | < 10s |
| Deprecation warnings | 131 | 0 |

### CI/CD Integration

```yaml
# .github/workflows/test.yml additions
test:
  steps:
    - name: Unit & Integration Tests
      run: pytest -v --cov=app --cov-fail-under=85

    - name: Property-Based Tests
      run: pytest tests/test_invariants -v --hypothesis-seed=0

    - name: Contract Tests
      run: schemathesis run openapi.yaml --base-url=http://localhost:8000

    - name: Mutation Testing (weekly)
      if: github.event_name == 'schedule'
      run: mutmut run && mutmut results --ci
```

---

## Appendix A: Test File Templates

### Property-Based Test Template

```python
"""Property-based tests for [component]."""

from hypothesis import given, strategies as st, settings, Phase
import pytest

class TestComponentInvariants:
    """Invariant tests for [component]."""

    @given(st.integers(min_value=0, max_value=1000))
    @settings(max_examples=100, phases=[Phase.generate, Phase.target])
    def test_invariant_name(self, value):
        """[Invariant description]."""
        result = component.operation(value)
        assert invariant_holds(result), f"Invariant violated for {value}"
```

### Fault Injection Test Template

```python
"""Fault injection tests for [component]."""

import pytest
from unittest.mock import patch, AsyncMock

class TestComponentFaults:
    """Fault injection tests for [component]."""

    @pytest.mark.asyncio
    async def test_handles_connection_failure(self):
        """[Component] gracefully handles connection failure."""
        with patch('app.database.get_db') as mock_db:
            mock_db.side_effect = ConnectionError("Database unavailable")

            result = await component.operation()

            assert result.status == "retry"
            assert "connection" in result.error.lower()
```

---

## Appendix B: Coverage Gap Details

### `app/db_utils.py` Uncovered Lines Analysis

| Line Range | Function/Block | Risk Level | Test Needed |
|------------|----------------|------------|-------------|
| 63-92 | Error handling for bulk operations | High | Partial failure scenarios |
| 146-147 | Connection retry logic | Medium | Transient failure simulation |
| 154-160 | Transaction rollback | High | Rollback trigger conditions |
| 203-222 | Query timeout handling | Medium | Slow query simulation |
| 241-292 | Batch insert optimization | Low | Large batch edge cases |
| 314-324 | Connection pool management | Medium | Pool exhaustion |

### `app/text_utils.py` Uncovered Lines Analysis

| Line Range | Function | Risk Level | Test Needed |
|------------|----------|------------|-------------|
| 9-20 | Text normalization | Medium | Unicode edge cases |
| 25-39 | Chunk boundary detection | High | Edge cases at boundaries |
| 44-53 | Encoding detection | Medium | Various encodings |

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | Nov 2025 | - | Initial requirements document |
