"""Worker State Machine - Explicit state management for worker lifecycle.

This module provides a formal state machine for managing worker lifecycle,
replacing implicit state management with explicit states, events, and transitions.
"""

import contextlib
import signal
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import Enum

from prometheus_client import Counter, Gauge
from psycopg2.extras import RealDictCursor

from app.config import settings
from app.db_sync import get_connection
from app.instance import get_instance_name
from app.logging_config import get_logger
from app.metrics import active_leases, worker_heartbeat
from app.task_state import TaskStateMachine
from app.worker_helpers import claim_next_task
from app.worker_lease import recover_expired_leases

logger = get_logger(__name__)


# ============================================================================
# State and Event Definitions
# ============================================================================


class WorkerState(Enum):
    """Worker lifecycle states."""

    STARTING = "starting"  # Initializing logging, metrics, tracing
    CONNECTING = "connecting"  # Establishing DB connection
    RUNNING = "running"  # Main loop: poll, delegate to TaskSM, backoff
    RECOVERING = "recovering"  # Checking for expired leases
    BACKING_OFF = "backing_off"  # Sleeping due to no tasks
    SHUTTING_DOWN = "shutting_down"  # Graceful shutdown in progress
    STOPPED = "stopped"  # Terminal state


class WorkerEvent(Enum):
    """Events that trigger worker state transitions."""

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


# ============================================================================
# Transition Table
# ============================================================================

WORKER_TRANSITIONS: dict[tuple[WorkerState, WorkerEvent], WorkerState] = {
    # Startup sequence
    (WorkerState.STARTING, WorkerEvent.INITIALIZED): WorkerState.CONNECTING,
    (WorkerState.CONNECTING, WorkerEvent.CONNECTED): WorkerState.RECOVERING,
    (WorkerState.CONNECTING, WorkerEvent.CONNECTION_FAILED): WorkerState.CONNECTING,  # Retry
    # Main loop
    (WorkerState.RECOVERING, WorkerEvent.RECOVERY_COMPLETE): WorkerState.RUNNING,
    (WorkerState.RUNNING, WorkerEvent.NO_TASKS_AVAILABLE): WorkerState.BACKING_OFF,
    (WorkerState.RUNNING, WorkerEvent.POLL_CYCLE_COMPLETE): WorkerState.RUNNING,  # Continue
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


# ============================================================================
# Context and Exceptions
# ============================================================================


@dataclass
class WorkerContext:
    """Runtime context for worker state machine."""

    connection: object | None = None  # Database connection (type: Connection)
    backoff_count: int = 0
    last_recovery_time: datetime | None = None
    shutdown_requested: bool = False
    current_task_sm: object | None = None  # Active TaskStateMachine (forward ref)
    tasks_processed: int = 0
    tasks_failed: int = 0


class InvalidTransitionError(Exception):
    """Raised when attempting an invalid state transition."""

    def __init__(self, current_state: WorkerState, event: WorkerEvent) -> None:
        """Initialize invalid transition error.

        Args:
            current_state: Current worker state
            event: Event that triggered invalid transition
        """
        self.current_state = current_state
        self.event = event
        super().__init__(
            f"Invalid transition: {current_state.value} + {event.value} (no transition defined)"
        )


# ============================================================================
# Metrics
# ============================================================================

worker_state_gauge = Gauge(
    "worker_state",
    "Current worker state",
    ["worker_id", "state"],
)

worker_state_transitions_total = Counter(
    "worker_state_transitions_total",
    "Worker state transitions",
    ["worker_id", "from_state", "to_state", "event"],
)


# ============================================================================
# Worker State Machine
# ============================================================================


class WorkerStateMachine:
    """State machine for managing worker lifecycle.

    Provides explicit state management with defined transitions, metrics,
    and logging for worker lifecycle events.
    """

    def __init__(self, worker_id: str) -> None:
        """Initialize worker state machine.

        Args:
            worker_id: Unique identifier for this worker
        """
        self.state: WorkerState = WorkerState.STARTING
        self.worker_id = worker_id
        self.context = WorkerContext()

        # Set initial state metric
        worker_state_gauge.labels(worker_id=self.worker_id, state=self.state.value).set(1)

        # Handler dispatch dictionary
        self.handlers = {
            WorkerState.STARTING: self._handle_starting,
            WorkerState.CONNECTING: self._handle_connecting,
            WorkerState.RECOVERING: self._handle_recovering,
            WorkerState.RUNNING: self._handle_running,
            WorkerState.BACKING_OFF: self._handle_backing_off,
            WorkerState.SHUTTING_DOWN: self._handle_shutting_down,
            WorkerState.STOPPED: self._handle_stopped,
        }

    def transition(self, event: WorkerEvent) -> WorkerState:
        """Execute state transition with metrics and logging.

        Args:
            event: Event triggering the transition

        Returns:
            New state after transition

        Raises:
            InvalidTransitionError: If transition is not defined
        """
        # Get target state from transition table
        transition_key = (self.state, event)
        if transition_key not in WORKER_TRANSITIONS:
            # Log invalid transition attempt
            logger.warning(
                "invalid_transition_attempted",
                machine="worker",
                worker_id=self.worker_id,
                current_state=self.state.value,
                event_type=event.value,
                reason="no_transition_defined",
            )
            raise InvalidTransitionError(self.state, event)

        # Execute transition
        old_state = self.state
        new_state = WORKER_TRANSITIONS[transition_key]
        self.state = new_state

        # Update metrics - clear old state, set new state
        worker_state_gauge.labels(worker_id=self.worker_id, state=old_state.value).set(0)
        worker_state_gauge.labels(worker_id=self.worker_id, state=new_state.value).set(1)
        worker_state_transitions_total.labels(
            worker_id=self.worker_id,
            from_state=old_state.value,
            to_state=new_state.value,
            event=event.value,
        ).inc()

        # Log transition
        logger.info(
            "worker_state_transition",
            worker_id=self.worker_id,
            from_state=old_state.value,
            to_state=new_state.value,
            event_type=event.value,
        )

        return new_state

    def can_transition(self, event: WorkerEvent) -> bool:
        """Check if transition is valid.

        Args:
            event: Event to check

        Returns:
            True if transition is valid, False otherwise
        """
        return (self.state, event) in WORKER_TRANSITIONS

    def is_accepting_tasks(self) -> bool:
        """Check if worker should process tasks.

        Returns:
            True if worker is in RUNNING state
        """
        return self.state == WorkerState.RUNNING

    def is_running(self) -> bool:
        """Check if worker is still active.

        Returns:
            True if worker is not in STOPPED state
        """
        return self.state != WorkerState.STOPPED

    # ========================================================================
    # State Handler Methods
    # ========================================================================

    def _handle_starting(self) -> None:
        """Handler for STARTING state.

        Initializes worker logging, metrics, and tracing.
        Transitions to CONNECTING after initialization.
        """
        self._initialize()

    def _handle_connecting(self) -> None:
        """Handler for CONNECTING state.

        Attempts to establish database connection.
        Transitions to RECOVERING on success, retries on failure.
        """
        conn = self._connect()
        if conn:
            self.context.connection = conn
            self.transition(WorkerEvent.CONNECTED)
        else:
            # Connection failed, will retry
            self.transition(WorkerEvent.CONNECTION_FAILED)
            time.sleep(5)

    def _handle_recovering(self) -> None:
        """Handler for RECOVERING state.

        Recovers expired leases from other workers.
        Transitions to RUNNING after recovery complete.
        """
        self._recover(self.context.connection)
        self.transition(WorkerEvent.RECOVERY_COMPLETE)

    def _handle_running(self) -> None:
        """Handler for RUNNING state.

        Polls for and processes tasks.
        Transitions based on task availability.
        """
        # Poll for and process tasks
        task_found = self._poll_and_process(self.context.connection, settings)

        if task_found:
            self.context.tasks_processed += 1
            self.transition(WorkerEvent.POLL_CYCLE_COMPLETE)
            # Sleep briefly to avoid CPU hogging
            time.sleep(0.01)
        else:
            # No tasks available
            self.transition(WorkerEvent.NO_TASKS_AVAILABLE)

    def _handle_backing_off(self) -> None:
        """Handler for BACKING_OFF state.

        Implements exponential backoff when no tasks available.
        Transitions back to RECOVERING after backoff period.
        """
        # Calculate backoff duration
        backoff = min(
            settings.worker_poll_min_interval_seconds
            * (settings.worker_poll_backoff_multiplier**self.context.backoff_count),
            settings.worker_poll_max_interval_seconds,
        )
        self.context.backoff_count += 1

        logger.debug(
            "worker_backing_off",
            worker_id=self.worker_id,
            backoff_duration=backoff,
            backoff_count=self.context.backoff_count,
        )

        time.sleep(backoff)
        self.transition(WorkerEvent.BACKOFF_COMPLETE)

    def _handle_shutting_down(self) -> None:
        """Handler for SHUTTING_DOWN state.

        Handles graceful shutdown of worker.
        Transitions to STOPPED after shutdown complete.
        """
        self._handle_shutdown(self.context.connection)
        self.transition(WorkerEvent.SHUTDOWN_COMPLETE)

    def _handle_stopped(self) -> None:
        """Handler for STOPPED state.

        Terminal state - no action needed.
        Loop will exit via is_running() check.
        """

    # ========================================================================
    # Main Loop
    # ========================================================================

    def run(self) -> None:
        """Main worker loop that processes tasks until shutdown.

        Manages complete worker lifecycle through handler dispatch:
        1. STARTING: Initialize logging/metrics
        2. CONNECTING: Establish DB connection
        3. RECOVERING: Recover expired leases
        4. RUNNING: Poll and process tasks
        5. BACKING_OFF: Wait when no tasks available
        6. SHUTTING_DOWN: Complete active task and cleanup
        7. STOPPED: Exit

        Raises:
            Exception: If critical error occurs during initialization
        """

        # Install signal handlers for graceful shutdown
        def shutdown_handler(signum, _frame):
            logger.info(
                "shutdown_signal_received",
                worker_id=self.worker_id,
                signal=signal.Signals(signum).name,
            )
            self.context.shutdown_requested = True

        signal.signal(signal.SIGTERM, shutdown_handler)
        signal.signal(signal.SIGINT, shutdown_handler)

        # Main loop - pure dispatch
        while self.is_running():
            # Check for shutdown request
            if self.context.shutdown_requested and self.state != WorkerState.SHUTTING_DOWN:
                self.transition(WorkerEvent.SHUTDOWN_REQUESTED)

            # Dispatch to state handler
            try:
                self.handlers[self.state]()
            except Exception as e:
                logger.error(
                    "worker_loop_error",
                    worker_id=self.worker_id,
                    state=self.state.value,
                    error=str(e),
                )
                # Try to reconnect on error
                if self.state in (WorkerState.RUNNING, WorkerState.RECOVERING):
                    try:
                        self.transition(WorkerEvent.ERROR)
                    except InvalidTransitionError:
                        # Can't transition from current state, try shutdown
                        self.context.shutdown_requested = True

        logger.info("worker_stopped", worker_id=self.worker_id)

    # ========================================================================
    # Helper Methods
    # ========================================================================

    def _initialize(self) -> None:
        """Initialize worker in STARTING state."""
        # Note: Imports moved to top-level to avoid PLC0415
        # configure_logging and get_logger are already imported
        # worker_heartbeat is already imported

        logger.info(
            "worker_starting",
            worker_id=self.worker_id,
            instance=get_instance_name(),
        )
        worker_heartbeat.labels(
            service="worker", instance=get_instance_name()
        ).set_to_current_time()

        # Transition to CONNECTING
        self.transition(WorkerEvent.INITIALIZED)

    def _connect(self) -> object | None:
        """Establish database connection.

        Returns:
            Connection object if successful, None if failed
        """
        try:
            conn = get_connection()
            logger.info("worker_db_connected", worker_id=self.worker_id)
            return conn  # type: ignore[no-any-return]

        except Exception as e:
            logger.error(
                "worker_db_connection_failed",
                worker_id=self.worker_id,
                error=str(e),
            )
            return None

    def _recover(self, conn: object) -> None:
        """Recover expired leases from other workers.

        Args:
            conn: Database connection
        """
        recovered = recover_expired_leases(conn, self.worker_id)
        self.context.last_recovery_time = datetime.now(UTC)

        if recovered > 0:
            logger.info(
                "leases_recovered",
                worker_id=self.worker_id,
                count=recovered,
            )

    def _poll_and_process(self, conn: object, settings: object) -> bool:
        """Poll for tasks and process if found.

        Args:
            conn: Database connection
            settings: Application settings

        Returns:
            True if task was found and processed, False otherwise
        """
        # Reset backoff on successful poll
        self.context.backoff_count = 0

        # Update heartbeat
        # Update heartbeat
        worker_heartbeat.labels(
            service="worker", instance=get_instance_name()
        ).set_to_current_time()

        # Create cursor
        cur = conn.cursor(cursor_factory=RealDictCursor)  # type: ignore[attr-defined]

        try:
            # Claim next task
            row = claim_next_task(conn, cur, self.worker_id, settings)

            if not row:
                return False

            # Task found - create state machine and execute
            task_id = str(row["id"])
            task_type = row.get("type") or row.get("agent_type", "unknown")
            source_type = row.get("source_type", "task")

            # Create TaskStateMachine
            task_sm = TaskStateMachine(
                task_id=task_id,
                task_type=task_type,
                worker_id=self.worker_id,
                source_type=source_type,
            )

            # Set as current task
            self.context.current_task_sm = task_sm

            # Execute task through state machine
            result = task_sm.execute(conn)

            # Clear current task
            self.context.current_task_sm = None

            # Update worker metrics
            if result.final_state.value in ("completed", "failed"):
                if result.error:
                    self.context.tasks_failed += 1
                else:
                    # Already incremented in main loop
                    pass

            # Decrement active leases for all tasks
            # Workflow tasks remain in PROCESSING but are handed off to async execution
            # so the worker can continue processing other tasks
            active_leases.labels(worker_id=self.worker_id).dec()

            return True

        finally:
            with contextlib.suppress(Exception):
                cur.close()

    def _handle_shutdown(self, conn: object | None) -> None:
        """Handle graceful shutdown.

        Waits for active task to complete (up to 30s timeout).
        Closes database connection.

        Args:
            conn: Database connection (may be None)
        """
        # Wait for active task to complete (with timeout)
        timeout = 30
        start_time = time.time()

        if self.context.current_task_sm:
            logger.info(
                "shutdown_waiting_for_task",
                worker_id=self.worker_id,
                task_id=self.context.current_task_sm.task_id,  # type: ignore[attr-defined]
            )

            while not self.context.current_task_sm.is_terminal():  # type: ignore[attr-defined]
                if time.time() - start_time > timeout:
                    logger.warning(
                        "shutdown_timeout_exceeded",
                        worker_id=self.worker_id,
                        task_id=self.context.current_task_sm.task_id,  # type: ignore[attr-defined]
                    )
                    break
                time.sleep(0.5)

        # Close connection
        if conn:
            with contextlib.suppress(Exception):
                conn.close()  # type: ignore[attr-defined]
            self.context.connection = None

        logger.info(
            "worker_shutdown_complete",
            worker_id=self.worker_id,
            tasks_processed=self.context.tasks_processed,
            tasks_failed=self.context.tasks_failed,
        )
