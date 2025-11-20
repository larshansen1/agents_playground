from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class TaskStatus(str, Enum):
    """Valid task status values - aligned with existing worker."""

    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


class TaskCreate(BaseModel):
    """Schema for creating a new task."""

    type: str = Field(..., description="Type of the task")
    input: dict[str, Any] = Field(..., description="Input data for the task")


class TaskUpdate(BaseModel):
    """Schema for updating an existing task."""

    status: TaskStatus | None = None
    output: dict[str, Any] | None = None
    error: str | None = None


class TaskResponse(BaseModel):
    """Schema for task response."""

    id: UUID
    type: str
    status: str
    input: dict[str, Any]
    output: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime

    # Cost tracking fields
    user_id_hash: str | None = None
    model_used: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_cost: float | None = None
    generation_id: str | None = None

    class Config:
        from_attributes = True


class TaskStatusUpdate(BaseModel):
    """Schema for WebSocket task status updates."""

    task_id: UUID
    status: str
    type: str
    output: dict[str, Any] | None = None
    error: str | None = None
    updated_at: datetime

    # Cost tracking fields (optional, usually only on completion)
    total_cost: float | None = None
    model_used: str | None = None
