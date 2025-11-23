import contextlib
from unittest.mock import MagicMock, patch

import pytest

from app.worker import _process_task_row, notify_api_async, run_worker


@pytest.fixture
def mock_requests():
    with patch("app.worker.requests") as mock:
        yield mock


@pytest.fixture
def mock_db_connection():
    with patch("app.worker.get_connection") as mock:
        conn = MagicMock()
        cur = MagicMock()
        conn.cursor.return_value = cur
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
        mock.start_as_current_span.return_value.__enter__.return_value = span
        yield mock, span


@pytest.fixture
def mock_audit_log():
    with patch("app.worker.log_audit_event") as mock:
        yield mock


class TestWorkerNotification:
    def test_notify_api_async_success(self, mock_requests):
        """Test successful API notification."""
        mock_requests.patch.return_value.status_code = 200

        notify_api_async("task-123", "running")

        mock_requests.patch.assert_called_once()
        args, kwargs = mock_requests.patch.call_args
        assert "task-123" in args[0]
        assert kwargs["json"] == {"status": "running"}

    def test_notify_api_async_with_output(self, mock_requests):
        """Test API notification with output."""
        mock_requests.patch.return_value.status_code = 200

        notify_api_async("task-123", "done", output={"result": "ok"})

        _, kwargs = mock_requests.patch.call_args
        assert kwargs["json"] == {"status": "done", "output": {"result": "ok"}}

    def test_notify_api_async_failure(self, mock_requests):
        """Test API notification failure (should not raise exception)."""
        mock_requests.patch.side_effect = Exception("Network error")

        # Should not raise exception
        notify_api_async("task-123", "running")
        mock_requests.patch.assert_called_once()


class TestTaskProcessing:
    @pytest.mark.usefixtures("mock_tracer")
    def test_process_task_success(
        self, mock_db_connection, mock_execute_task, mock_requests, mock_audit_log
    ):
        """Test successful task processing flow."""
        _, conn, cur = mock_db_connection

        # Mock task row
        row = {
            "id": "task-123",
            "type": "test_task",
            "input": {"key": "value", "_trace_context": {}},
        }

        # Mock execution result
        mock_execute_task.return_value = {"output": "result", "usage": {"total_cost": 0.01}}

        _process_task_row(conn, cur, row)

        # Verify DB updates
        # 1. Status update to running
        assert cur.execute.call_count >= 2
        # 2. Status update to done
        call_args_list = cur.execute.call_args_list
        assert "running" in call_args_list[0][0][0]
        assert "done" in call_args_list[1][0][0]

        # Verify API notifications
        assert mock_requests.patch.call_count == 2

        # Verify execute_task called
        mock_execute_task.assert_called_once_with("test_task", {"key": "value"}, None)

        # Verify audit logs (Start + Complete)
        assert mock_audit_log.call_count == 2
        assert mock_audit_log.call_args_list[0][0][1] == "task_started"
        assert mock_audit_log.call_args_list[1][0][1] == "task_completed"

    @pytest.mark.usefixtures("mock_tracer")
    def test_process_task_execution_error(
        self, mock_db_connection, mock_execute_task, mock_requests, mock_audit_log
    ):
        """Test task processing with execution error."""
        _, conn, cur = mock_db_connection

        row = {"id": "task-123", "type": "test_task", "input": {"key": "value"}}

        # Mock execution failure
        mock_execute_task.side_effect = ValueError("Processing failed")

        _process_task_row(conn, cur, row)

        # Verify DB update to error
        call_args_list = cur.execute.call_args_list
        assert "error" in call_args_list[-1][0][0]
        assert "Processing failed" in call_args_list[-1][0][1][0]

        # Verify API notification for error
        assert mock_requests.patch.call_count == 2  # running, then error

        # Verify audit logs (Start + Failed)
        assert mock_audit_log.call_count == 2
        assert mock_audit_log.call_args_list[0][0][1] == "task_started"
        assert mock_audit_log.call_args_list[1][0][1] == "task_failed"

    @pytest.mark.usefixtures("mock_requests", "mock_tracer", "mock_audit_log")
    def test_process_task_legacy_result(self, mock_db_connection, mock_execute_task):
        """Test backward compatibility for legacy result format (direct output)."""
        _, conn, cur = mock_db_connection

        row = {"id": "task-123", "type": "test", "input": {}}
        mock_execute_task.return_value = "direct_output_string"

        _process_task_row(conn, cur, row)

        # Verify done update uses the string output
        call_args = cur.execute.call_args
        # The Json wrapper makes it hard to check exact value, but we can check the structure
        assert "done" in call_args[0][0]


class TestWorkerLoop:
    def test_run_worker_one_loop(self, mock_db_connection):
        """Test one iteration of the worker loop."""
        _, _, cur = mock_db_connection

        # Mock sleep to avoid waiting
        with patch("app.worker.time.sleep"):
            # Mock finding no tasks then raising KeyboardInterrupt to break loop
            # This is a trick to test the loop logic without infinite loop
            # First call: returns None (no task), Second call: raises KeyboardInterrupt to break
            cur.fetchone.side_effect = [None, KeyboardInterrupt("Break Loop")]

            with contextlib.suppress(KeyboardInterrupt):
                run_worker()

        # Verify it tried to fetch a task
        assert cur.execute.called
        assert "SELECT id" in cur.execute.call_args[0][0]
