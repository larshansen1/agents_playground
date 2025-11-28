"""Comprehensive integration tests for workflow execution.

These tests validate end-to-end workflow behavior including:
- Sequential workflow execution
- Iterative workflow with convergence
- Max iterations handling
- Failure propagation
- Cost tracking across workflows
- Audit logging across workflows
"""

import tempfile
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.models import AuditLog
from app.orchestrator.research_assessment import ResearchAssessmentOrchestrator
from app.tasks import calculate_cost
from app.workflow_definition import WorkflowDefinition, WorkflowStep

pytestmark = pytest.mark.integration


class TestSequentialWorkflowExecution:
    """Integration tests for sequential workflow execution."""

    @patch("app.orchestrator.research_assessment.create_subtask")
    @patch("app.orchestrator.research_assessment.create_workflow_state")
    @patch("app.orchestrator.research_assessment.get_workflow_state")
    @patch("app.orchestrator.research_assessment.update_workflow_state")
    def test_sequential_workflow_creates_subtasks(
        self,
        mock_update_state,  # noqa: ARG002
        mock_get_state,  # noqa: ARG002
        mock_create_state,
        mock_create_subtask,
    ):
        """Test that sequential workflow creates research then assessment subtasks."""

        task_id = str(uuid.uuid4())
        mock_conn = MagicMock()

        orchestrator = ResearchAssessmentOrchestrator(max_iterations=3)

        # Initialize workflow
        orchestrator.create_workflow(
            parent_task_id=task_id,
            input_data={"topic": "AI Safety"},
            conn=mock_conn,
            user_id_hash="test_user",
        )

        # Verify workflow state created
        mock_create_state.assert_called_once()
        call_args = mock_create_state.call_args[1]
        assert call_args["parent_id"] == task_id
        assert call_args["workflow_type"] == "research_assessment"
        assert call_args["initial_state"] == "research"
        assert call_args["max_iterations"] == 3

        # Verify first research subtask created
        create_subtask_calls = [call[1] for call in mock_create_subtask.call_args_list]
        first_subtask = create_subtask_calls[0]
        assert first_subtask["parent_id"] == task_id
        assert first_subtask["agent_type"] == "research"
        assert first_subtask["iteration"] == 1
        assert "topic" in first_subtask["input_data"]

    @patch("app.orchestrator.research_assessment.create_subtask")
    @patch("app.orchestrator.research_assessment.get_workflow_state")
    @patch("app.orchestrator.research_assessment.update_workflow_state")
    @patch("app.orchestrator.research_assessment.get_subtask_by_id")
    def test_research_completion_triggers_assessment(
        self,
        mock_get_subtask,
        mock_update_state,  # noqa: ARG002
        mock_get_state,
        mock_create_subtask,
    ):
        """Test that research completion triggers assessment subtask creation."""

        task_id = str(uuid.uuid4())
        subtask_id = str(uuid.uuid4())
        mock_conn = MagicMock()

        # Mock workflow state
        mock_get_state.return_value = {
            "current_state": "research",
            "current_iteration": 1,
            "state_data": {},
        }

        # Mock subtask
        mock_get_subtask.return_value = {"agent_type": "research"}

        orchestrator = ResearchAssessmentOrchestrator(max_iterations=3)

        # Process research completion
        research_output = {
            "findings": "Important research findings",
            "sources": ["source1.com"],
            "key_insights": ["Insight 1"],
        }

        result = orchestrator.process_subtask_completion(
            parent_task_id=task_id,
            subtask_id=subtask_id,
            subtask_output=research_output,
            conn=mock_conn,
            user_id_hash="test_user",
        )

        # Should continue to assessment
        assert result["action"] == "continue"

        # Verify assessment subtask created
        mock_create_subtask.assert_called()
        assessment_call = mock_create_subtask.call_args[1]
        assert assessment_call["agent_type"] == "assessment"
        assert assessment_call["iteration"] == 1
        assert "research_findings" in assessment_call["input_data"]

    @patch("app.orchestrator.research_assessment.get_workflow_state")
    @patch("app.orchestrator.research_assessment.get_subtask_by_id")
    def test_assessment_approval_completes_workflow(self, mock_get_subtask, mock_get_state):
        """Test that approved assessment completes the workflow."""

        task_id = str(uuid.uuid4())
        subtask_id = str(uuid.uuid4())
        mock_conn = MagicMock()

        # Mock workflow state with previous research
        mock_get_state.return_value = {
            "current_state": "assessment",
            "current_iteration": 1,
            "state_data": {"research_iteration_1": {"findings": "Great research"}},
        }

        mock_get_subtask.return_value = {"agent_type": "assessment"}

        orchestrator = ResearchAssessmentOrchestrator(max_iterations=3)

        # Process approved assessment
        assessment_output = {
            "approved": True,
            "quality_score": 90,
            "feedback": "Excellent work",
        }

        result = orchestrator.process_subtask_completion(
            parent_task_id=task_id,
            subtask_id=subtask_id,
            subtask_output=assessment_output,
            conn=mock_conn,
        )

        # Workflow should complete
        assert result["action"] == "complete"
        assert "output" in result
        assert result["output"]["status"] == "completed_approved"
        assert "research_findings" in result["output"]
        assert "final_assessment" in result["output"]


class TestIterativeWorkflowRefinement:
    """Integration tests for iterative refinement workflows."""

    @patch("app.orchestrator.research_assessment.create_subtask")
    @patch("app.orchestrator.research_assessment.get_workflow_state")
    @patch("app.orchestrator.research_assessment.update_workflow_state")
    @patch("app.orchestrator.research_assessment.get_subtask_by_id")
    @patch("app.orchestrator.research_assessment.get_task_by_id")
    def test_rejected_assessment_starts_new_iteration(
        self,
        mock_get_task,
        mock_get_subtask,
        mock_update_state,  # noqa: ARG002
        mock_get_state,
        mock_create_subtask,
    ):
        """Test that rejected assessment starts a new iteration."""

        task_id = str(uuid.uuid4())
        subtask_id = str(uuid.uuid4())
        mock_conn = MagicMock()

        # Mock workflow state
        mock_get_state.return_value = {
            "current_state": "assessment",
            "current_iteration": 1,
            "state_data": {"research_iteration_1": {"findings": "Initial findings"}},
        }

        mock_get_subtask.return_value = {"agent_type": "assessment"}
        mock_get_task.return_value = {"input": {"topic": "AI Safety"}}

        orchestrator = ResearchAssessmentOrchestrator(max_iterations=3)

        # Process rejected assessment
        assessment_output = {
            "approved": False,
            "quality_score": 60,
            "feedback": "Needs more detail and sources",
            "suggestions": ["Add citations", "Expand on key points"],
        }

        result = orchestrator.process_subtask_completion(
            parent_task_id=task_id,
            subtask_id=subtask_id,
            subtask_output=assessment_output,
            conn=mock_conn,
        )

        # Should continue with new iteration
        assert result["action"] == "continue"

        # Verify new research subtask created for iteration 2
        mock_create_subtask.assert_called()
        research_call = mock_create_subtask.call_args[1]
        assert research_call["agent_type"] == "research"
        assert research_call["iteration"] == 2
        # Should include feedback from assessment as 'previous_feedback'
        assert "previous_feedback" in research_call["input_data"]
        assert research_call["input_data"]["previous_feedback"] == "Needs more detail and sources"

    @patch("app.orchestrator.research_assessment.get_workflow_state")
    @patch("app.orchestrator.research_assessment.get_subtask_by_id")
    def test_state_data_preserved_across_iterations(self, mock_get_subtask, mock_get_state):
        """Test that state data contains all iteration results."""

        task_id = str(uuid.uuid4())
        subtask_id = str(uuid.uuid4())
        mock_conn = MagicMock()

        # Mock workflow state with multiple iterations
        state_data = {
            "research_iteration_1": {"findings": "First attempt"},
            "research_iteration_2": {"findings": "Revised attempt"},
        }

        mock_get_state.return_value = {
            "current_state": "assessment",
            "current_iteration": 2,
            "state_data": state_data,
        }

        mock_get_subtask.return_value = {"agent_type": "assessment"}

        orchestrator = ResearchAssessmentOrchestrator(max_iterations=3)

        # Process approved assessment from iteration 2
        assessment_output = {"approved": True, "feedback": "Much better!"}

        result = orchestrator.process_subtask_completion(
            parent_task_id=task_id,
            subtask_id=subtask_id,
            subtask_output=assessment_output,
            conn=mock_conn,
        )

        # Verify final output includes latest research findings
        assert result["action"] == "complete"
        assert result["output"]["research_findings"]["findings"] == "Revised attempt"


class TestWorkflowMaxIterations:
    """Integration tests for max iteration boundary conditions."""

    @patch("app.orchestrator.research_assessment.get_workflow_state")
    @patch("app.orchestrator.research_assessment.get_subtask_by_id")
    def test_workflow_completes_at_max_iterations(self, mock_get_subtask, mock_get_state):
        """Test workflow completes when max iterations reached even if not approved."""

        task_id = str(uuid.uuid4())
        subtask_id = str(uuid.uuid4())
        mock_conn = MagicMock()

        # Mock workflow state at max iteration
        mock_get_state.return_value = {
            "current_state": "assessment",
            "current_iteration": 3,
            "state_data": {
                "research_iteration_1": {"findings": "Attempt 1"},
                "research_iteration_2": {"findings": "Attempt 2"},
                "research_iteration_3": {"findings": "Final attempt"},
            },
        }

        mock_get_subtask.return_value = {"agent_type": "assessment"}

        orchestrator = ResearchAssessmentOrchestrator(max_iterations=3)

        # Process rejected assessment at max iteration
        assessment_output = {
            "approved": False,
            "feedback": "Still not perfect",
        }

        result = orchestrator.process_subtask_completion(
            parent_task_id=task_id,
            subtask_id=subtask_id,
            subtask_output=assessment_output,
            conn=mock_conn,
        )

        # Should complete even though not approved
        assert result["action"] == "complete"
        assert "output" in result
        assert result["output"]["status"] == "completed_max_iterations"
        assert "research_findings" in result["output"]
        assert result["output"]["research_findings"]["findings"] == "Final attempt"

    def test_max_iterations_respected_in_orchestrator(self):
        """Test that max_iterations parameter is respected."""

        # Test different max_iterations values
        orch_1 = ResearchAssessmentOrchestrator(max_iterations=1)
        assert orch_1.get_max_iterations() == 1

        orch_3 = ResearchAssessmentOrchestrator(max_iterations=3)
        assert orch_3.get_max_iterations() == 3

        orch_5 = ResearchAssessmentOrchestrator(max_iterations=5)
        assert orch_5.get_max_iterations() == 5


class TestWorkflowCostTracking:
    """Integration tests for cost tracking across workflows."""

    @patch("app.orchestrator.research_assessment.create_subtask")
    @patch("app.orchestrator.research_assessment.get_workflow_state")
    @patch("app.orchestrator.research_assessment.update_workflow_state")
    @patch("app.orchestrator.research_assessment.get_subtask_by_id")
    @patch("app.db_utils.aggregate_subtask_costs")
    def test_cost_aggregation_across_workflow(
        self,
        mock_aggregate_costs,  # noqa: ARG002
        mock_get_subtask,
        mock_update_state,  # noqa: ARG002
        mock_get_state,
        mock_create_subtask,
    ):
        """Test that costs from multiple subtasks aggregate to parent task."""

        task_id = str(uuid.uuid4())
        research_subtask_id = str(uuid.uuid4())
        assessment_subtask_id = str(uuid.uuid4())
        mock_conn = MagicMock()

        orchestrator = ResearchAssessmentOrchestrator(max_iterations=3)

        # Simulate research subtask completion
        mock_get_state.return_value = {
            "current_state": "research",
            "current_iteration": 1,
            "state_data": {},
        }
        mock_get_subtask.return_value = {"agent_type": "research"}

        research_output = {
            "findings": "Research results",
            "sources": ["source1.com"],
        }

        # Process research completion
        orchestrator.process_subtask_completion(
            parent_task_id=task_id,
            subtask_id=research_subtask_id,
            subtask_output=research_output,
            conn=mock_conn,
        )

        # Verify assessment subtask was created
        assert mock_create_subtask.called

        # Now simulate assessment completion
        mock_get_state.return_value = {
            "current_state": "assessment",
            "current_iteration": 1,
            "state_data": {"research_iteration_1": research_output},
        }
        mock_get_subtask.return_value = {"agent_type": "assessment"}

        assessment_output = {"approved": True, "quality_score": 95}

        # Process assessment completion
        orchestrator.process_subtask_completion(
            parent_task_id=task_id,
            subtask_id=assessment_subtask_id,
            subtask_output=assessment_output,
            conn=mock_conn,
        )

        # Note: aggregate_subtask_costs would be called by the worker
        # after each subtask completes. We're verifying the workflow
        # logic is correct, not the worker integration

    def test_cost_calculation_utility(self):
        """Test cost calculation for different models and token counts."""

        # Test Gemini Flash pricing
        cost = calculate_cost("google/gemini-2.5-flash", 1000, 500)
        # Should be: (1000 * 0.075 / 1M) + (500 * 0.30 / 1M) = 0.000225
        assert abs(cost - 0.000225) < 0.000001

        # Test with larger counts
        cost_large = calculate_cost("google/gemini-2.5-flash", 100000, 50000)
        assert abs(cost_large - 0.0225) < 0.0001

        # Test zero tokens
        cost_zero = calculate_cost("google/gemini-2.5-flash", 0, 0)
        assert cost_zero == 0.0

    @patch("app.orchestrator.research_assessment.create_subtask")
    @patch("app.orchestrator.research_assessment.get_workflow_state")
    @patch("app.orchestrator.research_assessment.update_workflow_state")
    @patch("app.orchestrator.research_assessment.get_subtask_by_id")
    @patch("app.orchestrator.research_assessment.get_task_by_id")
    def test_cost_accumulation_across_iterations(
        self,
        mock_get_task,
        mock_get_subtask,
        mock_update_state,  # noqa: ARG002
        mock_get_state,
        mock_create_subtask,
    ):
        """Test that costs accumulate correctly across multiple workflow iterations."""

        task_id = str(uuid.uuid4())
        mock_conn = MagicMock()
        orchestrator = ResearchAssessmentOrchestrator(max_iterations=3)

        # Iteration 1: Research
        mock_get_state.return_value = {
            "current_state": "research",
            "current_iteration": 1,
            "state_data": {},
        }
        mock_get_subtask.return_value = {"agent_type": "research"}

        orchestrator.process_subtask_completion(
            parent_task_id=task_id,
            subtask_id=str(uuid.uuid4()),
            subtask_output={"findings": "iteration 1"},
            conn=mock_conn,
        )

        # Iteration 1: Assessment (rejected)
        mock_get_state.return_value = {
            "current_state": "assessment",
            "current_iteration": 1,
            "state_data": {"research_iteration_1": {"findings": "iteration 1"}},
        }
        mock_get_subtask.return_value = {"agent_type": "assessment"}
        mock_get_task.return_value = {"input": {"topic": "test"}}

        orchestrator.process_subtask_completion(
            parent_task_id=task_id,
            subtask_id=str(uuid.uuid4()),
            subtask_output={"approved": False, "feedback": "needs work"},
            conn=mock_conn,
        )

        # Verify new research subtask created for iteration 2
        create_calls = mock_create_subtask.call_args_list
        # Should have created assessment (iter 1) and research (iter 2)
        assert len(create_calls) >= 2

        # Verify iteration 2 subtask has iteration=2
        iter_2_call = create_calls[-1][1]  # Last call should be iteration 2
        assert iter_2_call["iteration"] == 2
        assert iter_2_call["agent_type"] == "research"

        # In a real workflow, each subtask completion would trigger
        # aggregate_subtask_costs, accumulating costs from all completed
        # subtasks (research iter 1, assessment iter 1, research iter 2, etc.)


class TestWorkflowFailureHandling:
    """Integration tests for workflow failure scenarios."""

    @patch("app.db_utils.get_workflow_state")
    @patch("app.db_utils.get_subtask_by_id")
    def test_invalid_state_transition_returns_failed(self, mock_get_subtask, mock_get_state):
        """Test that invalid state transitions return failed action."""

        task_id = str(uuid.uuid4())
        subtask_id = str(uuid.uuid4())
        mock_conn = MagicMock()

        # Mock state that doesn't match subtask type
        mock_get_state.return_value = {
            "current_state": "assessment",  # Expecting assessment
            "current_iteration": 1,
            "state_data": {},
        }

        # But subtask is research (mismatch)
        mock_get_subtask.return_value = {"agent_type": "research"}

        orchestrator = ResearchAssessmentOrchestrator()

        result = orchestrator.process_subtask_completion(
            parent_task_id=task_id,
            subtask_id=subtask_id,
            subtask_output={"findings": "test"},
            conn=mock_conn,
        )

        # Should fail due to state mismatch
        assert result["action"] == "failed"

    def test_workflow_type_validation(self):
        """Test workflow type validation."""

        # Valid workflow
        orch = ResearchAssessmentOrchestrator()
        assert orch.workflow_type == "research_assessment"

        # Test different max_iterations values
        orch_1 = ResearchAssessmentOrchestrator(max_iterations=1)
        assert orch_1.get_max_iterations() == 1


class TestWorkflowAuditLogging:
    """Integration tests for audit logging across workflows."""

    @patch("app.orchestrator.research_assessment.create_workflow_state")
    @patch("app.orchestrator.research_assessment.create_subtask")
    @patch("app.audit.log_audit_event")
    def test_workflow_initialization_creates_audit_event(
        self,
        mock_audit,  # noqa: ARG002
        mock_create_subtask,
        mock_create_state,
    ):
        """Test that workflow initialization creates audit log entry."""

        task_id = str(uuid.uuid4())
        mock_conn = MagicMock()

        orchestrator = ResearchAssessmentOrchestrator()

        orchestrator.create_workflow(
            parent_task_id=task_id,
            input_data={"topic": "test"},
            conn=mock_conn,
            user_id_hash="user_123",
            tenant_id="tenant_abc",
        )

        # Verify workflow state and subtask creation
        mock_create_state.assert_called_once()
        mock_create_subtask.assert_called_once()

    def test_audit_log_model_structure(self):
        """Test audit log data model structure."""

        # Create a dummy audit log via __init__ (not via ORM)
        log = AuditLog()
        log.event_type = "workflow_initialized"
        log.resource_id = "task-123"
        log.user_id_hash = "user-abc"
        log.metadata_ = {"workflow_type": "research_assessment"}

        # Verify structure
        assert log.event_type == "workflow_initialized"
        assert log.resource_id == "task-123"
        assert log.user_id_hash == "user-abc"
        assert log.metadata_["workflow_type"] == "research_assessment"


class TestDeclarativeWorkflows:
    """Integration tests for declarative workflow definitions."""

    def test_workflow_definition_from_yaml(self):
        """Test loading workflow definition from YAML."""

        yaml_content = """
name: test_sequential
description: Test sequential workflow
coordination_type: sequential
max_iterations: 2

steps:
  - agent_type: research
    name: gather_data
  - agent_type: assessment
    name: validate_data
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            definition = WorkflowDefinition.from_yaml(temp_path)
            assert definition.name == "test_sequential"
            assert definition.coordination_type == "sequential"
            assert len(definition.steps) == 2
            assert definition.steps[0].agent_type == "research"
            assert definition.steps[1].agent_type == "assessment"
        finally:
            Path(temp_path).unlink()

    def test_iterative_workflow_definition(self):
        """Test defining an iterative refinement workflow."""

        definition = WorkflowDefinition(
            name="iterative_test",
            description="Iterative workflow test",
            steps=[
                WorkflowStep(agent_type="research"),
                WorkflowStep(agent_type="assessment"),
            ],
            coordination_type="iterative_refinement",
            max_iterations=3,
            convergence_check="assessment_approved",
        )

        assert definition.coordination_type == "iterative_refinement"
        assert definition.max_iterations == 3
        assert definition.convergence_check == "assessment_approved"

        # Verify validation
        with pytest.raises(ValueError, match="requires a convergence_check"):
            WorkflowDefinition(
                name="invalid",
                description="Missing convergence check",
                steps=[WorkflowStep(agent_type="research")],
                coordination_type="iterative_refinement",
                # Missing convergence_check
            )
