import hashlib
import time
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.audit import log_task_completed, log_task_created, log_task_updated
from app.database import get_db
from app.logging_config import get_logger
from app.metrics import (
    task_duration_seconds,
    tasks_completed_total,
    tasks_created_total,
)
from app.models import Task
from app.schemas import TaskCreate, TaskResponse, TaskStatusUpdate, TaskUpdate
from app.trace_utils import inject_trace_context
from app.websocket import manager

logger = get_logger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task_create: TaskCreate, db: AsyncSession = Depends(get_db)) -> TaskResponse:  # noqa: B008
    """Create a new task with trace context for distributed tracing."""

    start_time = time.time()

    # Extract user and tenant context
    user_id = task_create.user_id
    tenant_id = task_create.tenant_id

    # Hash the user_id if provided (for privacy)
    user_id_hash = None
    if user_id:
        user_id_hash = hashlib.sha256(user_id.encode()).hexdigest()

    # Inject trace context into input for worker to continue the trace
    # Preserve trace context from client (e.g., OpenWebUI tool) if already present
    if "_trace_context" not in task_create.input:
        task_input_with_context = inject_trace_context(task_create.input)
    else:
        # Client already provided trace context, use it as-is
        task_input_with_context = task_create.input

    # Inject user context into task input for worker propagation
    if user_id_hash:
        task_input_with_context["_user_id_hash"] = user_id_hash
    if tenant_id:
        task_input_with_context["_tenant_id"] = tenant_id

    # Create task with trace context and user context
    task = Task(
        type=task_create.type,
        input=task_input_with_context,  # Includes _trace_context, _user_id_hash, _tenant_id
        status="pending",
        user_id_hash=user_id_hash,
        tenant_id=tenant_id,
    )

    db.add(task)

    # Log audit event (add to same session, will commit together)
    audit_log = log_task_created(
        db,
        task_id=task.id,
        task_type=task.type,
        user_id_hash=user_id_hash,
        tenant_id=tenant_id,
    )
    db.add(audit_log)

    await db.commit()

    # Reload with relationships for response validation
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.subtasks), selectinload(Task.workflow_state))
        .where(Task.id == task.id)
    )
    task = result.scalar_one()

    # Track metrics
    tasks_created_total.labels(task_type=task.type).inc()
    duration = time.time() - start_time

    # Log event
    logger.info(
        "task_created",
        task_id=str(task.id),
        task_type=task.type,
        status=task.status,
        user_id_hash=user_id_hash,
        tenant_id=tenant_id,
        duration_seconds=f"{duration:.3f}",
    )

    # Broadcast task creation via WebSocket
    await manager.broadcast(
        TaskStatusUpdate(
            task_id=task.id,
            status=task.status,
            type=task.type,
            output=task.output,
            error=task.error,
            updated_at=task.updated_at,
        )
    )

    return TaskResponse.model_validate(task)


@router.get("/costs/by-user/{user_hash}")
async def get_user_costs(user_hash: str, db: AsyncSession = Depends(get_db)):  # noqa: B008
    """
    Aggregate costs for a specific user.
    """

    query = text("""
        SELECT
            COUNT(*) as total_tasks,
            COALESCE(SUM(input_tokens), 0) as total_input_tokens,
            COALESCE(SUM(output_tokens), 0) as total_output_tokens,
            COALESCE(SUM(total_cost), 0) as total_cost
        FROM tasks
        WHERE user_id_hash = :hash
          AND total_cost IS NOT NULL
    """)

    result = await db.execute(query, {"hash": user_hash})
    row = result.first()

    if not row:
        return {
            "total_tasks": 0,
            "total_input_tokens": 0,
            "total_output_tokens": 0,
            "total_cost": 0,
        }

    return {
        "total_tasks": row.total_tasks,
        "total_input_tokens": row.total_input_tokens,
        "total_output_tokens": row.total_output_tokens,
        "total_cost": float(row.total_cost),
    }


@router.get("/costs/summary")
async def get_costs_summary(db: AsyncSession = Depends(get_db)):  # noqa: B008
    """
    Get overall cost statistics.
    """

    query = text("""
        SELECT
            COUNT(DISTINCT user_id_hash) as unique_users,
            COUNT(*) as total_tasks,
            COALESCE(SUM(total_cost), 0) as total_cost,
            COALESCE(AVG(total_cost), 0) as avg_cost_per_task
        FROM tasks
        WHERE total_cost > 0
    """)

    result = await db.execute(query)
    row = result.first()

    if not row:
        return {"unique_users": 0, "total_tasks": 0, "total_cost": 0, "avg_cost_per_task": 0}

    return {
        "unique_users": row.unique_users,
        "total_tasks": row.total_tasks,
        "total_cost": float(row.total_cost),
        "avg_cost_per_task": float(row.avg_cost_per_task),
    }


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: UUID, db: AsyncSession = Depends(get_db)) -> TaskResponse:  # noqa: B008
    """
    Get a task by ID.

    Args:
        task_id: UUID of the task
        db: Database session

    Returns:
        Task data

    Raises:
        HTTPException: If task not found
    """
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.subtasks), selectinload(Task.workflow_state))
        .where(Task.id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found"
        )

    return TaskResponse.model_validate(task)


@router.get("", response_model=list[TaskResponse])
async def list_tasks(
    status_filter: str | None = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[TaskResponse]:
    """
    List all tasks, optionally filtered by status.

    Args:
        status_filter: Optional status to filter by
        limit: Maximum number of tasks to return
        db: Database session

    Returns:
        List of tasks
    """
    query = select(Task).options(selectinload(Task.subtasks), selectinload(Task.workflow_state))

    if status_filter:
        query = query.where(Task.status == status_filter)

    query = query.order_by(Task.created_at.desc()).limit(limit)

    result = await db.execute(query)
    return [TaskResponse.model_validate(t) for t in result.scalars().all()]


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    task_update: TaskUpdate,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> TaskResponse:
    """
    Update a task's status, output, or error.

    Args:
        task_id: UUID of the task
        task_update: Update data
        db: Database session

    Returns:
        Updated task

    Raises:
        HTTPException: If task not found
    """
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found"
        )

    # Update fields if provided
    update_data_dict = {}

    if task_update.status is not None:
        task.status = task_update.status.value
        update_data_dict["status"] = task.status
    if task_update.output is not None:
        task.output = task_update.output
        update_data_dict["output"] = "present"
    if task_update.error is not None:
        task.error = task_update.error
        update_data_dict["error"] = task.error

    # Log audit event for update

    if task.status in ["done", "error"]:
        # Log completion event
        audit_log = log_task_completed(
            db,
            task_id=task.id,
            status=task.status,
            user_id_hash=task.user_id_hash,
            tenant_id=task.tenant_id,
            metadata=update_data_dict,
        )
    else:
        # Log regular update event
        audit_log = log_task_updated(
            db,
            task_id=task.id,
            user_id_hash=task.user_id_hash,
            tenant_id=task.tenant_id,
            changes=update_data_dict,
        )
    db.add(audit_log)

    await db.commit()

    # Reload with relationships
    result = await db.execute(
        select(Task)
        .options(selectinload(Task.subtasks), selectinload(Task.workflow_state))
        .where(Task.id == task_id)
    )
    task = result.scalar_one()

    # Track metrics for completed tasks
    # Note: Worker updates DB directly, then calls API, so we always record metrics
    # when status is done/error (no need to check previous status)
    # task.status from DB is a string, not enum
    if task.status in ["done", "error"]:
        tasks_completed_total.labels(task_type=task.type, status=task.status).inc()

        # Calculate duration if we have timestamps
        if task.created_at and task.updated_at:
            duration = (task.updated_at - task.created_at).total_seconds()
            task_duration_seconds.labels(task_type=task.type, status=task.status).observe(duration)

            logger.info(
                "task_metrics_recorded",
                task_id=str(task.id),
                task_type=task.type,
                status=task.status,
                duration_seconds=f"{duration:.3f}",
            )
    else:
        # Debug: log why metrics weren't recorded
        logger.debug(
            "metrics_skipped",
            task_id=str(task.id),
            status=task.status,
            status_type=type(task.status).__name__,
        )

    # Log event
    logger.info(
        "task_updated",
        task_id=str(task.id),
        task_type=task.type,
        **update_data_dict,
    )

    # Broadcast task update via WebSocket
    await manager.broadcast(
        TaskStatusUpdate(
            task_id=task.id,
            status=task.status,
            type=task.type,
            output=task.output,
            error=task.error,
            updated_at=task.updated_at,
        )
    )

    return TaskResponse.model_validate(task)
