"""Base orchestrator abstract class for multi-agent workflows."""

from abc import ABC, abstractmethod
from typing import Any

import psycopg2


class Orchestrator(ABC):
    """
    Base abstract class for workflow orchestrators.

    Orchestrators manage multi-step workflows involving multiple agents.
    They handle state transitions, iteration tracking, and cost aggregation.
    """

    def __init__(self, workflow_type: str):
        """
        Initialize orchestrator.

        Args:
            workflow_type: Unique identifier for this workflow type
        """
        self.workflow_type = workflow_type

    @abstractmethod
    def create_workflow(
        self,
        parent_task_id: str,
        input_data: dict[str, Any],
        conn: psycopg2.extensions.connection,
        user_id_hash: str | None = None,
        tenant_id: str | None = None,
    ) -> None:
        """
        Initialize the workflow.

        Creates workflow_state and first subtask.

        Args:
            parent_task_id: UUID of parent task
            input_data: Initial workflow input
            conn: Database connection
            user_id_hash: Optional user ID for cost tracking
            tenant_id: Optional tenant ID for multi-tenant isolation
        """

    @abstractmethod
    def process_subtask_completion(
        self,
        parent_task_id: str,
        subtask_id: str,
        output: dict[str, Any],
        conn: psycopg2.extensions.connection,
        user_id_hash: str | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Process a completed subtask and determine next action.

        Args:
            parent_task_id: UUID of parent task
            subtask_id: UUID of completed subtask
            subtask_output: Output from the completed subtask
            conn: Database connection
            user_id_hash: Optional user ID

        Returns:
            Dict with 'action' key:
            - 'continue': Workflow continues, another subtask created
            - 'complete': Workflow finished successfully
            - 'failed': Workflow failed
        """

    @abstractmethod
    def get_max_iterations(self) -> int:
        """
        Get maximum number of iterations allowed for this workflow.

        Returns:
            Maximum iteration count
        """
