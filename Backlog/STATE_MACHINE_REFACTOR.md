Feature: Refactor Worker to Explicit Dual State Machines
Overview
Refactor app/worker.py from implicit control-flow states to two explicit state machines:

WorkerStateMachine: Manages worker process lifecycle (connection, polling, shutdown)
TaskStateMachine: Manages individual task processing lifecycle (claim, process, report)

This separation enables independent testing, clearer invariants, and future concurrency.

Part 1: Worker State Machine
Functional Requirements
FR1.1: Worker States
pythonclass WorkerState(Enum):
    STARTING = "starting"       # Initializing logging, metrics, tracing
    CONNECTING = "connecting"   # Establishing DB connection
    RUNNING = "running"         # Main loop: poll, delegate to TaskSM, backoff
    RECOVERING = "recovering"   # Checking for expired leases
    BACKING_OFF = "backing_off" # Sleeping due to no tasks
    SHUTTING_DOWN = "shutting_down"  # Graceful shutdown in progress
    STOPPED = "stopped"         # Terminal state
FR1.2: Worker Events
pythonclass WorkerEvent(Enum):
    INITIALIZED = "initialized"
    CONNECTED = "connected"
    CONNECTION_FAILED = "connection_failed"
    RECOVERY_COMPLETE = "recovery_complete"
    POLL_CYCLE_COMPLETE = "poll_cycle_complete"
    NO_TASKS_AVAILABLE = "no_tasks_available"
    BACKOFF_COMPLETE = "backoff_complete"
    SHUTDOWN_REQUESTED = "shutdown_requested"
    SHUTDOWN_COMPLETE = "shutdown_complete"
    ERROR = "error"
FR1.3: Worker Transition Table
pythonWORKER_TRANSITIONS: Dict[Tuple[WorkerState, WorkerEvent], WorkerState] = {
    # Startup sequence
    (WorkerState.STARTING, WorkerEvent.INITIALIZED): WorkerState.CONNECTING,
    (WorkerState.CONNECTING, WorkerEvent.CONNECTED): WorkerState.RECOVERING,
    (WorkerState.CONNECTING, WorkerEvent.CONNECTION_FAILED): WorkerState.CONNECTING,  # Retry with backoff

    # Main loop
    (WorkerState.RECOVERING, WorkerEvent.RECOVERY_COMPLETE): WorkerState.RUNNING,
    (WorkerState.RUNNING, WorkerEvent.NO_TASKS_AVAILABLE): WorkerState.BACKING_OFF,
    (WorkerState.RUNNING, WorkerEvent.POLL_CYCLE_COMPLETE): WorkerState.RUNNING,  # Continue polling
    (WorkerState.BACKING_OFF, WorkerEvent.BACKOFF_COMPLETE): WorkerState.RECOVERING,

    # Shutdown from any active state
    (WorkerState.RUNNING, WorkerEvent.SHUTDOWN_REQUESTED): WorkerState.SHUTTING_DOWN,
    (WorkerState.BACKING_OFF, WorkerEvent.SHUTDOWN_REQUESTED): WorkerState.SHUTTING_DOWN,
    (WorkerState.RECOVERING, WorkerEvent.SHUTDOWN_REQUESTED): WorkerState.SHUTTING_DOWN,
    (WorkerState.CONNECTING, WorkerEvent.SHUTDOWN_REQUESTED): WorkerState.SHUTTING_DOWN,
    (WorkerState.SHUTTING_DOWN, WorkerEvent.SHUTDOWN_COMPLETE): WorkerState.STOPPED,

    # Error handling
    (WorkerState.RUNNING, WorkerEvent.ERROR): WorkerState.CONNECTING,  # Reconnect
    (WorkerState.RECOVERING, WorkerEvent.ERROR): WorkerState.CONNECTING,
}
FR1.4: Worker State Machine Class
pythonclass WorkerStateMachine:
    def __init__(self, worker_id: str):
        self.state: WorkerState = WorkerState.STARTING
        self.worker_id = worker_id
        self.context = WorkerContext()

    def transition(self, event: WorkerEvent) -> WorkerState:
        """Execute state transition, emit metrics, return new state."""
        ...

    def can_transition(self, event: WorkerEvent) -> bool:
        """Check if transition is valid."""
        ...

    def is_accepting_tasks(self) -> bool:
        """Returns True if worker should process tasks."""
        return self.state == WorkerState.RUNNING

    def is_running(self) -> bool:
        """Returns True if worker is not stopped."""
        return self.state != WorkerState.STOPPED
FR1.5: Worker Context
python@dataclass
class WorkerContext:
    connection: Optional[Connection] = None
    backoff_count: int = 0
    last_recovery_time: Optional[datetime] = None
    shutdown_requested: bool = False
    current_task_sm: Optional["TaskStateMachine"] = None  # Active task being processed
    tasks_processed: int = 0
    tasks_failed: int = 0
FR1.6: Graceful Shutdown

Signal handlers (SIGTERM, SIGINT) call transition(WorkerEvent.SHUTDOWN_REQUESTED)
SHUTTING_DOWN state waits for context.current_task_sm to reach terminal state
Timeout: 30 seconds, then force stop
Emit shutdown metrics before STOPPED


Part 2: Task State Machine
Functional Requirements
FR2.1: Task States
pythonclass TaskState(Enum):
    PENDING = "pending"         # Task identified, not yet claimed
    CLAIMING = "claiming"       # Attempting to acquire lease
    PROCESSING = "processing"   # Executing task logic
    REPORTING = "reporting"     # Writing results to DB, notifying API
    COMPLETED = "completed"     # Terminal: success
    FAILED = "failed"           # Terminal: error
    ABANDONED = "abandoned"     # Terminal: worker shutdown before completion
FR2.2: Task Events
pythonclass TaskEvent(Enum):
    CLAIM_REQUESTED = "claim_requested"
    CLAIM_SUCCEEDED = "claim_succeeded"
    CLAIM_FAILED = "claim_failed"
    PROCESSING_SUCCEEDED = "processing_succeeded"
    PROCESSING_FAILED = "processing_failed"
    REPORT_SUCCEEDED = "report_succeeded"
    REPORT_FAILED = "report_failed"
    LEASE_EXPIRED = "lease_expired"
    SHUTDOWN_REQUESTED = "shutdown_requested"
FR2.3: Task Transition Table
pythonTASK_TRANSITIONS: Dict[Tuple[TaskState, TaskEvent], TaskState] = {
    # Happy path
    (TaskState.PENDING, TaskEvent.CLAIM_REQUESTED): TaskState.CLAIMING,
    (TaskState.CLAIMING, TaskEvent.CLAIM_SUCCEEDED): TaskState.PROCESSING,
    (TaskState.PROCESSING, TaskEvent.PROCESSING_SUCCEEDED): TaskState.REPORTING,
    (TaskState.REPORTING, TaskEvent.REPORT_SUCCEEDED): TaskState.COMPLETED,

    # Failure paths
    (TaskState.CLAIMING, TaskEvent.CLAIM_FAILED): TaskState.FAILED,
    (TaskState.PROCESSING, TaskEvent.PROCESSING_FAILED): TaskState.REPORTING,  # Report the failure
    (TaskState.REPORTING, TaskEvent.REPORT_FAILED): TaskState.FAILED,  # Log and abandon

    # Lease expiry (detected during processing)
    (TaskState.PROCESSING, TaskEvent.LEASE_EXPIRED): TaskState.ABANDONED,

    # Shutdown interruption
    (TaskState.PROCESSING, TaskEvent.SHUTDOWN_REQUESTED): TaskState.REPORTING,  # Try to report partial
    (TaskState.CLAIMING, TaskEvent.SHUTDOWN_REQUESTED): TaskState.ABANDONED,
}
FR2.4: Task State Machine Class
pythonclass TaskStateMachine:
    def __init__(self, task_id: str, task_type: str, worker_id: str):
        self.state: TaskState = TaskState.PENDING
        self.task_id = task_id
        self.task_type = task_type
        self.worker_id = worker_id
        self.context = TaskContext()

    def transition(self, event: TaskEvent) -> TaskState:
        """Execute state transition, emit metrics, return new state."""
        ...

    def is_terminal(self) -> bool:
        """Returns True if task reached terminal state."""
        return self.state in (TaskState.COMPLETED, TaskState.FAILED, TaskState.ABANDONED)

    def execute(self, conn: Connection) -> TaskResult:
        """
        Run task through state machine to completion.

        Called by WorkerStateMachine when in RUNNING state.
        """
        ...
FR2.5: Task Context
python@dataclass
class TaskContext:
    lease_acquired_at: Optional[datetime] = None
    lease_timeout: Optional[datetime] = None
    input_data: Optional[dict] = None
    output_data: Optional[dict] = None
    error: Optional[str] = None
    cost: Optional[float] = None
    processing_started_at: Optional[datetime] = None
    processing_completed_at: Optional[datetime] = None
FR2.6: Task Result
python@dataclass
class TaskResult:
    task_id: str
    final_state: TaskState
    output: Optional[dict] = None
    error: Optional[str] = None
    cost: Optional[float] = None
    duration_ms: Optional[int] = None

Part 3: Integration
FR3.1: Worker-Task Coordination
python# In WorkerStateMachine.run()
while self.is_running():
    if self.state == WorkerState.RUNNING:
        task_row = claim_next_task(self.context.connection, self.worker_id)
        if task_row:
            task_sm = TaskStateMachine(
                task_id=task_row["id"],
                task_type=task_row["type"],
                worker_id=self.worker_id
            )
            self.context.current_task_sm = task_sm
            result = task_sm.execute(self.context.connection)
            self.context.current_task_sm = None
            self._record_result(result)
            self.transition(WorkerEvent.POLL_CYCLE_COMPLETE)
        else:
            self.transition(WorkerEvent.NO_TASKS_AVAILABLE)
FR3.2: Lease Renewal Integration

renew_lease() called periodically during TaskState.PROCESSING
If renewal fails, emit TaskEvent.LEASE_EXPIRED
Renewal runs in background or between processing chunks

FR3.3: Existing Helper Integration

worker_helpers.py functions called from TaskStateMachine.execute()
worker_lease.py functions called from WorkerStateMachine (recovery) and TaskStateMachine (renewal)
notify_api_async called from TaskStateMachine during REPORTING state


Non-Functional Requirements
NFR1: Cyclomatic Complexity
Function/MethodTargetCurrentWorkerStateMachine.transition()< 5N/A (new)TaskStateMachine.transition()< 5N/A (new)WorkerStateMachine.run()< 1013 (run_worker)TaskStateMachine.execute()< 1020 (_process_task_row)
NFR2: Performance

State transition overhead: < 0.1ms
No additional DB round-trips vs. current implementation
Memory per task: single TaskContext (~500 bytes)

NFR3: Observability
python# Worker metrics
worker_state = Gauge(
    "worker_state",
    "Current worker state",
    ["worker_id", "state"]
)

worker_state_transitions_total = Counter(
    "worker_state_transitions_total",
    "Worker state transitions",
    ["worker_id", "from_state", "to_state", "event"]
)

# Task metrics
task_state_transitions_total = Counter(
    "task_state_transitions_total",
    "Task state transitions",
    ["task_type", "from_state", "to_state", "event"]
)

task_state_duration_seconds = Histogram(
    "task_state_duration_seconds",
    "Time spent in each task state",
    ["task_type", "state"]
)
python# Log events
logger.info("worker_state_transition",
    worker_id=..., from_state=..., to_state=..., event=...)

logger.info("task_state_transition",
    task_id=..., task_type=..., from_state=..., to_state=..., event=...)

logger.warning("invalid_transition_attempted",
    machine=..., current_state=..., event=..., reason=...)
```

Part 4: Wire Up worker.py
Functional Requirements
FR4.1: Replace run_worker() Implementation
python# app/worker.py

from app.worker_state import WorkerStateMachine

def run_worker() -> None:
    """Main entry point for worker process."""
    from app.instance import get_instance_name

    worker_id = get_instance_name()
    state_machine = WorkerStateMachine(worker_id=worker_id)
    state_machine.run()
FR4.2: Deprecate Old Implementation

Rename current run_worker() to run_worker_legacy()
Keep _process_task_row() as _process_task_row_legacy() for reference
Add deprecation comment with removal date

FR4.3: Preserve Entry Points

if __name__ == "__main__" block unchanged
CLI entry points unchanged
Docker entrypoint unchanged


Test Cases
Regression Tests (existing tests must pass)
python# All existing tests in:
# - tests/test_worker.py
# - tests/test_worker_helpers.py
# - tests/test_worker_integration.py (if exists)
Smoke Tests
pythondef test_run_worker_creates_state_machine()
def test_run_worker_uses_instance_name_as_worker_id()
def test_worker_entrypoint_unchanged()

Verification
bash# Full regression
pytest -v

# Complexity check on new worker.py
radon cc app/worker.py -s

# Verify entrypoint works
python -c "from app.worker import run_worker; print('OK')"
```

---

### Files to Modify
```
app/worker.py           # Replace run_worker() implementation
app/worker_backup.py    # Optional: copy old implementation

Verification Criteria

 All existing 452+ tests pass
 New smoke tests pass
 run_worker() delegates to WorkerStateMachine.run()
 Cyclomatic complexity of run_worker() < 3
 No changes to CLI or Docker entrypoints


Part 5: Cleanup (Optional)
After validation period (1 week):

Remove _legacy functions
Remove worker_backup.py
Update documentation

---

## Invariants

**Worker Invariants**
```
W-INV1: Worker in RUNNING has non-null context.connection
W-INV2: Worker in SHUTTING_DOWN does not start new TaskStateMachines
W-INV3: Worker reaches STOPPED within 30s of SHUTDOWN_REQUESTED
W-INV4: Worker in STOPPED has context.connection = None
W-INV5: Only one TaskStateMachine active per worker (context.current_task_sm)
```

**Task Invariants**
```
T-INV1: Task in PROCESSING has context.lease_timeout in future (or within grace period)
T-INV2: Task in PROCESSING has context.lease_acquired_at set
T-INV3: Task in terminal state (COMPLETED, FAILED, ABANDONED) does not transition
T-INV4: Task in REPORTING has either output_data or error set
T-INV5: Task state transitions are atomic (no partial transitions)

Test Cases
Worker State Machine Tests (10 tests)
pythondef test_worker_startup_to_connecting()
def test_worker_connecting_success_to_recovering()
def test_worker_connecting_failure_retries()
def test_worker_recovery_to_running()
def test_worker_running_no_tasks_to_backing_off()
def test_worker_backoff_complete_to_recovering()
def test_worker_shutdown_from_running()
def test_worker_shutdown_from_backing_off()
def test_worker_shutdown_waits_for_active_task()
def test_worker_invalid_transition_raises_error()
Worker Invariant Tests (5 tests)
pythondef test_worker_running_has_connection()
def test_worker_shutting_down_rejects_new_tasks()
def test_worker_shutdown_timeout_forces_stop()
def test_worker_stopped_releases_connection()
def test_worker_single_active_task()
Task State Machine Tests (12 tests)
pythondef test_task_pending_to_claiming()
def test_task_claim_success_to_processing()
def test_task_claim_failure_to_failed()
def test_task_processing_success_to_reporting()
def test_task_processing_failure_to_reporting()
def test_task_reporting_success_to_completed()
def test_task_reporting_failure_to_failed()
def test_task_lease_expired_to_abandoned()
def test_task_shutdown_during_processing()
def test_task_shutdown_during_claiming()
def test_task_is_terminal_completed()
def test_task_invalid_transition_raises_error()
Task Invariant Tests (5 tests)
pythondef test_task_processing_has_valid_lease()
def test_task_processing_has_lease_acquired_time()
def test_task_terminal_state_no_transitions()
def test_task_reporting_has_output_or_error()
def test_task_transitions_are_atomic()
Integration Tests (8 tests)
pythondef test_worker_processes_single_task_to_completion()
def test_worker_processes_failing_task()
def test_worker_recovers_expired_lease_from_other_worker()
def test_worker_graceful_shutdown_completes_active_task()
def test_worker_backoff_increases_on_empty_queue()
def test_task_lease_renewal_during_long_processing()
def test_worker_reconnects_after_db_failure()
def test_notify_api_called_on_task_completion()
Regression Tests
python# All existing tests must pass:
# - tests/test_worker.py
# - tests/test_worker_helpers.py
# - tests/test_tasks.py
```

---

## Files
```
# New files
app/worker_state.py         # WorkerStateMachine, WorkerState, WorkerEvent, WorkerContext
app/task_state.py           # TaskStateMachine, TaskState, TaskEvent, TaskContext, TaskResult
tests/test_worker_state.py  # Worker SM unit tests
tests/test_task_state.py    # Task SM unit tests

# Modified files
app/worker.py               # Refactor to use WorkerStateMachine
app/worker_helpers.py       # May need minor interface adjustments
app/worker_lease.py         # Integrate with TaskStateMachine for renewal
app/metrics.py              # Add new state metrics

# Unchanged
app/worker_backup.py        # Keep as reference/rollback

Verification Criteria

 All existing tests pass (452 tests)
 40 new state machine tests pass
 Cyclomatic complexity targets met (radon cc)
 No new mypy errors
 No new ruff errors
 State metrics visible in Prometheus
 Graceful shutdown completes within 30s
 SIGTERM triggers clean shutdown
 No data loss during shutdown (task either completes or returns to pending)
