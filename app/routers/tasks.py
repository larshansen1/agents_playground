from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from uuid import UUID
import time

from app.database import get_db
from app.models import Task
from app.schemas import TaskCreate, TaskUpdate, TaskResponse, TaskStatusUpdate
from app.websocket import manager
from app.logging_config import get_logger
from app.trace_utils import inject_trace_context
from app.metrics import (
    tasks_created_total,
    tasks_completed_total,
    task_duration_seconds,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_create: TaskCreate,
    db: AsyncSession = Depends(get_db)
) -> TaskResponse:
    """Create a new task with trace context for distributed tracing."""
    start_time = time.time()
    
    # Inject trace context into input for worker to continue the trace
    task_input_with_context = inject_trace_context(task_create.input)
    
    # Create task with trace context
    task = Task(
        type=task_create.type,
        input=task_input_with_context,  # Includes _trace_context
        status="pending"
    )
    
    db.add(task)
    await db.commit()
    await db.refresh(task)
    
    # Track metrics
    tasks_created_total.labels(task_type=task.type).inc()
    duration = time.time() - start_time
    
    # Log event
    logger.info(
        "task_created",
        task_id=str(task.id),
        task_type=task.type,
        status=task.status,
        duration_seconds=f"{duration:.3f}",
    )
    
    # Broadcast task creation via WebSocket
    await manager.broadcast(TaskStatusUpdate(
        task_id=task.id,
        status=task.status,
        type=task.type,
        output=task.output,
        error=task.error,
        updated_at=task.updated_at
    ))
    
    return task


@router.get("/costs/by-user/{user_hash}")
async def get_user_costs(
    user_hash: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Aggregate costs for a specific user.
    """
    from sqlalchemy import text
    
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
            "total_cost": 0
        }
        
    return {
        "total_tasks": row.total_tasks,
        "total_input_tokens": row.total_input_tokens,
        "total_output_tokens": row.total_output_tokens,
        "total_cost": float(row.total_cost)
    }


@router.get("/costs/summary")
async def get_costs_summary(
    db: AsyncSession = Depends(get_db)
):
    """
    Get overall cost statistics.
    """
    from sqlalchemy import text
    
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
        return {
            "unique_users": 0,
            "total_tasks": 0,
            "total_cost": 0,
            "avg_cost_per_task": 0
        }
        
    return {
        "unique_users": row.unique_users,
        "total_tasks": row.total_tasks,
        "total_cost": float(row.total_cost),
        "avg_cost_per_task": float(row.avg_cost_per_task)
    }


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: UUID,
    db: AsyncSession = Depends(get_db)
) -> TaskResponse:
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
    result = await db.execute(select(Task).where(Task.id == task_id))
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
        )
    
    return task


@router.get("", response_model=List[TaskResponse])
async def list_tasks(
    status_filter: Optional[str] = None,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> List[TaskResponse]:
    """
    List all tasks, optionally filtered by status.
    
    Args:
        status_filter: Optional status to filter by
        limit: Maximum number of tasks to return
        db: Database session
        
    Returns:
        List of tasks
    """
    query = select(Task)
    
    if status_filter:
        query = query.where(Task.status == status_filter)
    
    query = query.order_by(Task.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    tasks = result.scalars().all()
    
    return tasks


@router.patch("/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: UUID,
    task_update: TaskUpdate,
    db: AsyncSession = Depends(get_db)
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task {task_id} not found"
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
    
    await db.commit()
    await db.refresh(task)
    
    # Track metrics for completed tasks
    # Note: Worker updates DB directly, then calls API, so we always record metrics
    # when status is done/error (no need to check previous status)
    # task.status from DB is a string, not enum
    if task.status in ["done", "error"]:
        tasks_completed_total.labels(
            task_type=task.type,
            status=task.status
        ).inc()
        
        # Calculate duration if we have timestamps
        if task.created_at and task.updated_at:
            duration = (task.updated_at - task.created_at).total_seconds()
            task_duration_seconds.labels(
                task_type=task.type,
                status=task.status
            ).observe(duration)
            
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
    await manager.broadcast(TaskStatusUpdate(
        task_id=task.id,
        status=task.status,
        type=task.type,
        output=task.output,
        error=task.error,
        updated_at=task.updated_at
    ))
    
    return task



