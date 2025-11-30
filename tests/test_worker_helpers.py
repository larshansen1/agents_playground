from unittest.mock import MagicMock, patch

import pytest

from app.worker_helpers import _process_subtask, _process_workflow_task, claim_next_task


@pytest.fixture
def mock_conn():
    return MagicMock()


@pytest.fixture
def mock_cur():
    return MagicMock()


@pytest.fixture
def mock_worker_deps():
    with patch("app.worker_helpers._get_worker_deps") as mock:
        notify = MagicMock()
        heartbeat = MagicMock()
        mock.return_value = (notify, heartbeat)
        yield notify, heartbeat


class TestSubtaskProcessing:
    @patch("app.worker_helpers.get_agent")
    @patch("app.worker_helpers.aggregate_subtask_costs")
    @patch("app.worker_helpers.get_workflow_state")
    @patch("app.worker_helpers.get_orchestrator")
    def test_process_subtask_success(
        self,
        mock_get_orch,
        mock_get_state,
        mock_agg,
        mock_get_agent,
        mock_conn,
        mock_cur,
        mock_worker_deps,
    ):
        # Setup
        row = {
            "id": "sub-1",
            "parent_task_id": "parent-1",
            "agent_type": "researcher",
            "input": {"topic": "AI"},
            "iteration": 1,
        }

        mock_agent = MagicMock()
        mock_agent.execute.return_value = {
            "output": {"result": "data"},
            "usage": {"total_cost": 0.1},
        }
        mock_get_agent.return_value = mock_agent

        mock_get_state.return_value = {"workflow_type": "declarative:test"}

        mock_orch = MagicMock()
        mock_orch.process_subtask_completion.return_value = {"action": "continue"}
        mock_get_orch.return_value = mock_orch

        # Execute
        _process_subtask(mock_conn, mock_cur, row)

        # Verify
        mock_agent.execute.assert_called_once()
        # Should update status to running then done
        assert mock_cur.execute.call_count >= 2
        mock_conn.commit.assert_called()

    @patch("app.worker_helpers.get_agent")
    def test_process_subtask_failure(self, mock_get_agent, mock_conn, mock_cur, mock_worker_deps):
        row = {
            "id": "sub-1",
            "parent_task_id": "parent-1",
            "agent_type": "researcher",
            "input": {"topic": "AI"},
            "iteration": 1,
        }

        mock_get_agent.side_effect = Exception("Agent failed")

        _process_subtask(mock_conn, mock_cur, row)

        # Verify error handling
        # Should update subtask to error and parent task to error
        error_calls = [
            call for call in mock_cur.execute.call_args_list if "status = 'error'" in call[0][0]
        ]
        assert len(error_calls) >= 2


class TestWorkflowTaskProcessing:
    @patch("app.worker_helpers.extract_workflow_type")
    @patch("app.worker_helpers.get_orchestrator")
    def test_process_workflow_task_success(
        self, mock_get_orch, mock_extract, mock_conn, mock_cur, mock_worker_deps
    ):
        row = {"id": "task-1", "type": "declarative:test", "input": {"topic": "AI"}}

        mock_extract.return_value = "test"
        mock_orch = MagicMock()
        mock_get_orch.return_value = mock_orch

        _process_workflow_task(mock_conn, mock_cur, row)

        mock_orch.create_workflow.assert_called_once()
        mock_cur.execute.assert_called()  # Update to running
        mock_conn.commit.assert_called()

    @patch("app.worker_helpers.get_orchestrator")
    def test_process_workflow_task_failure(
        self, mock_get_orch, mock_conn, mock_cur, mock_worker_deps
    ):
        row = {"id": "task-1", "type": "declarative:test", "input": {"topic": "AI"}}

        mock_get_orch.side_effect = Exception("Orchestrator failed")

        _process_workflow_task(mock_conn, mock_cur, row)

        # Verify error update
        error_calls = [
            call for call in mock_cur.execute.call_args_list if "status = 'error'" in call[0][0]
        ]
        assert len(error_calls) >= 1


class TestClaimTask:
    def test_claim_next_task_subtask(self, mock_conn, mock_cur):
        # Mock finding a subtask
        mock_cur.fetchone.side_effect = [
            {
                "id": "sub-1",
                "parent_task_id": "p-1",
                "agent_type": "a",
                "iteration": 1,
                "status": "pending",
                "input": {},
                "try_count": 0,
                "max_tries": 3,
                "source_type": "subtask",
            },
            None,  # Second fetchone call (if any)
        ]

        settings = MagicMock()
        settings.worker_lease_duration_seconds = 60

        result = claim_next_task(mock_conn, mock_cur, "worker-1", settings)

        assert result["id"] == "sub-1"
        # Verify update
        update_call = mock_cur.execute.call_args_list[-1]
        assert "UPDATE subtasks" in update_call[0][0]

    def test_claim_next_task_task(self, mock_conn, mock_cur):
        # Mock no subtask, but find task
        mock_cur.fetchone.side_effect = [
            None,  # No subtask
            {
                "id": "task-1",
                "type": "t",
                "input": {},
                "try_count": 0,
                "max_tries": 3,
                "source_type": "task",
            },
        ]

        settings = MagicMock()
        settings.worker_lease_duration_seconds = 60

        result = claim_next_task(mock_conn, mock_cur, "worker-1", settings)

        assert result["id"] == "task-1"
        # Verify update
        update_call = mock_cur.execute.call_args_list[-1]
        assert "UPDATE tasks" in update_call[0][0]

    def test_claim_next_task_none(self, mock_conn, mock_cur):
        # Mock nothing found
        mock_cur.fetchone.return_value = None

        settings = MagicMock()
        settings.worker_lease_duration_seconds = 60

        result = claim_next_task(mock_conn, mock_cur, "worker-1", settings)

        assert result is None
