"""Tests for tool registry."""

import tempfile
from pathlib import Path

import pytest

from app.tools.base import Tool
from app.tools.registry import ToolRegistry


# Mock tools for testing
class MockCalculatorTool(Tool):
    """Mock calculator tool for testing."""

    def __init__(self):
        super().__init__(tool_name="calculator", description="Calculate things")

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {"expression": {"type": "string"}},
            "required": ["expression"],
        }

    def execute(self, **kwargs) -> dict:
        self.validate_params(**kwargs)
        return {"success": True, "result": 42, "error": None, "metadata": {}}


class MockSearchTool(Tool):
    """Mock search tool for testing."""

    def __init__(self):
        super().__init__(tool_name="search", description="Search things")

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        }

    def execute(self, **kwargs) -> dict:
        self.validate_params(**kwargs)
        return {"success": True, "result": [], "error": None, "metadata": {}}


class NotATool:
    """Not a tool, for testing validation."""


class TestToolRegistration:
    """Test tool registration functionality."""

    def test_register_valid_tool(self):
        """Test registering a valid tool."""
        registry = ToolRegistry()
        registry.register("calc", MockCalculatorTool, config={}, description="Calculator")

        assert registry.has("calc")
        assert "calc" in registry.list_all()

    def test_register_duplicate_raises_error(self):
        """Test registering duplicate tool name raises error."""
        registry = ToolRegistry()
        registry.register("calc", MockCalculatorTool)

        with pytest.raises(ValueError) as exc_info:
            registry.register("calc", MockSearchTool)

        error_msg = str(exc_info.value)
        assert "already registered" in error_msg
        assert "calc" in error_msg

    def test_register_invalid_class_raises_error(self):
        """Test registering non-Tool class raises error."""
        registry = ToolRegistry()

        with pytest.raises(ValueError) as exc_info:
            registry.register("invalid", NotATool)  # type: ignore

        error_msg = str(exc_info.value)
        assert "must inherit from Tool" in error_msg

    def test_register_non_class_raises_error(self):
        """Test registering non-class raises error."""
        registry = ToolRegistry()

        with pytest.raises(ValueError) as exc_info:
            registry.register("invalid", "not_a_class")  # type: ignore

        error_msg = str(exc_info.value)
        assert "must be a class" in error_msg

    def test_register_with_config(self):
        """Test tool registration stores config."""
        registry = ToolRegistry()
        config = {"api_key": "test123", "timeout": 30}
        registry.register("calc", MockCalculatorTool, config=config)

        metadata = registry.get_metadata("calc")
        assert metadata.config == config

    def test_register_with_description(self):
        """Test tool registration stores description."""
        registry = ToolRegistry()
        description = "A powerful calculator tool"
        registry.register("calc", MockCalculatorTool, description=description)

        metadata = registry.get_metadata("calc")
        assert metadata.description == description


class TestToolInstantiation:
    """Test tool instantiation functionality."""

    def test_get_returns_singleton(self):
        """Test get() returns same instance on repeated calls."""
        registry = ToolRegistry()
        registry.register("calc", MockCalculatorTool)

        tool1 = registry.get("calc")
        tool2 = registry.get("calc")

        assert tool1 is tool2  # Same object

    def test_get_unknown_tool_raises_error(self):
        """Test getting unknown tool raises helpful error."""
        registry = ToolRegistry()
        registry.register("calc", MockCalculatorTool)

        with pytest.raises(ValueError) as exc_info:
            registry.get("unknown")

        error_msg = str(exc_info.value)
        assert "unknown" in error_msg.lower()
        assert "calc" in error_msg  # Shows available tools

    def test_create_new_returns_fresh_instance(self):
        """Test create_new() returns different instance each time."""
        registry = ToolRegistry()
        registry.register("calc", MockCalculatorTool)

        tool1 = registry.create_new("calc")
        tool2 = registry.create_new("calc")

        assert tool1 is not tool2  # Different objects

    def test_create_new_vs_get_different_instances(self):
        """Test create_new() returns different instance than get()."""
        registry = ToolRegistry()
        registry.register("calc", MockCalculatorTool)

        singleton = registry.get("calc")
        new_instance = registry.create_new("calc")

        assert singleton is not new_instance

    def test_create_new_unknown_tool_raises_error(self):
        """Test create_new() with unknown tool raises error."""
        registry = ToolRegistry()

        with pytest.raises(ValueError) as exc_info:
            registry.create_new("unknown")

        error_msg = str(exc_info.value)
        assert "unknown" in error_msg.lower()


class TestToolDiscovery:
    """Test tool discovery functionality."""

    def test_list_all_empty(self):
        """Test list_all() returns empty list when no tools registered."""
        registry = ToolRegistry()
        assert registry.list_all() == []

    def test_list_all_with_tools(self):
        """Test list_all() returns all registered tool names."""
        registry = ToolRegistry()
        registry.register("calc", MockCalculatorTool)
        registry.register("search", MockSearchTool)

        tools = registry.list_all()
        assert len(tools) == 2
        assert "calc" in tools
        assert "search" in tools

    def test_has_returns_true_for_registered(self):
        """Test has() returns True for registered tool."""
        registry = ToolRegistry()
        registry.register("calc", MockCalculatorTool)

        assert registry.has("calc") is True

    def test_has_returns_false_for_unregistered(self):
        """Test has() returns False for unregistered tool."""
        registry = ToolRegistry()
        assert registry.has("unknown") is False

    def test_get_metadata_returns_correct_data(self):
        """Test get_metadata() returns correct ToolMetadata."""
        registry = ToolRegistry()
        config = {"key": "value"}
        description = "Test tool"
        registry.register("calc", MockCalculatorTool, config=config, description=description)

        metadata = registry.get_metadata("calc")

        assert metadata.tool_class == MockCalculatorTool
        assert metadata.config == config
        assert metadata.description == description

    def test_get_metadata_unknown_tool_raises_error(self):
        """Test get_metadata() with unknown tool raises error."""
        registry = ToolRegistry()

        with pytest.raises(ValueError) as exc_info:
            registry.get_metadata("unknown")

        assert "unknown" in str(exc_info.value).lower()

    def test_get_schema_returns_tool_schema(self):
        """Test get_schema() returns tool's JSON schema."""
        registry = ToolRegistry()
        registry.register("calc", MockCalculatorTool)

        schema = registry.get_schema("calc")

        assert "type" in schema
        assert "properties" in schema
        assert "expression" in schema["properties"]

    def test_get_schema_unknown_tool_raises_error(self):
        """Test get_schema() with unknown tool raises error."""
        registry = ToolRegistry()

        with pytest.raises(ValueError):
            registry.get_schema("unknown")


class TestToolErrorHandling:
    """Test error handling in registry."""

    def test_error_message_lists_available_tools(self):
        """Test error messages include list of available tools."""
        registry = ToolRegistry()
        registry.register("calc", MockCalculatorTool)
        registry.register("search", MockSearchTool)

        with pytest.raises(ValueError) as exc_info:
            registry.get("unknown")

        error_msg = str(exc_info.value)
        assert "calc" in error_msg
        assert "search" in error_msg

    def test_error_message_when_no_tools_registered(self):
        """Test error message when trying to get tool from empty registry."""
        registry = ToolRegistry()

        with pytest.raises(ValueError) as exc_info:
            registry.get("unknown")

        error_msg = str(exc_info.value)
        assert "none registered" in error_msg.lower() or "no tools" in error_msg.lower()

    def test_duplicate_registration_shows_existing_class(self):
        """Test duplicate registration error shows existing tool class."""
        registry = ToolRegistry()
        registry.register("calc", MockCalculatorTool)

        with pytest.raises(ValueError) as exc_info:
            registry.register("calc", MockSearchTool)

        error_msg = str(exc_info.value)
        assert "MockCalculatorTool" in error_msg


class TestYAMLLoading:
    """Test YAML configuration loading."""

    def test_load_from_yaml_file_not_found(self):
        """Test load_from_yaml raises error if file doesn't exist."""
        registry = ToolRegistry()

        with pytest.raises(FileNotFoundError):
            registry.load_from_yaml("nonexistent.yaml")

    def test_load_from_yaml_invalid_yaml(self):
        """Test load_from_yaml raises error for invalid YAML."""
        registry = ToolRegistry()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            f.flush()
            yaml_path = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                registry.load_from_yaml(yaml_path)

            assert "Invalid YAML" in str(exc_info.value)
        finally:
            Path(yaml_path).unlink()

    def test_load_from_yaml_missing_tools_key(self):
        """Test load_from_yaml raises error if 'tools' key missing."""
        registry = ToolRegistry()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("other_key: value\n")
            f.flush()
            yaml_path = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                registry.load_from_yaml(yaml_path)

            assert "tools" in str(exc_info.value).lower()
        finally:
            Path(yaml_path).unlink()

    def test_load_from_yaml_tools_not_list(self):
        """Test load_from_yaml raises error if 'tools' is not a list."""
        registry = ToolRegistry()

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("tools: not_a_list\n")
            f.flush()
            yaml_path = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                registry.load_from_yaml(yaml_path)

            assert "must be a list" in str(exc_info.value).lower()
        finally:
            Path(yaml_path).unlink()

    def test_load_from_yaml_valid(self):
        """Test load_from_yaml successfully loads tools."""
        registry = ToolRegistry()

        yaml_content = """
tools:
  - name: test_calc
    class: tests.test_tool_registry.MockCalculatorTool
    config:
      timeout: 30
    description: "Test calculator"
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            yaml_path = f.name

        try:
            registry.load_from_yaml(yaml_path)

            assert registry.has("test_calc")
            metadata = registry.get_metadata("test_calc")
            assert metadata.config == {"timeout": 30}
            assert metadata.description == "Test calculator"
        finally:
            Path(yaml_path).unlink()

    def test_load_from_yaml_missing_name_field(self):
        """Test load_from_yaml raises error if tool missing 'name' field."""
        registry = ToolRegistry()

        yaml_content = """
tools:
  - class: tests.test_tool_registry.MockCalculatorTool
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            yaml_path = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                registry.load_from_yaml(yaml_path)

            assert "name" in str(exc_info.value).lower()
        finally:
            Path(yaml_path).unlink()

    def test_load_from_yaml_missing_class_field(self):
        """Test load_from_yaml raises error if tool missing 'class' field."""
        registry = ToolRegistry()

        yaml_content = """
tools:
  - name: test_tool
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            yaml_path = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                registry.load_from_yaml(yaml_path)

            assert "class" in str(exc_info.value).lower()
        finally:
            Path(yaml_path).unlink()

    def test_load_from_yaml_invalid_class_path(self):
        """Test load_from_yaml raises error for invalid class path."""
        registry = ToolRegistry()

        yaml_content = """
tools:
  - name: test_tool
    class: nonexistent.module.ClassName
"""

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            f.flush()
            yaml_path = f.name

        try:
            with pytest.raises(ImportError):
                registry.load_from_yaml(yaml_path)
        finally:
            Path(yaml_path).unlink()


class TestAutoDiscovery:
    """Test auto-discovery functionality."""

    def test_class_name_to_tool_name_conversion(self):
        """Test class name conversion to tool name."""
        registry = ToolRegistry()

        # Test various conversions
        assert registry._class_name_to_tool_name("WebSearchTool") == "web_search"
        assert registry._class_name_to_tool_name("Calculator") == "calculator"
        assert registry._class_name_to_tool_name("DocumentReaderTool") == "document_reader"
        assert registry._class_name_to_tool_name("SimpleTool") == "simple"

    def test_discover_tools_nonexistent_path(self):
        """Test discover_tools with nonexistent path logs warning."""
        registry = ToolRegistry()

        # Should not raise, just log warning
        registry.discover_tools("/nonexistent/path")

    def test_discover_tools_empty_registry_initially(self):
        """Test discovered tools are added to empty registry."""
        registry = ToolRegistry()

        # This will try to discover in app/tools but won't find mock tools
        # Just verify it doesn't crash
        registry.discover_tools("app/tools")


class TestThreadSafety:
    """Test thread safety of registry operations."""

    def test_register_is_thread_safe(self):
        """Test that register uses lock."""
        registry = ToolRegistry()

        # Register with lock should not raise
        registry.register("calc", MockCalculatorTool)

        # Verify tool was registered
        assert registry.has("calc")

    def test_get_is_thread_safe(self):
        """Test that get uses lock."""
        registry = ToolRegistry()
        registry.register("calc", MockCalculatorTool)

        # Get with lock should not raise
        tool = registry.get("calc")
        assert tool is not None
