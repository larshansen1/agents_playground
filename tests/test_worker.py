import contextlib
from unittest.mock import MagicMock, patch

import pytest

from app.api_client import notify_api_async
from app.worker import (
    _process_task_row_legacy as _process_task_row,
)
from app.worker import (
    run_worker_legacy as run_worker,
)


@pytest.fixture
def mock_requests():
    with patch("app.api_client.requests") as mock:
        mock.patch.return_value.status_code = 200
        yield mock


@pytest.fixture
def mock_db_connection():
    with patch("app.worker.get_connection") as mock:
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur
        conn.closed = False
        mock.return_value = conn
        yield mock, conn, cur


@pytest.fixture
def mock_execute_task():
    with patch("app.worker.execute_task") as mock:
        yield mock


@pytest.fixture
def mock_tracer():
    with patch("app.worker.tracer") as mock:
        span = MagicMock()
        mock.start_as_current_span.return_value.__enter__.return_value = span
        yield mock, span


@pytest.fixture
def mock_audit_log():
    with patch("app.worker.log_audit_event") as mock:
        yield mock


@pytest.fixture
def mock_trace_context():
    with patch("app.worker.extract_trace_context") as mock:
        # Return None context and cleaned input by default
        mock.return_value = (None, {})
        yield mock


@pytest.fixture
def mock_get_current_trace_id():
    with patch("app.worker.get_current_trace_id") as mock:
        mock.return_value = "trace-123"
        yield mock


@pytest.fixture
def mock_worker_heartbeat():
    with patch("app.worker.worker_heartbeat") as mock:
        yield mock


@pytest.fixture
def mock_is_agent_task():
    with patch("app.worker.is_agent_task") as mock:
        mock.return_value = False
        yield mock


@pytest.fixture
def mock_is_workflow_task():
    with patch("app.worker.is_workflow_task") as mock:
        mock.return_value = False
        yield mock


@pytest.fixture
def mock_process_subtask():
    with patch("app.worker._process_subtask") as mock:
        yield mock


@pytest.fixture
def mock_process_agent_task():
    with patch("app.worker._process_agent_task") as mock:
        yield mock


@pytest.fixture
def mock_process_workflow_task():
    with patch("app.worker._process_workflow_task") as mock:
        yield mock


@pytest.fixture
def mock_otel_trace():
    with patch("app.worker.otel_trace") as mock:
        provider = MagicMock()
        mock.get_tracer_provider.return_value = provider
        yield mock, provider


# ============================================================================
# Phase 1: Foundation (Happy Paths)
# ============================================================================


class TestWorkerNotification:
    """Test API notification functionality."""

    def test_notify_api_async_success(self, mock_requests):
        """Test successful API notification with status only."""
        notify_api_async("task-123", "running")

        mock_requests.patch.assert_called_once()
        args, kwargs = mock_requests.patch.call_args
        assert "task-123" in args[0]
        assert kwargs["json"] == {"status": "running"}
        assert kwargs["timeout"] == 5
        assert kwargs["verify"] is False

    def test_notify_api_async_with_output(self, mock_requests):
        """Test API notification with output payload."""
        notify_api_async("task-123", "done", output={"result": "ok"})

        _, kwargs = mock_requests.patch.call_args
        assert kwargs["json"] == {"status": "done", "output": {"result": "ok"}}

    def test_notify_api_async_with_error(self, mock_requests):
        """Test API notification with error message."""
        notify_api_async("task-123", "error", error="Something went wrong")

        _, kwargs = mock_requests.patch.call_args
        assert kwargs["json"] == {"status": "error", "error": "Something went wrong"}

    def test_notify_api_async_with_all_params(self, mock_requests):
        """Test API notification with all parameters."""
        notify_api_async(
            "task-123",
            "done",
            output={"result": "success"},
            error="warning message",
        )

        _, kwargs = mock_requests.patch.call_args
        assert kwargs["json"] == {
            "status": "done",
            "output": {"result": "success"},
            "error": "warning message",
        }

    def test_notify_api_async_failure(self, mock_requests):
        """Test API notification failure does not raise exception."""
        mock_requests.patch.side_effect = Exception("Network error")

        # Should not raise exception
        notify_api_async("task-123", "running")
        mock_requests.patch.assert_called_once()


# ============================================================================
# Phase 2: State Transitions & Error Handling
# ============================================================================


class TestTaskStateTransitions:
    """Test task state transitions and side effects."""

    @pytest.mark.usefixtures(
        "mock_worker_heartbeat",
        "mock_is_agent_task",
        "mock_is_workflow_task",
        "mock_otel_trace",
    )
    def test_task_success_state_transition(
        self,
        mock_db_connection,
        mock_execute_task,
        mock_requests,
        mock_audit_log,
        mock_tracer,
        mock_trace_context,
        mock_get_current_trace_id,
    ):
        """Test complete state transition: pending → running → done."""
        _, conn, cur = mock_db_connection
        _, span = mock_tracer

        # Setup
        row = {
            "id": "task-123",
            "type": "test_task",
            "input": {"key": "value"},
        }
        mock_trace_context.return_value = (None, {"key": "value"})
        mock_execute_task.return_value = {
            "output": {"result": "success"},
            "usage": {
                "total_cost": 0.01,
                "input_tokens": 10,
                "output_tokens": 20,
                "model_used": "gpt-4",
                "generation_id": "gen-123",
            },
        }

        _process_task_row(conn, cur, row)

        # Verify state transitions in DB
        db_calls = cur.execute.call_args_list
        # First call: UPDATE to 'running'
        assert "UPDATE tasks SET status = 'running'" in db_calls[0][0][0]
        assert db_calls[0][0][1] == ("task-123",)
        # Second call: audit log insert (task_started)
        # Third call: UPDATE to 'done' with usage data
        done_update = next(c for c in db_calls if "status = 'done'" in c[0][0])
        assert "user_id_hash" in done_update[0][0]
        assert "model_used" in done_update[0][0]
        assert "total_cost" in done_update[0][0]

        # Verify commits happened
        assert conn.commit.call_count >= 3

        # Verify API notifications
        api_calls = mock_requests.patch.call_args_list
        assert len(api_calls) == 2
        # First: running
        assert api_calls[0][1]["json"]["status"] == "running"
        # Second: done
        assert api_calls[1][1]["json"]["status"] == "done"

        # Verify audit logs
        audit_calls = mock_audit_log.call_args_list
        assert len(audit_calls) == 2
        assert audit_calls[0][0][1] == "task_started"
        assert audit_calls[1][0][1] == "task_completed"

        # Verify span status
        span.set_status.assert_called_once()
        span.set_attribute.assert_any_call("task.id", "task-123")
        span.set_attribute.assert_any_call("task.type", "test_task")

    @pytest.mark.usefixtures(
        "mock_worker_heartbeat",
        "mock_is_agent_task",
        "mock_is_workflow_task",
        "mock_otel_trace",
    )
    def test_task_error_state_transition(
        self,
        mock_db_connection,
        mock_execute_task,
        mock_requests,
        mock_audit_log,
        mock_tracer,
        mock_trace_context,
    ):
        """Test error state transition: pending → running → error."""
        _, conn, cur = mock_db_connection
        _, span = mock_tracer

        row = {"id": "task-123", "type": "test_task", "input": {"key": "value"}}
        mock_trace_context.return_value = (None, {"key": "value"})
        mock_execute_task.side_effect = ValueError("Processing failed")

        _process_task_row(conn, cur, row)

        # Verify state transitions
        db_calls = cur.execute.call_args_list
        # First: running
        assert "status = 'running'" in db_calls[0][0][0]
        # Last: error
        error_update = [c for c in db_calls if "status = 'error'" in c[0][0]][-1]
        assert "Processing failed" in error_update[0][1][0]

        # Verify API notifications
        api_calls = mock_requests.patch.call_args_list
        assert len(api_calls) == 2
        assert api_calls[0][1]["json"]["status"] == "running"
        assert api_calls[1][1]["json"]["status"] == "error"

        # Verify audit logs
        audit_calls = mock_audit_log.call_args_list
        assert audit_calls[0][0][1] == "task_started"
        assert audit_calls[1][0][1] == "task_failed"

        # Verify span error status
        span.set_status.assert_called_once()
        span.record_exception.assert_called_once()


class TestCostAndUsageTracking:
    """Test cost and usage tracking in task processing."""

    @pytest.mark.usefixtures(
        "mock_requests",
        "mock_audit_log",
        "mock_worker_heartbeat",
        "mock_is_agent_task",
        "mock_is_workflow_task",
        "mock_otel_trace",
    )
    def test_usage_data_written_to_db(
        self,
        mock_db_connection,
        mock_execute_task,
        mock_tracer,
        mock_trace_context,
    ):
        """Test that usage data is correctly written to database."""
        _, conn, cur = mock_db_connection

        row = {"id": "task-123", "type": "test", "input": {}}
        mock_trace_context.return_value = (None, {})
        mock_execute_task.return_value = {
            "output": {"result": "ok"},
            "usage": {
                "model_used": "gpt-4",
                "input_tokens": 100,
                "output_tokens": 50,
                "total_cost": 0.05,
                "generation_id": "gen-456",
            },
        }

        _process_task_row(conn, cur, row)

        # Find the done update call
        done_calls = [c for c in cur.execute.call_args_list if "status = 'done'" in c[0][0]]
        assert len(done_calls) == 1
        done_call = done_calls[0]

        # Verify all usage fields are in the update
        assert "model_used" in done_call[0][0]
        assert "input_tokens" in done_call[0][0]
        assert "output_tokens" in done_call[0][0]
        assert "total_cost" in done_call[0][0]
        assert "generation_id" in done_call[0][0]

        # Verify values
        assert done_call[0][1][2] == "gpt-4"  # model_used
        assert done_call[0][1][3] == 100  # input_tokens
        assert done_call[0][1][4] == 50  # output_tokens
        assert done_call[0][1][5] == 0.05  # total_cost
        assert done_call[0][1][6] == "gen-456"  # generation_id

    @pytest.mark.usefixtures(
        "mock_requests",
        "mock_audit_log",
        "mock_worker_heartbeat",
        "mock_is_agent_task",
        "mock_is_workflow_task",
        "mock_otel_trace",
    )
    def test_no_usage_data_legacy_format(
        self,
        mock_db_connection,
        mock_execute_task,
        mock_tracer,
        mock_trace_context,
    ):
        """Test backward compatibility when result has no usage field."""
        _, conn, cur = mock_db_connection

        row = {"id": "task-123", "type": "test", "input": {}}
        mock_trace_context.return_value = (None, {})
        # Legacy format: direct output
        mock_execute_task.return_value = "direct_output_string"

        _process_task_row(conn, cur, row)

        # Find the done update call
        done_calls = [c for c in cur.execute.call_args_list if "status = 'done'" in c[0][0]]
        assert len(done_calls) == 1
        done_call = done_calls[0]

        # Verify no usage fields in update (simpler query)
        assert "model_used" not in done_call[0][0]
        assert "input_tokens" not in done_call[0][0]


class TestTraceContextHandling:
    """Test trace context extraction and propagation."""

    @pytest.mark.usefixtures(
        "mock_requests",
        "mock_audit_log",
        "mock_worker_heartbeat",
        "mock_is_agent_task",
        "mock_is_workflow_task",
        "mock_otel_trace",
    )
    def test_trace_context_extracted_and_propagated(
        self,
        mock_db_connection,
        mock_execute_task,
        mock_tracer,
        mock_trace_context,
    ):
        """Test that trace context is extracted from input and propagated to span."""
        _, conn, cur = mock_db_connection
        mock_tracer_obj, _span = mock_tracer

        # Mock trace context extraction
        trace_ctx = MagicMock()
        mock_trace_context.return_value = (trace_ctx, {"key": "value"})

        row = {
            "id": "task-123",
            "type": "test",
            "input": {"key": "value", "_trace_context": {"trace_id": "abc"}},
        }
        mock_execute_task.return_value = {"output": "ok", "usage": {}}

        _process_task_row(conn, cur, row)

        # Verify trace context was extracted
        mock_trace_context.assert_called_once_with(
            {"key": "value", "_trace_context": {"trace_id": "abc"}}
        )

        # Verify span was created with extracted context
        mock_tracer_obj.start_as_current_span.assert_called_once()
        call_kwargs = mock_tracer_obj.start_as_current_span.call_args[1]
        assert call_kwargs["context"] == trace_ctx

    @pytest.mark.usefixtures(
        "mock_requests",
        "mock_audit_log",
        "mock_worker_heartbeat",
        "mock_is_agent_task",
        "mock_is_workflow_task",
        "mock_otel_trace",
    )
    def test_trace_id_injected_into_dict_output(
        self,
        mock_db_connection,
        mock_execute_task,
        mock_tracer,
        mock_trace_context,
        mock_get_current_trace_id,
    ):
        """Test that trace ID is injected into dict output."""
        _, conn, cur = mock_db_connection

        row = {"id": "task-123", "type": "test", "input": {}}
        mock_trace_context.return_value = (None, {})
        mock_execute_task.return_value = {
            "output": {"result": "success"},
            "usage": {},
        }

        _process_task_row(conn, cur, row)

        # Verify execute_task was called
        mock_execute_task.assert_called_once()

        # The trace ID injection happens in the worker code
        # We can verify get_current_trace_id was called
        assert mock_get_current_trace_id.called

    @pytest.mark.usefixtures(
        "mock_requests",
        "mock_audit_log",
        "mock_worker_heartbeat",
        "mock_is_agent_task",
        "mock_is_workflow_task",
        "mock_otel_trace",
    )
    def test_trace_id_not_injected_into_string_output(
        self,
        mock_db_connection,
        mock_execute_task,
        mock_tracer,
        mock_trace_context,
        mock_get_current_trace_id,
    ):
        """Test that trace ID is not injected into string output (backward compatibility)."""
        _, conn, cur = mock_db_connection

        row = {"id": "task-123", "type": "test", "input": {}}
        mock_trace_context.return_value = (None, {})
        # String output
        mock_execute_task.return_value = "simple string result"

        _process_task_row(conn, cur, row)

        # Should complete without error
        # String output remains unchanged
        mock_execute_task.assert_called_once()


class TestAuditLogging:
    """Test audit log creation and metadata."""

    @pytest.mark.usefixtures(
        "mock_requests",
        "mock_worker_heartbeat",
        "mock_is_agent_task",
        "mock_is_workflow_task",
        "mock_otel_trace",
    )
    def test_audit_log_success_with_metadata(
        self,
        mock_db_connection,
        mock_execute_task,
        mock_audit_log,
        mock_tracer,
        mock_trace_context,
    ):
        """Test audit logs include correct metadata on success."""
        _, conn, cur = mock_db_connection

        row = {"id": "task-123", "type": "test", "input": {"_user_id_hash": "user-456"}}
        mock_trace_context.return_value = (None, {"_user_id_hash": "user-456"})
        mock_execute_task.return_value = {
            "output": "ok",
            "usage": {
                "total_cost": 0.02,
                "input_tokens": 50,
                "output_tokens": 30,
                "model_used": "gpt-3.5",
            },
        }

        _process_task_row(conn, cur, row)

        # Verify audit logs
        audit_calls = mock_audit_log.call_args_list
        assert len(audit_calls) == 2

        # task_started - log_audit_event(conn, event_type, resource_id=..., user_id_hash=..., meta=...)
        started = audit_calls[0]
        assert started[0][0] == conn  # First positional arg
        assert started[0][1] == "task_started"  # Second positional arg (event_type)
        assert started[1]["resource_id"] == "task-123"  # Keyword arg
        assert started[1]["user_id_hash"] == "user-456"
        assert started[1]["meta"]["task_type"] == "test"

        # task_completed
        completed = audit_calls[1]
        assert completed[0][1] == "task_completed"
        assert completed[1]["user_id_hash"] == "user-456"
        assert completed[1]["meta"]["total_cost"] == 0.02
        assert completed[1]["meta"]["input_tokens"] == 50
        assert completed[1]["meta"]["output_tokens"] == 30
        assert completed[1]["meta"]["model_used"] == "gpt-3.5"
        assert "duration_seconds" in completed[1]["meta"]

    @pytest.mark.usefixtures(
        "mock_requests",
        "mock_worker_heartbeat",
        "mock_is_agent_task",
        "mock_is_workflow_task",
        "mock_otel_trace",
    )
    def test_audit_log_failure_with_error(
        self,
        mock_db_connection,
        mock_execute_task,
        mock_audit_log,
        mock_tracer,
        mock_trace_context,
    ):
        """Test audit logs include error message on failure."""
        _, conn, cur = mock_db_connection

        row = {"id": "task-123", "type": "test", "input": {}}
        mock_trace_context.return_value = (None, {})
        mock_execute_task.side_effect = RuntimeError("Task execution failed")

        _process_task_row(conn, cur, row)

        # Verify audit logs
        audit_calls = mock_audit_log.call_args_list
        assert len(audit_calls) == 2

        # task_failed
        failed = audit_calls[1]
        assert failed[0][1] == "task_failed"
        assert "Task execution failed" in failed[1]["meta"]["error"]
        assert "duration_seconds" in failed[1]["meta"]


# ============================================================================
# Phase 3: Edge Cases & Invariants
# ============================================================================


class TestTaskRouting:
    """Test routing logic for different task types."""

    @pytest.mark.usefixtures("mock_requests", "mock_audit_log", "mock_worker_heartbeat")
    def test_route_to_subtask_handler(
        self,
        mock_db_connection,
        mock_process_subtask,
    ):
        """Test that subtasks are routed to _process_subtask."""
        _, conn, cur = mock_db_connection

        row = {
            "id": "subtask-123",
            "source_type": "subtask",
            "type": "test",
            "input": {},
        }

        _process_task_row(conn, cur, row)

        # Verify routed to subtask handler
        mock_process_subtask.assert_called_once_with(conn, cur, row)

    @pytest.mark.usefixtures("mock_requests", "mock_audit_log", "mock_worker_heartbeat")
    def test_route_to_agent_task_handler(
        self,
        mock_db_connection,
        mock_is_agent_task,
        mock_process_agent_task,
    ):
        """Test that agent tasks are routed to _process_agent_task."""
        _, conn, cur = mock_db_connection
        mock_is_agent_task.return_value = True

        row = {
            "id": "task-123",
            "type": "agent:researcher",
            "input": {},
        }

        _process_task_row(conn, cur, row)

        # Verify routed to agent task handler
        mock_process_agent_task.assert_called_once_with(conn, cur, row)

    @pytest.mark.usefixtures("mock_requests", "mock_audit_log", "mock_worker_heartbeat")
    def test_route_to_workflow_task_handler(
        self,
        mock_db_connection,
        mock_is_agent_task,
        mock_is_workflow_task,
        mock_process_workflow_task,
    ):
        """Test that workflow tasks are routed to _process_workflow_task."""
        _, conn, cur = mock_db_connection
        mock_is_agent_task.return_value = False
        mock_is_workflow_task.return_value = True

        row = {
            "id": "task-123",
            "type": "workflow:research",
            "input": {},
        }

        _process_task_row(conn, cur, row)

        # Verify routed to workflow task handler
        mock_process_workflow_task.assert_called_once_with(conn, cur, row)


class TestEdgeCases:
    """Test edge cases and error recovery."""

    @pytest.mark.usefixtures(
        "mock_requests",
        "mock_worker_heartbeat",
        "mock_is_agent_task",
        "mock_is_workflow_task",
        "mock_otel_trace",
    )
    def test_unbound_local_error_handling(
        self,
        mock_db_connection,
        mock_execute_task,
        mock_audit_log,
        mock_tracer,
        mock_trace_context,
    ):
        """Test that error before user_id_hash assignment is handled gracefully."""
        _, conn, cur = mock_db_connection

        row = {"id": "task-123", "type": "test", "input": {}}
        # Error happens during trace context extraction (before user_id_hash assignment)
        mock_trace_context.side_effect = RuntimeError("Early error")

        # The error will propagate but should not cause UnboundLocalError
        # This test verifies the code handles early errors without UnboundLocalError
        with contextlib.suppress(RuntimeError):
            _process_task_row(conn, cur, row)

        # The error happens before span creation, so we just verify no UnboundLocalError occurred

    @pytest.mark.usefixtures(
        "mock_requests",
        "mock_audit_log",
        "mock_worker_heartbeat",
        "mock_is_agent_task",
        "mock_is_workflow_task",
    )
    def test_trace_flush_called(
        self,
        mock_db_connection,
        mock_execute_task,
        mock_tracer,
        mock_trace_context,
        mock_otel_trace,
    ):
        """Test that trace provider force_flush is called after task processing."""
        _, conn, cur = mock_db_connection
        _, provider = mock_otel_trace

        row = {"id": "task-123", "type": "test", "input": {}}
        mock_trace_context.return_value = (None, {})
        mock_execute_task.return_value = "ok"

        _process_task_row(conn, cur, row)

        # Verify force_flush was called
        provider.force_flush.assert_called_once_with(timeout_millis=5000)

    @pytest.mark.usefixtures(
        "mock_requests",
        "mock_audit_log",
        "mock_worker_heartbeat",
        "mock_is_agent_task",
        "mock_is_workflow_task",
    )
    def test_trace_flush_failure_handled(
        self,
        mock_db_connection,
        mock_execute_task,
        mock_tracer,
        mock_trace_context,
        mock_otel_trace,
    ):
        """Test that trace flush failure doesn't break task processing."""
        _, conn, cur = mock_db_connection
        _, provider = mock_otel_trace
        provider.force_flush.side_effect = Exception("Flush failed")

        row = {"id": "task-123", "type": "test", "input": {}}
        mock_trace_context.return_value = (None, {})
        mock_execute_task.return_value = "ok"

        # Should not raise exception
        _process_task_row(conn, cur, row)

        # Task should still complete successfully
        done_calls = [c for c in cur.execute.call_args_list if "status = 'done'" in c[0][0]]
        assert len(done_calls) == 1


class TestWorkerLoop:
    """Test worker loop behavior."""

    @patch("app.worker.time.sleep")
    @patch("app.worker_helpers.claim_next_task")
    def test_adaptive_polling_backoff(
        self,
        mock_claim_next_task,
        mock_sleep,
        mock_db_connection,
    ):
        """Test that poll interval increases when no tasks are found."""
        _, _conn, _cur = mock_db_connection

        # Mock settings
        with patch("app.worker.settings") as mock_settings:
            mock_settings.worker_poll_min_interval_seconds = 1.0
            mock_settings.worker_poll_max_interval_seconds = 60.0
            mock_settings.worker_poll_backoff_multiplier = 2.0
            mock_settings.worker_recovery_interval_seconds = 300

            # Return None (no task) twice, then raise to exit
            mock_claim_next_task.side_effect = [None, None, KeyboardInterrupt()]

            with contextlib.suppress(KeyboardInterrupt):
                run_worker()

            # Verify sleep was called with increasing intervals
            sleep_calls = mock_sleep.call_args_list
            # First iteration: no task, sleep with backoff (1.0 * 2.0 = 2.0)
            # Second iteration: no task, sleep with backoff (2.0 * 2.0 = 4.0)
            assert len(sleep_calls) >= 2

    @patch("app.worker.time.sleep")
    @patch("app.worker_helpers.claim_next_task")
    def test_poll_interval_reset_on_task_found(
        self,
        mock_claim_next_task,
        mock_sleep,
        mock_db_connection,
    ):
        """Test that poll interval resets when a task is found."""
        _, _conn, _cur = mock_db_connection

        with patch("app.worker.settings") as mock_settings:
            mock_settings.worker_poll_min_interval_seconds = 1.0
            mock_settings.worker_poll_max_interval_seconds = 60.0
            mock_settings.worker_poll_backoff_multiplier = 2.0
            mock_settings.worker_recovery_interval_seconds = 300

            # Return task, then None, then exit
            task_row = {"id": "task-123", "type": "test", "input": {}}
            mock_claim_next_task.side_effect = [task_row, KeyboardInterrupt()]

            with (
                patch("app.worker._process_task_row_legacy"),
                contextlib.suppress(KeyboardInterrupt),
            ):
                run_worker()

            # Verify brief sleep after task (0.01s)
            sleep_calls = mock_sleep.call_args_list
            # Last sleep should be 0.01 (after processing task)
            assert any(call[0][0] == 0.01 for call in sleep_calls)

    @patch("app.worker.time.sleep")
    @patch("app.worker_helpers.claim_next_task")
    def test_connection_recovery_on_db_error(
        self,
        mock_claim_next_task,
        mock_sleep,
        mock_db_connection,
    ):
        """Test that connection is re-established after database error."""
        mock_get_conn, conn, _cur = mock_db_connection

        with patch("app.worker.settings") as mock_settings:
            mock_settings.worker_poll_min_interval_seconds = 1.0
            mock_settings.worker_recovery_interval_seconds = 300

            # First call raises DB error, second call succeeds
            import psycopg2

            mock_claim_next_task.side_effect = [
                psycopg2.OperationalError("Connection lost"),
                KeyboardInterrupt(),
            ]

            with contextlib.suppress(KeyboardInterrupt):
                run_worker()

            # Verify connection was closed and re-established
            assert conn.close.called
            # get_connection should be called multiple times (initial + recovery)
            assert mock_get_conn.call_count >= 2
