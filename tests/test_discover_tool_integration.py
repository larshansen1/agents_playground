"""Integration tests for the discover OpenWebUI tool."""

import asyncio

# Import the discover tool
import sys
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "integrations" / "openwebui"))

from integrations.openwebui.openwebui_discover import Tools


@pytest.fixture
def discover_tool():
    """Create a discover tool instance with test configuration."""
    tool = Tools()
    tool.valves.task_api_url = "http://test-api:8000"
    tool.valves.verify_ssl = False
    tool.valves.cache_ttl_seconds = 60
    return tool


@pytest.fixture
def full_registry_data():
    """Full registry data with all resource types."""
    return {
        "agents": {
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
        },
        "tools": {
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
                                "description": "Max results",
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
                                "description": "Mathematical expression",
                            }
                        },
                        "required": ["expression"],
                    },
                },
            ]
        },
        "workflows": {
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
        },
    }


class TestDiscoverToolIntegration:
    """Integration tests for discover tool."""

    @pytest.mark.asyncio
    async def test_discover_real_backend(self, discover_tool, full_registry_data):
        """Test @discover against mocked backend with full registry."""
        with patch("integrations.openwebui.openwebui_discover.requests.get") as mock_get:

            def side_effect(url, **kwargs):
                mock_resp = MagicMock()
                mock_resp.raise_for_status = MagicMock()
                if "/admin/agents" in url:
                    mock_resp.json.return_value = full_registry_data["agents"]
                elif "/admin/tools" in url:
                    mock_resp.json.return_value = full_registry_data["tools"]
                elif "/admin/workflows" in url:
                    mock_resp.json.return_value = full_registry_data["workflows"]
                return mock_resp

            mock_get.side_effect = side_effect

            # Test discover all
            result = await discover_tool.discover("all")

            # Verify all resources are present
            assert "research" in result
            assert "assessment" in result
            assert "web_search" in result
            assert "calculator" in result
            assert "research_assessment" in result
            assert "simple_sequential" in result

            # Verify counts
            assert "2" in result  # 2 agents, 2 tools, 2 workflows

            # Verify usage instructions
            assert "@flow" in result
            assert "@agent" in result
            assert "@tool" in result

    @pytest.mark.asyncio
    async def test_discover_trace_propagation(self, discover_tool, full_registry_data):
        """Test @discover creates proper trace context (mocked)."""
        # Note: Full tracing integration requires OpenTelemetry setup
        # This test verifies the structure is correct for future tracing

        with patch("integrations.openwebui.openwebui_discover.requests.get") as mock_get:

            def side_effect(url, **kwargs):
                mock_resp = MagicMock()
                mock_resp.raise_for_status = MagicMock()
                if "/admin/agents" in url:
                    mock_resp.json.return_value = full_registry_data["agents"]
                elif "/admin/tools" in url:
                    mock_resp.json.return_value = full_registry_data["tools"]
                elif "/admin/workflows" in url:
                    mock_resp.json.return_value = full_registry_data["workflows"]
                return mock_resp

            mock_get.side_effect = side_effect

            # Execute discover with all resources
            result = await discover_tool.discover("all")

            # Verify all API endpoints were called
            assert mock_get.call_count == 3

            # Verify correct endpoints
            calls = [call[0][0] for call in mock_get.call_args_list]
            assert any("/admin/agents" in call for call in calls)
            assert any("/admin/tools" in call for call in calls)
            assert any("/admin/workflows" in call for call in calls)

            # Verify result is complete
            assert "Available Resources" in result

    @pytest.mark.asyncio
    async def test_discover_emits_status_updates(self, discover_tool, full_registry_data):
        """Test @discover emits UI status updates."""
        emitter = AsyncMock()

        with patch("integrations.openwebui.openwebui_discover.requests.get") as mock_get:

            def side_effect(url, **kwargs):
                mock_resp = MagicMock()
                mock_resp.raise_for_status = MagicMock()
                if "/admin/agents" in url:
                    mock_resp.json.return_value = full_registry_data["agents"]
                elif "/admin/tools" in url:
                    mock_resp.json.return_value = full_registry_data["tools"]
                elif "/admin/workflows" in url:
                    mock_resp.json.return_value = full_registry_data["workflows"]
                return mock_resp

            mock_get.side_effect = side_effect

            # Execute discover with event emitter
            await discover_tool.discover("all", __event_emitter__=emitter)

            # Verify status updates were emitted
            assert emitter.call_count >= 4  # Fetch agents, tools, workflows, format, complete

            # Verify event structure
            for call in emitter.call_args_list:
                event = call[0][0]
                assert "type" in event
                assert "data" in event
                assert event["type"] == "status"
                assert "description" in event["data"]
                assert "done" in event["data"]

            # Verify final status is "done"
            final_event = emitter.call_args_list[-1][0][0]
            assert final_event["data"]["done"] is True

    @pytest.mark.asyncio
    async def test_discover_caching_integration(self, discover_tool, full_registry_data):
        """Test that caching works across multiple discover calls."""
        with patch("integrations.openwebui.openwebui_discover.requests.get") as mock_get:

            def side_effect(url, **kwargs):
                mock_resp = MagicMock()
                mock_resp.raise_for_status = MagicMock()
                if "/admin/agents" in url:
                    mock_resp.json.return_value = full_registry_data["agents"]
                elif "/admin/tools" in url:
                    mock_resp.json.return_value = full_registry_data["tools"]
                elif "/admin/workflows" in url:
                    mock_resp.json.return_value = full_registry_data["workflows"]
                return mock_resp

            mock_get.side_effect = side_effect

            # First discover all - should fetch all 3 resources
            result1 = await discover_tool.discover("all")
            assert mock_get.call_count == 3

            # Second discover all - should use cache
            result2 = await discover_tool.discover("all")
            assert mock_get.call_count == 3  # No additional calls

            # Verify results are identical
            assert result1 == result2

            # Discover specific resources - should use cache
            await discover_tool.discover("agents")
            await discover_tool.discover("tools")
            await discover_tool.discover("workflows")
            assert mock_get.call_count == 3  # Still no additional calls

    @pytest.mark.asyncio
    async def test_discover_error_recovery(self, discover_tool):
        """Test discover recovers gracefully from API errors."""
        with patch("integrations.openwebui.openwebui_discover.requests.get") as mock_get:
            # First call fails
            mock_get.side_effect = Exception("Connection timeout")

            result1 = await discover_tool.discover("agents")
            assert "Unexpected Error" in result1

            # Second call succeeds
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raise_for_status = MagicMock()
            mock_response.json.return_value = {
                "agents": [{"name": "test", "description": "Test agent", "config": {}}]
            }
            mock_get.side_effect = None
            mock_get.return_value = mock_response

            result2 = await discover_tool.discover("agents")
            assert "test" in result2
            assert "Available Agents" in result2

    @pytest.mark.asyncio
    async def test_discover_concurrent_calls(self, discover_tool, full_registry_data):
        """Test discover handles concurrent calls correctly."""
        with patch("integrations.openwebui.openwebui_discover.requests.get") as mock_get:

            def side_effect(url, **kwargs):
                # Simulate slight delay
                import time

                time.sleep(0.01)
                mock_resp = MagicMock()
                mock_resp.raise_for_status = MagicMock()
                if "/admin/agents" in url:
                    mock_resp.json.return_value = full_registry_data["agents"]
                elif "/admin/tools" in url:
                    mock_resp.json.return_value = full_registry_data["tools"]
                elif "/admin/workflows" in url:
                    mock_resp.json.return_value = full_registry_data["workflows"]
                return mock_resp

            mock_get.side_effect = side_effect

            # Launch multiple concurrent discover calls
            tasks = [
                discover_tool.discover("agents"),
                discover_tool.discover("tools"),
                discover_tool.discover("workflows"),
            ]

            results = await asyncio.gather(*tasks)

            # All should succeed
            assert len(results) == 3
            assert all(isinstance(r, str) for r in results)
            assert "Available Agents" in results[0]
            assert "Available Tools" in results[1]
            assert "Available Workflows" in results[2]
