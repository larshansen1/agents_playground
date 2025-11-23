from unittest.mock import MagicMock, patch

import pytest

from app.orchestrator.research_assessment import ResearchAssessmentOrchestrator


@pytest.fixture
def mock_db_utils():
    with (
        patch("app.orchestrator.research_assessment.get_workflow_state") as mock_get_state,
        patch("app.orchestrator.research_assessment.get_subtask_by_id") as mock_get_subtask,
        patch("app.orchestrator.research_assessment.update_workflow_state") as mock_update_state,
    ):
        yield mock_get_state, mock_get_subtask, mock_update_state


def test_process_assessment_completion_approved(mock_db_utils):
    """Test that approved assessment returns the full final output."""
    mock_get_state, mock_get_subtask, _mock_update_state = mock_db_utils

    orchestrator = ResearchAssessmentOrchestrator()
    conn = MagicMock()

    # Mock workflow state with previous research
    mock_get_state.return_value = {
        "current_state": "assessment",
        "current_iteration": 1,
        "state_data": {"research_iteration_1": {"findings": "Great research"}},
    }

    # Mock subtask
    mock_get_subtask.return_value = {"agent_type": "assessment"}

    # Mock assessment output (approved)
    assessment_output = {"approved": True, "feedback": "Good job"}

    result = orchestrator.process_subtask_completion(
        parent_task_id="parent-123",
        subtask_id="subtask-123",
        subtask_output=assessment_output,
        conn=conn,
    )

    # Verify result contains the full output
    assert result["action"] == "complete"
    assert "output" in result
    assert result["output"]["status"] == "completed_approved"
    assert result["output"]["research_findings"] == {"findings": "Great research"}
    assert result["output"]["final_assessment"] == assessment_output


def test_process_assessment_completion_max_iterations(mock_db_utils):
    """Test that max iterations returns the full final output."""
    mock_get_state, mock_get_subtask, _mock_update_state = mock_db_utils

    orchestrator = ResearchAssessmentOrchestrator(max_iterations=1)
    conn = MagicMock()

    # Mock workflow state (at max iterations)
    mock_get_state.return_value = {
        "current_state": "assessment",
        "current_iteration": 1,
        "state_data": {"research_iteration_1": {"findings": "Okay research"}},
    }

    mock_get_subtask.return_value = {"agent_type": "assessment"}

    # Mock assessment output (not approved)
    assessment_output = {"approved": False, "feedback": "Needs work"}

    result = orchestrator.process_subtask_completion(
        parent_task_id="parent-123",
        subtask_id="subtask-123",
        subtask_output=assessment_output,
        conn=conn,
    )

    # Verify result contains the full output despite failure to approve
    assert result["action"] == "complete"
    assert "output" in result
    assert result["output"]["status"] == "completed_max_iterations"
    assert result["output"]["research_findings"] == {"findings": "Okay research"}
