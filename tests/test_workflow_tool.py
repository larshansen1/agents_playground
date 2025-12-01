"""Unit tests for the workflow OpenWebUI tool."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import requests

# Add integrations to path
sys.path.insert(0, str(Path(__file__).parent.parent / "integrations" / "openwebui"))

from openwebui_workflow_tool import Tools


@pytest.fixture
def workflow_tool():
    """Create a workflow tool instance with test configuration."""
    tool = Tools()
    tool.valves.task_api_url = "http://test-api:8000"
    tool.valves.verify_ssl = False
    tool.valves.poll_interval = 0.1  # Fast polling for tests
    tool.valves.timeout = 1  # Short timeout for tests
    tool.valves.cache_ttl_seconds = 60
    return tool


@pytest.fixture
def mock_workflows():
    """Sample workflows data."""
    return {
        "workflows": [
            {
                "name": "research_assessment",
                "description": "Iterative research with quality assessment",
                "strategy": "iterative_refinement",
                "max_iterations": 3,
                "steps": [
                    {"name": "conduct_research", "agent_type": "research"},
                    {"name": "evaluate_quality", "agent_type": "assessment"},
                ],
            },
            {
                "name": "simple_sequential",
                "description": "Simple sequential two-agent workflow",
                "strategy": "sequential",
                "max_iterations": None,
                "steps": [
                    {"name": "step_one", "agent_type": "agent_one"},
                    {"name": "step_two", "agent_type": "agent_two"},
                ],
            },
        ]
    }


class TestWorkflowTool:
    """Test workflow tool core functionality."""

    @pytest.mark.asyncio
    async def test_list_workflows(self, workflow_tool, mock_workflows):
        """Test listing workflows when no command is provided."""
        with patch("openwebui_workflow_tool.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = mock_workflows
            mock_get.return_value = mock_response

            result = await workflow_tool.workflow("")

            assert "Available Workflows" in result
            assert "research_assessment" in result
            assert "simple_sequential" in result
            assert "Iterative research with quality assessment" in result
            assert "iterative_refinement" in result
            assert "conduct_research → evaluate_quality" in result
            assert mock_get.call_count == 1
            assert "/admin/workflows" in mock_get.call_args[0][0]

    @pytest.mark.asyncio
    async def test_execute_workflow_success(self, workflow_tool):
        """Test successful workflow execution."""
        with (
            patch("openwebui_workflow_tool.requests.post") as mock_post,
            patch("openwebui_workflow_tool.requests.get") as mock_get,
        ):
            # Mock task creation
            mock_post_resp = MagicMock()
            mock_post_resp.status_code = 201
            mock_post_resp.raise_for_status = MagicMock()
            mock_post_resp.json.return_value = {"id": "task-123", "status": "pending"}
            mock_post.return_value = mock_post_resp

            # Mock task polling (pending then done)
            mock_get_resp_pending = MagicMock()
            mock_get_resp_pending.status_code = 200
            mock_get_resp_pending.json.return_value = {"id": "task-123", "status": "running"}

            mock_get_resp_done = MagicMock()
            mock_get_resp_done.status_code = 200
            mock_get_resp_done.json.return_value = {
                "id": "task-123",
                "status": "done",
                "output": {"result": "Workflow completed successfully"},
            }

            mock_get.side_effect = [mock_get_resp_pending, mock_get_resp_done]

            result = await workflow_tool.workflow(
                'research_assessment "quantum computing"', __user__={"id": "user1"}
            )

            assert "Workflow completed successfully" in result
            assert mock_post.call_count == 1
            assert mock_get.call_count == 2

            # Verify payload
            _args, kwargs = mock_post.call_args
            assert kwargs["json"]["type"] == "workflow:research_assessment"
            assert kwargs["json"]["input"]["topic"] == '"quantum computing"'
            assert kwargs["json"]["user_id"] == "user1"

    @pytest.mark.asyncio
    async def test_execute_workflow_missing_topic(self, workflow_tool):
        """Test error when topic is missing."""
        result = await workflow_tool.workflow("research_assessment")
        assert "Missing Topic" in result
        assert "Usage:" in result
        assert '@workflow research_assessment "your topic"' in result

    @pytest.mark.asyncio
    async def test_execute_workflow_not_found(self, workflow_tool, mock_workflows):
        """Test error when workflow is not found."""
        with (
            patch("openwebui_workflow_tool.requests.post") as mock_post,
            patch("openwebui_workflow_tool.requests.get") as mock_get,
        ):
            # Mock task creation failure
            mock_post_resp = MagicMock()
            mock_post_resp.status_code = 400
            mock_post_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
                "400 Bad Request"
            )
            mock_post_resp.json.return_value = {"detail": "Workflow 'invalid_workflow' not found"}

            # Attach response to exception
            mock_post_resp.raise_for_status.side_effect.response = mock_post_resp
            mock_post.return_value = mock_post_resp

            # Mock list workflows for suggestion
            mock_get_resp = MagicMock()
            mock_get_resp.status_code = 200
            mock_get_resp.json.return_value = mock_workflows
            mock_get.return_value = mock_get_resp

            result = await workflow_tool.workflow('invalid_workflow "topic"')

            assert "Workflow 'invalid_workflow' not found" in result
            assert "Available Workflows" in result
            assert "research_assessment" in result

    @pytest.mark.asyncio
    async def test_execute_workflow_timeout(self, workflow_tool):
        """Test timeout waiting for workflow."""
        with (
            patch("openwebui_workflow_tool.requests.post") as mock_post,
            patch("openwebui_workflow_tool.requests.get") as mock_get,
        ):
            # Mock task creation
            mock_post_resp = MagicMock()
            mock_post_resp.status_code = 201
            mock_post_resp.json.return_value = {"id": "task-123", "status": "pending"}
            mock_post.return_value = mock_post_resp

            # Mock task polling (always running)
            mock_get_resp = MagicMock()
            mock_get_resp.status_code = 200
            mock_get_resp.json.return_value = {"id": "task-123", "status": "running"}
            mock_get.return_value = mock_get_resp

            result = await workflow_tool.workflow('research_assessment "topic"')

            assert "timed out" in result.lower() or "failed" in result.lower()

    @pytest.mark.asyncio
    async def test_event_emitter(self, workflow_tool):
        """Test event emitter updates."""
        emitter = AsyncMock()

        with (
            patch("openwebui_workflow_tool.requests.post") as mock_post,
            patch("openwebui_workflow_tool.requests.get") as mock_get,
        ):
            mock_post.return_value.json.return_value = {"id": "task-123", "status": "pending"}
            mock_get.return_value.json.return_value = {
                "id": "task-123",
                "status": "done",
                "output": {"result": "done"},
            }

            await workflow_tool.workflow('research_assessment "topic"', __event_emitter__=emitter)

            # Verify emitter calls
            calls = [call[0][0] for call in emitter.call_args_list]
            assert any("Starting workflow" in str(c) for c in calls)
            assert any("Workflow complete" in str(c) for c in calls)

    @pytest.mark.asyncio
    async def test_workflow_validation(self, workflow_tool, mock_workflows):
        """Test workflow name validation."""
        with patch("openwebui_workflow_tool.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_workflows
            mock_get.return_value = mock_response

            # Empty workflow name
            result = await workflow_tool.workflow("")
            assert "Available Workflows" in result

            # Only whitespace
            result = await workflow_tool.workflow("   ")
            assert "Available Workflows" in result

    @pytest.mark.asyncio
    async def test_api_error_handling(self, workflow_tool):
        """Test API error scenarios."""
        with patch("openwebui_workflow_tool.requests.get") as mock_get:
            # Simulate network error during fetch
            mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

            result = await workflow_tool.workflow("")

            assert "Error" in result
            assert "Connection refused" in result

    @pytest.mark.asyncio
    async def test_ssl_config(self, workflow_tool):
        """Test SSL/mTLS configuration."""
        # Test with SSL verification disabled
        workflow_tool.valves.verify_ssl = False
        config = workflow_tool._get_ssl_config()
        assert config["verify"] is False
        assert "cert" in config

        # Test with SSL verification enabled
        workflow_tool.valves.verify_ssl = True
        config = workflow_tool._get_ssl_config()
        assert config["verify"] == workflow_tool.valves.ca_cert_path

    @pytest.mark.asyncio
    async def test_cache_functionality(self, workflow_tool, mock_workflows):
        """Test workflow list caching."""
        with patch("openwebui_workflow_tool.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_workflows
            mock_get.return_value = mock_response

            # First call - should hit API
            await workflow_tool.workflow("")
            assert mock_get.call_count == 1

            # Second call within cache TTL - should use cache
            await workflow_tool.workflow("")
            assert mock_get.call_count == 1  # Still 1, not 2

    @pytest.mark.asyncio
    async def test_user_context_extraction(self, workflow_tool):
        """Test user ID extraction from context."""
        with (
            patch("openwebui_workflow_tool.requests.post") as mock_post,
            patch("openwebui_workflow_tool.requests.get") as mock_get,
        ):
            mock_post.return_value.json.return_value = {"id": "task-123", "status": "pending"}
            mock_get.return_value.json.return_value = {
                "id": "task-123",
                "status": "done",
                "output": {"result": "done"},
            }

            # With user context
            await workflow_tool.workflow(
                'research_assessment "topic"', __user__={"id": "test-user-123"}
            )

            _args, kwargs = mock_post.call_args
            assert kwargs["json"]["user_id"] == "test-user-123"

            # Without user context
            await workflow_tool.workflow('research_assessment "topic"', __user__=None)

            _args, kwargs = mock_post.call_args
            assert kwargs["json"]["user_id"] is None
