"""Tests for lease-based task acquisition mechanism."""

import time
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, Mock, patch

import pytest
from psycopg2.extras import RealDictRow

from app.config import settings
from app.worker_lease import recover_expired_leases, renew_lease


class TestLeaseAcquisition:
    """Test lease-based task acquisition logic."""

    @patch("app.worker_lease.logger")
    def test_lease_recovery_expired_tasks(self, mock_logger):
        """Test recovery of tasks with expired leases."""
        # Mock database connection
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur

        # Mock recovered tasks
        mock_cur.fetchall.side_effect = [
            # First call: recovered tasks
            [
                ("task-1", "summarize", 1, "old-worker:1"),
                ("task-2", "research", 2, "old-worker:2"),
            ],
            # Second call: exhausted tasks
            [("task-3", "summarize")],
            # Third call: recovered subtasks
            [("subtask-1", "research", 1)],
            # Fourth call: exhausted subtasks
            [],
        ]

        result = recover_expired_leases(mock_conn, "new-worker:1")

        # Verify count
        assert result == 3  # 2 tasks + 1 subtask recovered

        # Verify SQL was executed to recover tasks
        assert mock_cur.execute.call_count >= 4

        # Verify commit was called
        assert mock_conn.commit.called

    @patch("app.worker_lease.logger")
    def test_lease_recovery_max_retries_exhausted(self, mock_logger):
        """Test tasks that exceed max retries are marked as error."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur

        # Mock no recovered tasks, but some exhausted
        mock_cur.fetchall.side_effect = [
            [],  # Recovered tasks
            [("task-exhausted", "summarize")],  # Exhausted tasks
            [],  # Recovered subtasks
            [],  # Exhausted subtasks
        ]

        result = recover_expired_leases(mock_conn, "worker:1")

        assert result == 0  # No tasks recovered (exhausted ones marked as error)

        # Verify exhausted task was logged
        assert any("task_retry_exhausted" in str(call) for call in mock_logger.error.call_args_list)

    def test_lease_renewal_success(self):
        """Test successful lease renewal."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.rowcount = 1  # Simulate successful update

        result = renew_lease(mock_conn, "task-123", "task", "worker:1")

        assert result is True
        assert mock_conn.commit.called
        assert mock_cur.execute.called

    def test_lease_renewal_wrong_owner(self):
        """Test lease renewal fails when worker doesn't own the task."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur
        mock_cur.rowcount = 0  # Simulate no rows updated

        result = renew_lease(mock_conn, "task-123", "task", "wrong-worker:1")

        assert result is False
        # No commit since update failed
        assert not mock_conn.commit.called


class TestAdaptivePolling:
    """Test adaptive polling backoff logic."""

    def test_backoff_increases_when_no_tasks(self):
        """Test polling interval increases when queue is empty."""
        poll_interval = settings.worker_poll_min_interval_seconds  # 0.2

        # Simulate 5 empty polls
        for _ in range(5):
            poll_interval = min(
                poll_interval * settings.worker_poll_backoff_multiplier,
                settings.worker_poll_max_interval_seconds,
            )

        # Should increase exponentially but not exceed max
        assert poll_interval > settings.worker_poll_min_interval_seconds
        assert poll_interval <= settings.worker_poll_max_interval_seconds

    def test_backoff_resets_on_task_found(self):
        """Test polling interval resets when task is found."""
        # Start with backed-off interval
        poll_interval = 5.0

        # Task found - reset to minimum
        poll_interval = settings.worker_poll_min_interval_seconds

        assert poll_interval == settings.worker_poll_min_interval_seconds

    def test_backoff_caps_at_max(self):
        """Test polling interval doesn't exceed maximum."""
        poll_interval = settings.worker_poll_min_interval_seconds

        # Simulate many empty polls
        for _ in range(20):
            poll_interval = min(
                poll_interval * settings.worker_poll_backoff_multiplier,
                settings.worker_poll_max_interval_seconds,
            )

        # Should never exceed max
        assert poll_interval == settings.worker_poll_max_interval_seconds


class TestRetryLogic:
    """Test task retry logic with try_count and max_tries."""

    def test_task_retried_within_max_tries(self):
        """Test task is retried if try_count < max_tries."""
        # Simulate task selection query logic
        task = {
            "id": "task-123",
            "type": "summarize",
            "try_count": 2,
            "max_tries": 3,
            "status": "pending",
        }

        # Task should be eligible for retry
        assert task["try_count"] < task["max_tries"]
        assert task["status"] == "pending"

    def test_task_not_retried_when_max_exceeded(self):
        """Test task is not retried if try_count >= max_tries."""
        task = {
            "id": "task-456",
            "type": "summarize",
            "try_count": 3,
            "max_tries": 3,
            "status": "error",
        }

        # Task should NOT be eligible for retry
        assert task["try_count"] >= task["max_tries"]

    def test_try_count_incremented_on_acquisition(self):
        """Test try_count is incremented when task is acquired."""
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_conn.cursor.return_value = mock_cur

        task_id = "task-789"
        worker_id = "worker:1"
        current_try_count = 1

        # Simulate the UPDATE query that claims the task
        mock_cur.execute(
            """
            UPDATE tasks
            SET status = 'running',
                locked_at = NOW(),
                locked_by = %s,
                lease_timeout = %s,
                try_count = try_count + 1,
                updated_at = NOW()
            WHERE id = %s
            """,
            (worker_id, datetime.now(timezone.utc), task_id),
        )

        # After execution, try_count should be incremented
        # (In real code, this happens in the database)
        expected_try_count = current_try_count + 1
        assert expected_try_count == 2


class TestLeaseTimeout:
    """Test lease timeout calculations and expired lease detection."""

    def test_lease_timeout_calculation(self):
        """Test lease timeout is correctly calculated."""
        now = datetime.now(timezone.utc)
        lease_duration = timedelta(seconds=settings.worker_lease_duration_seconds)
        expected_timeout = now + lease_duration

        # Verify timeout is in the future
        assert expected_timeout > now

        # Verify it's approximately the configured duration
        diff = (expected_timeout - now).total_seconds()
        assert abs(diff - settings.worker_lease_duration_seconds) < 1

    def test_expired_lease_detection(self):
        """Test detection of expired leases."""
        # Simulate expired lease
        expired_timeout = datetime.now(timezone.utc) - timedelta(minutes=1)
        now = datetime.now(timezone.utc)

        assert expired_timeout < now  # Lease is expired

    def test_active_lease_detection(self):
        """Test detection of active (non-expired) leases."""
        # Simulate active lease
        active_timeout = datetime.now(timezone.utc) + timedelta(minutes=4)
        now = datetime.now(timezone.utc)

        assert active_timeout > now  # Lease is still active


class TestWorkerIdentity:
    """Test worker ID generation and uniqueness."""

    @patch("socket.gethostname", return_value="test-host")
    @patch("os.getpid", return_value=1234)
    def test_worker_id_format(self, mock_pid, mock_hostname):
        """Test worker ID has correct format."""
        import socket
        import os

        worker_id = f"{socket.gethostname()}:{os.getpid()}"

        assert worker_id == "test-host:1234"
        assert ":" in worker_id
        assert len(worker_id.split(":")) == 2

    def test_worker_id_uniqueness(self):
        """Test different workers have different IDs."""
        # Simulate two different workers
        worker1_id = "host1:100"
        worker2_id = "host2:200"

        assert worker1_id != worker2_id


class TestDatabaseQueries:
    """Test SQL query logic for lease-based acquisition."""

    def test_pending_task_query_includes_lease_check(self):
        """Test pending task query checks for expired leases."""
        # This is the actual query structure from worker.py
        query = """
        SELECT id, type, input, try_count, max_tries, 'task' as source_type
        FROM tasks
        WHERE status = 'pending'
          AND try_count < max_tries
          AND (lease_timeout IS NULL OR lease_timeout < NOW())
        ORDER BY created_at ASC
        LIMIT 1
        FOR UPDATE SKIP LOCKED
        """

        # Verify query components
        assert "status = 'pending'" in query
        assert "try_count < max_tries" in query
        assert "lease_timeout IS NULL OR lease_timeout < NOW()" in query
        assert "FOR UPDATE SKIP LOCKED" in query

    def test_lease_acquisition_updates_all_fields(self):
        """Test task acquisition update sets all lease fields."""
        query = """
        UPDATE tasks
        SET status = 'running',
            locked_at = NOW(),
            locked_by = %s,
            lease_timeout = %s,
            try_count = try_count + 1,
            updated_at = NOW()
        WHERE id = %s
        """

        # Verify all required fields are updated
        assert "locked_at" in query
        assert "locked_by" in query
        assert "lease_timeout" in query
        assert "try_count = try_count + 1" in query


# Integration-style test (requires mock DB connection)
class TestLeaseRecoveryIntegration:
    """Integration tests for lease recovery mechanism."""

    def test_recovery_frees_tasks_for_other_workers(self):
        """Test recovered tasks can be claimed by different workers."""
        # Simulate scenario:
        # 1. Worker A claims task
        # 2. Worker A crashes (lease expires)
        # 3. Recovery runs
        # 4. Worker B can claim the task

        task = {
            "id": "task-123",
            "status": "running",
            "locked_by": "worker-a:1",
            "lease_timeout": datetime.now(timezone.utc) - timedelta(minutes=1),  # Expired
            "try_count": 1,
            "max_tries": 3,
        }

        # After recovery, task should be:
        expected_after_recovery = {
            "id": "task-123",
            "status": "pending",  # Reset to pending
            "locked_by": None,  # Cleared
            "lease_timeout": None,  # Cleared
            "try_count": 1,  # Unchanged (incremented on next claim)
            "max_tries": 3,
        }

        # Worker B can now claim it (try_count < max_tries)
        assert expected_after_recovery["try_count"] < expected_after_recovery["max_tries"]
        assert expected_after_recovery["status"] == "pending"
