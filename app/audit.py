import logging
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from app.models import AuditLog

logger = logging.getLogger(__name__)


def log_audit_event(
    db: Session,
    event_type: str,
    resource_id: str | UUID | None = None,
    user_id_hash: str | None = None,
    meta: dict[str, Any] | None = None,
) -> AuditLog:
    """
    Log an immutable audit event to the database.

    Args:
        db: Database session
        event_type: Type of event (e.g., "task_started", "task_completed")
        resource_id: ID of the resource involved (Task/Subtask ID)
        user_id_hash: Hash of the user ID who initiated the action
        meta: Additional metadata (cost, tokens, error details)

    Returns:
        The created AuditLog instance
    """
    try:
        audit_log = AuditLog(
            event_type=event_type,
            resource_id=str(resource_id) if resource_id else None,
            user_id_hash=user_id_hash,
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
