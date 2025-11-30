from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_registries():
    with (
        patch("app.routers.admin.agent_registry") as mock_agent_reg,
        patch("app.routers.admin.tool_registry") as mock_tool_reg,
        patch("app.routers.admin.workflow_registry") as mock_workflow_reg,
    ):
        yield mock_agent_reg, mock_tool_reg, mock_workflow_reg


class TestAgentRegistryEndpoint:
    def test_list_agents_success(self, mock_registries):
        """Test /admin/agents returns registered agents."""
        mock_agent_reg, _, _ = mock_registries
        mock_agent_reg.list_all.return_value = ["test_agent"]
        mock_metadata = MagicMock()
        mock_metadata.description = "Test Description"
        mock_metadata.config = {"model": "gpt-4"}
        mock_metadata.tools = ["web_search"]
        mock_agent_reg.get_metadata.return_value = mock_metadata

        response = client.get("/admin/agents")
        assert response.status_code == 200
        data = response.json()
        assert len(data["agents"]) == 1
        assert data["agents"][0]["name"] == "test_agent"
        assert data["agents"][0]["description"] == "Test Description"
        assert data["agents"][0]["tools"] == ["web_search"]

    def test_list_agents_empty_registry(self, mock_registries):
        """Test /admin/agents with no agents registered."""
        mock_agent_reg, _, _ = mock_registries
        mock_agent_reg.list_all.return_value = []

        response = client.get("/admin/agents")
        assert response.status_code == 200
        data = response.json()
        assert len(data["agents"]) == 0


class TestToolRegistryEndpoint:
    def test_list_tools_success(self, mock_registries):
        """Test /admin/tools returns registered tools."""
        _, mock_tool_reg, _ = mock_registries
        mock_tool_reg.list_all.return_value = ["test_tool"]
        mock_metadata = MagicMock()
        mock_metadata.description = "Test Tool Description"
        mock_tool_reg.get_metadata.return_value = mock_metadata
        mock_tool_reg.get_schema.return_value = {"type": "object"}

        response = client.get("/admin/tools")
        assert response.status_code == 200
        data = response.json()
        assert len(data["tools"]) == 1
        assert data["tools"][0]["name"] == "test_tool"
        assert data["tools"][0]["description"] == "Test Tool Description"
        assert data["tools"][0]["schema"] == {"type": "object"}

    def test_list_tools_empty_registry(self, mock_registries):
        """Test /admin/tools with no tools registered."""
        _, mock_tool_reg, _ = mock_registries
        mock_tool_reg.list_all.return_value = []

        response = client.get("/admin/tools")
        assert response.status_code == 200
        data = response.json()
        assert len(data["tools"]) == 0


class TestWorkflowRegistryEndpoint:
    def test_list_workflows_success(self, mock_registries):
        """Test /admin/workflows returns registered workflows."""
        _, _, mock_workflow_reg = mock_registries
        mock_workflow_reg.list_all.return_value = ["test_workflow"]

        mock_workflow = MagicMock()
        mock_workflow.name = "test_workflow"
        mock_workflow.description = "Test Workflow Description"
        mock_workflow.coordination_type = "sequential"
        mock_workflow.max_iterations = 1

        mock_step = MagicMock()
        mock_step.name = "step1"
        mock_step.agent_type = "research"

        mock_workflow.steps = [mock_step]
        mock_workflow_reg.get.return_value = mock_workflow

        response = client.get("/admin/workflows")
        assert response.status_code == 200
        data = response.json()
        assert len(data["workflows"]) == 1
        assert data["workflows"][0]["name"] == "test_workflow"
        assert data["workflows"][0]["strategy"] == "sequential"
        assert data["workflows"][0]["steps"][0]["name"] == "step1"

    def test_list_workflows_empty_registry(self):
        """Test /admin/workflows with no workflows registered."""
        with patch("app.routers.admin.workflow_registry") as mock_workflow_reg:
            mock_workflow_reg.list_all.return_value = []

            response = client.get("/admin/workflows")
            assert response.status_code == 200
            data = response.json()
            assert len(data["workflows"]) == 0
