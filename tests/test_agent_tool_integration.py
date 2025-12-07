"""Integration tests for the agent OpenWebUI tool."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

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
    tool.valves.poll_interval = 0.1
    tool.valves.timeout = 5
    return tool


@pytest.fixture
def mock_agents_response():
    """Mock agents registry response."""
    return {
        "agents": [
            {
                "name": "research",
                "description": "Research agent for deep topic investigation",
                "config": {"model": "gpt-4-turbo", "temperature": 0.7},
                "tools": ["web_search"],
            },
            {
                "name": "assessment",
                "description": "Assessment agent for quality evaluation",
                "config": {"model": "gpt-4-turbo", "temperature": 0.3},
                "tools": [],
            },
        ]
    }


class TestAgentToolIntegration:
    """Integration tests for agent tool."""

    @pytest.mark.asyncio
    async def test_end_to_end_agent_execution(self, agent_tool):
        """Test complete agent execution flow."""
        with (
            patch("integrations.openwebui.openwebui_agent.requests.post") as mock_post,
            patch("integrations.openwebui.openwebui_agent.requests.get") as mock_get,
        ):
            # Mock task creation
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = {
                "id": "task-123",
                "status": "pending",
            }

            # Mock polling - running then done
            mock_get_running = MagicMock()
            mock_get_running.status_code = 200
            mock_get_running.json.return_value = {
                "id": "task-123",
                "status": "running",
            }

            mock_get_done = MagicMock()
            mock_get_done.status_code = 200
            mock_get_done.json.return_value = {
                "id": "task-123",
                "status": "done",
                "output": {
                    "result": "Research findings about quantum computing.",
                },
            }

            mock_get.side_effect = [mock_get_running, mock_get_done]

            result = await agent_tool.agent(
                "research 'quantum computing'",
                __user__={"id": "user-123"},
            )

            # Verify result
            assert "Research findings" in result
            assert "quantum computing" in result

            # Verify API calls
            assert mock_post.call_count == 1
            _post_args, post_kwargs = mock_post.call_args
            assert post_kwargs["json"]["agent_type"] == "research"
            assert post_kwargs["json"]["input"]["description"] == "'quantum computing'"
            assert post_kwargs["json"]["user_id"] == "user-123"

            assert mock_get.call_count == 2

    @pytest.mark.asyncio
    async def test_agent_not_found_shows_available(self, agent_tool, mock_agents_response):
        """Test that invalid agent shows available agents."""
        with (
            patch("integrations.openwebui.openwebui_agent.requests.post") as mock_post,
            patch("integrations.openwebui.openwebui_agent.requests.get") as mock_get,
        ):
            # Mock task creation failure
            error_response = MagicMock()
            error_response.status_code = 400
            error_response.json.return_value = {
                "detail": "Agent 'invalid' not found. Available agents: ['research', 'assessment']"
            }

            # Create HTTPError with response attached
            http_error = requests.exceptions.HTTPError("400 Bad Request")
            http_error.response = error_response

            # Mock post to raise the error
            mock_post_result = MagicMock()
            mock_post_result.raise_for_status.side_effect = http_error
            mock_post.return_value = mock_post_result

            # Mock agents list
            mock_get_result = MagicMock()
            mock_get_result.status_code = 200
            mock_get_result.json.return_value = mock_agents_response
            mock_get.return_value = mock_get_result

            result = await agent_tool.agent("invalid 'test'")

            # Should show available agents
            assert "Agent 'invalid' not found" in result or "not found" in result.lower()
            assert "Available Agents" in result or "research" in result

    @pytest.mark.asyncio
    async def test_task_error_handling(self, agent_tool):
        """Test handling of task errors."""
        with (
            patch("integrations.openwebui.openwebui_agent.requests.post") as mock_post,
            patch("integrations.openwebui.openwebui_agent.requests.get") as mock_get,
        ):
            # Mock task creation
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = {
                "id": "task-456",
                "status": "pending",
            }

            # Mock task polling - error status
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "id": "task-456",
                "status": "error",
                "error": "Agent execution failed: invalid input",
            }

            result = await agent_tool.agent("research 'test'")

            assert "Task failed" in result
            assert "Agent execution failed" in result

    @pytest.mark.asyncio
    async def test_network_error_handling(self, agent_tool):
        """Test handling of network errors."""
        with patch("integrations.openwebui.openwebui_agent.requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError("Connection refused")

            result = await agent_tool.agent("research 'test'")

            assert "Error" in result
            assert "Connection refused" in result

    @pytest.mark.asyncio
    async def test_user_context_propagation(self, agent_tool):
        """Test that user context is properly propagated."""
        with (
            patch("integrations.openwebui.openwebui_agent.requests.post") as mock_post,
            patch("integrations.openwebui.openwebui_agent.requests.get") as mock_get,
        ):
            mock_post.return_value.json.return_value = {"id": "task-789", "status": "pending"}
            mock_get.return_value.json.return_value = {
                "id": "task-789",
                "status": "done",
                "output": {"result": "done"},
            }

            await agent_tool.agent(
                "research 'test'",
                __user__={"id": "user-xyz", "email": "test@example.com"},
            )

            # Verify user_id was included in request
            _post_args, post_kwargs = mock_post.call_args
            assert post_kwargs["json"]["user_id"] == "user-xyz"

    @pytest.mark.asyncio
    async def test_output_format_variations(self, agent_tool):
        """Test handling different output formats."""
        with (
            patch("integrations.openwebui.openwebui_agent.requests.post") as mock_post,
            patch("integrations.openwebui.openwebui_agent.requests.get") as mock_get,
        ):
            mock_post.return_value.json.return_value = {"id": "task-1", "status": "pending"}

            # Test different output formats
            test_cases = [
                {"result": "Simple result"},
                {"response": "Response format"},
                {"content": "Content format"},
                {"data": "Complex", "nested": {"structure": "here"}},
            ]

            for i, output in enumerate(test_cases):
                mock_get.return_value.json.return_value = {
                    "id": f"task-{i}",
                    "status": "done",
                    "output": output,
                }

                result = await agent_tool.agent("research 'test'")

                # Should extract or format the output appropriately
                assert len(result) > 0
                assert "Error" not in result or "```json" in result
