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
    """Mock database connection."""
    return MagicMock()


@pytest.fixture
def mock_definition():
    """Create a realistic sequential workflow definition."""
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
    """Create sequential strategy instance."""
    return SequentialStrategy(mock_definition)


@pytest.fixture
def iterative_definition():
    """Create a realistic iterative workflow definition."""
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
    """Create iterative strategy instance."""
    return IterativeRefinementStrategy(iterative_definition)


class TestSequentialStrategy:
    """Tests for SequentialStrategy coordination."""

    # Phase 1: Foundation (Happy Paths)

    @patch("app.orchestrator.coordination_strategies.create_workflow_state")
    @patch("app.orchestrator.coordination_strategies.create_subtask")
    def test_sequential_initialization(
        self, mock_create_subtask, mock_create_state, sequential_strategy, mock_conn
    ):
        """Test sequential workflow initialization with realistic input."""
        input_data = {"topic": "AI Ethics", "depth": "comprehensive"}
        parent_id = "parent-123"

        sequential_strategy.initialize(parent_id, input_data, mock_conn)

        # Verify workflow state creation
        mock_create_state.assert_called_once()
        state_call = mock_create_state.call_args[1]
        assert state_call["parent_id"] == parent_id
        assert state_call["workflow_type"] == "declarative:test_workflow"
        assert state_call["initial_state"] == "step_0"
        assert state_call["max_iterations"] == 1
        assert state_call["state_data"]["current_step_index"] == 0
        assert state_call["state_data"]["total_steps"] == 2
        assert state_call["state_data"]["step_outputs"] == []

        # Verify first subtask creation
        mock_create_subtask.assert_called_once()
        subtask_call = mock_create_subtask.call_args[1]
        assert subtask_call["parent_id"] == parent_id
        assert subtask_call["agent_type"] == "researcher"
        assert subtask_call["iteration"] == 1
        assert subtask_call["input_data"] == input_data

    @patch("app.orchestrator.coordination_strategies.create_workflow_state")
    @patch("app.orchestrator.coordination_strategies.create_subtask")
    def test_sequential_initialization_with_user_tenant(
        self, mock_create_subtask, mock_create_state, sequential_strategy, mock_conn
    ):
        """Test that user_id_hash and tenant_id propagate during initialization."""
        input_data = {"topic": "AI"}
        parent_id = "parent-123"
        user_id_hash = "user-hash-456"
        tenant_id = "tenant-789"

        sequential_strategy.initialize(
            parent_id, input_data, mock_conn, user_id_hash=user_id_hash, tenant_id=tenant_id
        )

        # Verify workflow state includes tenant_id
        state_call = mock_create_state.call_args[1]
        assert state_call["tenant_id"] == tenant_id

        # Verify subtask includes user_id_hash and tenant_id
        subtask_call = mock_create_subtask.call_args[1]
        assert subtask_call["user_id_hash"] == user_id_hash
        assert subtask_call["tenant_id"] == tenant_id

    @patch("app.orchestrator.coordination_strategies.update_workflow_state")
    @patch("app.orchestrator.coordination_strategies.create_subtask")
    @patch("app.orchestrator.coordination_strategies.get_task_by_id")
    def test_sequential_process_completion_continue(
        self, mock_get_task, mock_create_subtask, mock_update_state, sequential_strategy, mock_conn
    ):
        """Test sequential workflow continues to next step with proper state updates."""
        parent_id = "parent-123"
        subtask_id = "sub-1"
        output = {"findings": "AI has ethical implications", "sources": ["paper1", "paper2"]}
        workflow_state = {"state_data": {"current_step_index": 0, "step_outputs": []}}
        mock_get_task.return_value = {"input": {}}

        result = sequential_strategy.process_completion(
            parent_id, subtask_id, output, workflow_state, mock_conn
        )

        # Verify action is continue
        assert result["action"] == "continue"

        # Verify next subtask creation
        mock_create_subtask.assert_called_once()
        subtask_call = mock_create_subtask.call_args[1]
        assert subtask_call["parent_id"] == parent_id
        assert subtask_call["agent_type"] == "analyst"
        assert subtask_call["iteration"] == 1
        assert subtask_call["input_data"]["previous_output"] == output
        assert subtask_call["input_data"]["research_findings"] == output

        # Verify workflow state update
        mock_update_state.assert_called_once()
        state_call = mock_update_state.call_args[1]
        assert state_call["parent_id"] == parent_id
        assert state_call["current_state"] == "step_1"
        assert state_call["state_data"]["current_step_index"] == 1
        assert state_call["state_data"]["step_outputs"] == [output]

    @patch("app.orchestrator.coordination_strategies.update_workflow_state")
    def test_sequential_process_completion_finish(
        self, mock_update_state, sequential_strategy, mock_conn
    ):
        """Test sequential workflow completes with final state updates."""
        parent_id = "parent-123"
        subtask_id = "sub-2"
        output = {
            "analysis": "Ethical frameworks needed",
            "recommendations": ["policy1", "policy2"],
        }
        workflow_state = {
            "state_data": {
                "current_step_index": 1,  # Last step (0-indexed, length is 2)
                "step_outputs": [{"findings": "data"}],
            }
        }

        result = sequential_strategy.process_completion(
            parent_id, subtask_id, output, workflow_state, mock_conn
        )

        # Verify completion
        assert result["action"] == "complete"
        assert result["output"]["status"] == "completed"
        assert result["output"]["final_output"] == output
        assert len(result["output"]["step_outputs"]) == 2
        assert result["output"]["step_outputs"][1] == output

        # Verify final workflow state update
        mock_update_state.assert_called_once()
        state_call = mock_update_state.call_args[1]
        assert state_call["parent_id"] == parent_id
        assert state_call["current_state"] == "completed"
        assert state_call["state_data"]["completion_reason"] == "all_steps_completed"

    # Phase 2: State Transitions & Error Handling

    @patch("app.orchestrator.coordination_strategies.update_workflow_state")
    @patch("app.orchestrator.coordination_strategies.create_subtask")
    @patch("app.orchestrator.coordination_strategies.get_task_by_id")
    def test_sequential_step_outputs_accumulation(
        self, mock_get_task, mock_create_subtask, mock_update_state, sequential_strategy, mock_conn
    ):
        """Test that step_outputs array accumulates correctly through workflow."""
        parent_id = "parent-123"
        first_output = {"step": "1"}
        workflow_state = {"state_data": {"current_step_index": 0, "step_outputs": []}}
        mock_get_task.return_value = {"input": {}}

        sequential_strategy.process_completion(
            parent_id, "sub-1", first_output, workflow_state, mock_conn
        )

        # Verify step_outputs contains first output
        state_call = mock_update_state.call_args[1]
        assert state_call["state_data"]["step_outputs"] == [first_output]

    @patch("app.orchestrator.coordination_strategies.update_workflow_state")
    @patch("app.orchestrator.coordination_strategies.create_subtask")
    @patch("app.orchestrator.coordination_strategies.get_task_by_id")
    def test_sequential_handles_missing_state_data(
        self, mock_get_task, mock_create_subtask, mock_update_state, sequential_strategy, mock_conn
    ):
        """Test graceful handling of missing state_data fields."""
        parent_id = "parent-123"
        output = {"result": "data"}
        # Missing state_data entirely
        workflow_state = {}
        mock_get_task.return_value = {"input": {}}

        result = sequential_strategy.process_completion(
            parent_id, "sub-1", output, workflow_state, mock_conn
        )

        # Should continue to next step (defaults to step 0, which becomes step 1)
        assert result["action"] == "continue"
        mock_create_subtask.assert_called_once()

    # Phase 3: Edge Cases & Invariants

    @patch("app.orchestrator.coordination_strategies.create_workflow_state")
    @patch("app.orchestrator.coordination_strategies.create_subtask")
    def test_sequential_trace_context_propagation_init(
        self, mock_create_subtask, mock_create_state, sequential_strategy, mock_conn
    ):
        """Test trace context propagates from input to first subtask."""
        input_data = {
            "topic": "AI",
            "_trace_context": {"trace_id": "trace-123", "span_id": "span-456"},
        }
        parent_id = "parent-123"

        sequential_strategy.initialize(parent_id, input_data, mock_conn)

        # Verify trace context in subtask
        subtask_call = mock_create_subtask.call_args[1]
        assert subtask_call["input_data"]["_trace_context"] == {
            "trace_id": "trace-123",
            "span_id": "span-456",
        }

    @patch("app.orchestrator.coordination_strategies.update_workflow_state")
    @patch("app.orchestrator.coordination_strategies.create_subtask")
    @patch("app.orchestrator.coordination_strategies.get_task_by_id")
    def test_sequential_trace_context_propagation_steps(
        self, mock_get_task, mock_create_subtask, mock_update_state, sequential_strategy, mock_conn
    ):
        """Test trace context propagates between workflow steps."""
        parent_id = "parent-123"
        output = {"result": "data"}
        workflow_state = {"state_data": {"current_step_index": 0, "step_outputs": []}}
        trace_context = {"trace_id": "trace-789"}
        mock_get_task.return_value = {"input": {"_trace_context": trace_context}}

        sequential_strategy.process_completion(
            parent_id, "sub-1", output, workflow_state, mock_conn
        )

        # Verify trace context in next subtask
        subtask_call = mock_create_subtask.call_args[1]
        assert subtask_call["input_data"]["_trace_context"] == trace_context

    @patch("app.orchestrator.coordination_strategies.update_workflow_state")
    @patch("app.orchestrator.coordination_strategies.create_subtask")
    @patch("app.orchestrator.coordination_strategies.get_task_by_id")
    def test_sequential_user_tenant_propagation_steps(
        self, mock_get_task, mock_create_subtask, mock_update_state, sequential_strategy, mock_conn
    ):
        """Test user_id_hash and tenant_id propagate to subsequent steps."""
        parent_id = "parent-123"
        output = {"result": "data"}
        workflow_state = {"state_data": {"current_step_index": 0, "step_outputs": []}}
        mock_get_task.return_value = {"input": {}}
        user_id_hash = "user-hash-abc"
        tenant_id = "tenant-xyz"

        sequential_strategy.process_completion(
            parent_id,
            "sub-1",
            output,
            workflow_state,
            mock_conn,
            user_id_hash=user_id_hash,
            tenant_id=tenant_id,
        )

        # Verify propagation to next subtask
        subtask_call = mock_create_subtask.call_args[1]
        assert subtask_call["user_id_hash"] == user_id_hash
        assert subtask_call["tenant_id"] == tenant_id


class TestIterativeRefinementStrategy:
    """Tests for IterativeRefinementStrategy coordination."""

    # Phase 1: Foundation (Happy Paths)

    @patch("app.orchestrator.coordination_strategies.create_workflow_state")
    @patch("app.orchestrator.coordination_strategies.create_subtask")
    def test_iterative_initialization(
        self, mock_create_subtask, mock_create_state, iterative_strategy, mock_conn
    ):
        """Test iterative workflow initialization with realistic input."""
        input_data = {"draft": "Initial content", "requirements": ["accuracy", "clarity"]}
        parent_id = "parent-123"

        iterative_strategy.initialize(parent_id, input_data, mock_conn)

        # Verify workflow state creation
        mock_create_state.assert_called_once()
        state_call = mock_create_state.call_args[1]
        assert state_call["parent_id"] == parent_id
        assert state_call["workflow_type"] == "declarative:iterative_workflow"
        assert state_call["initial_state"] == "researcher"
        assert state_call["max_iterations"] == 3
        assert state_call["state_data"]["original_input"] == input_data
        assert state_call["state_data"]["current_step_index"] == 0

        # Verify first subtask creation
        mock_create_subtask.assert_called_once()
        subtask_call = mock_create_subtask.call_args[1]
        assert subtask_call["parent_id"] == parent_id
        assert subtask_call["agent_type"] == "researcher"
        assert subtask_call["iteration"] == 1
        assert subtask_call["input_data"] == input_data

    @patch("app.orchestrator.coordination_strategies.update_workflow_state")
    @patch("app.orchestrator.coordination_strategies.create_subtask")
    @patch("app.orchestrator.coordination_strategies.get_task_by_id")
    def test_iterative_process_completion_next_step(
        self, mock_get_task, mock_create_subtask, mock_update_state, iterative_strategy, mock_conn
    ):
        """Test iterative workflow transitions to next step in same iteration."""
        parent_id = "parent-123"
        output = {"draft": "Improved content v1", "changes": ["added intro", "fixed typos"]}
        workflow_state = {
            "current_iteration": 1,
            "state_data": {"current_step_index": 0, "original_input": {"topic": "AI"}},
        }
        mock_get_task.return_value = {"input": {}}

        result = iterative_strategy.process_completion(
            parent_id, "sub-1", output, workflow_state, mock_conn
        )

        # Verify action is continue
        assert result["action"] == "continue"

        # Verify next step creation (reviewer)
        mock_create_subtask.assert_called_once()
        subtask_call = mock_create_subtask.call_args[1]
        assert subtask_call["parent_id"] == parent_id
        assert subtask_call["agent_type"] == "reviewer"
        assert subtask_call["iteration"] == 1
        assert subtask_call["input_data"]["previous_output"] == output

        # Verify workflow state update
        mock_update_state.assert_called_once()
        state_call = mock_update_state.call_args[1]
        assert state_call["parent_id"] == parent_id
        assert state_call["current_state"] == "reviewer"
        assert state_call["state_data"]["current_step_index"] == 1
        assert state_call["state_data"]["step_0_iteration_1"] == output

    @patch("app.orchestrator.coordination_strategies.update_workflow_state")
    def test_iterative_process_completion_converged(
        self, mock_update_state, iterative_strategy, mock_conn
    ):
        """Test iterative workflow completes when convergence condition is met."""
        parent_id = "parent-123"
        output = {"approved": True, "feedback": "Excellent work", "quality_score": 0.95}
        workflow_state = {
            "current_iteration": 1,
            "state_data": {
                "current_step_index": 1,  # Last step
                "step_0_iteration_1": {"draft": "Final content"},
            },
        }

        result = iterative_strategy.process_completion(
            parent_id, "sub-2", output, workflow_state, mock_conn
        )

        # Verify completion
        assert result["action"] == "complete"
        assert result["output"]["status"] == "completed_converged"
        assert result["output"]["iterations"] == 1
        assert result["output"]["final_assessment"] == output

        # Verify final workflow state update
        mock_update_state.assert_called_once()
        state_call = mock_update_state.call_args[1]
        assert state_call["parent_id"] == parent_id
        assert state_call["current_state"] == "completed"
        assert state_call["state_data"]["completion_reason"] == "converged"

    @patch("app.orchestrator.coordination_strategies.update_workflow_state")
    @patch("app.orchestrator.coordination_strategies.create_subtask")
    @patch("app.orchestrator.coordination_strategies.get_task_by_id")
    def test_iterative_process_completion_new_iteration(
        self, mock_get_task, mock_create_subtask, mock_update_state, iterative_strategy, mock_conn
    ):
        """Test iterative workflow starts new iteration when not converged."""
        parent_id = "parent-123"
        output = {"approved": False, "feedback": "Needs more detail in section 2"}
        workflow_state = {
            "current_iteration": 1,
            "state_data": {"current_step_index": 1, "original_input": {"topic": "AI"}},
        }
        mock_get_task.return_value = {"input": {}}

        result = iterative_strategy.process_completion(
            parent_id, "sub-2", output, workflow_state, mock_conn
        )

        # Verify action is continue
        assert result["action"] == "continue"

        # Verify new iteration starts with researcher
        mock_create_subtask.assert_called_once()
        subtask_call = mock_create_subtask.call_args[1]
        assert subtask_call["parent_id"] == parent_id
        assert subtask_call["agent_type"] == "researcher"
        assert subtask_call["iteration"] == 2
        assert subtask_call["input_data"]["previous_feedback"] == "Needs more detail in section 2"

        # Verify workflow state update
        mock_update_state.assert_called_once()
        state_call = mock_update_state.call_args[1]
        assert state_call["parent_id"] == parent_id
        assert state_call["current_state"] == "researcher"
        assert state_call["current_iteration"] == 2
        assert state_call["state_data"]["current_step_index"] == 0

    # Phase 2: State Transitions & Error Handling

    @patch("app.orchestrator.coordination_strategies.update_workflow_state")
    def test_iterative_handles_missing_state_data(
        self, mock_update_state, iterative_strategy, mock_conn
    ):
        """Test graceful handling of missing state_data fields."""
        parent_id = "parent-123"
        output = {"approved": True}
        # Missing state_data fields
        workflow_state = {"current_iteration": 1, "state_data": {}}

        result = iterative_strategy.process_completion(
            parent_id, "sub-1", output, workflow_state, mock_conn
        )

        # Should still process (defaults to step 0, not last step)
        assert result["action"] == "continue"

    # Phase 3: Edge Cases & Invariants

    @patch("app.orchestrator.coordination_strategies.update_workflow_state")
    def test_iterative_max_iterations_boundary(
        self, mock_update_state, iterative_strategy, mock_conn
    ):
        """Test iterative workflow completes at max_iterations boundary."""
        parent_id = "parent-123"
        output = {"approved": False, "feedback": "Still needs work"}
        workflow_state = {
            "current_iteration": 3,  # At max_iterations
            "state_data": {"current_step_index": 1, "step_0_iteration_3": {"draft": "v3"}},
        }

        result = iterative_strategy.process_completion(
            parent_id, "sub-2", output, workflow_state, mock_conn
        )

        # Verify completion at boundary
        assert result["action"] == "complete"
        assert result["output"]["status"] == "completed_max_iterations"
        assert result["output"]["iterations"] == 3

        # Verify final state update
        mock_update_state.assert_called_once()
        state_call = mock_update_state.call_args[1]
        assert state_call["current_state"] == "completed"
        assert state_call["state_data"]["completion_reason"] == "max_iterations"

    @patch("app.orchestrator.coordination_strategies.update_workflow_state")
    @patch("app.orchestrator.coordination_strategies.create_subtask")
    @patch("app.orchestrator.coordination_strategies.get_task_by_id")
    def test_iterative_convergence_quality_threshold(
        self, mock_get_task, mock_create_subtask, mock_update_state, mock_conn
    ):
        """Test quality_threshold convergence check."""
        # Create strategy with quality_threshold convergence
        definition = WorkflowDefinition(
            name="quality_workflow",
            description="Quality-based workflow",
            steps=[
                WorkflowStep(agent_type="researcher"),
                WorkflowStep(agent_type="reviewer"),
            ],
            coordination_type="iterative_refinement",
            max_iterations=3,
            convergence_check="quality_threshold",
        )
        strategy = IterativeRefinementStrategy(definition)

        parent_id = "parent-123"
        # Quality score above threshold (0.8)
        output = {"quality_score": 0.85, "feedback": "Good"}
        workflow_state = {
            "current_iteration": 1,
            "state_data": {"current_step_index": 1, "step_0_iteration_1": {"draft": "v1"}},
        }

        result = strategy.process_completion(parent_id, "sub-1", output, workflow_state, mock_conn)

        # Should converge
        assert result["action"] == "complete"
        assert result["output"]["status"] == "completed_converged"

    @patch("app.orchestrator.coordination_strategies.update_workflow_state")
    @patch("app.orchestrator.coordination_strategies.create_subtask")
    @patch("app.orchestrator.coordination_strategies.get_task_by_id")
    def test_iterative_unknown_convergence_check(
        self, mock_get_task, mock_create_subtask, mock_update_state, mock_conn
    ):
        """Test unknown convergence check defaults to not converged."""
        # Create strategy with unknown convergence check
        definition = WorkflowDefinition(
            name="unknown_workflow",
            description="Unknown convergence workflow",
            steps=[
                WorkflowStep(agent_type="researcher"),
                WorkflowStep(agent_type="reviewer"),
            ],
            coordination_type="iterative_refinement",
            max_iterations=2,
            convergence_check="unknown_check",
        )
        strategy = IterativeRefinementStrategy(definition)

        parent_id = "parent-123"
        output = {"some_field": "value"}
        workflow_state = {
            "current_iteration": 1,
            "state_data": {"current_step_index": 1, "original_input": {}},
        }
        mock_get_task.return_value = {"input": {}}

        result = strategy.process_completion(parent_id, "sub-1", output, workflow_state, mock_conn)

        # Should not converge, start new iteration
        assert result["action"] == "continue"
        mock_create_subtask.assert_called_once()

    @patch("app.orchestrator.coordination_strategies.create_workflow_state")
    @patch("app.orchestrator.coordination_strategies.create_subtask")
    def test_iterative_trace_context_propagation_init(
        self, mock_create_subtask, mock_create_state, iterative_strategy, mock_conn
    ):
        """Test trace context propagates from input to first subtask."""
        input_data = {
            "draft": "content",
            "_trace_context": {"trace_id": "trace-abc", "span_id": "span-def"},
        }
        parent_id = "parent-123"

        iterative_strategy.initialize(parent_id, input_data, mock_conn)

        # Verify trace context in subtask
        subtask_call = mock_create_subtask.call_args[1]
        assert subtask_call["input_data"]["_trace_context"] == {
            "trace_id": "trace-abc",
            "span_id": "span-def",
        }

    @patch("app.orchestrator.coordination_strategies.update_workflow_state")
    @patch("app.orchestrator.coordination_strategies.create_subtask")
    @patch("app.orchestrator.coordination_strategies.get_task_by_id")
    def test_iterative_trace_context_propagation_steps(
        self, mock_get_task, mock_create_subtask, mock_update_state, iterative_strategy, mock_conn
    ):
        """Test trace context propagates between steps in iteration."""
        parent_id = "parent-123"
        output = {"draft": "v1"}
        workflow_state = {
            "current_iteration": 1,
            "state_data": {"current_step_index": 0, "original_input": {}},
        }
        trace_context = {"trace_id": "trace-123"}
        mock_get_task.return_value = {"input": {"_trace_context": trace_context}}

        iterative_strategy.process_completion(parent_id, "sub-1", output, workflow_state, mock_conn)

        # Verify trace context in next step
        subtask_call = mock_create_subtask.call_args[1]
        assert subtask_call["input_data"]["_trace_context"] == trace_context

    @patch("app.orchestrator.coordination_strategies.update_workflow_state")
    @patch("app.orchestrator.coordination_strategies.create_subtask")
    @patch("app.orchestrator.coordination_strategies.get_task_by_id")
    def test_iterative_trace_context_propagation_iterations(
        self, mock_get_task, mock_create_subtask, mock_update_state, iterative_strategy, mock_conn
    ):
        """Test trace context propagates across iterations."""
        parent_id = "parent-123"
        output = {"approved": False, "feedback": "Revise"}
        workflow_state = {
            "current_iteration": 1,
            "state_data": {"current_step_index": 1, "original_input": {}},
        }
        trace_context = {"trace_id": "trace-456"}
        mock_get_task.return_value = {"input": {"_trace_context": trace_context}}

        iterative_strategy.process_completion(parent_id, "sub-2", output, workflow_state, mock_conn)

        # Verify trace context in new iteration
        subtask_call = mock_create_subtask.call_args[1]
        assert subtask_call["input_data"]["_trace_context"] == trace_context

    @patch("app.orchestrator.coordination_strategies.create_workflow_state")
    @patch("app.orchestrator.coordination_strategies.create_subtask")
    def test_iterative_user_tenant_propagation_init(
        self, mock_create_subtask, mock_create_state, iterative_strategy, mock_conn
    ):
        """Test user_id_hash and tenant_id propagate during initialization."""
        input_data = {"draft": "content"}
        parent_id = "parent-123"
        user_id_hash = "user-hash-123"
        tenant_id = "tenant-456"

        iterative_strategy.initialize(
            parent_id, input_data, mock_conn, user_id_hash=user_id_hash, tenant_id=tenant_id
        )

        # Verify workflow state includes tenant_id
        state_call = mock_create_state.call_args[1]
        assert state_call["tenant_id"] == tenant_id

        # Verify subtask includes user_id_hash and tenant_id
        subtask_call = mock_create_subtask.call_args[1]
        assert subtask_call["user_id_hash"] == user_id_hash
        assert subtask_call["tenant_id"] == tenant_id

    @patch("app.orchestrator.coordination_strategies.update_workflow_state")
    @patch("app.orchestrator.coordination_strategies.create_subtask")
    @patch("app.orchestrator.coordination_strategies.get_task_by_id")
    def test_iterative_user_tenant_propagation_steps(
        self, mock_get_task, mock_create_subtask, mock_update_state, iterative_strategy, mock_conn
    ):
        """Test user_id_hash and tenant_id propagate to next step."""
        parent_id = "parent-123"
        output = {"draft": "v1"}
        workflow_state = {
            "current_iteration": 1,
            "state_data": {"current_step_index": 0, "original_input": {}},
        }
        mock_get_task.return_value = {"input": {}}
        user_id_hash = "user-hash-789"
        tenant_id = "tenant-abc"

        iterative_strategy.process_completion(
            parent_id,
            "sub-1",
            output,
            workflow_state,
            mock_conn,
            user_id_hash=user_id_hash,
            tenant_id=tenant_id,
        )

        # Verify propagation to next step
        subtask_call = mock_create_subtask.call_args[1]
        assert subtask_call["user_id_hash"] == user_id_hash
        assert subtask_call["tenant_id"] == tenant_id

    @patch("app.orchestrator.coordination_strategies.update_workflow_state")
    @patch("app.orchestrator.coordination_strategies.create_subtask")
    @patch("app.orchestrator.coordination_strategies.get_task_by_id")
    def test_iterative_state_data_preservation(
        self, mock_get_task, mock_create_subtask, mock_update_state, iterative_strategy, mock_conn
    ):
        """Test state_data is preserved and accumulated across iterations."""
        parent_id = "parent-123"
        output = {"approved": False, "feedback": "Improve"}
        original_input = {"topic": "AI", "requirements": ["accuracy"]}
        workflow_state = {
            "current_iteration": 1,
            "state_data": {
                "current_step_index": 1,
                "original_input": original_input,
                "custom_field": "preserved",
            },
        }
        mock_get_task.return_value = {"input": {}}

        iterative_strategy.process_completion(parent_id, "sub-2", output, workflow_state, mock_conn)

        # Verify state_data preservation
        state_call = mock_update_state.call_args[1]
        assert state_call["state_data"]["original_input"] == original_input
        assert state_call["state_data"]["custom_field"] == "preserved"
        assert state_call["state_data"]["current_step_index"] == 0  # Reset for new iteration
        assert "last_step_iteration_1" in state_call["state_data"]


class TestStrategyFactory:
    """Tests for create_strategy factory function."""

    def test_create_strategy_sequential(self):
        """Test factory creates SequentialStrategy for sequential coordination."""
        definition = WorkflowDefinition(
            name="seq",
            description="Sequential workflow",
            steps=[WorkflowStep(agent_type="agent1")],
            coordination_type="sequential",
        )
        strategy = create_strategy(definition)

        assert isinstance(strategy, SequentialStrategy)
        assert strategy.definition == definition

    def test_create_strategy_iterative(self):
        """Test factory creates IterativeRefinementStrategy for iterative coordination."""
        definition = WorkflowDefinition(
            name="iter",
            description="Iterative workflow",
            steps=[WorkflowStep(agent_type="agent1")],
            coordination_type="iterative_refinement",
            convergence_check="assessment_approved",
        )
        strategy = create_strategy(definition)

        assert isinstance(strategy, IterativeRefinementStrategy)
        assert strategy.definition == definition

    def test_create_strategy_unknown_type(self):
        """Test factory raises ValueError for unknown coordination type."""
        definition = WorkflowDefinition(
            name="bad",
            description="Unknown workflow",
            steps=[WorkflowStep(agent_type="agent1")],
            coordination_type="unknown_type",
        )

        with pytest.raises(ValueError, match="Unknown coordination type: unknown_type"):
            create_strategy(definition)
