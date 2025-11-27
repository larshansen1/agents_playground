"""Coordination strategies for declarative workflows."""

from abc import ABC, abstractmethod
from typing import Any

import psycopg2

from app.db_utils import (
    create_subtask,
    create_workflow_state,
    get_task_by_id,
    update_workflow_state,
)
from app.logging_config import get_logger
from app.workflow_definition import WorkflowDefinition

logger = get_logger(__name__)


class CoordinationStrategy(ABC):
    """Base class for coordination strategies."""

    def __init__(self, definition: WorkflowDefinition):
        """
        Initialize strategy with workflow definition.

        Args:
            definition: WorkflowDefinition to execute
        """
        self.definition = definition

    @abstractmethod
    def initialize(
        self,
        parent_task_id: str,
        input_data: dict[str, Any],
        conn: psycopg2.extensions.connection,
        user_id_hash: str | None = None,
        tenant_id: str | None = None,
    ) -> None:
        """
        Initialize workflow state and create first subtask(s).

        Args:
            parent_task_id: UUID of parent task
            input_data: Initial workflow input
            conn: Database connection
            user_id_hash: Optional user ID
            tenant_id: Optional tenant ID
        """

    @abstractmethod
    def process_completion(
        self,
        parent_task_id: str,
        subtask_id: str,
        output: dict[str, Any],
        workflow_state: dict[str, Any],
        conn: psycopg2.extensions.connection,
        user_id_hash: str | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Process subtask completion and determine next action.

        Args:
            parent_task_id: UUID of parent task
            subtask_id: UUID of completed subtask
            output: Output from completed subtask
            workflow_state: Current workflow state from DB
            conn: Database connection
            user_id_hash: Optional user ID
            tenant_id: Optional tenant ID

        Returns:
            Dict with 'action' key: 'continue' | 'complete' | 'failed'
            and optional 'output' key for final output
        """


class SequentialStrategy(CoordinationStrategy):
    """Execute workflow steps sequentially, one after another."""

    def initialize(
        self,
        parent_task_id: str,
        input_data: dict[str, Any],
        conn: psycopg2.extensions.connection,
        user_id_hash: str | None = None,
        tenant_id: str | None = None,
    ) -> None:
        """Initialize sequential workflow."""
        # Create workflow state
        create_workflow_state(
            parent_id=parent_task_id,
            workflow_type=f"declarative:{self.definition.name}",
            initial_state="step_0",
            max_iterations=1,  # Sequential doesn't iterate
            conn=conn,
            state_data={
                "current_step_index": 0,
                "total_steps": len(self.definition.steps),
                "step_outputs": [],
            },
            tenant_id=tenant_id,
        )

        # Create first subtask
        first_step = self.definition.steps[0]
        subtask_input = {**input_data}

        # Propagate trace context
        if "_trace_context" in input_data:
            subtask_input["_trace_context"] = input_data["_trace_context"]

        create_subtask(
            parent_id=parent_task_id,
            agent_type=first_step.agent_type,
            iteration=1,
            input_data=subtask_input,
            conn=conn,
            user_id_hash=user_id_hash,
            tenant_id=tenant_id,
        )

        logger.info(
            "sequential_workflow_initialized",
            parent_task_id=parent_task_id,
            total_steps=len(self.definition.steps),
        )

    def process_completion(
        self,
        parent_task_id: str,
        subtask_id: str,  # noqa: ARG002
        output: dict[str, Any],
        workflow_state: dict[str, Any],
        conn: psycopg2.extensions.connection,
        user_id_hash: str | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        """Process sequential step completion."""
        state_data = workflow_state.get("state_data", {})
        current_step_index = state_data.get("current_step_index", 0)
        step_outputs = state_data.get("step_outputs", [])

        # Store this step's output
        step_outputs.append(output)
        next_step_index = current_step_index + 1

        # Check if we have more steps
        if next_step_index >= len(self.definition.steps):
            # Workflow complete
            final_output = {
                "status": "completed",
                "step_outputs": step_outputs,
                "final_output": output,  # Last step's output
            }

            update_workflow_state(
                parent_id=parent_task_id,
                current_state="completed",
                state_data={
                    **state_data,
                    "step_outputs": step_outputs,
                    "completion_reason": "all_steps_completed",
                },
                conn=conn,
            )

            logger.info(
                "sequential_workflow_completed",
                parent_task_id=parent_task_id,
                total_steps=len(self.definition.steps),
            )

            return {"action": "complete", "output": final_output}

        # Create next subtask
        next_step = self.definition.steps[next_step_index]

        # Pass previous output as input to next step
        next_input = {"previous_output": output}

        # For research -> assessment pattern, pass research findings
        # If previous step was index 0 (research), pass its output as findings
        if current_step_index == 0:
            next_input["research_findings"] = output

        # Propagate trace context
        parent_task = get_task_by_id(parent_task_id, conn)
        if parent_task and "_trace_context" in parent_task.get("input", {}):
            next_input["_trace_context"] = parent_task["input"]["_trace_context"]

        create_subtask(
            parent_id=parent_task_id,
            agent_type=next_step.agent_type,
            iteration=1,
            input_data=next_input,
            conn=conn,
            user_id_hash=user_id_hash,
            tenant_id=tenant_id,
        )

        # Update workflow state
        update_workflow_state(
            parent_id=parent_task_id,
            current_state=f"step_{next_step_index}",
            state_data={
                **state_data,
                "current_step_index": next_step_index,
                "step_outputs": step_outputs,
            },
            conn=conn,
        )

        logger.info(
            "sequential_step_completed",
            parent_task_id=parent_task_id,
            current_step=next_step_index,
            total_steps=len(self.definition.steps),
        )

        return {"action": "continue"}


class IterativeRefinementStrategy(CoordinationStrategy):
    """
    Execute steps in iterations with convergence checking.

    Workflow pattern: step1 -> step2 -> (converged? done : iterate)
    """

    def initialize(
        self,
        parent_task_id: str,
        input_data: dict[str, Any],
        conn: psycopg2.extensions.connection,
        user_id_hash: str | None = None,
        tenant_id: str | None = None,
    ) -> None:
        """Initialize iterative refinement workflow."""
        # Create workflow state
        create_workflow_state(
            parent_id=parent_task_id,
            workflow_type=f"declarative:{self.definition.name}",
            initial_state=self.definition.steps[0].agent_type,
            max_iterations=self.definition.max_iterations,
            conn=conn,
            state_data={
                "original_input": input_data,
                "current_step_index": 0,
            },
            tenant_id=tenant_id,
        )

        # Create first subtask (first step)
        first_step = self.definition.steps[0]
        subtask_input = {**input_data}

        # Propagate trace context
        if "_trace_context" in input_data:
            subtask_input["_trace_context"] = input_data["_trace_context"]

        create_subtask(
            parent_id=parent_task_id,
            agent_type=first_step.agent_type,
            iteration=1,
            input_data=subtask_input,
            conn=conn,
            user_id_hash=user_id_hash,
            tenant_id=tenant_id,
        )

        logger.info(
            "iterative_workflow_initialized",
            parent_task_id=parent_task_id,
            max_iterations=self.definition.max_iterations,
        )

    def process_completion(
        self,
        parent_task_id: str,
        subtask_id: str,  # noqa: ARG002
        output: dict[str, Any],
        workflow_state: dict[str, Any],
        conn: psycopg2.extensions.connection,
        user_id_hash: str | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        """Process iterative refinement step completion."""
        state_data = workflow_state.get("state_data", {})
        current_iteration = workflow_state.get("current_iteration", 1)

        # Get current step index from state
        current_step_index = state_data.get("current_step_index", 0)

        # Determine if this is the last step in the cycle
        is_last_step = current_step_index == len(self.definition.steps) - 1

        if not is_last_step:
            # Not last step, continue to next step in same iteration
            return self._transition_to_next_step(
                parent_task_id,
                output,
                current_iteration,
                current_step_index,
                state_data,
                workflow_state,
                conn,
                user_id_hash,
                tenant_id,
            )

        # Last step completed - check convergence
        return self._check_convergence_and_iterate(
            parent_task_id,
            output,
            current_iteration,
            state_data,
            workflow_state,
            conn,
            user_id_hash,
            tenant_id,
        )

    def _transition_to_next_step(
        self,
        parent_task_id: str,
        output: dict[str, Any],
        current_iteration: int,
        current_step_index: int,
        state_data: dict[str, Any],
        _workflow_state: dict[str, Any],  # Unused but kept for future use
        conn: psycopg2.extensions.connection,
        user_id_hash: str | None,
        tenant_id: str | None,
    ) -> dict[str, str]:
        """Transition to next step in current iteration."""
        next_step_index = current_step_index + 1
        next_step = self.definition.steps[next_step_index]

        # Update workflow state
        update_workflow_state(
            parent_id=parent_task_id,
            current_state=next_step.agent_type,
            state_data={
                **state_data,
                "current_step_index": next_step_index,
                f"step_{current_step_index}_iteration_{current_iteration}": output,
            },
            conn=conn,
        )

        # Create next subtask
        next_input = self._build_next_step_input(
            parent_task_id, output, current_step_index, state_data, conn
        )

        create_subtask(
            parent_id=parent_task_id,
            agent_type=next_step.agent_type,
            iteration=current_iteration,
            input_data=next_input,
            conn=conn,
            user_id_hash=user_id_hash,
            tenant_id=tenant_id,
        )

        logger.info(
            "transitioned_to_next_step",
            parent_task_id=parent_task_id,
            iteration=current_iteration,
            step=next_step_index,
        )

        return {"action": "continue"}

    def _check_convergence_and_iterate(
        self,
        parent_task_id: str,
        output: dict[str, Any],
        current_iteration: int,
        state_data: dict[str, Any],
        _workflow_state: dict[str, Any],  # Unused but kept for future use
        conn: psycopg2.extensions.connection,
        user_id_hash: str | None,
        tenant_id: str | None,
    ) -> dict[str, Any]:
        """Check convergence and either complete or start new iteration."""
        converged = self._check_convergence(output)

        if converged:
            # Workflow completed successfully
            final_output = self._build_final_output(
                output, current_iteration, state_data, "converged"
            )

            update_workflow_state(
                parent_id=parent_task_id,
                current_state="completed",
                state_data={
                    **state_data,
                    "completion_reason": "converged",
                    "final_output": final_output,
                },
                conn=conn,
            )

            logger.info(
                "iterative_workflow_converged",
                parent_task_id=parent_task_id,
                iteration=current_iteration,
            )

            return {"action": "complete", "output": final_output}

        # Check if we've reached max iterations
        if current_iteration >= self.definition.max_iterations:
            # Max iterations reached - complete anyway
            final_output = self._build_final_output(
                output, current_iteration, state_data, "max_iterations"
            )

            update_workflow_state(
                parent_id=parent_task_id,
                current_state="completed",
                state_data={
                    **state_data,
                    "completion_reason": "max_iterations",
                    "final_output": final_output,
                },
                conn=conn,
            )

            logger.info(
                "iterative_workflow_max_iterations",
                parent_task_id=parent_task_id,
                max_iterations=self.definition.max_iterations,
            )

            return {"action": "complete", "output": final_output}

        # Start new iteration
        next_iteration = current_iteration + 1
        first_step = self.definition.steps[0]

        update_workflow_state(
            parent_id=parent_task_id,
            current_state=first_step.agent_type,
            current_iteration=next_iteration,
            state_data={
                **state_data,
                "current_step_index": 0,
                f"last_step_iteration_{current_iteration}": output,
            },
            conn=conn,
        )

        # Create first subtask of new iteration with feedback
        next_input = self._build_iteration_input(parent_task_id, output, state_data, conn)

        create_subtask(
            parent_id=parent_task_id,
            agent_type=first_step.agent_type,
            iteration=next_iteration,
            input_data=next_input,
            conn=conn,
            user_id_hash=user_id_hash,
            tenant_id=tenant_id,
        )

        logger.info(
            "starting_new_iteration",
            parent_task_id=parent_task_id,
            iteration=next_iteration,
        )

        return {"action": "continue"}

    def _check_convergence(self, output: dict[str, Any]) -> bool:
        """
        Check if convergence condition is met.

        Args:
            output: Output from last step

        Returns:
            True if converged
        """
        check_name = self.definition.convergence_check

        if check_name == "assessment_approved":
            return bool(output.get("approved", False))
        if check_name == "quality_threshold":
            # Could add threshold from definition in future
            return bool(output.get("quality_score", 0) >= 0.8)

        # Unknown convergence check - log warning and assume not converged
        logger.warning(
            "unknown_convergence_check",
            check_name=check_name,
            workflow=self.definition.name,
        )
        return False

    def _build_next_step_input(
        self,
        parent_task_id: str,
        previous_output: dict[str, Any],
        previous_step_index: int,
        _state_data: dict[str, Any],  # Unused but kept for future use
        conn: psycopg2.extensions.connection,
    ) -> dict[str, Any]:
        """Build input for next step using previous step's output."""
        # For now, simple pass-through pattern
        next_input = {"previous_output": previous_output}

        # Propagate trace context
        parent_task = get_task_by_id(parent_task_id, conn)
        if parent_task and "_trace_context" in parent_task.get("input", {}):
            next_input["_trace_context"] = parent_task["input"]["_trace_context"]

        # For research -> assessment pattern, pass research findings
        if previous_step_index == 0:
            next_input["research_findings"] = previous_output

        return next_input

    def _build_iteration_input(
        self,
        parent_task_id: str,
        feedback_output: dict[str, Any],
        state_data: dict[str, Any],
        conn: psycopg2.extensions.connection,
    ) -> dict[str, Any]:
        """Build input for new iteration with feedback."""
        original_input = state_data.get("original_input", {})

        next_input = {
            **original_input,
            "previous_feedback": feedback_output.get("feedback", ""),
        }

        # Propagate trace context
        parent_task = get_task_by_id(parent_task_id, conn)
        if parent_task and "_trace_context" in parent_task.get("input", {}):
            next_input["_trace_context"] = parent_task["input"]["_trace_context"]

        return next_input

    def _build_final_output(
        self,
        last_output: dict[str, Any],
        iteration: int,
        state_data: dict[str, Any],
        reason: str,
    ) -> dict[str, Any]:
        """Build final workflow output."""
        # Get the first step's last output (e.g., research findings)
        first_step_output = state_data.get(f"step_0_iteration_{iteration}", {})

        return {
            "status": f"completed_{reason}",
            "research_findings": first_step_output,
            "final_assessment": last_output,
            "iterations": iteration,
        }


def create_strategy(definition: WorkflowDefinition) -> CoordinationStrategy:
    """
    Factory function to create coordination strategy.

    Args:
        definition: WorkflowDefinition

    Returns:
        CoordinationStrategy instance

    Raises:
        ValueError: If coordination_type is unknown
    """
    if definition.coordination_type == "sequential":
        return SequentialStrategy(definition)
    if definition.coordination_type == "iterative_refinement":
        return IterativeRefinementStrategy(definition)

    msg = f"Unknown coordination type: {definition.coordination_type}"
    raise ValueError(msg)
