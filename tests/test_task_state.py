"""Tests for Task State Machine.

Tests cover:
- 12 transition tests (happy paths, failure paths, shutdown flows)
- 5 invariant tests (lease validation, terminal states, reporting requirements)
"""

from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

import pytest

from app.task_state import (
    InvalidTransitionError,
    TaskContext,
    TaskEvent,
    TaskResult,
    TaskState,
    TaskStateMachine,
)

# ============================================================================
# Transition Tests (12 tests)
# ============================================================================


def test_task_pending_to_claiming():
    """Test PENDING + CLAIM_REQUESTED -> CLAIMING."""
    # Arrange
    task = TaskStateMachine(task_id="task-1", task_type="transcribe", worker_id="worker-1")
    assert task.state == TaskState.PENDING

    # Act
    new_state = task.transition(TaskEvent.CLAIM_REQUESTED)

    # Assert
    assert new_state == TaskState.CLAIMING
    assert task.state == TaskState.CLAIMING


def test_task_claim_success_to_processing():
    """Test CLAIMING + CLAIM_SUCCEEDED -> PROCESSING."""
    # Arrange
    task = TaskStateMachine(task_id="task-2", task_type="transcribe", worker_id="worker-1")
    task.transition(TaskEvent.CLAIM_REQUESTED)  # -> CLAIMING
    assert task.state == TaskState.CLAIMING

    # Act
    new_state = task.transition(TaskEvent.CLAIM_SUCCEEDED)

    # Assert
    assert new_state == TaskState.PROCESSING
    assert task.state == TaskState.PROCESSING


def test_task_claim_failure_to_failed():
    """Test CLAIMING + CLAIM_FAILED -> FAILED."""
    # Arrange
    task = TaskStateMachine(task_id="task-3", task_type="transcribe", worker_id="worker-1")
    task.transition(TaskEvent.CLAIM_REQUESTED)  # -> CLAIMING
    assert task.state == TaskState.CLAIMING

    # Act
    new_state = task.transition(TaskEvent.CLAIM_FAILED)

    # Assert
    assert new_state == TaskState.FAILED
    assert task.state == TaskState.FAILED
    assert task.is_terminal()


def test_task_processing_success_to_reporting():
    """Test PROCESSING + PROCESSING_SUCCEEDED -> REPORTING."""
    # Arrange
    task = TaskStateMachine(task_id="task-4", task_type="transcribe", worker_id="worker-1")
    task.transition(TaskEvent.CLAIM_REQUESTED)  # -> CLAIMING
    task.transition(TaskEvent.CLAIM_SUCCEEDED)  # -> PROCESSING
    assert task.state == TaskState.PROCESSING

    # Act
    new_state = task.transition(TaskEvent.PROCESSING_SUCCEEDED)

    # Assert
    assert new_state == TaskState.REPORTING
    assert task.state == TaskState.REPORTING


def test_task_processing_failure_to_reporting():
    """Test PROCESSING + PROCESSING_FAILED -> REPORTING (report the failure)."""
    # Arrange
    task = TaskStateMachine(task_id="task-5", task_type="transcribe", worker_id="worker-1")
    task.transition(TaskEvent.CLAIM_REQUESTED)  # -> CLAIMING
    task.transition(TaskEvent.CLAIM_SUCCEEDED)  # -> PROCESSING
    assert task.state == TaskState.PROCESSING

    # Set error in context
    task.context.error = "Processing timeout"

    # Act
    new_state = task.transition(TaskEvent.PROCESSING_FAILED)

    # Assert
    assert new_state == TaskState.REPORTING
    assert task.state == TaskState.REPORTING
    assert task.context.error == "Processing timeout"


def test_task_reporting_success_to_completed():
    """Test REPORTING + REPORT_SUCCEEDED -> COMPLETED."""
    # Arrange
    task = TaskStateMachine(task_id="task-6", task_type="transcribe", worker_id="worker-1")
    task.transition(TaskEvent.CLAIM_REQUESTED)  # -> CLAIMING
    task.transition(TaskEvent.CLAIM_SUCCEEDED)  # -> PROCESSING
    task.transition(TaskEvent.PROCESSING_SUCCEEDED)  # -> REPORTING
    assert task.state == TaskState.REPORTING

    # Act
    new_state = task.transition(TaskEvent.REPORT_SUCCEEDED)

    # Assert
    assert new_state == TaskState.COMPLETED
    assert task.state == TaskState.COMPLETED
    assert task.is_terminal()


def test_task_reporting_failure_to_failed():
    """Test REPORTING + REPORT_FAILED -> FAILED."""
    # Arrange
    task = TaskStateMachine(task_id="task-7", task_type="transcribe", worker_id="worker-1")
    task.transition(TaskEvent.CLAIM_REQUESTED)  # -> CLAIMING
    task.transition(TaskEvent.CLAIM_SUCCEEDED)  # -> PROCESSING
    task.transition(TaskEvent.PROCESSING_FAILED)  # -> REPORTING
    assert task.state == TaskState.REPORTING

    # Act
    new_state = task.transition(TaskEvent.REPORT_FAILED)

    # Assert
    assert new_state == TaskState.FAILED
    assert task.state == TaskState.FAILED
    assert task.is_terminal()


def test_task_lease_expired_to_abandoned():
    """Test PROCESSING + LEASE_EXPIRED -> ABANDONED."""
    # Arrange
    task = TaskStateMachine(task_id="task-8", task_type="transcribe", worker_id="worker-1")
    task.transition(TaskEvent.CLAIM_REQUESTED)  # -> CLAIMING
    task.transition(TaskEvent.CLAIM_SUCCEEDED)  # -> PROCESSING
    assert task.state == TaskState.PROCESSING

    # Simulate lease expiration
    task.context.lease_timeout = datetime.now(UTC) - timedelta(seconds=10)

    # Act
    new_state = task.transition(TaskEvent.LEASE_EXPIRED)

    # Assert
    assert new_state == TaskState.ABANDONED
    assert task.state == TaskState.ABANDONED
    assert task.is_terminal()


def test_task_shutdown_during_processing():
    """Test PROCESSING + SHUTDOWN_REQUESTED -> REPORTING (try to report partial)."""
    # Arrange
    task = TaskStateMachine(task_id="task-9", task_type="transcribe", worker_id="worker-1")
    task.transition(TaskEvent.CLAIM_REQUESTED)  # -> CLAIMING
    task.transition(TaskEvent.CLAIM_SUCCEEDED)  # -> PROCESSING
    assert task.state == TaskState.PROCESSING

    # Simulate partial work
    task.context.output_data = {"partial": "result"}

    # Act
    new_state = task.transition(TaskEvent.SHUTDOWN_REQUESTED)

    # Assert
    assert new_state == TaskState.REPORTING
    assert task.state == TaskState.REPORTING
    assert task.context.output_data == {"partial": "result"}


def test_task_shutdown_during_claiming():
    """Test CLAIMING + SHUTDOWN_REQUESTED -> ABANDONED."""
    # Arrange
    task = TaskStateMachine(task_id="task-10", task_type="transcribe", worker_id="worker-1")
    task.transition(TaskEvent.CLAIM_REQUESTED)  # -> CLAIMING
    assert task.state == TaskState.CLAIMING

    # Act
    new_state = task.transition(TaskEvent.SHUTDOWN_REQUESTED)

    # Assert
    assert new_state == TaskState.ABANDONED
    assert task.state == TaskState.ABANDONED
    assert task.is_terminal()


def test_task_is_terminal_completed():
    """Test is_terminal returns True for COMPLETED state."""
    # Arrange
    task = TaskStateMachine(task_id="task-11", task_type="transcribe", worker_id="worker-1")

    # Assert - not terminal in PENDING
    assert not task.is_terminal()

    # Transition to COMPLETED
    task.transition(TaskEvent.CLAIM_REQUESTED)  # -> CLAIMING
    assert not task.is_terminal()

    task.transition(TaskEvent.CLAIM_SUCCEEDED)  # -> PROCESSING
    assert not task.is_terminal()

    task.transition(TaskEvent.PROCESSING_SUCCEEDED)  # -> REPORTING
    assert not task.is_terminal()

    task.transition(TaskEvent.REPORT_SUCCEEDED)  # -> COMPLETED
    assert task.is_terminal()


def test_task_invalid_transition_raises_error():
    """Test that invalid transition raises InvalidTransitionError."""
    # Arrange
    task = TaskStateMachine(task_id="task-12", task_type="transcribe", worker_id="worker-1")
    assert task.state == TaskState.PENDING

    # Act & Assert - invalid event for PENDING state
    with pytest.raises(InvalidTransitionError) as exc_info:
        task.transition(TaskEvent.CLAIM_SUCCEEDED)

    # Verify error details
    assert exc_info.value.current_state == TaskState.PENDING
    assert exc_info.value.event == TaskEvent.CLAIM_SUCCEEDED
    assert "Invalid transition" in str(exc_info.value)
    assert "pending" in str(exc_info.value)
    assert "claim_succeeded" in str(exc_info.value)


# ============================================================================
# Invariant Tests (5 tests)
# ============================================================================


def test_task_processing_has_valid_lease():
    """Test T-INV1: Task in PROCESSING has context.lease_timeout in future."""
    # Arrange
    task = TaskStateMachine(task_id="task-inv1", task_type="transcribe", worker_id="worker-1")
    task.transition(TaskEvent.CLAIM_REQUESTED)  # -> CLAIMING

    # Set up lease (simulating successful claim)
    now = datetime.now(UTC)
    task.context.lease_acquired_at = now
    task.context.lease_timeout = now + timedelta(seconds=30)

    # Act
    task.transition(TaskEvent.CLAIM_SUCCEEDED)  # -> PROCESSING

    # Assert
    assert task.state == TaskState.PROCESSING
    assert task.context.lease_timeout is not None
    assert task.context.lease_timeout > datetime.now(UTC)


def test_task_processing_has_lease_acquired_time():
    """Test T-INV2: Task in PROCESSING has context.lease_acquired_at set."""
    # Arrange
    task = TaskStateMachine(task_id="task-inv2", task_type="transcribe", worker_id="worker-1")
    task.transition(TaskEvent.CLAIM_REQUESTED)  # -> CLAIMING

    # Set up lease
    now = datetime.now(UTC)
    task.context.lease_acquired_at = now
    task.context.lease_timeout = now + timedelta(seconds=30)

    # Act
    task.transition(TaskEvent.CLAIM_SUCCEEDED)  # -> PROCESSING

    # Assert
    assert task.state == TaskState.PROCESSING
    assert task.context.lease_acquired_at is not None
    assert isinstance(task.context.lease_acquired_at, datetime)


def test_task_terminal_state_no_transitions():
    """Test T-INV3: Task in terminal state does not transition."""
    # Arrange - task in COMPLETED state
    task = TaskStateMachine(task_id="task-inv3", task_type="transcribe", worker_id="worker-1")
    task.transition(TaskEvent.CLAIM_REQUESTED)  # -> CLAIMING
    task.transition(TaskEvent.CLAIM_SUCCEEDED)  # -> PROCESSING
    task.transition(TaskEvent.PROCESSING_SUCCEEDED)  # -> REPORTING
    task.transition(TaskEvent.REPORT_SUCCEEDED)  # -> COMPLETED
    assert task.state == TaskState.COMPLETED
    assert task.is_terminal()

    # Act & Assert - any event should raise InvalidTransitionError
    with pytest.raises(InvalidTransitionError):
        task.transition(TaskEvent.CLAIM_REQUESTED)

    # State should remain unchanged
    assert task.state == TaskState.COMPLETED


def test_task_reporting_has_output_or_error():
    """Test T-INV4: Task in REPORTING has either output_data or error set."""
    # Arrange - success case
    task_success = TaskStateMachine(
        task_id="task-inv4a", task_type="transcribe", worker_id="worker-1"
    )
    task_success.transition(TaskEvent.CLAIM_REQUESTED)  # -> CLAIMING
    task_success.transition(TaskEvent.CLAIM_SUCCEEDED)  # -> PROCESSING

    # Set output data
    task_success.context.output_data = {"transcription": "Hello world"}

    # Act
    task_success.transition(TaskEvent.PROCESSING_SUCCEEDED)  # -> REPORTING

    # Assert
    assert task_success.state == TaskState.REPORTING
    assert task_success.context.output_data is not None
    assert task_success.context.output_data == {"transcription": "Hello world"}

    # Arrange - failure case
    task_failure = TaskStateMachine(
        task_id="task-inv4b", task_type="transcribe", worker_id="worker-1"
    )
    task_failure.transition(TaskEvent.CLAIM_REQUESTED)  # -> CLAIMING
    task_failure.transition(TaskEvent.CLAIM_SUCCEEDED)  # -> PROCESSING

    # Set error
    task_failure.context.error = "Audio file corrupted"

    # Act
    task_failure.transition(TaskEvent.PROCESSING_FAILED)  # -> REPORTING

    # Assert
    assert task_failure.state == TaskState.REPORTING
    assert task_failure.context.error is not None
    assert task_failure.context.error == "Audio file corrupted"


def test_task_transitions_are_atomic():
    """Test T-INV5: Task state transitions are atomic (no partial transitions)."""
    # Arrange
    import contextlib

    task = TaskStateMachine(task_id="task-inv5", task_type="transcribe", worker_id="worker-1")
    initial_state = task.state

    # Act - attempt invalid transition
    with contextlib.suppress(InvalidTransitionError):
        task.transition(TaskEvent.REPORT_SUCCEEDED)

    # Assert - state should be unchanged after failed transition
    assert task.state == initial_state
    assert task.state == TaskState.PENDING

    # Valid transition should work
    task.transition(TaskEvent.CLAIM_REQUESTED)
    assert task.state == TaskState.CLAIMING


# ============================================================================
# Additional Helper Method Tests
# ============================================================================


def test_task_context_initialization():
    """Test TaskContext initializes with correct defaults."""
    # Arrange & Act
    context = TaskContext()

    # Assert
    assert context.lease_acquired_at is None
    assert context.lease_timeout is None
    assert context.input_data is None
    assert context.output_data is None
    assert context.error is None
    assert context.cost is None
    assert context.processing_started_at is None
    assert context.processing_completed_at is None


def test_task_context_update():
    """Test TaskContext can be updated."""
    # Arrange
    context = TaskContext()
    now = datetime.now(UTC)

    # Act
    context.lease_acquired_at = now
    context.lease_timeout = now + timedelta(seconds=30)
    context.input_data = {"file": "audio.mp3"}
    context.output_data = {"text": "Transcription"}
    context.error = None
    context.cost = 0.05
    context.processing_started_at = now
    context.processing_completed_at = now + timedelta(seconds=10)

    # Assert
    assert context.lease_acquired_at == now
    assert context.lease_timeout == now + timedelta(seconds=30)
    assert context.input_data == {"file": "audio.mp3"}
    assert context.output_data == {"text": "Transcription"}
    assert context.error is None
    assert context.cost == 0.05
    assert context.processing_started_at == now
    assert context.processing_completed_at == now + timedelta(seconds=10)


def test_task_result_creation():
    """Test TaskResult creation."""
    # Arrange & Act
    result = TaskResult(
        task_id="task-result-1",
        final_state=TaskState.COMPLETED,
        output={"transcription": "Hello"},
        error=None,
        cost=0.10,
        duration_ms=5000,
    )

    # Assert
    assert result.task_id == "task-result-1"
    assert result.final_state == TaskState.COMPLETED
    assert result.output == {"transcription": "Hello"}
    assert result.error is None
    assert result.cost == 0.10
    assert result.duration_ms == 5000


# ============================================================================
# Integration Tests for execute() (3 tests)
# ============================================================================


def test_execute_successful_task():
    """Test execute() successfully processes a task through complete lifecycle."""
    from unittest.mock import patch

    # Arrange
    task = TaskStateMachine(
        task_id="integration-task-1",
        task_type="transcribe",
        worker_id="worker-integration-1",
    )

    # Mock connection and cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # Mock database query results
    mock_cursor.fetchone.return_value = {
        "id": "integration-task-1",
        "type": "transcribe",
        "input": {"file": "audio.mp3", "_user_id_hash": "user123"},
    }

    # Mock execute_task to return successful result
    mock_output = {"transcription": "Hello world"}
    mock_usage = {
        "model_used": "gpt-4",
        "input_tokens": 100,
        "output_tokens": 50,
        "total_cost": 0.05,
        "generation_id": "gen-123",
    }

    with (
        patch("app.task_state.execute_task") as mock_execute,
        patch("app.task_state.notify_api_async") as mock_notify,
        patch("app.task_state.log_audit_event") as mock_audit,
    ):
        mock_execute.return_value = {"output": mock_output, "usage": mock_usage}

        # Act
        result = task.execute(mock_conn)

        # Assert - Final state should be COMPLETED
        assert result.final_state == TaskState.COMPLETED
        assert result.output == mock_output
        assert result.error is None
        assert result.cost == 0.05
        assert result.duration_ms is not None
        assert result.duration_ms >= 0

        # Verify state transitions occurred
        assert task.state == TaskState.COMPLETED
        assert task.is_terminal()

        # Verify DB updates were called
        assert mock_cursor.execute.call_count >= 3  # running, done, audit logs

        # Verify API notifications
        assert mock_notify.call_count >= 2  # running, done

        # Verify audit logs
        assert mock_audit.call_count >= 2  # task_started, task_completed


def test_execute_failing_task():
    """Test execute() handles task execution failure correctly."""
    from unittest.mock import patch

    # Arrange
    task = TaskStateMachine(
        task_id="integration-task-2",
        task_type="transcribe",
        worker_id="worker-integration-2",
    )

    # Mock connection and cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # Mock database query results
    mock_cursor.fetchone.return_value = {
        "id": "integration-task-2",
        "type": "transcribe",
        "input": {"file": "corrupted.mp3", "_user_id_hash": "user456"},
    }

    # Mock execute_task to raise an exception
    with (
        patch("app.task_state.execute_task") as mock_execute,
        patch("app.task_state.notify_api_async") as mock_notify,
        patch("app.task_state.log_audit_event") as mock_audit,
    ):
        mock_execute.side_effect = ValueError("Audio file is corrupted")

        # Act
        result = task.execute(mock_conn)

        # Assert - Final state should be COMPLETED (reporting succeeded)
        # The error was reported to the database
        assert result.final_state == TaskState.COMPLETED
        assert result.output is None
        assert result.error == "Audio file is corrupted"
        assert result.duration_ms is not None

        # Verify state reached terminal
        assert task.is_terminal()

        # Verify error was written to DB
        execute_calls = [str(call) for call in mock_cursor.execute.call_args_list]
        assert any("error" in call.lower() for call in execute_calls)

        # Verify API was notified of error
        notify_calls = [str(call) for call in mock_notify.call_args_list]
        assert any("error" in call.lower() for call in notify_calls)

        # Verify audit log for failure
        assert mock_audit.call_count >= 2  # task_started, task_failed


def test_execute_with_lease_renewal():
    """Test execute() with lease renewal during long-running task."""
    from datetime import datetime
    from unittest.mock import patch

    # Arrange
    task = TaskStateMachine(
        task_id="integration-task-3",
        task_type="transcribe",
        worker_id="worker-integration-3",
    )

    # Mock connection and cursor
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # Mock database query results
    mock_cursor.fetchone.return_value = {
        "id": "integration-task-3",
        "type": "transcribe",
        "input": {"file": "long-audio.mp3", "_user_id_hash": "user789"},
    }

    # Mock execute_task to simulate long-running task
    mock_output = {"transcription": "Long transcription result"}
    mock_usage = {
        "model_used": "gpt-4",
        "input_tokens": 500,
        "output_tokens": 200,
        "total_cost": 0.15,
    }

    with (
        patch("app.task_state.execute_task") as mock_execute,
        patch("app.task_state.notify_api_async"),
        patch("app.task_state.log_audit_event"),
    ):
        mock_execute.return_value = {"output": mock_output, "usage": mock_usage}

        # Act
        result = task.execute(mock_conn)

        # Assert - Successfully completed
        assert result.final_state == TaskState.COMPLETED
        assert result.output == mock_output
        assert result.cost == 0.15

        # Verify lease was set up in context
        assert task.context.lease_acquired_at is not None
        assert task.context.lease_timeout is not None
        assert isinstance(task.context.lease_acquired_at, datetime)
        assert isinstance(task.context.lease_timeout, datetime)

        # Lease timeout should be in future from when it was set
        # (it may be in past now, but when set it was future + lease_duration)
        assert task.context.lease_acquired_at.tzinfo is not None  # Should have timezone
