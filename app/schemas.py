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
    user_id: str | None = Field(None, description="User ID initiating the task")
    tenant_id: str | None = Field(None, description="Tenant ID for multi-tenant isolation")


class TaskUpdate(BaseModel):
    """Schema for updating an existing task."""

    status: TaskStatus | None = None
    output: dict[str, Any] | None = None
    error: str | None = None


class SubtaskResponse(BaseModel):
    """Schema for subtask response."""

    id: UUID
    parent_task_id: UUID
    agent_type: str
    iteration: int
    status: str
    input: dict[str, Any]
    output: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime

    # Cost tracking fields
    user_id_hash: str | None = None
    tenant_id: str | None = None
    model_used: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_cost: float | None = None
    generation_id: str | None = None

    class Config:
        from_attributes = True


class WorkflowStateResponse(BaseModel):
    """Schema for workflow state response."""

    id: UUID
    parent_task_id: UUID
    workflow_type: str
    current_iteration: int
    max_iterations: int
    current_state: str
    state_data: dict[str, Any] | None = None
    tenant_id: str | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


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
    tenant_id: str | None = None
    model_used: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_cost: float | None = None
    generation_id: str | None = None

    # Multi-agent workflow fields (optional, populated on request)
    subtasks: list[SubtaskResponse] | None = None
    workflow_state: WorkflowStateResponse | None = None

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


# Registry Schemas


class AgentInfo(BaseModel):
    """Information about a registered agent."""

    name: str
    description: str
    config: dict[str, Any]
    tools: list[str]


class AgentListResponse(BaseModel):
    """Response for listing agents."""

    agents: list[AgentInfo]


class ToolInfo(BaseModel):
    """Information about a registered tool."""

    name: str
    description: str
    schema_info: dict[str, Any] = Field(..., alias="schema")


class ToolListResponse(BaseModel):
    """Response for listing tools."""

    tools: list[ToolInfo]


class WorkflowStepInfo(BaseModel):
    """Information about a workflow step."""

    name: str
    agent_type: str
    description: str | None = None
    tools: list[str] | None = None


class WorkflowInfo(BaseModel):
    """Information about a registered workflow."""

    name: str
    description: str
    strategy: str
    max_iterations: int
    steps: list[WorkflowStepInfo]


class WorkflowListResponse(BaseModel):
    """Response for listing workflows."""

    workflows: list[WorkflowInfo]


class AgentTaskRequest(BaseModel):
    """Request to execute a specific agent directly."""

    agent_type: str = Field(..., description="Type of agent to execute")
    input: dict[str, Any] = Field(..., description="Input data for the agent")
    user_id: str | None = Field(None, description="User ID initiating the task")
    tenant_id: str | None = Field(None, description="Tenant ID for multi-tenant isolation")
