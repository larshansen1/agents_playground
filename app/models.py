import uuid

from sqlalchemy import TIMESTAMP, Column, ForeignKey, Index, Integer, Numeric, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


class Task(Base):
    """SQLAlchemy model for tasks table."""

    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(Text, nullable=False)
    status = Column(Text, nullable=False, default="pending")
    input = Column(JSONB, nullable=False)
    output = Column(JSONB, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Cost tracking fields
    user_id_hash = Column(String(64), nullable=True)
    tenant_id = Column(String(100), nullable=True)
    model_used = Column(String(100), nullable=True)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_cost = Column(Numeric(10, 6), default=0)
    generation_id = Column(String(100), nullable=True)

    # Relationships for multi-agent workflows
    subtasks: "Mapped[list[Subtask]]" = relationship(
        "Subtask", back_populates="parent_task", cascade="all, delete-orphan"
    )
    workflow_state: "Mapped[WorkflowState | None]" = relationship(
        "WorkflowState", back_populates="parent_task", uselist=False, cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("idx_tasks_status", "status"),
        Index("idx_tasks_user_hash", "user_id_hash"),
        Index("idx_tasks_tenant", "tenant_id"),
        Index("idx_tasks_user_tenant", "user_id_hash", "tenant_id"),
        Index("idx_tasks_cost", "total_cost"),
    )


class Subtask(Base):
    """SQLAlchemy model for subtasks table (individual agent executions)."""

    __tablename__ = "subtasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_task_id = Column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False
    )
    agent_type = Column(Text, nullable=False)
    iteration = Column(Integer, nullable=False, default=1)
    status = Column(Text, nullable=False, default="pending")
    input = Column(JSONB, nullable=False)
    output = Column(JSONB, nullable=True)
    error = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Cost tracking fields
    user_id_hash = Column(String(64), nullable=True)
    tenant_id = Column(String(100), nullable=True)
    model_used = Column(String(100), nullable=True)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    total_cost = Column(Numeric(10, 6), default=0)
    generation_id = Column(String(100), nullable=True)

    # Relationship
    parent_task: "Mapped[Task]" = relationship("Task", back_populates="subtasks")

    __table_args__ = (
        Index("idx_subtasks_parent", "parent_task_id"),
        Index("idx_subtasks_status", "status"),
        Index("idx_subtasks_agent_type", "agent_type"),
        Index("idx_subtasks_iteration", "parent_task_id", "iteration"),
        Index("idx_subtasks_tenant", "tenant_id"),
    )


class WorkflowState(Base):
    """SQLAlchemy model for workflow_state table (state machine tracking)."""

    __tablename__ = "workflow_state"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    parent_task_id = Column(
        UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), nullable=False, unique=True
    )
    workflow_type = Column(Text, nullable=False)
    current_iteration = Column(Integer, nullable=False, default=1)
    max_iterations = Column(Integer, nullable=False, default=3)
    current_state = Column(Text, nullable=False)
    state_data = Column(JSONB, nullable=True)
    tenant_id = Column(String(100), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    updated_at = Column(TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relationship
    parent_task: "Mapped[Task]" = relationship("Task", back_populates="workflow_state")

    __table_args__ = (
        Index("idx_workflow_state_parent", "parent_task_id"),
        Index("idx_workflow_state_type", "workflow_type"),
        Index("idx_workflow_state_current_state", "current_state"),
        Index("idx_workflow_state_tenant", "tenant_id"),
    )


class AuditLog(Base):
    """SQLAlchemy model for audit_logs table (immutable event history)."""

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    event_type = Column(Text, nullable=False)  # e.g., task_created, task_completed
    user_id_hash = Column(String(64), nullable=True)
    tenant_id = Column(String(100), nullable=True)
    resource_id = Column(String(36), nullable=True)  # Task ID or Subtask ID
    metadata_ = Column(
        "metadata", JSONB, nullable=True
    )  # 'metadata' is reserved in SQLAlchemy Base

    __table_args__ = (
        Index("idx_audit_user", "user_id_hash"),
        Index("idx_audit_tenant", "tenant_id"),
        Index("idx_audit_user_tenant", "user_id_hash", "tenant_id"),
        Index("idx_audit_resource", "resource_id"),
        Index("idx_audit_event", "event_type"),
        Index("idx_audit_timestamp", "timestamp"),
    )
