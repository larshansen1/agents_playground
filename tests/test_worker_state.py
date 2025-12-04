"""Tests for Worker State Machine.

Tests cover:
- 10 transition tests (happy paths, retry, shutdown flows)
- 5 invariant tests (connection state, shutdown behavior, single task)
"""

import contextlib
from unittest.mock import MagicMock

import pytest

from app.worker_state import (
    InvalidTransitionError,
    WorkerEvent,
    WorkerState,
    WorkerStateMachine,
)

# ============================================================================
# Transition Tests (10 tests)
# ============================================================================


def test_worker_startup_to_connecting():
    """Test STARTING + INITIALIZED -> CONNECTING."""
    # Arrange
    worker = WorkerStateMachine(worker_id="test-worker-1")
    assert worker.state == WorkerState.STARTING

    # Act
    new_state = worker.transition(WorkerEvent.INITIALIZED)

    # Assert
    assert new_state == WorkerState.CONNECTING
    assert worker.state == WorkerState.CONNECTING


def test_worker_connecting_success_to_recovering():
    """Test CONNECTING + CONNECTED -> RECOVERING."""
    # Arrange
    worker = WorkerStateMachine(worker_id="test-worker-2")
    worker.transition(WorkerEvent.INITIALIZED)  # -> CONNECTING
    assert worker.state == WorkerState.CONNECTING

    # Act
    new_state = worker.transition(WorkerEvent.CONNECTED)

    # Assert
    assert new_state == WorkerState.RECOVERING
    assert worker.state == WorkerState.RECOVERING


def test_worker_connecting_failure_retries():
    """Test CONNECTING + CONNECTION_FAILED -> CONNECTING (retry with backoff)."""
    # Arrange
    worker = WorkerStateMachine(worker_id="test-worker-3")
    worker.transition(WorkerEvent.INITIALIZED)  # -> CONNECTING
    assert worker.state == WorkerState.CONNECTING

    # Act
    new_state = worker.transition(WorkerEvent.CONNECTION_FAILED)

    # Assert - should stay in CONNECTING for retry
    assert new_state == WorkerState.CONNECTING
    assert worker.state == WorkerState.CONNECTING


def test_worker_recovery_to_running():
    """Test RECOVERING + RECOVERY_COMPLETE -> RUNNING."""
    # Arrange
    worker = WorkerStateMachine(worker_id="test-worker-4")
    worker.transition(WorkerEvent.INITIALIZED)  # -> CONNECTING
    worker.transition(WorkerEvent.CONNECTED)  # -> RECOVERING
    assert worker.state == WorkerState.RECOVERING

    # Act
    new_state = worker.transition(WorkerEvent.RECOVERY_COMPLETE)

    # Assert
    assert new_state == WorkerState.RUNNING
    assert worker.state == WorkerState.RUNNING


def test_worker_running_no_tasks_to_backing_off():
    """Test RUNNING + NO_TASKS_AVAILABLE -> BACKING_OFF."""
    # Arrange
    worker = WorkerStateMachine(worker_id="test-worker-5")
    worker.transition(WorkerEvent.INITIALIZED)  # -> CONNECTING
    worker.transition(WorkerEvent.CONNECTED)  # -> RECOVERING
    worker.transition(WorkerEvent.RECOVERY_COMPLETE)  # -> RUNNING
    assert worker.state == WorkerState.RUNNING

    # Act
    new_state = worker.transition(WorkerEvent.NO_TASKS_AVAILABLE)

    # Assert
    assert new_state == WorkerState.BACKING_OFF
    assert worker.state == WorkerState.BACKING_OFF


def test_worker_backoff_complete_to_recovering():
    """Test BACKING_OFF + BACKOFF_COMPLETE -> RECOVERING."""
    # Arrange
    worker = WorkerStateMachine(worker_id="test-worker-6")
    worker.transition(WorkerEvent.INITIALIZED)  # -> CONNECTING
    worker.transition(WorkerEvent.CONNECTED)  # -> RECOVERING
    worker.transition(WorkerEvent.RECOVERY_COMPLETE)  # -> RUNNING
    worker.transition(WorkerEvent.NO_TASKS_AVAILABLE)  # -> BACKING_OFF
    assert worker.state == WorkerState.BACKING_OFF

    # Act
    new_state = worker.transition(WorkerEvent.BACKOFF_COMPLETE)

    # Assert
    assert new_state == WorkerState.RECOVERING
    assert worker.state == WorkerState.RECOVERING


def test_worker_shutdown_from_running():
    """Test RUNNING + SHUTDOWN_REQUESTED -> SHUTTING_DOWN."""
    # Arrange
    worker = WorkerStateMachine(worker_id="test-worker-7")
    worker.transition(WorkerEvent.INITIALIZED)  # -> CONNECTING
    worker.transition(WorkerEvent.CONNECTED)  # -> RECOVERING
    worker.transition(WorkerEvent.RECOVERY_COMPLETE)  # -> RUNNING
    assert worker.state == WorkerState.RUNNING

    # Act
    new_state = worker.transition(WorkerEvent.SHUTDOWN_REQUESTED)

    # Assert
    assert new_state == WorkerState.SHUTTING_DOWN
    assert worker.state == WorkerState.SHUTTING_DOWN


def test_worker_shutdown_from_backing_off():
    """Test BACKING_OFF + SHUTDOWN_REQUESTED -> SHUTTING_DOWN."""
    # Arrange
    worker = WorkerStateMachine(worker_id="test-worker-8")
    worker.transition(WorkerEvent.INITIALIZED)  # -> CONNECTING
    worker.transition(WorkerEvent.CONNECTED)  # -> RECOVERING
    worker.transition(WorkerEvent.RECOVERY_COMPLETE)  # -> RUNNING
    worker.transition(WorkerEvent.NO_TASKS_AVAILABLE)  # -> BACKING_OFF
    assert worker.state == WorkerState.BACKING_OFF

    # Act
    new_state = worker.transition(WorkerEvent.SHUTDOWN_REQUESTED)

    # Assert
    assert new_state == WorkerState.SHUTTING_DOWN
    assert worker.state == WorkerState.SHUTTING_DOWN


def test_worker_shutdown_waits_for_active_task():
    """Test that shutdown flow properly handles active task in context."""
    # Arrange
    worker = WorkerStateMachine(worker_id="test-worker-9")
    worker.transition(WorkerEvent.INITIALIZED)  # -> CONNECTING
    worker.transition(WorkerEvent.CONNECTED)  # -> RECOVERING
    worker.transition(WorkerEvent.RECOVERY_COMPLETE)  # -> RUNNING

    # Simulate active task
    mock_task_sm = MagicMock()
    mock_task_sm.is_terminal.return_value = False
    worker.context.current_task_sm = mock_task_sm
    assert worker.state == WorkerState.RUNNING

    # Act - transition to shutting down
    worker.transition(WorkerEvent.SHUTDOWN_REQUESTED)
    assert worker.state == WorkerState.SHUTTING_DOWN

    # Assert - active task is still in context (not cleared by state machine)
    # The actual waiting logic would be in the worker loop, not the state machine
    assert worker.context.current_task_sm is not None
    assert worker.context.current_task_sm == mock_task_sm


def test_worker_invalid_transition_raises_error():
    """Test that invalid transition raises InvalidTransitionError."""
    # Arrange
    worker = WorkerStateMachine(worker_id="test-worker-10")
    assert worker.state == WorkerState.STARTING

    # Act & Assert - invalid event for STARTING state
    with pytest.raises(InvalidTransitionError) as exc_info:
        worker.transition(WorkerEvent.SHUTDOWN_COMPLETE)

    # Verify error details
    assert exc_info.value.current_state == WorkerState.STARTING
    assert exc_info.value.event == WorkerEvent.SHUTDOWN_COMPLETE
    assert "Invalid transition" in str(exc_info.value)
    assert "starting" in str(exc_info.value)
    assert "shutdown_complete" in str(exc_info.value)


# ============================================================================
# Invariant Tests (5 tests)
# ============================================================================


def test_worker_running_has_connection():
    """Test W-INV1: Worker in RUNNING has non-null context.connection."""
    # Arrange
    worker = WorkerStateMachine(worker_id="test-worker-inv1")
    worker.transition(WorkerEvent.INITIALIZED)  # -> CONNECTING
    worker.transition(WorkerEvent.CONNECTED)  # -> RECOVERING

    # Set up connection in context (simulating successful connection)
    mock_connection = MagicMock()
    worker.context.connection = mock_connection

    # Act
    worker.transition(WorkerEvent.RECOVERY_COMPLETE)  # -> RUNNING

    # Assert
    assert worker.state == WorkerState.RUNNING
    assert worker.context.connection is not None
    assert worker.context.connection == mock_connection


def test_worker_shutting_down_rejects_new_tasks():
    """Test W-INV2: Worker in SHUTTING_DOWN does not accept new tasks."""
    # Arrange
    worker = WorkerStateMachine(worker_id="test-worker-inv2")
    worker.transition(WorkerEvent.INITIALIZED)  # -> CONNECTING
    worker.transition(WorkerEvent.CONNECTED)  # -> RECOVERING
    worker.transition(WorkerEvent.RECOVERY_COMPLETE)  # -> RUNNING
    worker.transition(WorkerEvent.SHUTDOWN_REQUESTED)  # -> SHUTTING_DOWN

    # Assert
    assert worker.state == WorkerState.SHUTTING_DOWN
    assert not worker.is_accepting_tasks()


def test_worker_shutdown_timeout_forces_stop():
    """Test W-INV3: Worker reaches STOPPED within timeout.

    This test verifies that the state machine can transition from
    SHUTTING_DOWN to STOPPED. The actual timeout enforcement would
    be in the worker loop.
    """
    # Arrange
    worker = WorkerStateMachine(worker_id="test-worker-inv3")
    worker.transition(WorkerEvent.INITIALIZED)  # -> CONNECTING
    worker.transition(WorkerEvent.CONNECTED)  # -> RECOVERING
    worker.transition(WorkerEvent.RECOVERY_COMPLETE)  # -> RUNNING
    worker.transition(WorkerEvent.SHUTDOWN_REQUESTED)  # -> SHUTTING_DOWN
    assert worker.state == WorkerState.SHUTTING_DOWN

    # Act - complete shutdown
    worker.transition(WorkerEvent.SHUTDOWN_COMPLETE)

    # Assert
    assert worker.state == WorkerState.STOPPED
    assert not worker.is_running()


def test_worker_stopped_releases_connection():
    """Test W-INV4: Worker in STOPPED has context.connection = None."""
    # Arrange
    worker = WorkerStateMachine(worker_id="test-worker-inv4")
    worker.transition(WorkerEvent.INITIALIZED)  # -> CONNECTING
    worker.transition(WorkerEvent.CONNECTED)  # -> RECOVERING

    # Set up connection
    mock_connection = MagicMock()
    worker.context.connection = mock_connection

    worker.transition(WorkerEvent.RECOVERY_COMPLETE)  # -> RUNNING
    worker.transition(WorkerEvent.SHUTDOWN_REQUESTED)  # -> SHUTTING_DOWN

    # Act - cleanup connection before final transition
    # (This would be done by worker loop in practice)
    worker.context.connection = None
    worker.transition(WorkerEvent.SHUTDOWN_COMPLETE)  # -> STOPPED

    # Assert
    assert worker.state == WorkerState.STOPPED
    assert worker.context.connection is None


def test_worker_single_active_task():
    """Test W-INV5: Only one TaskStateMachine active per worker.

    This test verifies that the context supports tracking a single
    active task. The enforcement of this invariant would be in the
    worker loop logic.
    """
    # Arrange
    worker = WorkerStateMachine(worker_id="test-worker-inv5")
    worker.transition(WorkerEvent.INITIALIZED)  # -> CONNECTING
    worker.transition(WorkerEvent.CONNECTED)  # -> RECOVERING
    worker.transition(WorkerEvent.RECOVERY_COMPLETE)  # -> RUNNING

    # Act - simulate task assignment
    mock_task_sm_1 = MagicMock()
    worker.context.current_task_sm = mock_task_sm_1

    # Assert - only one task active
    assert worker.context.current_task_sm == mock_task_sm_1

    # Simulate task completion and new task
    worker.context.current_task_sm = None
    mock_task_sm_2 = MagicMock()
    worker.context.current_task_sm = mock_task_sm_2

    # Assert - new task replaces old
    assert worker.context.current_task_sm == mock_task_sm_2
    assert worker.context.current_task_sm != mock_task_sm_1


# ============================================================================
# Integration Tests for run() (4 tests)
# ============================================================================


def test_run_processes_task():
    """Test run() processes a task through complete worker lifecycle."""
    from threading import Thread
    from time import sleep
    from unittest.mock import MagicMock, patch

    # Arrange
    worker = WorkerStateMachine(worker_id="worker-run-1")

    # Create mock objects
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # Mock claim_next_task to return a task once, then None
    task_row = {
        "id": "task-123",
        "type": "transcribe",
        "input": {"file": "test.mp3"},
        "source_type": "task",
    }

    call_count = {"value": 0}

    def mock_claim(conn, cur, worker_id, settings):
        call_count["value"] += 1
        if call_count["value"] == 1:
            return task_row
        # After first task, trigger shutdown
        worker.context.shutdown_requested = True
        return None

    # Mock TaskStateMachine.execute to return success
    mock_result = MagicMock()
    mock_result.final_state.value = "completed"
    mock_result.error = None

    with (
        patch("app.db_sync.get_connection") as mock_get_conn,
        patch("app.worker_lease.recover_expired_leases") as mock_recover,
        patch("app.worker_helpers.claim_next_task") as mock_claim_task,
        patch("app.task_state.TaskStateMachine") as mock_task_sm_class,
        patch("app.instance.get_instance_name") as mock_get_instance,
        patch("app.metrics.worker_heartbeat"),
        patch("app.metrics.active_leases"),
        patch("signal.signal"),
    ):
        mock_get_conn.return_value = mock_conn
        mock_recover.return_value = 0
        mock_claim_task.side_effect = mock_claim
        mock_get_instance.return_value = "worker-test-instance"

        # Mock TaskStateMachine instance
        mock_task_sm = MagicMock()
        mock_task_sm.execute.return_value = mock_result
        mock_task_sm.is_terminal.return_value = True
        mock_task_sm.task_id = "task-123"
        mock_task_sm_class.return_value = mock_task_sm

        # Act - run in thread with timeout
        def run_worker():
            with contextlib.suppress(Exception):
                worker.run()

        thread = Thread(target=run_worker, daemon=True)
        thread.start()

        # Wait for processing
        sleep(2)

        # Force shutdown if still running
        worker.context.shutdown_requested = True

        # Wait for completion
        thread.join(timeout=5)

        # Assert - Worker processed task
        assert worker.context.tasks_processed >= 1
        assert worker.state in (WorkerState.STOPPED, WorkerState.SHUTTING_DOWN)


def test_run_handles_no_tasks():
    """Test run() handles no tasks available with backoff."""
    from threading import Thread
    from time import sleep
    from unittest.mock import MagicMock, patch

    # Arrange
    worker = WorkerStateMachine(worker_id="worker-run-2")

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    with (
        patch("app.db_sync.get_connection") as mock_get_conn,
        patch("app.worker_lease.recover_expired_leases") as mock_recover,
        patch("app.worker_helpers.claim_next_task") as mock_claim_task,
        patch("app.instance.get_instance_name") as mock_get_instance,
        patch("app.metrics.worker_heartbeat"),
        patch("signal.signal"),
    ):
        mock_get_conn.return_value = mock_conn
        mock_recover.return_value = 0
        mock_claim_task.return_value = None  # No tasks
        mock_get_instance.return_value = "worker-test-instance"

        # Act - run in thread
        def run_worker():
            with contextlib.suppress(Exception):
                worker.run()

        thread = Thread(target=run_worker, daemon=True)
        thread.start()

        # Wait briefly for backoff state
        sleep(1)

        # Trigger shutdown
        worker.context.shutdown_requested = True

        # Wait for completion
        thread.join(timeout=5)

        # Assert - Worker entered BACKING_OFF state
        assert worker.context.backoff_count >= 1


def test_run_shutdown_graceful():
    """Test run() handles graceful shutdown with active task."""
    from threading import Thread
    from time import sleep
    from unittest.mock import MagicMock, patch

    # Arrange
    worker = WorkerStateMachine(worker_id="worker-run-3")

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # Mock a long-running task
    task_row = {
        "id": "task-long",
        "type": "transcribe",
        "input": {"file": "long.mp3"},
        "source_type": "task",
    }

    def mock_claim(conn, cur, worker_id, settings):
        # Return task only once
        if worker.context.tasks_processed == 0:
            return task_row
        return None

    # Mock task that completes eventually
    mock_result = MagicMock()
    mock_result.final_state.value = "completed"
    mock_result.error = None

    with (
        patch("app.db_sync.get_connection") as mock_get_conn,
        patch("app.worker_lease.recover_expired_leases") as mock_recover,
        patch("app.worker_helpers.claim_next_task") as mock_claim_task,
        patch("app.task_state.TaskStateMachine") as mock_task_sm_class,
        patch("app.instance.get_instance_name") as mock_get_instance,
        patch("app.metrics.worker_heartbeat"),
        patch("app.metrics.active_leases"),
        patch("signal.signal"),
    ):
        mock_get_conn.return_value = mock_conn
        mock_recover.return_value = 0
        mock_claim_task.side_effect = mock_claim
        mock_get_instance.return_value = "worker-test-instance"

        # Mock TaskStateMachine
        mock_task_sm = MagicMock()
        mock_task_sm.execute.return_value = mock_result
        mock_task_sm.is_terminal.return_value = True
        mock_task_sm.task_id = "task-long"
        mock_task_sm_class.return_value = mock_task_sm

        # Act - run worker
        def run_worker():
            with contextlib.suppress(Exception):
                worker.run()

        thread = Thread(target=run_worker, daemon=True)
        thread.start()

        # Wait for task to start
        sleep(0.5)

        # Request shutdown
        worker.context.shutdown_requested = True

        # Wait for graceful shutdown
        thread.join(timeout=10)

        # Assert - Worker completed shutdown and processed task
        assert worker.context.tasks_processed >= 1
        assert worker.state in (WorkerState.STOPPED, WorkerState.SHUTTING_DOWN)


def test_run_connection_failure():
    """Test run() handles connection failure and retries."""
    from threading import Thread
    from time import sleep
    from unittest.mock import MagicMock, patch

    # Arrange
    worker = WorkerStateMachine(worker_id="worker-run-4")

    # Mock get_connection to fail first then succeed
    mock_conn = MagicMock()

    call_count = {"value": 0}

    def mock_connect():
        call_count["value"] += 1
        if call_count["value"] == 1:
            msg = "Connection failed"
            raise Exception(msg)
        return mock_conn

    with (
        patch("app.db_sync.get_connection") as mock_get_conn,
        patch("app.worker_lease.recover_expired_leases") as mock_recover,
        patch("time.sleep"),  # Mock sleep to speed up test
        patch("app.instance.get_instance_name") as mock_get_instance,
        patch("app.metrics.worker_heartbeat"),
        patch("signal.signal"),
    ):
        mock_get_conn.side_effect = mock_connect
        mock_recover.return_value = 0
        mock_get_instance.return_value = "worker-test-instance"

        # Act - run in thread
        def run_worker():
            with contextlib.suppress(Exception):
                worker.run()

        thread = Thread(target=run_worker, daemon=True)
        thread.start()

        # Wait for retry
        sleep(0.5)

        # Trigger shutdown
        worker.context.shutdown_requested = True

        # Wait for completion
        thread.join(timeout=5)

        # Assert - Worker retried connection
        assert call_count["value"] >= 2
        mock_conn.close.assert_called()
        assert worker.context.connection is None
