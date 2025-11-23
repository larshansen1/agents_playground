"""
Database utility functions for multi-agent orchestration.

These functions are synchronous and designed to work with psycopg2 connections
used by the worker process.
"""

import uuid
from typing import Any

import psycopg2
from psycopg2.extras import Json, RealDictCursor

from app.logging_config import get_logger

logger = get_logger(__name__)


def get_task_by_id(task_id: str, conn: psycopg2.extensions.connection) -> dict[str, Any] | None:
    """
    Get task by ID.

    Args:
        task_id: UUID of the task
        conn: Database connection

    Returns:
        Task dict or None if not found
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            "SELECT * FROM tasks WHERE id = %s",
            (task_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def create_subtask(
    parent_id: str,
    agent_type: str,
    iteration: int,
    input_data: dict[str, Any],
    conn: psycopg2.extensions.connection,
    user_id_hash: str | None = None,
) -> str:
    """
    Create a new subtask in the database.

    Args:
        parent_id: UUID of the parent task
        agent_type: Type of agent ('research', 'assessment', etc.)
        iteration: Current iteration number
        input_data: Input data for the agent
        conn: Database connection
        user_id_hash: Optional user ID hash for cost tracking

    Returns:
        UUID of the created subtask as string
    """
    subtask_id = str(uuid.uuid4())

    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO subtasks (
                id, parent_task_id, agent_type, iteration, status, input, user_id_hash
            )
            VALUES (%s, %s, %s, %s, 'pending', %s, %s)
            """,
            (subtask_id, parent_id, agent_type, iteration, Json(input_data), user_id_hash),
        )
        conn.commit()

    logger.info(
        "subtask_created",
        subtask_id=subtask_id,
        parent_id=parent_id,
        agent_type=agent_type,
        iteration=iteration,
    )
    return subtask_id


def get_workflow_state(
    parent_id: str, conn: psycopg2.extensions.connection
) -> dict[str, Any] | None:
    """
    Get workflow state for a parent task.

    Args:
        parent_id: UUID of the parent task
        conn: Database connection

    Returns:
        Workflow state dict or None if not found
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT *
            FROM workflow_state
            WHERE parent_task_id = %s
            """,
            (parent_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None


def update_workflow_state(
    parent_id: str,
    current_state: str | None = None,
    current_iteration: int | None = None,
    state_data: dict[str, Any] | None = None,
    conn: psycopg2.extensions.connection | None = None,
) -> None:
    """
    Update workflow state for a parent task.

    Args:
        parent_id: UUID of the parent task
        current_state: New state value (optional)
        current_iteration: New iteration number (optional)
        state_data: New state data (optional)
        conn: Database connection
    """
    updates = []
    params = []

    if current_state is not None:
        updates.append("current_state = %s")
        params.append(current_state)

    if current_iteration is not None:
        updates.append("current_iteration = %s")
        params.append(current_iteration)

    if state_data is not None:
        updates.append("state_data = %s")
        params.append(Json(state_data))

    if not updates:
        logger.warning("update_workflow_state_no_changes", parent_id=parent_id)
        return

    updates.append("updated_at = now()")
    params.append(parent_id)

    with conn.cursor() as cur:
        cur.execute(
            f"""
            UPDATE workflow_state
            SET {', '.join(updates)}
            WHERE parent_task_id = %s
            """,
            params,
        )
        conn.commit()

    logger.info(
        "workflow_state_updated",
        parent_id=parent_id,
        current_state=current_state,
        current_iteration=current_iteration,
    )


def create_workflow_state(
    parent_id: str,
    workflow_type: str,
    initial_state: str,
    max_iterations: int,
    conn: psycopg2.extensions.connection,
    state_data: dict[str, Any] | None = None,
) -> None:
    """
    Create workflow state for a parent task.

    Args:
        parent_id: UUID of the parent task
        workflow_type: Type of workflow ('research_assessment', etc.)
        initial_state: Initial state name
        max_iterations: Maximum number of iterations
        conn: Database connection
        state_data: Optional initial state data
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO workflow_state (
                parent_task_id, workflow_type, current_state, max_iterations, state_data
            )
            VALUES (%s, %s, %s, %s, %s)
            """,
            (parent_id, workflow_type, initial_state, max_iterations, Json(state_data or {})),
        )
        conn.commit()

    logger.info(
        "workflow_state_created",
        parent_id=parent_id,
        workflow_type=workflow_type,
        initial_state=initial_state,
        max_iterations=max_iterations,
    )


def aggregate_subtask_costs(parent_id: str, conn: psycopg2.extensions.connection) -> None:
    """
    Aggregate costs from all subtasks to the parent task.

    Updates the parent task's cost tracking fields by summing all subtask costs.

    Args:
        parent_id: UUID of the parent task
        conn: Database connection
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        # Get aggregated costs
        cur.execute(
            """
            SELECT
                SUM(input_tokens) as total_input_tokens,
                SUM(output_tokens) as total_output_tokens,
                SUM(total_cost) as total_cost,
                string_agg(DISTINCT model_used, ', ') as models_used,
                string_agg(generation_id, ', ') as generation_ids
            FROM subtasks
            WHERE parent_task_id = %s
            """,
            (parent_id,),
        )
        result = cur.fetchone()

        if result:
            # Truncate aggregated strings to fit varchar(100) constraint
            models_used = result["models_used"] or ""
            if len(models_used) > 95:
                models_used = models_used[:92] + "..."

            generation_ids = result["generation_ids"] or ""
            if len(generation_ids) > 95:
                generation_ids = generation_ids[:92] + "..."

            # Update parent task with aggregated costs
            cur.execute(
                """
                UPDATE tasks
                SET
                    input_tokens = %s,
                    output_tokens = %s,
                    total_cost = %s,
                    model_used = %s,
                    generation_id = %s,
                    updated_at = now()
                WHERE id = %s
                """,
                (
                    result["total_input_tokens"] or 0,
                    result["total_output_tokens"] or 0,
                    result["total_cost"] or 0,
                    models_used,
                    generation_ids,
                    parent_id,
                ),
            )
            conn.commit()

            logger.info(
                "parent_costs_aggregated",
                parent_id=parent_id,
                total_cost=float(result["total_cost"] or 0),
                total_input_tokens=result["total_input_tokens"] or 0,
                total_output_tokens=result["total_output_tokens"] or 0,
            )


def get_subtask_by_id(
    subtask_id: str, conn: psycopg2.extensions.connection
) -> dict[str, Any] | None:
    """
    Get a subtask by its ID.

    Args:
        subtask_id: UUID of the subtask
        conn: Database connection

    Returns:
        Subtask dict or None if not found
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT *
            FROM subtasks
            WHERE id = %s
            """,
            (subtask_id,),
        )
        row = cur.fetchone()
        return dict(row) if row else None
