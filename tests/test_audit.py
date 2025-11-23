from unittest.mock import MagicMock

from app.audit import log_audit_event
from app.models import AuditLog


def test_log_audit_event_success():
    """Test successful audit log creation."""
    mock_db = MagicMock()

    log = log_audit_event(
        mock_db,
        event_type="test_event",
        resource_id="resource-123",
        user_id_hash="user-hash-123",
        meta={"key": "value"},
    )

    assert isinstance(log, AuditLog)
    assert log.event_type == "test_event"
    assert log.resource_id == "resource-123"
    assert log.user_id_hash == "user-hash-123"
    assert log.metadata_ == {"key": "value"}

    mock_db.add.assert_called_once_with(log)


def test_log_audit_event_failure():
    """Test audit log failure handling."""
    mock_db = MagicMock()
    mock_db.add.side_effect = Exception("DB Error")

    log = log_audit_event(mock_db, event_type="test_event")

    # Should return a dummy/empty AuditLog and not raise exception
    assert isinstance(log, AuditLog)
    assert log.event_type is None  # Default empty object
