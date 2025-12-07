from unittest.mock import MagicMock, patch

import pytest

from app.worker_helpers import (
    _handle_workflow_completion,
    _process_agent_task,
    _process_subtask,
    _process_workflow_task,
    claim_next_task,
)


@pytest.fixture
def mock_conn():
    return MagicMock()


@pytest.fixture
def mock_cur():
    return MagicMock()


@pytest.fixture
def mock_notify_api():
    with patch("app.worker_helpers.notify_api_async") as mock:
        yield mock


@pytest.fixture
def mock_worker_heartbeat():
    with patch("app.worker_helpers.worker_heartbeat") as mock:
        yield mock


class TestHandleWorkflowCompletion:
    def test_handle_workflow_completion_complete(self, mock_conn, mock_cur, mock_notify_api):
        _handle_workflow_completion(
            "complete", "task-1", {"result": "ok"}, mock_conn, mock_cur, mock_notify_api
        )

        # Verify UPDATE tasks SET status='done' executed
        mock_cur.execute.assert_called_once()
        sql = mock_cur.execute.call_args[0][0]
        assert "UPDATE tasks" in sql
        assert "status = 'done'" in sql
        assert "output = %s" in sql

        mock_conn.commit.assert_called_once()
        mock_notify_api.assert_called_once_with("task-1", "done", output={"result": "ok"})

    def test_handle_workflow_completion_failed(self, mock_conn, mock_cur, mock_notify_api):
        _handle_workflow_completion(
            "failed", "task-1", {"error": "bad"}, mock_conn, mock_cur, mock_notify_api
        )

        # Verify UPDATE tasks SET status='error' executed
        mock_cur.execute.assert_called_once()
        sql = mock_cur.execute.call_args[0][0]
        assert "UPDATE tasks" in sql
        assert "status = 'error'" in sql
        assert "error = %s" in sql

        mock_conn.commit.assert_called_once()
        mock_notify_api.assert_called_once()
        assert mock_notify_api.call_args[0][1] == "error"


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
        mock_notify_api,
        mock_worker_heartbeat,
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

        # Verify status transitions: running -> done
        calls = mock_cur.execute.call_args_list
        running_update = any("status = 'running'" in str(call) for call in calls)
        done_update = any("status = 'done'" in str(call) for call in calls)
        assert running_update, "Subtask should be updated to running"
        assert done_update, "Subtask should be updated to done"

        mock_conn.commit.assert_called()

        # Verify orchestrator interaction
        mock_orch.process_subtask_completion.assert_called_once()
        mock_agg.assert_called_once_with("parent-1", mock_conn)

    @patch("app.worker_helpers.get_agent")
    @patch("app.worker_helpers.aggregate_subtask_costs")
    @patch("app.worker_helpers.get_workflow_state")
    @patch("app.worker_helpers.get_orchestrator")
    @patch("app.worker_helpers._handle_workflow_completion")
    def test_process_subtask_workflow_completion_actions(
        self,
        mock_handle_complete,
        mock_get_orch,
        mock_get_state,
        mock_agg,
        mock_get_agent,
        mock_conn,
        mock_cur,
        mock_notify_api,
        mock_worker_heartbeat,
    ):
        row = {
            "id": "sub-1",
            "parent_task_id": "parent-1",
            "agent_type": "researcher",
            "input": {"topic": "AI"},
            "iteration": 1,
        }

        mock_agent = MagicMock()
        mock_agent.execute.return_value = {"output": {"result": "data"}}
        mock_get_agent.return_value = mock_agent
        mock_get_state.return_value = {"workflow_type": "declarative:test"}

        # Test 'complete' action
        mock_get_orch.return_value.process_subtask_completion.return_value = {
            "action": "complete",
            "output": {"final": "result"},
        }

        _process_subtask(mock_conn, mock_cur, row)

        mock_handle_complete.assert_called_with(
            "complete", "parent-1", {"final": "result"}, mock_conn, mock_cur, mock_notify_api
        )

    @patch("app.worker_helpers.get_agent")
    def test_process_subtask_failure(
        self, mock_get_agent, mock_conn, mock_cur, mock_notify_api, mock_worker_heartbeat
    ):
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

        # Verify specific error updates
        subtask_error = any("UPDATE subtasks" in str(call) for call in error_calls)
        parent_error = any("UPDATE tasks" in str(call) for call in error_calls)
        assert subtask_error, "Subtask should be updated to error"
        assert parent_error, "Parent task should be updated to error"

        # Verify notification
        mock_notify_api.assert_called_with("parent-1", "error", error="Agent failed")

    @patch("app.worker_helpers.get_agent")
    @patch("app.worker_helpers.aggregate_subtask_costs")
    @patch("app.worker_helpers.get_workflow_state")
    @patch("app.worker_helpers.get_orchestrator")
    def test_process_subtask_cost_usage_handling(
        self,
        mock_get_orch,
        mock_get_state,
        mock_agg,
        mock_get_agent,
        mock_conn,
        mock_cur,
        mock_notify_api,
        mock_worker_heartbeat,
    ):
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
            "usage": {
                "total_cost": 0.5,
                "model_used": "gpt-4",
                "input_tokens": 100,
                "output_tokens": 50,
                "generation_id": "gen-1",
            },
        }
        mock_get_agent.return_value = mock_agent
        mock_get_state.return_value = {"workflow_type": "declarative:test"}
        mock_get_orch.return_value.process_subtask_completion.return_value = {"action": "continue"}

        _process_subtask(mock_conn, mock_cur, row)

        # Verify usage fields updated
        update_calls = [
            call
            for call in mock_cur.execute.call_args_list
            if "UPDATE subtasks" in str(call) and "total_cost" in str(call)
        ]
        assert len(update_calls) == 1
        # call.args is the first element of the call tuple
        args = update_calls[0][0]
        sql = args[0]
        params = args[1]

        assert "model_used = %s" in sql
        assert "input_tokens = %s" in sql
        assert "output_tokens = %s" in sql
        assert "total_cost = %s" in sql

        # Verify params (order depends on query, but checking values exist in params)
        assert 0.5 in params
        assert "gpt-4" in params
        assert 100 in params
        assert 50 in params
        assert "gen-1" in params

    @patch("app.worker_helpers.get_agent")
    def test_process_subtask_parent_child_error_updates(
        self, mock_get_agent, mock_conn, mock_cur, mock_notify_api, mock_worker_heartbeat
    ):
        row = {
            "id": "sub-1",
            "parent_task_id": "parent-1",
            "agent_type": "researcher",
            "input": {"topic": "AI"},
            "iteration": 1,
        }

        mock_get_agent.side_effect = Exception("Critical failure")

        _process_subtask(mock_conn, mock_cur, row)

        # Verify two separate error updates
        error_calls = [
            call for call in mock_cur.execute.call_args_list if "status = 'error'" in call[0][0]
        ]
        assert len(error_calls) >= 2

        # Check subtask update
        subtask_update = next(call for call in error_calls if "UPDATE subtasks" in call[0][0])
        assert "Critical failure" in subtask_update[0][1]

        # Check parent task update
        parent_update = next(call for call in error_calls if "UPDATE tasks" in call[0][0])
        assert "Subtask failed: Critical failure" in parent_update[0][1]

    @patch("app.worker_helpers.get_agent")
    @patch("app.worker_helpers.aggregate_subtask_costs")
    @patch("app.worker_helpers.get_workflow_state")
    @patch("app.worker_helpers.get_orchestrator")
    def test_process_subtask_with_trace_context(
        self,
        mock_get_orch,
        mock_get_state,
        mock_agg,
        mock_get_agent,
        mock_conn,
        mock_cur,
        mock_notify_api,
        mock_worker_heartbeat,
    ):
        # Setup row with trace context
        row = {
            "id": "sub-1",
            "parent_task_id": "parent-1",
            "agent_type": "researcher",
            "input": {"topic": "AI", "_trace_context": {"traceparent": "00-123-456-01"}},
            "iteration": 1,
        }

        mock_agent = MagicMock()
        mock_agent.execute.return_value = {"output": {"result": "data"}}
        mock_get_agent.return_value = mock_agent
        mock_get_state.return_value = {"workflow_type": "declarative:test"}
        mock_get_orch.return_value.process_subtask_completion.return_value = {"action": "continue"}

        # Execute
        _process_subtask(mock_conn, mock_cur, row)

        # Verify agent called with cleaned input (no _trace_context)
        call_args = mock_agent.execute.call_args
        assert "_trace_context" not in call_args[0][0]
        assert call_args[0][0]["topic"] == "AI"

    @patch("app.worker_helpers.get_agent")
    @patch("app.worker_helpers.aggregate_subtask_costs")
    @patch("app.worker_helpers.get_workflow_state")
    @patch("app.worker_helpers.get_orchestrator")
    def test_process_subtask_without_usage(
        self,
        mock_get_orch,
        mock_get_state,
        mock_agg,
        mock_get_agent,
        mock_conn,
        mock_cur,
        mock_notify_api,
        mock_worker_heartbeat,
    ):
        row = {
            "id": "sub-1",
            "parent_task_id": "parent-1",
            "agent_type": "researcher",
            "input": {"topic": "AI"},
            "iteration": 1,
        }

        mock_agent = MagicMock()
        # Return result WITHOUT usage
        mock_agent.execute.return_value = {"output": {"result": "data"}}
        mock_get_agent.return_value = mock_agent
        mock_get_state.return_value = {"workflow_type": "declarative:test"}
        mock_get_orch.return_value.process_subtask_completion.return_value = {"action": "continue"}

        _process_subtask(mock_conn, mock_cur, row)

        # Verify simple update query used (no usage fields)
        update_calls = [
            call
            for call in mock_cur.execute.call_args_list
            if "UPDATE subtasks SET status = 'done'" in call[0][0]
        ]
        assert len(update_calls) == 1
        assert "total_cost" not in update_calls[0][0]


class TestAgentTaskProcessing:
    @patch("app.worker_helpers.get_agent")
    def test_process_agent_task_success(
        self, mock_get_agent, mock_conn, mock_cur, mock_notify_api, mock_worker_heartbeat
    ):
        row = {
            "id": "task-1",
            "type": "agent:researcher",
            "input": {"topic": "AI"},
        }

        mock_agent = MagicMock()
        mock_agent.execute.return_value = {
            "output": {"result": "data"},
            "usage": {"total_cost": 0.1, "model_used": "gpt-4"},
        }
        mock_get_agent.return_value = mock_agent

        _process_agent_task(mock_conn, mock_cur, row)

        # Verify
        mock_agent.execute.assert_called_once()
        # Should update status to running then done
        assert mock_cur.execute.call_count >= 2
        mock_conn.commit.assert_called()

        # Verify usage update
        done_call = mock_cur.execute.call_args_list[-1]
        assert "UPDATE tasks" in done_call[0][0]
        assert "status = 'done'" in done_call[0][0]
        assert "total_cost" in done_call[0][0]

    @patch("app.worker_helpers.get_agent")
    def test_process_agent_task_failure(
        self, mock_get_agent, mock_conn, mock_cur, mock_notify_api, mock_worker_heartbeat
    ):
        row = {
            "id": "task-1",
            "type": "agent:researcher",
            "input": {"topic": "AI"},
        }

        mock_get_agent.side_effect = Exception("Agent failed")

        _process_agent_task(mock_conn, mock_cur, row)

        # Verify error update
        error_calls = [
            call for call in mock_cur.execute.call_args_list if "status = 'error'" in call[0][0]
        ]
        assert len(error_calls) >= 1

        # Verify notification
        mock_notify_api.assert_called_with("task-1", "error", error="Agent failed")

    @patch("app.worker_helpers.get_agent")
    def test_process_agent_task_cost_usage_handling(
        self, mock_get_agent, mock_conn, mock_cur, mock_notify_api, mock_worker_heartbeat
    ):
        row = {
            "id": "task-1",
            "type": "agent:researcher",
            "input": {"topic": "AI"},
        }

        mock_agent = MagicMock()
        mock_agent.execute.return_value = {
            "output": {"result": "data"},
            "usage": {
                "total_cost": 0.2,
                "model_used": "claude-3",
                "input_tokens": 200,
                "output_tokens": 100,
            },
        }
        mock_get_agent.return_value = mock_agent

        _process_agent_task(mock_conn, mock_cur, row)

        # Verify usage fields updated
        update_calls = [
            call
            for call in mock_cur.execute.call_args_list
            if "UPDATE tasks" in str(call) and "total_cost" in str(call)
        ]
        assert len(update_calls) == 1
        args = update_calls[0][0]
        sql = args[0]
        params = args[1]

        assert "model_used = %s" in sql
        assert "total_cost = %s" in sql

        assert 0.2 in params
        assert "claude-3" in params

    @patch("app.worker_helpers.get_agent")
    def test_process_agent_task_without_usage(
        self, mock_get_agent, mock_conn, mock_cur, mock_notify_api, mock_worker_heartbeat
    ):
        row = {
            "id": "task-1",
            "type": "agent:researcher",
            "input": {"topic": "AI"},
        }

        mock_agent = MagicMock()
        # Return result WITHOUT usage
        mock_agent.execute.return_value = {"output": {"result": "data"}}
        mock_get_agent.return_value = mock_agent

        _process_agent_task(mock_conn, mock_cur, row)

        # Verify simple update query used (no usage fields)
        update_calls = [
            call
            for call in mock_cur.execute.call_args_list
            if "UPDATE tasks" in str(call) and "status = 'done'" in str(call)
        ]
        assert len(update_calls) == 1
        assert "total_cost" not in update_calls[0][0]


class TestWorkflowTaskProcessing:
    @patch("app.worker_helpers.extract_workflow_type")
    @patch("app.worker_helpers.get_orchestrator")
    def test_process_workflow_task_success(
        self,
        mock_get_orch,
        mock_extract,
        mock_conn,
        mock_cur,
        mock_notify_api,
        mock_worker_heartbeat,
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
        self, mock_get_orch, mock_conn, mock_cur, mock_notify_api, mock_worker_heartbeat
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

    def test_claim_next_task_respects_max_tries(self, mock_conn, mock_cur):
        # Mock subtask with try_count >= max_tries (should be filtered by SQL, but testing logic)
        # In reality, SQL filters this, but we want to ensure if fetchone returns it (simulating race/bug),
        # we handle it or at least the SQL query structure is correct.
        # Since we mock fetchone, we are testing the Python side logic.
        # The Python code doesn't explicitly check try_count < max_tries after fetch,
        # it relies on the SQL query.
        # So this test mainly verifies that we construct the correct SQL query.

        settings = MagicMock()
        settings.worker_lease_duration_seconds = 60

        claim_next_task(mock_conn, mock_cur, "worker-1", settings)

        # Verify SQL contains max_tries check
        calls = mock_cur.execute.call_args_list
        assert any("try_count < max_tries" in str(call) for call in calls)

    def test_claim_next_task_respects_lease_timeout(self, mock_conn, mock_cur):
        settings = MagicMock()
        settings.worker_lease_duration_seconds = 60

        claim_next_task(mock_conn, mock_cur, "worker-1", settings)

        # Verify SQL contains lease timeout check
        calls = mock_cur.execute.call_args_list
        assert any("lease_timeout IS NULL OR lease_timeout < NOW()" in str(call) for call in calls)

    def test_claim_next_task_field_updates(self, mock_conn, mock_cur):
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
            None,
        ]

        settings = MagicMock()
        settings.worker_lease_duration_seconds = 60

        claim_next_task(mock_conn, mock_cur, "worker-1", settings)

        # Verify update fields
        update_call = mock_cur.execute.call_args_list[-1]
        sql = update_call[0][0]
        params = update_call[0][1]

        assert "status = 'running'" in sql
        assert "locked_by = %s" in sql
        assert "lease_timeout = %s" in sql
        assert "try_count = try_count + 1" in sql

        assert params[0] == "worker-1"
        # Lease timeout should be in future
        assert params[1] is not None
