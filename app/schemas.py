from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    """Valid task status values - aligned with existing worker."""
    PENDING = "pending"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"


class TaskCreate(BaseModel):
    """Schema for creating a new task."""
    type: str = Field(..., description="Type of the task")
    input: Dict[str, Any] = Field(..., description="Input data for the task")


class TaskUpdate(BaseModel):
    """Schema for updating an existing task."""
    status: Optional[TaskStatus] = None
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class TaskResponse(BaseModel):
    """Schema for task response."""
    id: UUID
    type: str
    status: str
    input: Dict[str, Any]
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    
    # Cost tracking fields
    user_id_hash: Optional[str] = None
    model_used: Optional[str] = None
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_cost: Optional[float] = None
    generation_id: Optional[str] = None
    
    class Config:
        from_attributes = True


class TaskStatusUpdate(BaseModel):
    """Schema for WebSocket task status updates."""
    task_id: UUID
    status: str
    type: str
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    updated_at: datetime
    
    # Cost tracking fields (optional, usually only on completion)
    total_cost: Optional[float] = None
    model_used: Optional[str] = None


