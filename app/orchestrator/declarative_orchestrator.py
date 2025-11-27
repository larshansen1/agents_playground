"""Generic declarative orchestrator for YAML-defined workflows."""

from typing import Any

import psycopg2

from app.db_utils import get_workflow_state
from app.logging_config import get_logger
from app.orchestrator.base import Orchestrator
from app.orchestrator.coordination_strategies import create_strategy
from app.workflow_definition import WorkflowDefinition

logger = get_logger(__name__)


class DeclarativeOrchestrator(Orchestrator):
    """
    Generic orchestrator for declarative workflows.

    Interprets WorkflowDefinition and executes the defined steps
    using the configured coordination strategy.
    """

    def __init__(self, definition: WorkflowDefinition):
        """
        Initialize declarative orchestrator.

        Args:
            definition: WorkflowDefinition to execute
        """
        super().__init__(workflow_type=f"declarative:{definition.name}")
        self.definition = definition
        self.strategy = create_strategy(definition)

    def get_max_iterations(self) -> int:
        """Get maximum iterations from definition."""
        return self.definition.max_iterations

    def create_workflow(
        self,
        parent_task_id: str,
        input_data: dict[str, Any],
        conn: psycopg2.extensions.connection,
        user_id_hash: str | None = None,
        tenant_id: str | None = None,
    ) -> None:
        """
        Initialize workflow using definition and strategy.

        Args:
            parent_task_id: UUID of parent task
            input_data: Initial workflow input
            conn: Database connection
            user_id_hash: Optional user ID
            tenant_id: Optional tenant ID
        """
        logger.info(
            "declarative_workflow_create",
            parent_task_id=parent_task_id,
            workflow_name=self.definition.name,
            coordination_type=self.definition.coordination_type,
        )

        # Delegate to coordination strategy
        self.strategy.initialize(
            parent_task_id=parent_task_id,
            input_data=input_data,
            conn=conn,
            user_id_hash=user_id_hash,
            tenant_id=tenant_id,
        )

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
        Process subtask completion using strategy.

        Args:
            parent_task_id: UUID of parent task
            subtask_id: UUID of completed subtask
            output: Output from completed subtask
            conn: Database connection
            user_id_hash: Optional user ID
            tenant_id: Optional tenant ID

        Returns:
            Dict with 'action' key: 'continue' | 'complete' | 'failed'
            and optional 'output' key for final output
        """
        # Get current workflow state
        workflow_state = get_workflow_state(parent_task_id, conn)
        if not workflow_state:
            logger.error(
                "workflow_state_not_found",
                parent_task_id=parent_task_id,
            )
            return {"action": "failed"}

        logger.info(
            "declarative_subtask_completion",
            parent_task_id=parent_task_id,
            subtask_id=subtask_id,
            current_state=workflow_state.get("current_state"),
        )

        # Delegate to coordination strategy
        return self.strategy.process_completion(
            parent_task_id=parent_task_id,
            subtask_id=subtask_id,
            output=output,
            workflow_state=workflow_state,
            conn=conn,
            user_id_hash=user_id_hash,
            tenant_id=tenant_id,
        )
