"""Task State Machine - Explicit state management for task lifecycle.

This module provides a formal state machine for managing task lifecycle,
replacing implicit state management with explicit states, events, and transitions.
"""

import contextlib
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from typing import Any

from prometheus_client import Counter, Histogram
from psycopg2.extras import Json, RealDictCursor

from app.agents import get_agent
from app.api_client import notify_api_async
from app.audit import log_audit_event
from app.config import settings
from app.logging_config import get_logger
from app.orchestrator import (
    extract_agent_type,
    extract_tool_type,
    extract_workflow_type,
    get_orchestrator,
    is_agent_task,
    is_tool_task,
    is_workflow_task,
)
from app.tasks import execute_task
from app.tools.registry_init import tool_registry
from app.trace_utils import extract_trace_context
from app.worker_helpers import _process_subtask

logger = get_logger(__name__)


# ============================================================================
# State and Event Definitions
# ============================================================================


class TaskState(Enum):
    """Task lifecycle states."""

    PENDING = "pending"  # Task identified, not yet claimed
    CLAIMING = "claiming"  # Attempting to acquire lease
    PROCESSING = "processing"  # Executing task logic
    REPORTING = "reporting"  # Writing results to DB, notifying API
    COMPLETED = "completed"  # Terminal: success
    FAILED = "failed"  # Terminal: error
    ABANDONED = "abandoned"  # Terminal: worker shutdown before completion


class TaskEvent(Enum):
    """Events that trigger task state transitions."""

    CLAIM_REQUESTED = "claim_requested"
    CLAIM_SUCCEEDED = "claim_succeeded"
    CLAIM_FAILED = "claim_failed"
    PROCESSING_SUCCEEDED = "processing_succeeded"
    PROCESSING_FAILED = "processing_failed"
    REPORT_SUCCEEDED = "report_succeeded"
    REPORT_FAILED = "report_failed"
    LEASE_EXPIRED = "lease_expired"
    SHUTDOWN_REQUESTED = "shutdown_requested"


# ============================================================================
# Transition Table
# ============================================================================

TASK_TRANSITIONS: dict[tuple[TaskState, TaskEvent], TaskState] = {
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
    (
        TaskState.PROCESSING,
        TaskEvent.SHUTDOWN_REQUESTED,
    ): TaskState.REPORTING,  # Try to report partial
    (TaskState.CLAIMING, TaskEvent.SHUTDOWN_REQUESTED): TaskState.ABANDONED,
}


# ============================================================================
# Context and Result Classes
# ============================================================================


@dataclass
class TaskContext:
    """Runtime context for task state machine."""

    lease_acquired_at: datetime | None = None
    lease_timeout: datetime | None = None
    input_data: dict | None = None
    output_data: dict | None = None
    error: str | None = None
    cost: float | None = None
    processing_started_at: datetime | None = None
    processing_completed_at: datetime | None = None


@dataclass
class TaskResult:
    """Result of task execution."""

    task_id: str
    final_state: TaskState
    output: dict | None = None
    error: str | None = None
    cost: float | None = None
    duration_ms: int | None = None


# ============================================================================
# Exception Classes
# ============================================================================


class InvalidTransitionError(Exception):
    """Raised when attempting an invalid state transition."""

    def __init__(self, current_state: TaskState, event: TaskEvent) -> None:
        """Initialize invalid transition error.

        Args:
            current_state: Current task state
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

task_state_transitions_total = Counter(
    "task_state_transitions_total",
    "Task state transitions",
    ["task_type", "from_state", "to_state", "event"],
)

task_state_duration_seconds = Histogram(
    "task_state_duration_seconds",
    "Time spent in each task state",
    ["task_type", "state"],
)


# ============================================================================
# Task State Machine
# ============================================================================


class TaskStateMachine:
    """State machine for managing task lifecycle.

    Provides explicit state management with defined transitions, metrics,
    and logging for task lifecycle events.
    """

    def __init__(
        self, task_id: str, task_type: str, worker_id: str, source_type: str = "task"
    ) -> None:
        """Initialize task state machine.

        Args:
            task_id: Unique identifier for this task
            task_type: Type of task being processed
            worker_id: ID of worker processing this task
            source_type: Type of source (task or subtask)
        """
        self.state: TaskState = TaskState.PENDING
        self.task_id = task_id
        self.task_type = task_type
        self.worker_id = worker_id
        self.source_type = source_type
        self.context = TaskContext()

    def transition(self, event: TaskEvent) -> TaskState:
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
        if transition_key not in TASK_TRANSITIONS:
            # Log invalid transition attempt
            logger.warning(
                "invalid_transition_attempted",
                machine="task",
                task_id=self.task_id,
                task_type=self.task_type,
                current_state=self.state.value,
                event_type=event.value,
                reason="no_transition_defined",
            )
            raise InvalidTransitionError(self.state, event)

        # Execute transition
        old_state = self.state
        new_state = TASK_TRANSITIONS[transition_key]
        self.state = new_state

        # Update metrics
        task_state_transitions_total.labels(
            task_type=self.task_type,
            from_state=old_state.value,
            to_state=new_state.value,
            event=event.value,
        ).inc()

        # Log transition
        logger.info(
            "task_state_transition",
            task_id=self.task_id,
            task_type=self.task_type,
            from_state=old_state.value,
            to_state=new_state.value,
            event_type=event.value,
        )

        return new_state

    def is_terminal(self) -> bool:
        """Check if task has reached a terminal state.

        Returns:
            True if task is in COMPLETED, FAILED, or ABANDONED state
        """
        return self.state in (TaskState.COMPLETED, TaskState.FAILED, TaskState.ABANDONED)

    def execute(self, conn: object) -> TaskResult:
        """Run task through state machine to completion.

        Called by WorkerStateMachine when in RUNNING state.

        Args:
            conn: Database connection

        Returns:
            TaskResult with execution outcome
        """
        # Initialize timing
        start_time = time.time()
        self.context.processing_started_at = datetime.now(UTC)

        try:
            # State: PENDING → CLAIMING
            if not self._claim_lease(conn):
                # Lease claim failed
                duration_ms = int((time.time() - start_time) * 1000)
                return TaskResult(
                    task_id=self.task_id,
                    final_state=TaskState.FAILED,
                    error="Failed to acquire task lease",
                    duration_ms=duration_ms,
                )

            # State: CLAIMING → PROCESSING
            # Execute task processing
            success = self._execute_processing(conn)

            # Special handling for workflow tasks which are async
            if success and is_workflow_task(self.task_type):
                # Async workflow started, return result in current state (PROCESSING)
                # Do not transition to REPORTING/COMPLETED
                self.context.processing_completed_at = datetime.now(UTC)
                duration_ms = int((time.time() - start_time) * 1000)

                return TaskResult(
                    task_id=self.task_id,
                    final_state=self.state,
                    output=self.context.output_data,
                    error=None,
                    cost=0,
                    duration_ms=duration_ms,
                )

            # Special handling for subtasks (fully handled in _execute_processing)
            if self.source_type == "subtask":
                self.context.processing_completed_at = datetime.now(UTC)
                duration_ms = int((time.time() - start_time) * 1000)

                final_state = TaskState.COMPLETED if success else TaskState.FAILED
                if success:
                    self.transition(TaskEvent.PROCESSING_SUCCEEDED)
                    self.transition(TaskEvent.REPORT_SUCCEEDED)
                else:
                    self.transition(TaskEvent.PROCESSING_FAILED)
                    self.transition(TaskEvent.REPORT_FAILED)

                return TaskResult(
                    task_id=self.task_id,
                    final_state=final_state,
                    output=self.context.output_data,
                    error=self.context.error,
                    cost=self.context.cost,
                    duration_ms=duration_ms,
                )

            # State: PROCESSING → REPORTING
            # Report results to database
            if self._report_results(conn, success):
                # State: REPORTING → COMPLETED or FAILED
                if success:
                    self.transition(TaskEvent.REPORT_SUCCEEDED)
                else:
                    # Report succeeded but task failed
                    self.transition(TaskEvent.REPORT_SUCCEEDED)
            else:
                # Reporting failed
                self.transition(TaskEvent.REPORT_FAILED)

        except Exception as e:
            # Unexpected error during execution
            logger.error(
                "task_execution_error",
                task_id=self.task_id,
                task_type=self.task_type,
                error=str(e),
            )
            self.context.error = str(e)
            # Try to report the error, suppressing any exceptions during reporting
            with contextlib.suppress(Exception):
                self._report_results(conn, success=False)
                self.transition(TaskEvent.REPORT_SUCCEEDED)
            # If reporting itself failed (i.e., an exception was suppressed),
            # we still want to transition to REPORT_FAILED if possible.
            # This is implicitly handled by the state not changing to REPORT_SUCCEEDED
            # if an exception occurred and was suppressed.
            # The final state will reflect the last successful transition or the initial state.
            # However, to explicitly ensure a failed report state if the attempt failed:
            if self.state not in (TaskState.COMPLETED, TaskState.FAILED):
                with contextlib.suppress(InvalidTransitionError):
                    self.transition(TaskEvent.REPORT_FAILED)

        # Calculate final duration
        self.context.processing_completed_at = datetime.now(UTC)
        duration_ms = int((time.time() - start_time) * 1000)

        # Return result
        return TaskResult(
            task_id=self.task_id,
            final_state=self.state,
            output=self.context.output_data,
            error=self.context.error,
            cost=self.context.cost,
            duration_ms=duration_ms,
        )

    def _claim_lease(self, _conn: object) -> bool:
        """Claim task lease and transition to CLAIMING state.

        Args:
            conn: Database connection

        Returns:
            True if lease claimed successfully, False otherwise
        """

        try:
            # Transition to CLAIMING
            self.transition(TaskEvent.CLAIM_REQUESTED)

            # Calculate lease timeout
            now = datetime.now(UTC)
            lease_duration = timedelta(seconds=settings.worker_lease_duration_seconds)
            self.context.lease_acquired_at = now
            self.context.lease_timeout = now + lease_duration

            # Lease is already acquired by claim_next_task in worker
            # Just mark it in context
            self.transition(TaskEvent.CLAIM_SUCCEEDED)
            return True

        except Exception as e:
            logger.error(
                "lease_claim_failed",
                task_id=self.task_id,
                task_type=self.task_type,
                error=str(e),
            )
            with contextlib.suppress(InvalidTransitionError):
                self.transition(TaskEvent.CLAIM_FAILED)
            return False

    def _execute_subtask_processing(self, conn: Any, cur: Any) -> bool:
        """Execute subtask processing logic."""
        # Fetch subtask data
        cur.execute(
            "SELECT id, parent_task_id, agent_type, input, iteration FROM subtasks WHERE id = %s",
            (self.task_id,),
        )
        row = cur.fetchone()
        if not row:
            msg = f"Subtask {self.task_id} not found"
            raise ValueError(msg)

        try:
            _process_subtask(conn, cur, row)
        except Exception as e:
            self.context.error = str(e)
            return False

        # Check status from DB
        cur.execute(
            "SELECT status, error, output, total_cost FROM subtasks WHERE id = %s", (self.task_id,)
        )
        status_row = cur.fetchone()
        if status_row:
            if status_row["status"] == "error":
                self.context.error = status_row.get("error")
                return False
            if status_row["status"] == "done":
                self.context.output_data = status_row.get("output")
                self.context.cost = status_row.get("total_cost", 0)
                return True
        return False

    def _execute_processing(self, conn: object) -> bool:
        """Execute task processing logic.

        Routes to appropriate handler based on task type:
        - workflow:* -> _process_workflow_task_execution
        - agent:* -> _process_agent_task_execution
        - subtask -> _execute_subtask_processing
        - regular tasks -> execute_task

        Args:
            conn: Database connection

        Returns:
            True if processing succeeded, False if it failed
        """

        cur = conn.cursor(cursor_factory=RealDictCursor)  # type: ignore[attr-defined]

        if self.source_type == "subtask":
            return self._execute_subtask_processing(conn, cur)

        try:
            # Fetch task data from database
            cur.execute(
                "SELECT input, type FROM tasks WHERE id = %s",
                (self.task_id,),
            )
            row = cur.fetchone()
            if not row:
                msg = f"Task {self.task_id} not found"
                raise ValueError(msg)

            task_input = row["input"]
            trace_ctx, cleaned_input = extract_trace_context(task_input)
            self.context.input_data = cleaned_input

            # Mark as running in DB
            cur.execute(
                "UPDATE tasks SET status = 'running', updated_at = now() WHERE id = %s",
                (self.task_id,),
            )
            conn.commit()  # type: ignore[attr-defined]

            # Notify API (best-effort)
            # Notify API (best-effort)
            notify_api_async(self.task_id, "running")

            # Extract user_id_hash for audit
            user_id_hash = cleaned_input.pop("_user_id_hash", None)

            # Audit log: Task started
            log_audit_event(
                conn,  # type: ignore[arg-type]
                "task_started",
                resource_id=self.task_id,
                user_id_hash=user_id_hash,
                meta={"task_type": self.task_type},
            )
            conn.commit()  # type: ignore[attr-defined]

            # Route to appropriate execution handler based on task type
            if is_workflow_task(self.task_type):
                # Workflow tasks are handled asynchronously via orchestrator
                # They create subtasks and complete later via process_subtask_completion
                result = self._process_workflow_task_execution(
                    conn, cur, task_input, cleaned_input, user_id_hash
                )
            elif is_agent_task(self.task_type):
                # Agent tasks execute directly
                result = self._process_agent_task_execution(cleaned_input, user_id_hash)
            elif is_tool_task(self.task_type):
                # Tool tasks execute directly
                result = self._process_tool_task_execution(cleaned_input, user_id_hash)
            else:
                # Regular tasks use execute_task
                result = execute_task(self.task_type, cleaned_input, user_id_hash)

            # Handle result format
            if isinstance(result, dict) and "usage" in result:
                self.context.output_data = result["output"]
                usage = result["usage"]
                self.context.cost = usage.get("total_cost", 0) if usage else 0
            else:
                self.context.output_data = result
                usage = None

            # Store usage for reporting
            self.context._usage = usage  # type: ignore
            self.context._user_id_hash = user_id_hash  # type: ignore

            # Transition to reporting (unless async workflow)
            if not is_workflow_task(self.task_type):
                self.transition(TaskEvent.PROCESSING_SUCCEEDED)
            return True

        except Exception as e:
            # Processing failed
            self.context.error = str(e)
            self.context._user_id_hash = locals().get("user_id_hash")  # type: ignore

            logger.error(
                "task_processing_failed",
                task_id=self.task_id,
                task_type=self.task_type,
                error=str(e),
            )

            with contextlib.suppress(InvalidTransitionError):
                self.transition(TaskEvent.PROCESSING_FAILED)

            return False
        finally:
            cur.close()

    def _process_agent_task_execution(self, cleaned_input: dict, user_id_hash: str | None) -> dict:
        """Execute an agent task directly.

        Args:
            cleaned_input: Task input with trace context removed
            user_id_hash: User ID hash for tracking

        Returns:
            Result dict with output and usage
        """

        agent_type = extract_agent_type(self.task_type)
        agent = get_agent(agent_type)
        return agent.execute(cleaned_input, user_id_hash)

    def _process_tool_task_execution(
        self,
        cleaned_input: dict,
        user_id_hash: str | None = None,  # noqa: ARG002
    ) -> dict:
        """Execute a tool task directly.

        Args:
            cleaned_input: Task input with trace context removed
            user_id_hash: User ID hash for tracking

        Returns:
            Result dict with output and usage
        """
        tool_name = extract_tool_type(self.task_type)
        tool = tool_registry.get(tool_name)

        # Execute tool
        result = tool.execute(**cleaned_input)

        # Tools currently don't track usage/cost, return simple format
        return {
            "output": result,
            "usage": None,
        }

    def _process_workflow_task_execution(
        self,
        conn: Any,
        _cur: Any,
        task_input: dict,
        cleaned_input: dict,
        user_id_hash: str | None,
    ) -> dict:
        """Initialize a workflow task by delegating to orchestrator.

        Workflows are processed asynchronously via subtasks.
        This method initializes the workflow and returns immediately.

        Args:
            conn: Database connection
            cur: Database cursor
            task_input: Original task input (with trace context)
            cleaned_input: Task input with trace context removed
            user_id_hash: User ID hash for tracking

        Returns:
            Empty result dict (workflow completion happens via subtasks)
        """
        tenant_id = cleaned_input.pop("_tenant_id", None)
        workflow_type = extract_workflow_type(self.task_type)
        orchestrator = get_orchestrator(workflow_type)

        # Initialize workflow - creates subtasks asynchronously
        # Pass original task_input to preserve trace context
        orchestrator.create_workflow(self.task_id, task_input, conn, user_id_hash, tenant_id)

        # Workflow tasks don't complete immediately
        # They're marked as running and complete when all subtasks finish
        # Return empty result - actual completion happens in process_subtask_completion
        return {
            "output": {"status": "workflow_initialized", "workflow_type": workflow_type},
            "usage": None,
        }

    def _report_results(self, conn: object, success: bool) -> bool:
        """Report task results to database.

        Args:
            conn: Database connection
            success: Whether task processing succeeded

        Returns:
            True if reporting succeeded, False otherwise
        """
        cur = conn.cursor(cursor_factory=RealDictCursor)  # type: ignore[attr-defined]

        try:
            usage = getattr(self.context, "_usage", None)
            user_id_hash = getattr(self.context, "_user_id_hash", None)

            if success:
                # Update task with success
                if usage:
                    cur.execute(
                        """
                        UPDATE tasks
                        SET status = 'done',
                            output = %s,
                            user_id_hash = %s,
                            model_used = %s,
                            input_tokens = %s,
                            output_tokens = %s,
                            total_cost = %s,
                            generation_id = %s,
                            updated_at = now()
                        WHERE id = %s
                        """,
                        (
                            Json(self.context.output_data),
                            user_id_hash,
                            usage.get("model_used"),
                            usage.get("input_tokens", 0),
                            usage.get("output_tokens", 0),
                            usage.get("total_cost", 0),
                            usage.get("generation_id"),
                            self.task_id,
                        ),
                    )
                else:
                    cur.execute(
                        """
                        UPDATE tasks
                        SET status = 'done', output = %s, updated_at = now()
                        WHERE id = %s
                        """,
                        (Json(self.context.output_data), self.task_id),
                    )
                conn.commit()  # type: ignore[attr-defined]

                # Notify API
                # Notify API
                notify_api_async(self.task_id, "done", output=self.context.output_data)

                # Audit log: Task completed
                log_audit_event(
                    conn,  # type: ignore[arg-type]
                    "task_completed",
                    resource_id=self.task_id,
                    user_id_hash=user_id_hash,
                    meta={
                        "total_cost": float(usage.get("total_cost", 0)) if usage else 0,
                        "input_tokens": usage.get("input_tokens", 0) if usage else 0,
                        "output_tokens": usage.get("output_tokens", 0) if usage else 0,
                        "model_used": usage.get("model_used") if usage else None,
                    },
                )
                conn.commit()  # type: ignore[attr-defined]

            else:
                # Update task with error
                cur.execute(
                    """
                    UPDATE tasks
                    SET status = 'error', error = %s, updated_at = now()
                    WHERE id = %s
                    """,
                    (self.context.error, self.task_id),
                )
                conn.commit()  # type: ignore[attr-defined]

                # Notify API
                # Notify API
                notify_api_async(self.task_id, "error", error=self.context.error)

                # Audit log: Task failed
                log_audit_event(
                    conn,  # type: ignore[arg-type]
                    "task_failed",
                    resource_id=self.task_id,
                    user_id_hash=user_id_hash,
                    meta={"error": self.context.error},
                )
                conn.commit()  # type: ignore[attr-defined]

            return True

        except Exception as e:
            logger.error(
                "task_reporting_failed",
                task_id=self.task_id,
                task_type=self.task_type,
                error=str(e),
            )
            return False
        finally:
            cur.close()
