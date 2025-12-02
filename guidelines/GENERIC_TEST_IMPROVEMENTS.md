# Generic Test Improvement Guidelines (Mutation Testing)

## Context
```
Module: {module_path}
Current coverage: {X}%
Surviving mutants: {N}
Goal: Kill semantically meaningful mutants, ignore syntactic noise
```

---

## Phase 1: Foundation (Happy Paths)

**Goal:** Every exported function has at least one realistic test.

For each public function:
- One happy-path test with realistic input data
- Assertions on:
  - Return value structure (not just `is not None`)
  - Side effects occurred (DB writes, API calls, state changes)
  - Commits/flushes happened if transactional

**Anti-patterns to avoid:**
- Empty dicts `{}` when code expects structure
- Asserting only that "something was called" without checking what

---

## Phase 2: State Transitions & Error Handling

**Goal:** Pin down what MUST happen in success vs failure.

For each function, create paired tests:

**Success test MUST assert:**
- Final state of primary entity (status, output fields)
- Final state of related entities (parent/child relationships)
- Correct collaborators were invoked

**Failure test MUST assert:**
- Controlled exception in dependency
- Primary entity ends in error state with message
- Related entities updated appropriately
- Error notification/logging occurred

---

## Phase 3: Edge Cases & Invariants

**Goal:** Protect critical business rules from regression.

Identify and test invariants:
- **Retry semantics:** `try_count < max_tries` respected
- **Lease/lock semantics:** expired leases allow reclaim, active leases block
- **Parent/child consistency:** both updated on failure, correct propagation
- **Resource tracking:** costs, tokens, usage written to correct fields

For each invariant:
- Test the boundary condition
- Test violation is handled correctly

---

## Phase 4: Quality Gates

**Coverage:** ≥ 85% line coverage for the module

**Mutation score:** 0 survivors in covered code (untested is acceptable if mocked)

**Explicitly document:**
- Lines intentionally uncovered (and why)
- Invariants now guaranteed by tests

---

## Mutation Categories

**Kill these (semantic):**
- Conditional flips (`==` → `!=`)
- State transitions (`status = 'done'` → `status = 'error'`)
- Return value changes
- Error handling removal

**Ignore these (syntactic noise):**
- Log message string changes
- Metric label changes
- Decorator removal (tracing, timing)
- String formatting in non-user-facing code

---

## Output Format

After improvements, document:

```markdown
## Test Summary: {module_name}

**Coverage:** {before}% → {after}%
**Tests:** {count} tests covering {behaviors}
**Uncovered:** {lines} - {reason}

### Invariants Guaranteed:
1. {invariant_1}
2. {invariant_2}
```

---

## Refactorability Notes

**Choose test style based on module layer:**

| Layer | Style | Example |
|-------|-------|---------|
| Business logic | Assert on outputs | `assert result["cost"] == 12.50` |
| Orchestration | Assert at boundaries | `mock_notifier.assert_called_with(...)` |
| Data access | Assert on SQL (intentional coupling) | `assert "status = 'done'" in sql` |

**Default to behavioral tests** (assert on outputs/boundaries). Only assert on implementation details (SQL strings, internal calls) when:

1. The implementation IS the contract (lease logic, retry semantics)
2. The module is expected to be stable
3. You document it: *"These tests are intentionally coupled to SQL structure"*

**Quick check:** If you renamed a column, should tests break?
- Business logic: No
- Data access layer: Yes (that's the point)
