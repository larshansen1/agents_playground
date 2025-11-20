"""Tests for Pydantic schemas."""
import pytest
from datetime import datetime
from uuid import UUID, uuid4
from pydantic import ValidationError

from app.schemas import (
    TaskStatus,
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskStatusUpdate
)


@pytest.mark.unit
class TestTaskStatus:
    """Tests for TaskStatus enum."""
    
    def test_task_status_values(self):
        """Test all task status enum values."""
        assert TaskStatus.PENDING == "pending"
        assert TaskStatus.RUNNING == "running"
        assert TaskStatus.DONE == "done"
        assert TaskStatus.ERROR == "error"
    
    def test_task_status_from_string(self):
        """Test creating TaskStatus from string."""
        status = TaskStatus("pending")
        assert status == TaskStatus.PENDING


@pytest.mark.unit
class TestTaskCreate:
    """Tests for TaskCreate schema."""
    
    def test_valid_task_create(self):
        """Test creating valid task."""
        data = {
            "type": "summarize_document",
            "input": {"text": "Test document"}
        }
        task = TaskCreate(**data)
        assert task.type == "summarize_document"
        assert task.input == {"text": "Test document"}
    
    def test_task_create_missing_type(self):
        """Test creating task without type."""
        with pytest.raises(ValidationError):
            TaskCreate(input={"text": "Test"})
    
    def test_task_create_missing_input(self):
        """Test creating task without input."""
        with pytest.raises(ValidationError):
            TaskCreate(type="summarize_document")
    
    def test_task_create_complex_input(self):
        """Test creating task with complex input."""
        data = {
            "type": "analyze_table",
            "input": {
                "table_name": "users",
                "columns": [
                    {"name": "id", "type": "int"},
                    {"name": "email", "type": "varchar"}
                ],
                "business_context": "User management"
            }
        }
        task = TaskCreate(**data)
        assert task.input["table_name"] == "users"
        assert len(task.input["columns"]) == 2


@pytest.mark.unit
class TestTaskUpdate:
    """Tests for TaskUpdate schema."""
    
    def test_valid_task_update_status(self):
        """Test updating task status."""
        update = TaskUpdate(status=TaskStatus.DONE)
        assert update.status == TaskStatus.DONE
        assert update.output is None
        assert update.error is None
    
    def test_valid_task_update_output(self):
        """Test updating task with output."""
        output = {"summary": "Test summary"}
        update = TaskUpdate(output=output)
        assert update.output == output
        assert update.status is None
    
    def test_valid_task_update_error(self):
        """Test updating task with error."""
        update = TaskUpdate(error="Test error message")
        assert update.error == "Test error message"
    
    def test_task_update_all_fields(self):
        """Test updating all fields."""
        update = TaskUpdate(
            status=TaskStatus.ERROR,
            output=None,
            error="Processing failed"
        )
        assert update.status == TaskStatus.ERROR
        assert update.error == "Processing failed"


@pytest.mark.unit
class TestTaskResponse:
    """Tests for TaskResponse schema."""
    
    def test_task_response_from_dict(self):
        """Test creating TaskResponse from dict."""
        data = {
            "id": uuid4(),
            "type": "summarize_document",
            "status": "pending",
            "input": {"text": "Test"},
            "output": None,
            "error": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        task = TaskResponse(**data)
        assert isinstance(task.id, UUID)
        assert task.type == "summarize_document"
        assert task.status == "pending"
    
    def test_task_response_with_output(self):
        """Test TaskResponse with output data."""
        data = {
            "id": uuid4(),
            "type": "summarize_document",
            "status": "done",
            "input": {"text": "Test"},
            "output": {"summary": "Test summary"},
            "error": None,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        task = TaskResponse(**data)
        assert task.status == "done"
        assert task.output["summary"] == "Test summary"


@pytest.mark.unit
class TestTaskStatusUpdate:
    """Tests for TaskStatusUpdate schema (WebSocket)."""
    
    def test_task_status_update_creation(self):
        """Test creating TaskStatusUpdate."""
        task_id = uuid4()
        update = TaskStatusUpdate(
            task_id=task_id,
            status="running",
            type="summarize_document",
            output=None,
            error=None,
            updated_at=datetime.now()
        )
        assert update.task_id == task_id
        assert update.status == "running"
        assert update.type == "summarize_document"
    
    def test_task_status_update_with_output(self):
        """Test TaskStatusUpdate with output."""
        update = TaskStatusUpdate(
            task_id=uuid4(),
            status="done",
            type="summarize_document",
            output={"summary": "Completed"},
            error=None,
            updated_at=datetime.now()
        )
        assert update.status == "done"
        assert update.output["summary"] == "Completed"
