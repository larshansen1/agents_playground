"""Unit tests for the agent OpenWebUI tool."""

import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import requests

# Add integrations to path
sys.path.insert(0, str(Path(__file__).parent.parent / "integrations" / "openwebui"))

from integrations.openwebui.openwebui_agent import Tools


@pytest.fixture
def agent_tool():
    """Create an agent tool instance with test configuration."""
    tool = Tools()
    tool.valves.task_api_url = "http://test-api:8000"
    tool.valves.verify_ssl = False
    tool.valves.poll_interval = 0.1  # Fast polling for tests
    tool.valves.timeout = 1  # Short timeout for tests
    return tool


@pytest.fixture
def mock_agents():
    """Sample agents data."""
    return {
        "agents": [
            {
                "name": "research",
                "description": "Research agent for deep topic investigation",
                "config": {"model": "gpt-4-turbo", "temperature": 0.7},
                "tools": ["web_search", "document_reader"],
            },
            {
                "name": "assessment",
                "description": "Assessment agent for quality evaluation",
                "config": {"model": "gpt-4-turbo", "temperature": 0.3},
                "tools": [],
            },
        ]
    }


class TestAgentTool:
    """Test agent tool core functionality."""

    @pytest.mark.asyncio
    async def test_list_agents(self, agent_tool, mock_agents):
        """Test listing agents when no command is provided."""
        with patch("integrations.openwebui.openwebui_agent.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = mock_agents
            mock_get.return_value = mock_response

            result = await agent_tool.agent("")

            assert "Available Agents" in result
            assert "research" in result
            assert "assessment" in result
            assert "Research agent for deep topic investigation" in result
            assert mock_get.call_count == 1
            assert "/admin/agents" in mock_get.call_args[0][0]

    @pytest.mark.asyncio
    async def test_execute_agent_success(self, agent_tool):
        """Test successful agent execution."""
        with (
            patch("integrations.openwebui.openwebui_agent.requests.post") as mock_post,
            patch("integrations.openwebui.openwebui_agent.requests.get") as mock_get,
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
                "output": {"result": "Agent output"},
            }

            mock_get.side_effect = [mock_get_resp_pending, mock_get_resp_done]

            result = await agent_tool.agent("research 'topic'", __user__={"id": "user1"})

            assert "Agent output" in result
            assert mock_post.call_count == 1
            assert mock_get.call_count == 2

            # Verify payload
            _args, kwargs = mock_post.call_args
            assert kwargs["json"]["agent_type"] == "research"
            assert kwargs["json"]["input"]["description"] == "'topic'"
            assert kwargs["json"]["user_id"] == "user1"

    @pytest.mark.asyncio
    async def test_execute_agent_missing_description(self, agent_tool):
        """Test error when description is missing."""
        result = await agent_tool.agent("research")
        assert "Missing Task Description" in result
        assert "Usage:" in result

    @pytest.mark.asyncio
    async def test_execute_agent_not_found(self, agent_tool, mock_agents):
        """Test error when agent is not found."""
        with (
            patch("integrations.openwebui.openwebui_agent.requests.post") as mock_post,
            patch("integrations.openwebui.openwebui_agent.requests.get") as mock_get,
        ):
            # Mock task creation failure
            mock_post_resp = MagicMock()
            mock_post_resp.status_code = 400
            mock_post_resp.raise_for_status.side_effect = requests.exceptions.HTTPError(
                "400 Bad Request"
            )
            mock_post_resp.json.return_value = {"detail": "Agent 'invalid' not found"}

            # Attach response to exception
            mock_post_resp.raise_for_status.side_effect.response = mock_post_resp
            mock_post.return_value = mock_post_resp

            # Mock list agents for suggestion
            mock_get_resp = MagicMock()
            mock_get_resp.status_code = 200
            mock_get_resp.json.return_value = mock_agents
            mock_get.return_value = mock_get_resp

            # We need to catch the RuntimeError raised by _create_agent_task
            # but the agent method catches it and returns a formatted string
            result = await agent_tool.agent("invalid 'topic'")

            assert "Agent 'invalid' not found" in result
            assert "Available Agents" in result
            assert "research" in result

    @pytest.mark.asyncio
    async def test_execute_agent_timeout(self, agent_tool):
        """Test timeout waiting for agent."""
        with (
            patch("integrations.openwebui.openwebui_agent.requests.post") as mock_post,
            patch("integrations.openwebui.openwebui_agent.requests.get") as mock_get,
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

            result = await agent_tool.agent("research 'topic'")

            assert "Task timed out" in result or "Task failed" in result

    @pytest.mark.asyncio
    async def test_event_emitter(self, agent_tool):
        """Test event emitter updates."""
        emitter = AsyncMock()

        with (
            patch("integrations.openwebui.openwebui_agent.requests.post") as mock_post,
            patch("integrations.openwebui.openwebui_agent.requests.get") as mock_get,
        ):
            mock_post.return_value.json.return_value = {"id": "task-123", "status": "pending"}
            mock_get.return_value.json.return_value = {
                "id": "task-123",
                "status": "done",
                "output": {"result": "done"},
            }

            await agent_tool.agent("research 'topic'", __event_emitter__=emitter)

            # Verify emitter calls
            calls = [call[0][0] for call in emitter.call_args_list]
            assert any("Starting research" in str(c) for c in calls)
            assert any("Task complete" in str(c) for c in calls)
