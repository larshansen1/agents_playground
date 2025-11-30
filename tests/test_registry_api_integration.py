from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def integration_registries():
    mock_agent_reg = MagicMock()
    mock_tool_reg = MagicMock()
    mock_workflow_reg = MagicMock()

    with (
        patch("app.routers.admin.agent_registry", mock_agent_reg),
        patch("app.routers.admin.tool_registry", mock_tool_reg),
        patch("app.routers.admin.workflow_registry", mock_workflow_reg),
    ):
        yield mock_agent_reg, mock_tool_reg, mock_workflow_reg


def test_discover_agents_tools_workflows(integration_registries):
    """Test complete registry discovery flow."""
    mock_agent_reg, mock_tool_reg, mock_workflow_reg = integration_registries

    # Setup Agents
    mock_agent_reg.list_all.return_value = ["integration_agent"]
    agent_meta = MagicMock()
    agent_meta.description = "Integration Agent"
    agent_meta.config = {"model": "gpt-4"}
    agent_meta.tools = ["integration_tool"]
    mock_agent_reg.get_metadata.return_value = agent_meta

    # Setup Tools
    mock_tool_reg.list_all.return_value = ["integration_tool"]
    tool_meta = MagicMock()
    tool_meta.description = "Integration Tool"
    mock_tool_reg.get_metadata.return_value = tool_meta
    mock_tool_reg.get_schema.return_value = {
        "type": "object",
        "properties": {"param": {"type": "string"}},
    }

    # Setup Workflows
    mock_workflow_reg.list_all.return_value = ["integration_workflow"]
    workflow = MagicMock()
    workflow.name = "integration_workflow"
    workflow.description = "Integration Workflow"
    workflow.coordination_type = "sequential"
    workflow.max_iterations = 1
    step = MagicMock()
    step.name = "step1"
    step.agent_type = "integration_agent"
    workflow.steps = [step]
    mock_workflow_reg.get.return_value = workflow

    # Verify Agents
    resp = client.get("/admin/agents")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["agents"]) == 1
    assert data["agents"][0]["name"] == "integration_agent"
    assert data["agents"][0]["tools"] == ["integration_tool"]

    # Verify Tools
    resp = client.get("/admin/tools")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["tools"]) == 1
    assert data["tools"][0]["name"] == "integration_tool"
    assert "schema" in data["tools"][0]

    # Verify Workflows
    resp = client.get("/admin/workflows")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["workflows"]) == 1
    assert data["workflows"][0]["name"] == "integration_workflow"
    assert data["workflows"][0]["steps"][0]["agent_type"] == "integration_agent"


def test_registry_updates_reflected_in_api(integration_registries):
    """Test dynamic registration reflected in API."""
    mock_agent_reg, _, _ = integration_registries

    # Initially empty
    mock_agent_reg.list_all.return_value = []
    resp = client.get("/admin/agents")
    assert len(resp.json()["agents"]) == 0

    # Register new agent (simulated)
    mock_agent_reg.list_all.return_value = ["new_agent"]
    meta = MagicMock()
    meta.description = "New Agent"
    meta.config = {}
    meta.tools = []
    mock_agent_reg.get_metadata.return_value = meta

    # Verify update
    resp = client.get("/admin/agents")
    assert len(resp.json()["agents"]) == 1
    assert resp.json()["agents"][0]["name"] == "new_agent"
