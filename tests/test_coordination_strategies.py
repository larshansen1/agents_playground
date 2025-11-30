from unittest.mock import MagicMock, patch

import pytest

from app.orchestrator.coordination_strategies import (
    IterativeRefinementStrategy,
    SequentialStrategy,
    create_strategy,
)
from app.workflow_definition import WorkflowDefinition, WorkflowStep


@pytest.fixture
def mock_conn():
    return MagicMock()


@pytest.fixture
def mock_definition():
    steps = [
        WorkflowStep(agent_type="researcher", name="research"),
        WorkflowStep(agent_type="analyst", name="analyze"),
    ]
    return WorkflowDefinition(
        name="test_workflow",
        description="Test workflow",
        steps=steps,
        coordination_type="sequential",
        max_iterations=1,
    )


@pytest.fixture
def sequential_strategy(mock_definition):
    return SequentialStrategy(mock_definition)


@pytest.fixture
def iterative_definition():
    steps = [
        WorkflowStep(agent_type="researcher", name="research"),
        WorkflowStep(agent_type="reviewer", name="review"),
    ]
    return WorkflowDefinition(
        name="iterative_workflow",
        description="Iterative workflow",
        steps=steps,
        coordination_type="iterative_refinement",
        max_iterations=3,
        convergence_check="assessment_approved",
    )


@pytest.fixture
def iterative_strategy(iterative_definition):
    return IterativeRefinementStrategy(iterative_definition)


class TestSequentialStrategy:
    @patch("app.orchestrator.coordination_strategies.create_workflow_state")
    @patch("app.orchestrator.coordination_strategies.create_subtask")
    def test_sequential_initialization(
        self, mock_create_subtask, mock_create_state, sequential_strategy, mock_conn
    ):
        input_data = {"topic": "AI"}
        parent_id = "parent-123"

        sequential_strategy.initialize(parent_id, input_data, mock_conn)

        mock_create_state.assert_called_once()
        mock_create_subtask.assert_called_once()

        # Verify first subtask creation
        call_args = mock_create_subtask.call_args[1]
        assert call_args["parent_id"] == parent_id
        assert call_args["agent_type"] == "researcher"
        assert call_args["iteration"] == 1
        assert call_args["input_data"] == input_data

    @patch("app.orchestrator.coordination_strategies.create_workflow_state")
    @patch("app.orchestrator.coordination_strategies.create_subtask")
    def test_sequential_trace_propagation(
        self, mock_create_subtask, mock_create_state, sequential_strategy, mock_conn
    ):
        input_data = {"topic": "AI", "_trace_context": {"trace_id": "123"}}
        parent_id = "parent-123"

        sequential_strategy.initialize(parent_id, input_data, mock_conn)

        call_args = mock_create_subtask.call_args[1]
        assert call_args["input_data"]["_trace_context"] == {"trace_id": "123"}

    @patch("app.orchestrator.coordination_strategies.update_workflow_state")
    @patch("app.orchestrator.coordination_strategies.create_subtask")
    @patch("app.orchestrator.coordination_strategies.get_task_by_id")
    def test_sequential_process_completion_continue(
        self, mock_get_task, mock_create_subtask, mock_update_state, sequential_strategy, mock_conn
    ):
        parent_id = "parent-123"
        subtask_id = "sub-1"
        output = {"result": "data"}
        workflow_state = {"state_data": {"current_step_index": 0, "step_outputs": []}}
        mock_get_task.return_value = {"input": {}}

        result = sequential_strategy.process_completion(
            parent_id, subtask_id, output, workflow_state, mock_conn
        )

        assert result["action"] == "continue"
        mock_create_subtask.assert_called_once()

        # Verify next step creation (analyst)
        call_args = mock_create_subtask.call_args[1]
        assert call_args["agent_type"] == "analyst"
        assert call_args["input_data"]["previous_output"] == output
        assert (
            call_args["input_data"]["research_findings"] == output
        )  # Special case for step 0 -> 1

    @patch("app.orchestrator.coordination_strategies.update_workflow_state")
    def test_sequential_process_completion_finish(
        self, mock_update_state, sequential_strategy, mock_conn
    ):
        parent_id = "parent-123"
        subtask_id = "sub-2"
        output = {"analysis": "done"}
        workflow_state = {
            "state_data": {
                "current_step_index": 1,  # Last step (0-indexed, length is 2)
                "step_outputs": [{"result": "data"}],
            }
        }

        result = sequential_strategy.process_completion(
            parent_id, subtask_id, output, workflow_state, mock_conn
        )

        assert result["action"] == "complete"
        assert result["output"]["status"] == "completed"
        assert result["output"]["final_output"] == output

        mock_update_state.assert_called_once()
        call_args = mock_update_state.call_args[1]
        assert call_args["current_state"] == "completed"


class TestIterativeRefinementStrategy:
    @patch("app.orchestrator.coordination_strategies.create_workflow_state")
    @patch("app.orchestrator.coordination_strategies.create_subtask")
    def test_iterative_initialization(
        self, mock_create_subtask, mock_create_state, iterative_strategy, mock_conn
    ):
        input_data = {"draft": "content"}
        parent_id = "parent-123"

        iterative_strategy.initialize(parent_id, input_data, mock_conn)

        mock_create_state.assert_called_once()
        mock_create_subtask.assert_called_once()

        call_args = mock_create_subtask.call_args[1]
        assert call_args["agent_type"] == "researcher"
        assert call_args["iteration"] == 1

    @patch("app.orchestrator.coordination_strategies.update_workflow_state")
    @patch("app.orchestrator.coordination_strategies.create_subtask")
    def test_iterative_process_completion_next_step(
        self, mock_create_subtask, mock_update_state, iterative_strategy, mock_conn
    ):
        parent_id = "parent-123"
        output = {"draft": "v1"}
        workflow_state = {
            "current_iteration": 1,
            "state_data": {"current_step_index": 0, "original_input": {"topic": "AI"}},
        }

        result = iterative_strategy.process_completion(
            parent_id, "sub-1", output, workflow_state, mock_conn
        )

        assert result["action"] == "continue"
        mock_create_subtask.assert_called_once()

        # Should move to reviewer
        call_args = mock_create_subtask.call_args[1]
        assert call_args["agent_type"] == "reviewer"

    @patch("app.orchestrator.coordination_strategies.update_workflow_state")
    def test_iterative_process_completion_converged(
        self, mock_update_state, iterative_strategy, mock_conn
    ):
        parent_id = "parent-123"
        output = {"approved": True, "feedback": "Good job"}
        workflow_state = {
            "current_iteration": 1,
            "state_data": {
                "current_step_index": 1,  # Last step
                "step_0_iteration_1": {"draft": "v1"},
            },
        }

        result = iterative_strategy.process_completion(
            parent_id, "sub-2", output, workflow_state, mock_conn
        )

        assert result["action"] == "complete"
        assert result["output"]["status"] == "completed_converged"

    @patch("app.orchestrator.coordination_strategies.update_workflow_state")
    @patch("app.orchestrator.coordination_strategies.create_subtask")
    def test_iterative_process_completion_new_iteration(
        self, mock_create_subtask, mock_update_state, iterative_strategy, mock_conn
    ):
        parent_id = "parent-123"
        output = {"approved": False, "feedback": "Fix it"}
        workflow_state = {
            "current_iteration": 1,
            "state_data": {"current_step_index": 1, "original_input": {"topic": "AI"}},
        }

        result = iterative_strategy.process_completion(
            parent_id, "sub-2", output, workflow_state, mock_conn
        )

        assert result["action"] == "continue"

        # Should start new iteration with researcher
        mock_create_subtask.assert_called_once()
        call_args = mock_create_subtask.call_args[1]
        assert call_args["agent_type"] == "researcher"
        assert call_args["iteration"] == 2
        assert call_args["input_data"]["previous_feedback"] == "Fix it"

    @patch("app.orchestrator.coordination_strategies.update_workflow_state")
    def test_iterative_process_completion_max_iterations(
        self, mock_update_state, iterative_strategy, mock_conn
    ):
        parent_id = "parent-123"
        output = {"approved": False, "feedback": "Still bad"}
        workflow_state = {
            "current_iteration": 3,  # Max iterations
            "state_data": {"current_step_index": 1, "step_0_iteration_3": {"draft": "v3"}},
        }

        result = iterative_strategy.process_completion(
            parent_id, "sub-2", output, workflow_state, mock_conn
        )

        assert result["action"] == "complete"
        assert result["output"]["status"] == "completed_max_iterations"


def test_create_strategy_factory():
    def1 = WorkflowDefinition(
        name="seq",
        description="d",
        steps=[WorkflowStep(agent_type="a")],
        coordination_type="sequential",
    )
    assert isinstance(create_strategy(def1), SequentialStrategy)

    def2 = WorkflowDefinition(
        name="iter",
        description="d",
        steps=[WorkflowStep(agent_type="a")],
        coordination_type="iterative_refinement",
        convergence_check="c",
    )
    assert isinstance(create_strategy(def2), IterativeRefinementStrategy)

    def3 = WorkflowDefinition(
        name="bad",
        description="d",
        steps=[WorkflowStep(agent_type="a")],
        coordination_type="unknown",
    )
    with pytest.raises(ValueError):
        create_strategy(def3)
