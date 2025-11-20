"""Tests for API endpoints."""

from uuid import UUID

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
class TestHealthEndpoint:
    """Tests for health check endpoint."""

    async def test_health_endpoint(self, client: AsyncClient):
        """Test health check returns 200 OK."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "database" in data
        assert "websocket_connections" in data

    async def test_root_endpoint(self, client: AsyncClient):
        """Test root endpoint."""
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "message" in data


@pytest.mark.asyncio
class TestTaskEndpoints:
    """Tests for task CRUD endpoints."""

    async def test_create_task(self, client: AsyncClient, sample_task_data):
        """Test creating a new task."""
        response = await client.post("/tasks", json=sample_task_data)
        assert response.status_code == 201

        data = response.json()
        assert "id" in data
        assert UUID(data["id"])  # Valid UUID
        assert data["type"] == sample_task_data["type"]
        assert data["status"] == "pending"
        assert data["input"] == sample_task_data["input"]
        assert data["output"] is None
        assert data["error"] is None
        assert "created_at" in data
        assert "updated_at" in data

    async def test_create_task_invalid_data(self, client: AsyncClient):
        """Test creating task with invalid data."""
        response = await client.post("/tasks", json={"type": "test"})
        assert response.status_code == 422  # Validation error

    async def test_get_task(self, client: AsyncClient, sample_task_data):
        """Test retrieving a task by ID."""
        # Create task first
        create_response = await client.post("/tasks", json=sample_task_data)
        task_id = create_response.json()["id"]

        # Get task
        response = await client.get(f"/tasks/{task_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == task_id
        assert data["type"] == sample_task_data["type"]

    async def test_get_nonexistent_task(self, client: AsyncClient):
        """Test getting a task that doesn't exist."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.get(f"/tasks/{fake_id}")
        assert response.status_code == 404

    async def test_list_tasks(self, client: AsyncClient, sample_task_data):
        """Test listing all tasks."""
        # Create multiple tasks
        await client.post("/tasks", json=sample_task_data)
        await client.post("/tasks", json={"type": "analyze_table", "input": {"table_name": "test"}})

        # List tasks
        response = await client.get("/tasks")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    async def test_list_tasks_with_filter(self, client: AsyncClient, sample_task_data):
        """Test listing tasks with status filter."""
        await client.post("/tasks", json=sample_task_data)

        response = await client.get("/tasks?status_filter=pending")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)
        for task in data:
            assert task["status"] == "pending"

    async def test_list_tasks_with_limit(self, client: AsyncClient, sample_task_data):
        """Test listing tasks with limit."""
        # Create multiple tasks
        for _ in range(5):
            await client.post("/tasks", json=sample_task_data)

        response = await client.get("/tasks?limit=3")
        assert response.status_code == 200

        data = response.json()
        assert len(data) <= 3

    async def test_update_task(self, client: AsyncClient, sample_task_data, sample_task_update):
        """Test updating a task."""
        # Create task
        create_response = await client.post("/tasks", json=sample_task_data)
        task_id = create_response.json()["id"]

        # Update task
        response = await client.patch(f"/tasks/{task_id}", json=sample_task_update)
        assert response.status_code == 200

        data = response.json()
        assert data["id"] == task_id
        assert data["status"] == sample_task_update["status"]
        assert data["output"] == sample_task_update["output"]

    async def test_update_task_status_only(self, client: AsyncClient, sample_task_data):
        """Test updating only task status."""
        # Create task
        create_response = await client.post("/tasks", json=sample_task_data)
        task_id = create_response.json()["id"]

        # Update status
        response = await client.patch(f"/tasks/{task_id}", json={"status": "running"})
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "running"
        assert data["output"] is None

    async def test_update_nonexistent_task(self, client: AsyncClient, sample_task_update):
        """Test updating a task that doesn't exist."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = await client.patch(f"/tasks/{fake_id}", json=sample_task_update)
        assert response.status_code == 404


@pytest.mark.asyncio
class TestTaskLifecycle:
    """Integration tests for complete task lifecycle."""

    async def test_complete_task_lifecycle(self, client: AsyncClient):
        """Test complete task lifecycle: create -> get -> update -> get."""
        # 1. Create task
        create_data = {"type": "summarize_document", "input": {"text": "Test document"}}
        create_response = await client.post("/tasks", json=create_data)
        assert create_response.status_code == 201
        task_id = create_response.json()["id"]

        # 2. Get task (should be pending)
        get_response = await client.get(f"/tasks/{task_id}")
        assert get_response.status_code == 200
        assert get_response.json()["status"] == "pending"

        # 3. Update to running
        await client.patch(f"/tasks/{task_id}", json={"status": "running"})
        get_response = await client.get(f"/tasks/{task_id}")
        assert get_response.json()["status"] == "running"

        # 4. Update to done with output
        update_data = {"status": "done", "output": {"summary": "Task completed successfully"}}
        update_response = await client.patch(f"/tasks/{task_id}", json=update_data)
        assert update_response.status_code == 200

        # 5. Final get - verify completion
        final_response = await client.get(f"/tasks/{task_id}")
        final_data = final_response.json()
        assert final_data["status"] == "done"
        assert final_data["output"]["summary"] == "Task completed successfully"

    async def test_task_error_flow(self, client: AsyncClient):
        """Test task failure flow."""
        # Create task
        create_data = {"type": "analyze_table", "input": {"table_name": "test"}}
        create_response = await client.post("/tasks", json=create_data)
        task_id = create_response.json()["id"]

        # Update to running
        await client.patch(f"/tasks/{task_id}", json={"status": "running"})

        # Update to error
        error_data = {"status": "error", "error": "Table not found"}
        await client.patch(f"/tasks/{task_id}", json=error_data)

        # Verify error state
        response = await client.get(f"/tasks/{task_id}")
        data = response.json()
        assert data["status"] == "error"
        assert data["error"] == "Table not found"
        assert data["output"] is None
