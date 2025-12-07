# Workflow: Refactor to State Machine

## Purpose

Convert code with implicit state management (nested conditionals, mode flags, status strings) into an explicit state machine with handler dispatch pattern. If provided code file is already in a state machine format, then make sure the state machine is refactored to use the instruction in this workflow.
## Trigger

Use this workflow when:
- Function cyclomatic complexity > 10 with state-like behavior
- Code has comments indicating states ("now polling", "connecting phase")
- Multiple boolean flags controlling behavior
- `if status == "..."` or `if mode == "..."` patterns
- Nested try/catch with different recovery paths

## Prerequisites

- [ ] Existing code with implicit states identified
- [ ] Existing tests for current behavior (baseline)
- [ ] Understanding of current state transitions (may need documentation)

---

## Phase 1: Document Current States

### Actions

1. **Read existing code** and identify implicit states:
   - Look for comments indicating phases
   - Look for mode/status variables
   - Look for conditional branches that represent different behaviors
   - Look for error recovery that changes behavior

2. **Create state documentation:**
   ```markdown
   ## Identified States

   | State Name | Code Signal | Description |
   |------------|-------------|-------------|
   | STARTING | Before main loop | Initializing |
   | CONNECTING | `conn = None` | Establishing connection |
   | RUNNING | Inside `while True` | Processing tasks |
   | ... | ... | ... |
   ```

3. **Document transitions:**
   ```markdown
   ## Identified Transitions

   | From | Trigger | To |
   |------|---------|-----|
   | STARTING | Initialization complete | CONNECTING |
   | CONNECTING | Connection success | RUNNING |
   | CONNECTING | Connection failure | CONNECTING (retry) |
   | ... | ... | ... |
   ```

4. **Identify invariants:**
   ```markdown
   ## Invariants

   - When processing, connection must be valid
   - When shutting down, no new tasks accepted
   - ...
   ```

### Output

State machine documentation file: `docs/STATE_MACHINE_{component}.md`

### Verification Gate

- [ ] All states identified and documented
- [ ] All transitions identified and documented
- [ ] Invariants identified

---

## Phase 2: Create Requirements Specification

### Actions

1. Create formal requirements using `refine_requirements` workflow output format
2. Include:
   - State enum with all identified states
   - Event enum with all triggers
   - Complete transition table
   - All invariants
   - Handler dispatch requirement

### Template

```markdown
# Feature: Refactor {Component} to State Machine

## Overview
Replace implicit state management in {component} with explicit state machine.

## State Machine: {Component}StateMachine

### States
- STATE_A: [description]
- STATE_B: [description]
- ... (from Phase 1 documentation)

### Events
- EVENT_X: [trigger description]
- EVENT_Y: [trigger description]
- ...

### Transitions
(Complete table from Phase 1)

### Invariants
- INV1: [from Phase 1]
- INV2: [from Phase 1]
- ...

### Implementation Constraint
Handler dispatch pattern required.
Main loop cyclomatic complexity < 5.

## Test Cases

### Transition Tests
- test_state_a_event_x_to_state_b
- ... (one per transition)

### Invariant Tests
- test_inv1_{description}
- ... (one per invariant)

### Structural Tests
- test_all_states_have_handlers
- test_handler_naming_convention
- test_run_dispatch_complexity

### Regression Tests
- All existing tests must pass
```

### Output

Requirements document: `docs/requirements/{component}_state_machine.md`

### Verification Gate

- [ ] Requirements follow SDD format
- [ ] Every state has clear description
- [ ] Every transition documented
- [ ] Handler dispatch constraint included

---

## Phase 3: Implement State Machine (Isolated)

### Actions

1. Create new file for state machine (do NOT modify original yet)
2. Implement:
   - State enum
   - Event enum
   - Transition table
   - Context dataclass
   - State machine class with:
     - `__init__` with handler dictionary
     - `transition()` method
     - `can_transition()` method
     - Handler methods (one per state)
     - Main loop using handler dispatch

### Handler Dispatch Structure

```python
class {Component}StateMachine:
    def __init__(self, ...):
        self.state = {State}.STARTING
        self.handlers = {
            {State}.STARTING: self._handle_starting,
            {State}.CONNECTING: self._handle_connecting,
            {State}.RUNNING: self._handle_running,
            # ... all states
        }

    def run(self) -> None:
        """Main loop - pure dispatch only."""
        while self.is_running():
            if self.context.shutdown_requested:
                self._request_shutdown()
            self.handlers[self.state]()

    def _handle_starting(self) -> None:
        """Handler for STARTING state."""
        # Logic extracted from original code
        self.transition({Event}.INITIALIZED)

    # ... handler for each state
```

### Constraints

- New file only, do NOT touch original code
- No integration yet (dependencies stubbed/injected)
- Each handler corresponds to one state
- Main loop is pure dispatch

### Files Created

```
app/{component}_state.py
```

### Verification Gate

```bash
# Type checking
mypy app/{component}_state.py

# Complexity check - main loop must be < 5
radon cc app/{component}_state.py -s | grep "run"

# Verify handler dispatch (no elif chains)
# Manual review or AST-based test

# Import test
python -c "from app.{component}_state import *; print('OK')"
```

**Critical:** If `run()` CC > 5, refactor before proceeding.

---

## Phase 4: Implement State Machine Tests

### Actions

1. Create test file
2. Implement:
   - Transition tests (one per transition in table)
   - Invalid transition test
   - Invariant tests (one per invariant)
   - Structural tests:
     - `test_all_states_have_handlers`
     - `test_handler_naming_convention`
     - `test_run_dispatch_complexity`

### Structural Test Templates

```python
def test_all_states_have_handlers():
    """Every state must have a handler."""
    sm = {Component}StateMachine(...)
    for state in {State}:
        assert state in sm.handlers, f"Missing handler for {state}"
        assert callable(sm.handlers[state])

def test_handler_naming_convention():
    """Handlers must follow _handle_{state} naming."""
    sm = {Component}StateMachine(...)
    for state, handler in sm.handlers.items():
        expected = f"_handle_{state.name.lower()}"
        assert handler.__name__ == expected, (
            f"Handler for {state} named {handler.__name__}, expected {expected}"
        )

def test_run_dispatch_complexity():
    """run() must use dispatch, not elif chains."""
    import ast
    import inspect

    source = inspect.getsource({Component}StateMachine.run)
    tree = ast.parse(source)

    if_count = sum(1 for n in ast.walk(tree) if isinstance(n, ast.If))
    assert if_count <= 2, (
        f"run() has {if_count} conditionals. "
        "Expected <= 2 (shutdown check only). "
        "Use handler dispatch pattern."
    )
```

### Files Created

```
tests/test_{component}_state.py
```

### Verification Gate

```bash
# All state machine tests pass
pytest tests/test_{component}_state.py -v

# Structural tests specifically
pytest tests/test_{component}_state.py -v -k "handler"
```

**Gate Rule:** All tests pass, including structural tests, before proceeding.

---

## Phase 5: Integrate with Existing Code

### Actions

1. Implement handler bodies with real logic:
   - Extract logic from original code into handlers
   - Wire up dependencies (DB, helpers, etc.)
   - Add observability (metrics, logs)

2. Keep original code intact for now

### Constraints

- Original file unchanged (can still roll back)
- Handler logic extracted, not duplicated
- All existing tests still pass

### Files Modified

```
app/{component}_state.py    # Add real logic to handlers
```

### Verification Gate

```bash
# State machine tests still pass
pytest tests/test_{component}_state.py -v

# Existing tests still pass
pytest tests/test_{component}.py -v

# Complexity still OK
radon cc app/{component}_state.py -s -n C
```

---

## Phase 6: Wire Up Entry Point

### Actions

1. Modify original module to use state machine:
   ```python
   # app/{component}.py

   from app.{component}_state import {Component}StateMachine

   def run_{component}() -> None:
       """Entry point - delegates to state machine."""
       sm = {Component}StateMachine(...)
       sm.run()

   # Keep old implementation for rollback
   def run_{component}_legacy() -> None:
       """Legacy implementation - remove after validation."""
       # ... original code
   ```

2. Update any callers to use new function (if interface unchanged, this is automatic)

### Files Modified

```
app/{component}.py    # Wire up state machine
```

### Verification Gate

```bash
# Full test suite passes
pytest tests/ -v

# Entry point works
python -c "from app.{component} import run_{component}; print('OK')"

# Original can still be called (rollback ready)
python -c "from app.{component} import run_{component}_legacy; print('OK')"
```

---

## Phase 7: Cleanup (After Validation)

### Timing

After 1 week successful operation:

### Actions

1. Remove `_legacy` functions
2. Remove old implementation code
3. Update documentation
4. Optionally merge `{component}_state.py` into `{component}.py`

### Verification Gate

```bash
# Full test suite
pytest tests/ -v

# No legacy references
grep -r "_legacy" app/  # Should return nothing
```

---

## Complexity Comparison

After refactoring, compare:

```bash
# Before (original)
radon cc app/{component}_original.py -s -a

# After (state machine)
radon cc app/{component}_state.py -s -a
```

**Expected improvement:**
- Individual functions: CC < 10 (down from > 10)
- `run()` method: CC < 5
- Average complexity: significant reduction

---

## Rollback Procedure

If issues discovered:

1. Revert entry point to use `_legacy` function
2. Investigate issues with state machine
3. Fix and re-validate
4. Re-enable state machine

Keep `_legacy` code until confident in new implementation.
