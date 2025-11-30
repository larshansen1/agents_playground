"""Unit tests for the discover OpenWebUI tool."""

import asyncio

# Import the discover tool
import sys
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import requests

# Add integrations to path
sys.path.insert(0, str(Path(__file__).parent.parent / "integrations" / "openwebui"))

from discover import Tools


@pytest.fixture
def discover_tool():
    """Create a discover tool instance with test configuration."""
    tool = Tools()
    tool.valves.task_api_url = "http://test-api:8000"
    tool.valves.verify_ssl = False
    tool.valves.cache_ttl_seconds = 60
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


@pytest.fixture
def mock_tools():
    """Sample tools data."""
    return {
        "tools": [
            {
                "name": "web_search",
                "description": "Search the web using Brave Search API",
                "schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {
                            "type": "integer",
                            "default": 5,
                            "description": "Max results to return",
                        },
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "calculator",
                "description": "Safe mathematical expression evaluator",
                "schema": {
                    "type": "object",
                    "properties": {
                        "expression": {
                            "type": "string",
                            "description": "Mathematical expression to evaluate",
                        }
                    },
                    "required": ["expression"],
                },
            },
        ]
    }


@pytest.fixture
def mock_workflows():
    """Sample workflows data."""
    return {
        "workflows": [
            {
                "name": "research_assessment",
                "description": "Research with iterative assessment and refinement",
                "strategy": "iterative_refinement",
                "max_iterations": 3,
                "steps": [
                    {
                        "name": "research",
                        "agent_type": "research",
                        "description": "Conduct initial research",
                        "tools": ["web_search"],
                    },
                    {
                        "name": "assessment",
                        "agent_type": "assessment",
                        "description": "Assess research quality",
                    },
                ],
            },
            {
                "name": "simple_sequential",
                "description": "Simple sequential two-agent workflow",
                "strategy": "sequential",
                "steps": [
                    {"name": "step_one", "agent_type": "research"},
                    {"name": "step_two", "agent_type": "assessment"},
                ],
            },
        ]
    }


class TestDiscoverTool:
    """Test discover tool core functionality."""

    @pytest.mark.asyncio
    async def test_discover_all_formats_correctly(
        self, discover_tool, mock_agents, mock_tools, mock_workflows
    ):
        """Test @discover all returns formatted output."""
        with patch("discover.requests.get") as mock_get:
            # Mock all three API calls
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()

            def side_effect(url, **kwargs):
                mock_resp = MagicMock()
                mock_resp.raise_for_status = MagicMock()
                if "/admin/agents" in url:
                    mock_resp.json.return_value = mock_agents
                elif "/admin/tools" in url:
                    mock_resp.json.return_value = mock_tools
                elif "/admin/workflows" in url:
                    mock_resp.json.return_value = mock_workflows
                return mock_resp

            mock_get.side_effect = side_effect

            result = await discover_tool.discover("all")

            assert "Available Resources" in result
            assert "research" in result
            assert "web_search" in result
            assert "research_assessment" in result
            assert "Agents: 2" in result or "Agents:** 2" in result
            assert "Tools: 2" in result or "Tools:** 2" in result
            assert "Workflows: 2" in result or "Workflows:** 2" in result

    @pytest.mark.asyncio
    async def test_discover_agents_only(self, discover_tool, mock_agents):
        """Test @discover agents returns only agents."""
        with patch("discover.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = mock_agents
            mock_get.return_value = mock_response

            result = await discover_tool.discover("agents")

            assert "Available Agents" in result
            assert "research" in result
            assert "assessment" in result
            # Should not fetch tools or workflows
            assert mock_get.call_count == 1
            assert "/admin/agents" in mock_get.call_args[0][0]

    @pytest.mark.asyncio
    async def test_discover_tools_only(self, discover_tool, mock_tools):
        """Test @discover tools returns only tools."""
        with patch("discover.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = mock_tools
            mock_get.return_value = mock_response

            result = await discover_tool.discover("tools")

            assert "Available Tools" in result
            assert "web_search" in result
            assert "calculator" in result
            assert mock_get.call_count == 1
            assert "/admin/tools" in mock_get.call_args[0][0]

    @pytest.mark.asyncio
    async def test_discover_workflows_only(self, discover_tool, mock_workflows):
        """Test @discover workflows returns only workflows."""
        with patch("discover.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = mock_workflows
            mock_get.return_value = mock_response

            result = await discover_tool.discover("workflows")

            assert "Available Workflows" in result
            assert "research_assessment" in result
            assert "simple_sequential" in result
            assert mock_get.call_count == 1
            assert "/admin/workflows" in mock_get.call_args[0][0]

    @pytest.mark.asyncio
    async def test_discover_empty_registry(self, discover_tool):
        """Test @discover with no resources registered."""
        with patch("discover.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {"agents": [], "tools": [], "workflows": []}

            def side_effect(url, **kwargs):
                mock_resp = MagicMock()
                mock_resp.raise_for_status = MagicMock()
                if "/admin/agents" in url:
                    mock_resp.json.return_value = {"agents": []}
                elif "/admin/tools" in url:
                    mock_resp.json.return_value = {"tools": []}
                elif "/admin/workflows" in url:
                    mock_resp.json.return_value = {"workflows": []}
                return mock_resp

            mock_get.side_effect = side_effect

            result = await discover_tool.discover("all")

            assert "No agents registered" in result
            assert "No tools registered" in result
            assert "No workflows registered" in result

    @pytest.mark.asyncio
    async def test_discover_api_error(self, discover_tool):
        """Test @discover handles API errors gracefully."""
        with patch("discover.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.HTTPError("404 Not Found")

            result = await discover_tool.discover("agents")

            assert "Error: Cannot connect to backend" in result
            assert "registry API is unavailable" in result

    @pytest.mark.asyncio
    async def test_discover_network_error(self, discover_tool):
        """Test @discover handles network errors."""
        with patch("discover.requests.get") as mock_get:
            mock_get.side_effect = requests.exceptions.ConnectionError("Connection refused")

            result = await discover_tool.discover("tools")

            assert "Error: Cannot connect to backend" in result

    @pytest.mark.asyncio
    async def test_discover_invalid_response(self, discover_tool):
        """Test @discover handles malformed API responses."""
        with patch("discover.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            # Return invalid JSON structure
            mock_response.json.return_value = {"invalid": "structure"}
            mock_get.return_value = mock_response

            result = await discover_tool.discover("agents")

            # Should handle gracefully and show empty list
            assert "No agents registered" in result or "Available Agents (0)" in result


class TestDiscoverCaching:
    """Test caching functionality."""

    @pytest.mark.asyncio
    async def test_cache_hit(self, discover_tool, mock_agents):
        """Test cached response returns quickly."""
        with patch("discover.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = mock_agents
            mock_get.return_value = mock_response

            # First call - should hit API
            start = time.time()
            await discover_tool.discover("agents")
            first_call_time = time.time() - start

            # Second call - should hit cache
            start = time.time()
            await discover_tool.discover("agents")
            second_call_time = time.time() - start

            # Cache should be faster (or at least not slower)
            # First call makes 1 API request, second makes 0
            assert mock_get.call_count == 1
            assert second_call_time <= first_call_time + 0.1  # Allow small variance

    @pytest.mark.asyncio
    async def test_cache_miss(self, discover_tool, mock_agents):
        """Test cache miss fetches from API."""
        with patch("discover.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = mock_agents
            mock_get.return_value = mock_response

            # First call
            await discover_tool.discover("agents")

            # Verify API was called
            assert mock_get.call_count == 1

    @pytest.mark.asyncio
    async def test_cache_expiry(self, discover_tool, mock_agents):
        """Test cache expires after TTL."""
        # Set short TTL for testing
        discover_tool.valves.cache_ttl_seconds = 1

        with patch("discover.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = mock_agents
            mock_get.return_value = mock_response

            # First call
            await discover_tool.discover("agents")
            assert mock_get.call_count == 1

            # Second call immediately - should use cache
            await discover_tool.discover("agents")
            assert mock_get.call_count == 1

            # Wait for cache to expire
            await asyncio.sleep(1.5)

            # Third call - should fetch from API again
            await discover_tool.discover("agents")
            assert mock_get.call_count == 2

    @pytest.mark.asyncio
    async def test_cache_per_resource_type(
        self, discover_tool, mock_agents, mock_tools, mock_workflows
    ):
        """Test separate cache per resource type."""
        with patch("discover.requests.get") as mock_get:

            def side_effect(url, **kwargs):
                mock_resp = MagicMock()
                mock_resp.raise_for_status = MagicMock()
                if "/admin/agents" in url:
                    mock_resp.json.return_value = mock_agents
                elif "/admin/tools" in url:
                    mock_resp.json.return_value = mock_tools
                elif "/admin/workflows" in url:
                    mock_resp.json.return_value = mock_workflows
                return mock_resp

            mock_get.side_effect = side_effect

            # Fetch each resource type
            await discover_tool.discover("agents")
            await discover_tool.discover("tools")
            await discover_tool.discover("workflows")

            # Should have made 3 API calls (one for each type)
            assert mock_get.call_count == 3

            # Fetch again - should use cache
            await discover_tool.discover("agents")
            await discover_tool.discover("tools")
            await discover_tool.discover("workflows")

            # Should still be 3 calls (cache hit)
            assert mock_get.call_count == 3

            # Verify cache has all three types
            assert "registry:agents" in discover_tool._cache
            assert "registry:tools" in discover_tool._cache
            assert "registry:workflows" in discover_tool._cache


class TestDiscoverFormatting:
    """Test formatting functions."""

    def test_format_agent_with_tools(self, discover_tool):
        """Test agent formatting includes tools."""
        agents = [
            {
                "name": "research",
                "description": "Research agent",
                "config": {"model": "gpt-4-turbo", "temperature": 0.7},
                "tools": ["web_search", "document_reader"],
            }
        ]

        result = discover_tool._format_agents(agents)

        assert "research" in result
        assert "Research agent" in result
        assert "web_search" in result
        assert "document_reader" in result
        assert "gpt-4-turbo" in result
        assert "0.7" in result

    def test_format_tool_with_schema(self, discover_tool):
        """Test tool formatting includes parameter schema."""
        tools = [
            {
                "name": "web_search",
                "description": "Search the web",
                "schema": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Search query"},
                        "max_results": {
                            "type": "integer",
                            "default": 5,
                            "description": "Max results",
                        },
                    },
                    "required": ["query"],
                },
            }
        ]

        result = discover_tool._format_tools(tools)

        assert "web_search" in result
        assert "Search the web" in result
        assert "query" in result
        assert "string" in result
        assert "required" in result
        assert "max_results" in result
        assert "optional" in result
        assert "default=5" in result

    def test_format_workflow_with_steps(self, discover_tool):
        """Test workflow formatting includes all steps."""
        workflows = [
            {
                "name": "research_assessment",
                "description": "Research with assessment",
                "strategy": "iterative_refinement",
                "max_iterations": 3,
                "steps": [
                    {
                        "name": "research",
                        "agent_type": "research",
                        "description": "Conduct research",
                        "tools": ["web_search"],
                    },
                    {"name": "assessment", "agent_type": "assessment", "description": "Assess"},
                ],
            }
        ]

        result = discover_tool._format_workflows(workflows)

        assert "research_assessment" in result
        assert "Research with assessment" in result
        assert "iterative_refinement" in result
        assert "Max Iterations: 3" in result
        assert "research" in result
        assert "assessment" in result
        assert "Conduct research" in result


class TestDiscoverEventEmitter:
    """Test event emitter functionality."""

    @pytest.mark.asyncio
    async def test_emits_status_updates(self, discover_tool, mock_agents):
        """Test that status updates are emitted during discovery."""
        emitter = AsyncMock()

        with patch("discover.requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = mock_agents
            mock_get.return_value = mock_response

            await discover_tool.discover("agents", __event_emitter__=emitter)

            # Verify emitter was called with status updates
            assert emitter.call_count >= 2  # At least fetch and complete
            # Check that status messages were sent
            calls = [call[0][0] for call in emitter.call_args_list]
            assert any("Fetching" in str(call) for call in calls)
