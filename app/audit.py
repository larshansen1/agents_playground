import logging
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models import AuditLog

logger = logging.getLogger(__name__)


def log_audit_event(
    db: Session | AsyncSession,
    event_type: str,
    resource_id: str | UUID | None = None,
    user_id_hash: str | None = None,
    tenant_id: str | None = None,
    meta: dict[str, Any] | None = None,
) -> AuditLog:
    """
    Log an immutable audit event to the database.

    Args:
        db: Database session
        event_type: Type of event (e.g., "task_started", "task_completed")
        resource_id: ID of the resource involved (Task/Subtask ID)
        user_id_hash: Hash of the user ID who initiated the action
        tenant_id: Tenant ID for multi-tenant isolation
        meta: Additional metadata (cost, tokens, error details)

    Returns:
        The created AuditLog instance
    """
    try:
        audit_log = AuditLog(
            event_type=event_type,
            resource_id=str(resource_id) if resource_id else None,
            user_id_hash=user_id_hash,
            tenant_id=tenant_id,
            metadata_=meta or {},
        )
        db.add(audit_log)
        # We don't commit here to allow the caller to bundle with other transactions
        # or commit explicitly.
        # However, for audit logs, we often want them to persist even if the main
        # transaction fails (if possible), but in this simple setup, we'll let
        # the caller handle the commit to keep it transactional with the task update.
        return audit_log
    except Exception as e:
        logger.error(f"Failed to create audit log: {e}")
        # Return a dummy object or None to avoid breaking the flow?
        # For now, just re-raise or swallow based on criticality.
        # Swallowing to ensure auditing doesn't break the main app flow.
        return AuditLog()


def log_task_created(
    db: Session | AsyncSession,
    task_id: str | UUID | None,
    task_type: str | None,
    user_id_hash: str | None = None,
    tenant_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    """Log task creation event."""
    meta = metadata or {}
    meta["task_type"] = task_type
    return log_audit_event(
        db,
        event_type="task_created",
        resource_id=task_id,
        user_id_hash=user_id_hash,
        tenant_id=tenant_id,
        meta=meta,
    )


def log_task_updated(
    db: Session | AsyncSession,
    task_id: str | UUID | None,
    user_id_hash: str | None = None,
    tenant_id: str | None = None,
    changes: dict[str, Any] | None = None,
) -> AuditLog:
    """Log task update event."""
    return log_audit_event(
        db,
        event_type="task_updated",
        resource_id=task_id,
        user_id_hash=user_id_hash,
        tenant_id=tenant_id,
        meta=changes or {},
    )


def log_task_completed(
    db: Session | AsyncSession,
    task_id: str | UUID | None,
    user_id_hash: str | None = None,
    tenant_id: str | None = None,
    status: str = "done",
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    """Log task completion event (done or error)."""
    meta = metadata or {}
    meta["final_status"] = status
    return log_audit_event(
        db,
        event_type="task_completed",
        resource_id=task_id,
        user_id_hash=user_id_hash,
        tenant_id=tenant_id,
        meta=meta,
    )


def log_workflow_initialized(
    db: Session,
    task_id: str | UUID,
    workflow_type: str,
    user_id_hash: str | None = None,
    tenant_id: str | None = None,
) -> AuditLog:
    """Log workflow initialization event."""
    return log_audit_event(
        db,
        event_type="workflow_initialized",
        resource_id=task_id,
        user_id_hash=user_id_hash,
        tenant_id=tenant_id,
        meta={"workflow_type": workflow_type},
    )


def log_subtask_event(
    db: Session,
    event_type: str,
    subtask_id: str | UUID,
    agent_type: str,
    user_id_hash: str | None = None,
    tenant_id: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditLog:
    """Log subtask lifecycle event."""
    meta = metadata or {}
    meta["agent_type"] = agent_type
    return log_audit_event(
        db,
        event_type=event_type,
        resource_id=subtask_id,
        user_id_hash=user_id_hash,
        tenant_id=tenant_id,
        meta=meta,
    )
