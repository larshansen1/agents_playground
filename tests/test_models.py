"""Tests for database models."""
import pytest
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Task


@pytest.mark.asyncio
class TestTaskModel:
    """Tests for Task ORM model."""
    
    async def test_create_task(self, async_session: AsyncSession):
        """Test creating a task in database."""
        task = Task(
            type="summarize_document",
            status="pending",
            input={"text": "Test document"}
        )
        
        async_session.add(task)
        await async_session.commit()
        await async_session.refresh(task)
        
        assert task.id is not None
        assert isinstance(task.id, UUID)
        assert task.type == "summarize_document"
        assert task.status == "pending"
        assert task.input == {"text": "Test document"}
        assert task.output is None
        assert task.error is None
        assert task.created_at is not None
        assert task.updated_at is not None
    
    async def test_task_with_output(self, async_session: AsyncSession):
        """Test creating task with output."""
        task = Task(
            type="summarize_document",
            status="done",
            input={"text": "Test"},
            output={"summary": "Test summary"}
        )
        
        async_session.add(task)
        await async_session.commit()
        await async_session.refresh(task)
        
        assert task.status == "done"
        assert task.output["summary"] == "Test summary"
    
    async def test_task_with_error(self, async_session: AsyncSession):
        """Test creating task with error."""
        task = Task(
            type="test_task",
            status="error",
            input={"data": "test"},
            error="Processing failed"
        )
        
        async_session.add(task)
        await async_session.commit()
        await async_session.refresh(task)
        
        assert task.status == "error"
        assert task.error == "Processing failed"
    
    async def test_query_task_by_id(self, async_session: AsyncSession):
        """Test querying task by ID."""
        # Create task
        task = Task(
            type="test_task",
            status="pending",
            input={"data": "test"}
        )
        async_session.add(task)
        await async_session.commit()
        await async_session.refresh(task)
        
        task_id = task.id
        
        # Query by ID
        result = await async_session.execute(
            select(Task).where(Task.id == task_id)
        )
        found_task = result.scalar_one_or_none()
        
        assert found_task is not None
        assert found_task.id == task_id
        assert found_task.type == "test_task"
    
    async def test_query_tasks_by_status(self, async_session: AsyncSession):
        """Test querying tasks by status."""
        # Create multiple tasks
        pending_task = Task(type="task1", status="pending", input={})
        done_task = Task(type="task2", status="done", input={})
        
        async_session.add_all([pending_task, done_task])
        await async_session.commit()
        
        # Query pending tasks
        result = await async_session.execute(
            select(Task).where(Task.status == "pending")
        )
        pending_tasks = result.scalars().all()
        
        assert len(pending_tasks) >= 1
        assert all(t.status == "pending" for t in pending_tasks)
    
    async def test_update_task(self, async_session: AsyncSession):
        """Test updating a task."""
        # Create task
        task = Task(
            type="test_task",
            status="pending",
            input={"data": "test"}
        )
        async_session.add(task)
        await async_session.commit()
        await async_session.refresh(task)
        
        # Update task
        task.status = "done"
        task.output = {"result": "success"}
        
        await async_session.commit()
        await async_session.refresh(task)
        
        assert task.status == "done"
        assert task.output["result"] == "success"
    
    async def test_task_jsonb_fields(self, async_session: AsyncSession):
        """Test JSONB fields store complex data."""
        complex_input = {
            "nested": {
                "field1": "value1",
                "field2": [1, 2, 3]
            },
            "list": ["a", "b", "c"]
        }
        
        task = Task(
            type="complex_task",
            status="pending",
            input=complex_input
        )
        
        async_session.add(task)
        await async_session.commit()
        await async_session.refresh(task)
        
        assert task.input == complex_input
        assert task.input["nested"]["field1"] == "value1"
        assert task.input["list"] == ["a", "b", "c"]
