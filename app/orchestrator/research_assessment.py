"""Research-Assessment workflow orchestrator."""

from typing import Any

import psycopg2

from app.db_utils import (
    create_subtask,
    create_workflow_state,
    get_subtask_by_id,
    get_task_by_id,
    get_workflow_state,
    update_workflow_state,
)
from app.logging_config import get_logger
from app.orchestrator.base import Orchestrator

logger = get_logger(__name__)


class ResearchAssessmentOrchestrator(Orchestrator):
    """
    Orchestrator for iterative research-assessment workflow.

    Workflow states:
    - 'research': Research agent is working
    - 'assessment': Assessment agent is evaluating
    - 'completed': Workflow completed successfully
    - 'failed': Workflow failed (max iterations or error)
    """

    def __init__(self, max_iterations: int = 3):
        """
        Initialize orchestrator.

        Args:
            max_iterations: Maximum number of research-assessment cycles
        """
        super().__init__(workflow_type="research_assessment")
        self.max_iterations_value = max_iterations

    def get_max_iterations(self) -> int:
        """Get maximum iterations."""
        return self.max_iterations_value

    def create_workflow(
        self,
        parent_task_id: str,
        input_data: dict[str, Any],
        conn: psycopg2.extensions.connection,
        user_id_hash: str | None = None,
    ) -> None:
        """
        Initialize research-assessment workflow.

        Creates workflow state and first research subtask.

        Args:
            parent_task_id: UUID of parent task
            input_data: Should contain 'topic' key
            conn: Database connection
            user_id_hash: Optional user ID
        """
        # Create workflow state
        create_workflow_state(
            parent_id=parent_task_id,
            workflow_type=self.workflow_type,
            initial_state="research",
            max_iterations=self.max_iterations_value,
            conn=conn,
            state_data={"original_topic": input_data.get("topic", "")},
        )

        # Create first research subtask
        research_input = {"topic": input_data.get("topic", "")}

        # Propagate trace context from parent task to subtask for distributed tracing
        if "_trace_context" in input_data:
            research_input["_trace_context"] = input_data["_trace_context"]

        create_subtask(
            parent_id=parent_task_id,
            agent_type="research",
            iteration=1,
            input_data=research_input,
            conn=conn,
            user_id_hash=user_id_hash,
        )

        logger.info(
            "workflow_created",
            parent_task_id=parent_task_id,
            workflow_type=self.workflow_type,
            initial_state="research",
        )

    def process_subtask_completion(
        self,
        parent_task_id: str,
        subtask_id: str,
        subtask_output: dict[str, Any],
        conn: psycopg2.extensions.connection,
        user_id_hash: str | None = None,
    ) -> dict[str, str]:
        """
        Process subtask completion and transition workflow state.

        Args:
            parent_task_id: UUID of parent task
            subtask_id: UUID of completed subtask
            subtask_output: Output from completed subtask
            conn: Database connection
            user_id_hash: Optional user ID

        Returns:
            Dict with 'action':  'continue' | 'complete' | 'failed'
        """
        # Get workflow state
        workflow_state = get_workflow_state(parent_task_id, conn)
        if not workflow_state:
            logger.error("workflow_state_not_found", parent_task_id=parent_task_id)
            return {"action": "failed"}

        # Get subtask details
        subtask = get_subtask_by_id(subtask_id, conn)
        if not subtask:
            logger.error("subtask_not_found", subtask_id=subtask_id)
            return {"action": "failed"}

        current_state = workflow_state["current_state"]
        current_iteration = workflow_state["current_iteration"]
        agent_type = subtask["agent_type"]

        logger.info(
            "processing_subtask_completion",
            parent_task_id=parent_task_id,
            agent_type=agent_type,
            current_state=current_state,
            iteration=current_iteration,
        )

        # State machine transitions
        if current_state == "research" and agent_type == "research":
            # Research completed -> create assessment subtask
            return self._transition_to_assessment(
                parent_task_id,
                subtask_output,
                current_iteration,
                workflow_state,
                conn,
                user_id_hash,
            )

        if current_state == "assessment" and agent_type == "assessment":
            # Assessment completed -> check approval
            return self._process_assessment_result(
                parent_task_id,
                subtask_output,
                current_iteration,
                workflow_state,
                conn,
                user_id_hash,
            )

        # Invalid state transition
        logger.error(
            "invalid_state_transition",
            current_state=current_state,
            agent_type=agent_type,
        )
        return {"action": "failed"}

    def _transition_to_assessment(
        self,
        parent_task_id: str,
        research_output: dict[str, Any],
        current_iteration: int,
        workflow_state: dict[str, Any],
        conn: psycopg2.extensions.connection,
        user_id_hash: str | None,
    ) -> dict[str, str]:
        """Transition from research to assessment."""
        # Update workflow state
        update_workflow_state(
            parent_id=parent_task_id,
            current_state="assessment",
            state_data={
                **workflow_state.get("state_data", {}),
                f"research_iteration_{current_iteration}": research_output,
            },
            conn=conn,
        )

        # Create assessment subtask
        assessment_input = {
            "research_findings": research_output,
            "iteration": current_iteration,
        }

        # Propagate trace context for distributed tracing
        parent_task = get_task_by_id(parent_task_id, conn)
        if parent_task and "_trace_context" in parent_task.get("input", {}):
            assessment_input["_trace_context"] = parent_task["input"]["_trace_context"]

        create_subtask(
            parent_id=parent_task_id,
            agent_type="assessment",
            iteration=current_iteration,
            input_data=assessment_input,
            conn=conn,
            user_id_hash=user_id_hash,
        )

        logger.info(
            "transitioned_to_assessment",
            parent_task_id=parent_task_id,
            iteration=current_iteration,
        )

        return {"action": "continue"}

    def _process_assessment_result(
        self,
        parent_task_id: str,
        assessment_output: dict[str, Any],
        current_iteration: int,
        workflow_state: dict[str, Any],
        conn: psycopg2.extensions.connection,
        user_id_hash: str | None,
    ) -> dict[str, str]:
        """Process assessment result and determine next action."""
        approved = assessment_output.get("approved", False)

        if approved:
            # Workflow completed successfully
            # Workflow completed successfully
            # Use the latest research findings as the final output
            latest_research = workflow_state.get("state_data", {}).get(
                f"research_iteration_{current_iteration}", {}
            )

            final_output = {
                "status": "completed_approved",
                "research_findings": latest_research,
                "final_assessment": assessment_output,
            }

            update_workflow_state(
                parent_id=parent_task_id,
                current_state="completed",
                state_data={
                    **workflow_state.get("state_data", {}),
                    "completion_reason": "assessment_approved",
                    "final_output": final_output,
                },
                conn=conn,
            )

            logger.info(
                "workflow_completed",
                parent_task_id=parent_task_id,
                iteration=current_iteration,
            )

            return {"action": "complete", "output": final_output}

        # Not approved - check if we can iterate again
        # Not approved - check if we can iterate again
        if current_iteration >= self.max_iterations_value:
            # Max iterations reached - COMPLETE instead of FAIL
            # Use the latest research findings as the final output
            latest_research = workflow_state.get("state_data", {}).get(
                f"research_iteration_{current_iteration}", {}
            )

            final_output = {
                "status": "completed_max_iterations",
                "research_findings": latest_research,
                "final_assessment": assessment_output,
                "note": "Workflow reached maximum iterations limit. Returning latest results.",
            }

            update_workflow_state(
                parent_id=parent_task_id,
                current_state="completed",
                state_data={
                    **workflow_state.get("state_data", {}),
                    "completion_reason": "max_iterations_reached",
                    "final_output": final_output,
                },
                conn=conn,
            )

            logger.info(
                "workflow_completed_max_iterations",
                parent_task_id=parent_task_id,
                max_iterations=self.max_iterations_value,
            )

            # Return complete action with the final output
            return {"action": "complete", "output": final_output}

        # Create new research iteration with feedback
        next_iteration = current_iteration + 1

        update_workflow_state(
            parent_id=parent_task_id,
            current_state="research",
            current_iteration=next_iteration,
            state_data={
                **workflow_state.get("state_data", {}),
                f"assessment_iteration_{current_iteration}": assessment_output,
            },
            conn=conn,
        )

        # Create new research subtask with feedback
        research_input = {
            "topic": workflow_state.get("state_data", {}).get("original_topic", ""),
            "previous_feedback": assessment_output.get("feedback", ""),
        }

        # Propagate trace context for distributed tracing
        parent_task = get_task_by_id(parent_task_id, conn)
        if parent_task and "_trace_context" in parent_task.get("input", {}):
            research_input["_trace_context"] = parent_task["input"]["_trace_context"]

        create_subtask(
            parent_id=parent_task_id,
            agent_type="research",
            iteration=next_iteration,
            input_data=research_input,
            conn=conn,
            user_id_hash=user_id_hash,
        )

        logger.info(
            "starting_revision_iteration",
            parent_task_id=parent_task_id,
            iteration=next_iteration,
            feedback_summary=assessment_output.get("feedback", "")[:100],
        )

        return {"action": "continue"}
