from datetime import UTC
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.database import get_db
from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.add = MagicMock()

    # Mock DB execute result
    mock_result = MagicMock()
    mock_task = MagicMock()
    mock_task.id = "12345678-1234-5678-1234-567812345678"
    mock_task.type = "agent:research"
    mock_task.status = "pending"
    mock_task.created_at = "2024-01-01T00:00:00"
    mock_task.updated_at = "2024-01-01T00:00:00"
    mock_task.input = {"topic": "test"}
    mock_task.output = None
    mock_task.error = None
    mock_task.user_id_hash = None
    mock_task.tenant_id = None

    mock_result.scalar_one.return_value = mock_task
    session.execute.return_value = mock_result

    return session


@pytest.fixture
def mock_dependencies(mock_session):
    # Override DB dependency
    async def override_get_db():
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db

    with (
        patch("app.routers.tasks.agent_registry") as mock_agent_reg,
        patch("app.routers.tasks.inject_trace_context") as mock_inject,
        patch("app.routers.tasks.log_task_created"),
        patch("app.routers.tasks.manager") as mock_manager,
        patch("app.routers.tasks.tasks_created_total"),
    ):
        mock_inject.side_effect = lambda x: x
        mock_manager.broadcast = AsyncMock()

        yield mock_session, mock_agent_reg, mock_manager

    # Clean up
    app.dependency_overrides = {}


def test_create_agent_task_success(mock_dependencies):
    mock_session, mock_agent_reg, _ = mock_dependencies
    mock_agent_reg.has.return_value = True

    # Create a fresh mock task for this test
    mock_task = MagicMock()
    mock_task.id = "12345678-1234-5678-1234-567812345678"
    mock_task.type = "agent:research"
    mock_task.status = "pending"  # Use string as per schema
    mock_task.created_at = "2024-01-01T00:00:00"
    mock_task.updated_at = "2024-01-01T00:00:00"
    mock_task.input = {"topic": "test"}
    mock_task.output = None
    mock_task.error = None
    mock_task.user_id_hash = None
    mock_task.tenant_id = None
    mock_task.subtasks = []
    mock_task.workflow_state = None

    # Update session mock to return this task
    mock_result = MagicMock()
    mock_result.scalar_one.return_value = mock_task
    mock_session.execute.return_value = mock_result

    payload = {"agent_type": "research", "input": {"topic": "test"}, "user_id": "user@example.com"}

    # Mock TaskResponse validation to avoid Pydantic/MagicMock issues
    from datetime import datetime
    from uuid import UUID

    from app.schemas import TaskResponse

    with patch("app.routers.tasks.TaskResponse.model_validate") as mock_validate:
        mock_response = TaskResponse(
            id=UUID(mock_task.id),
            type="agent:research",
            status="pending",
            input={"topic": "test"},
            output=None,
            error=None,
            created_at=datetime.now(UTC),
            updated_at=datetime.now(UTC),
        )
        mock_validate.return_value = mock_response

        response = client.post("/tasks/agent", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["type"] == "agent:research"
        assert data["status"] == "pending"


def test_create_agent_task_unknown_agent(mock_dependencies):
    _, mock_agent_reg, _ = mock_dependencies
    mock_agent_reg.has.return_value = False
    mock_agent_reg.list_all.return_value = ["other_agent"]

    payload = {"agent_type": "unknown", "input": {"topic": "test"}}

    response = client.post("/tasks/agent", json=payload)
    assert response.status_code == 400
    assert "not found" in response.json()["detail"]
