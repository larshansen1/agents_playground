"""Tests for tool integration with agents."""

import pytest

from app.agents.base import Agent
from app.tools.calculator import CalculatorTool
from app.tools.registry import ToolRegistry
from app.tools.web_search import WebSearchTool


class MockAgent(Agent):
    """Mock agent for testing tool integration."""

    def __init__(self, tools: list[str] | None = None):
        super().__init__(agent_type="mock_agent", tools=tools)

    def execute(self, input_data: dict, user_id_hash: str | None = None) -> dict:
        """Mock execute method."""
        return {
            "output": {"result": "test"},
            "usage": {
                "model_used": "none",
                "input_tokens": 0,
                "output_tokens": 0,
                "total_cost": 0.0,
                "generation_id": "test",
            },
        }


class TestAgentToolIntegration:
    """Test suite for agent-tool integration."""

    @pytest.fixture(autouse=True)
    def setup_registry(self):
        """Set up tool registry for tests."""
        from app.tools import registry_init

        # Register test tools if not already registered
        if not registry_init.tool_registry.has("calculator"):
            registry_init.tool_registry.register("calculator", CalculatorTool)

    def test_agent_initialization_without_tools(self):
        """Test agent can be initialized without tools (backward compatibility)."""
        agent = MockAgent()
        assert agent.tools == []
        assert agent._tool_instances == {}

    def test_agent_initialization_with_tools(self):
        """Test agent can be initialized with tools list."""
        agent = MockAgent(tools=["calculator"])
        assert agent.tools == ["calculator"]
        assert agent._tool_instances == {}  # Not loaded yet (lazy)

    def test_agent_get_tool_lazy_loading(self):
        """Test agent loads tools lazily."""
        agent = MockAgent(tools=["calculator"])

        # Tool not loaded yet
        assert "calculator" not in agent._tool_instances

        # Access tool
        tool = agent._get_tool("calculator")

        # Tool now cached
        assert "calculator" in agent._tool_instances
        assert tool is agent._tool_instances["calculator"]

        # Second access returns same instance
        tool2 = agent._get_tool("calculator")
        assert tool is tool2

    def test_agent_get_tool_unknown_raises_error(self):
        """Test getting unknown tool raises error."""
        agent = MockAgent()

        with pytest.raises(ValueError) as exc_info:
            agent._get_tool("nonexistent_tool")

        assert "nonexistent_tool" in str(exc_info.value).lower()

    def test_agent_execute_tool_success(self):
        """Test agent can execute tools successfully."""
        agent = MockAgent(tools=["calculator"])

        result = agent._execute_tool("calculator", expression="2 + 2")

        assert result["success"] is True
        assert result["result"] == 4
        assert result["error"] is None

    def test_agent_execute_tool_with_invalid_params(self):
        """Test tool execution with invalid params raises error."""
        agent = MockAgent(tools=["calculator"])

        with pytest.raises(ValueError):
            agent._execute_tool("calculator")  # Missing required param

    def test_agent_execute_tool_returns_standard_format(self):
        """Test tool execution returns standard result format."""
        agent = MockAgent(tools=["calculator"])

        result = agent._execute_tool("calculator", expression="5 * 3")

        assert "success" in result
        assert "result" in result
        assert "error" in result
        assert "metadata" in result

    def test_agent_tool_execution_error_handling(self):
        """Test tool execution errors are returned in standard format."""
        agent = MockAgent(tools=["calculator"])

        result = agent._execute_tool("calculator", expression="1 / 0")

        assert result["success"] is False
        assert result["error"] is not None
        assert "zero" in result["error"].lower()

    def test_agent_can_use_multiple_tools(self):
        """Test agent can use multiple different tools."""
        from app.tools.registry_init import tool_registry

        # Register web search if not already registered
        if not tool_registry.has("web_search"):
            tool_registry.register("web_search", WebSearchTool)

        agent = MockAgent(tools=["calculator", "web_search"])

        # Use calculator
        calc_result = agent._execute_tool("calculator", expression="10 + 5")
        assert calc_result["success"] is True
        assert calc_result["result"] == 15

        # Both tools now cached
        assert "calculator" in agent._tool_instances

    def test_backward_compatibility_existing_agents(self):
        """Test existing agent subclasses work without modification."""

        class LegacyAgent(Agent):
            """Agent without tool support (old style)."""

            def __init__(self):
                # Old-style initialization (no tools param)
                super().__init__(agent_type="legacy")

            def execute(self, input_data: dict, user_id_hash: str | None = None) -> dict:
                return {
                    "output": {},
                    "usage": {
                        "model_used": "none",
                        "input_tokens": 0,
                        "output_tokens": 0,
                        "total_cost": 0.0,
                        "generation_id": "test",
                    },
                }

        # Should work without errors
        agent = LegacyAgent()
        assert agent.tools == []
        assert hasattr(agent, "_tool_instances")


class TestToolRegistryIntegration:
    """Test tool registry integration."""

    def test_global_registry_exists(self):
        """Test global tool registry is initialized."""
        from app.tools.registry_init import tool_registry

        assert tool_registry is not None
        assert isinstance(tool_registry, ToolRegistry)

    def test_global_registry_is_singleton(self):
        """Test global registry is same instance across imports."""
        from app.tools.registry_init import tool_registry as registry1
        from app.tools.registry_init import tool_registry as registry2

        assert registry1 is registry2
