import os
import uuid
from unittest.mock import MagicMock

import openai
import pytest
from dotenv import load_dotenv

from app.agents.assessment_agent import AssessmentAgent
from app.agents.research_agent import ResearchAgent
from app.orchestrator.research_assessment import ResearchAssessmentOrchestrator

# Load environment variables from .env file
load_dotenv()

# Skip all tests in this module if no API key is present
pytestmark = pytest.mark.skipif(
    not os.getenv("OPENROUTER_API_KEY"), reason="OPENROUTER_API_KEY not set"
)


class TestE2EWorkflow:
    """End-to-end workflow tests using real LLM calls."""

    def test_real_research_assessment_workflow(self):  # noqa: PLR0915
        """
        Execute a real research-assessment workflow with live LLM calls.

        Verifies:
        1. Research agent produces actual findings
        2. Assessment agent evaluates them
        3. Workflow completes successfully
        4. Real costs are tracked
        """
        # Use a simple topic that's easy to research and assess
        topic = "The history of the Python programming language"
        task_id = str(uuid.uuid4())

        # We still mock the DB connection since we don't want to depend on a real DB
        # But we use real agents and orchestrator logic
        mock_conn = MagicMock()

        # Setup in-memory state storage to replace DB calls
        # This allows the orchestrator to "persist" state during the test
        workflow_state_storage = {}
        subtask_storage = {}

        # Mock DB functions to use our in-memory storage
        def mock_create_state(
            parent_id,
            workflow_type,
            initial_state,
            max_iterations,
            conn,
            state_data=None,
            tenant_id=None,
        ):
            workflow_state_storage[parent_id] = {
                "parent_id": parent_id,
                "workflow_type": workflow_type,
                "current_state": initial_state,
                "max_iterations": max_iterations,
                "current_iteration": 1,
                "state_data": state_data or {},
                "status": "running",
            }

        def mock_update_state(
            parent_id, current_state, conn, state_data=None, current_iteration=None
        ):
            if parent_id in workflow_state_storage:
                state = workflow_state_storage[parent_id]
                state["current_state"] = current_state
                if state_data:
                    state["state_data"] = state_data
                if current_iteration:
                    state["current_iteration"] = current_iteration
                if current_state == "completed":
                    state["status"] = "completed"

        def mock_get_state(parent_id, conn):
            return workflow_state_storage.get(parent_id)

        def mock_create_subtask(
            parent_id, agent_type, iteration, input_data, conn, user_id_hash=None, tenant_id=None
        ):
            subtask_id = str(uuid.uuid4())
            subtask_storage[subtask_id] = {
                "id": subtask_id,
                "parent_task_id": parent_id,
                "agent_type": agent_type,
                "iteration": iteration,
                "input": input_data,
                "status": "pending",
            }
            return subtask_id

        def mock_get_subtask(subtask_id, conn):
            return subtask_storage.get(subtask_id)

        # Apply mocks
        with pytest.MonkeyPatch.context() as m:
            m.setattr(
                "app.orchestrator.research_assessment.create_workflow_state", mock_create_state
            )
            m.setattr(
                "app.orchestrator.research_assessment.update_workflow_state", mock_update_state
            )
            m.setattr("app.orchestrator.research_assessment.get_workflow_state", mock_get_state)
            m.setattr("app.orchestrator.research_assessment.create_subtask", mock_create_subtask)
            m.setattr("app.orchestrator.research_assessment.get_subtask_by_id", mock_get_subtask)

            # Initialize orchestrator
            orchestrator = ResearchAssessmentOrchestrator(max_iterations=2)

            # 1. Start Workflow
            print(f"\nStarting E2E workflow for topic: {topic}")
            orchestrator.create_workflow(
                parent_task_id=task_id, input_data={"topic": topic}, conn=mock_conn
            )

            # Verify initial state
            state = workflow_state_storage[task_id]
            assert state["current_state"] == "research"
            assert len(subtask_storage) == 1

            # Get the research subtask
            research_subtask_id = next(iter(subtask_storage.keys()))
            research_subtask = subtask_storage[research_subtask_id]
            assert research_subtask["agent_type"] == "research"

            # 2. Execute Research Agent (Real Call)
            print("Executing Research Agent (this may take a few seconds)...")

            research_agent = ResearchAgent()

            try:
                research_result = research_agent.execute(research_subtask["input"])
            except openai.AuthenticationError:
                pytest.xfail(
                    "Authentication failed with OpenRouter. Please check your OPENROUTER_API_KEY in .env"
                )
            except Exception as e:
                pytest.fail(f"Research agent execution failed: {e!s}")

            # Verify research output
            assert "output" in research_result
            assert "findings" in research_result["output"]
            assert len(research_result["output"]["findings"]) > 0

            # Verify usage/cost tracking
            assert "usage" in research_result
            assert research_result["usage"]["total_cost"] > 0
            print(f"Research cost: ${research_result['usage']['total_cost']:.6f}")

            # 3. Process Research Completion
            result = orchestrator.process_subtask_completion(
                parent_task_id=task_id,
                subtask_id=research_subtask_id,
                subtask_output=research_result["output"],
                conn=mock_conn,
            )

            assert result["action"] == "continue"

            # Verify transition to assessment
            state = workflow_state_storage[task_id]
            assert state["current_state"] == "assessment"

            # Find the new assessment subtask
            # We expect 2 subtasks now
            assert len(subtask_storage) == 2
            assessment_subtask = None
            for _sid, task in subtask_storage.items():
                if task["agent_type"] == "assessment":
                    assessment_subtask = task
                    break

            assert assessment_subtask is not None

            # 4. Execute Assessment Agent (Real Call)
            print("Executing Assessment Agent...")

            assessment_agent = AssessmentAgent()

            # Add original topic to input as expected by agent
            assessment_input = assessment_subtask["input"]
            assessment_input["original_topic"] = topic

            try:
                assessment_result = assessment_agent.execute(assessment_input)
            except Exception as e:
                pytest.fail(f"Assessment agent execution failed: {e!s}")

            # Verify assessment output
            assert "output" in assessment_result
            assert "approved" in assessment_result["output"]
            assert isinstance(assessment_result["output"]["approved"], bool)

            # Verify usage/cost tracking
            assert "usage" in assessment_result
            assert assessment_result["usage"]["total_cost"] > 0
            print(f"Assessment cost: ${assessment_result['usage']['total_cost']:.6f}")

            # 5. Process Assessment Completion
            result = orchestrator.process_subtask_completion(
                parent_task_id=task_id,
                subtask_id=assessment_subtask["id"],
                subtask_output=assessment_result["output"],
                conn=mock_conn,
            )

            # Depending on approval, it should either complete or continue
            if assessment_result["output"]["approved"]:
                print("Assessment approved! Workflow completed.")
                assert result["action"] == "complete"
                assert result["output"]["status"] == "completed_approved"
            else:
                print("Assessment rejected. Starting refinement iteration.")
                assert result["action"] == "continue"
                # Should have created a new research subtask (iteration 2)
                assert len(subtask_storage) == 3
