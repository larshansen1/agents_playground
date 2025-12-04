I need to improve the testing for the worker_helpers module. Mutant testing has detected quite a few issues. Overall goals is to improve coverage and shore up testing.

Here’s a phased requirements spec for tests for worker_helpers, tuned for AI consumption.

Phase 1 – Basic coverage & happy paths (minimum bar)

Goal: Every main function has at least one realistic, meaningful test.

For each of:

_process_subtask

_process_workflow_task

claim_next_task

the tests must:

Have one happy-path test

Function is called with a plausible row.

No dependencies fail.

Test asserts:

Returned value (if any) is not None and structurally sane.

At least one DB update happened.

Commit was called.

Use realistic data

row includes all fields the function actually reads.

No dummy placeholders like {} if the real code expects structure.

👉 Phase 1 is allowed to be pretty rough; it just guarantees the AI can “see” all main flows.

Phase 2 – State transitions & error handling (behavioral bar)

Goal: Tests pin down what must happen to tasks/subtasks in success vs failure.

_process_subtask tests MUST:

Success test

Assert final subtask status (e.g. done).

Assert parent task status is set as expected (e.g. still running or done).

Assert agent + orchestrator were called (no details yet, just that they were used).

Failure test (agent or orchestrator error)

Cause a controlled exception in agent/orchestrator.

Assert:

subtask ends in an error-like status,

parent task ends in an error-like or degraded status (whatever your rule is).

_process_workflow_task tests MUST:

Success test

Assert task status moves to a “started/running” or equivalent status.

Assert an orchestrator was created and invoked.

Failure test

Simulate bad workflow type or orchestrator failure.

Assert task ends in an error-like status.

claim_next_task tests MUST:

Subtask-first test

Scenario where both a claimable subtask and task exist.

Assert:

returned object is the subtask,

subtask got its status updated (e.g. to running).

Task fallback test

Scenario with no claimable subtasks but a claimable task.

Assert:

returned object is the task,

task got its status updated.

None test

Scenario with nothing claimable.

Assert:

function returns None,

no updates executed.

👉 After Phase 2, success vs failure behavior is nailed down at a high level.

Phase 3 – Edge cases, retries & leases (robustness bar)

Goal: Tests protect the critical scheduling semantics from regressing.

claim_next_task edge tests MUST:

Respects max_tries

Have a row with try_count == max_tries.

Assert it is not returned.

If it’s the only candidate, function returns None.

Respects leases

Have a row that looks “leased” (e.g. active leased_until / running status).

Assert it is not returned.

Updates key fields on claim

For a claimed row (subtask or task), assert:

status changed (e.g. to running),

worker_id set,

try_count incremented.

_process_subtask / _process_workflow_task edge tests MUST:

Cost / usage handling

When the agent returns usage / cost, assert it is written somewhere (task, subtask, workflow).

Distinct parent vs child updates

In an error scenario, assert that both:

the subtask row,

and the parent task row
are updated as per your rules (not just “something with status='error' happened”).

👉 After Phase 3, the main invariants around retries, leases, and parent/child behavior are guarded.

Phase 4 – Safety metrics (for this file only)

Once Phases 1–3 are satisfied:

Coverage target (local to this file)

Line coverage for worker_helpers.py ≥ 85%.

Each main branch in the three functions is exercised by at least one test (happy / error / edge).
