"""Tests for tool base class."""

import pytest

from app.tools.base import Tool


class MockTool(Tool):
    """Mock tool for testing."""

    def __init__(self, tool_name: str = "mock_tool", description: str = "A mock tool"):
        super().__init__(tool_name=tool_name, description=description)

    def get_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "required_param": {"type": "string", "description": "A required parameter"},
                "optional_param": {
                    "type": "integer",
                    "default": 10,
                    "minimum": 1,
                    "maximum": 100,
                },
            },
            "required": ["required_param"],
        }

    def execute(self, **kwargs) -> dict:
        self.validate_params(**kwargs)
        return {
            "success": True,
            "result": {"echo": kwargs},
            "error": None,
            "metadata": {"tool": self.tool_name},
        }


class FailingTool(Tool):
    """Tool that always fails for testing error handling."""

    def __init__(self):
        super().__init__(tool_name="failing_tool", description="Always fails")

    def get_schema(self) -> dict:
        return {"type": "object", "properties": {}, "required": []}

    def execute(self, **kwargs) -> dict:
        return {
            "success": False,
            "result": None,
            "error": "Tool execution failed",
            "metadata": {},
        }


class TestToolBase:
    """Test suite for Tool base class."""

    def test_tool_initialization(self):
        """Test tool can be instantiated with name and description."""
        tool = MockTool(tool_name="test_tool", description="Test description")
        assert tool.tool_name == "test_tool"
        assert tool.description == "Test description"

    def test_tool_schema(self):
        """Test tool returns valid JSON Schema."""
        tool = MockTool()
        schema = tool.get_schema()

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "required" in schema
        assert "required_param" in schema["properties"]
        assert "required_param" in schema["required"]

    def test_validate_params_success(self):
        """Test parameter validation succeeds with valid params."""
        tool = MockTool()

        # Should not raise
        tool.validate_params(required_param="test", optional_param=50)

    def test_validate_params_missing_required(self):
        """Test parameter validation fails when required param is missing."""
        tool = MockTool()

        with pytest.raises(ValueError) as exc_info:
            tool.validate_params(optional_param=50)

        error_msg = str(exc_info.value)
        assert "required_param" in error_msg
        assert "Required fields" in error_msg or "required" in error_msg.lower()

    def test_validate_params_wrong_type(self):
        """Test parameter validation fails when param has wrong type."""
        tool = MockTool()

        with pytest.raises(ValueError) as exc_info:
            tool.validate_params(required_param="test", optional_param="not_an_integer")

        error_msg = str(exc_info.value)
        assert "mock_tool" in error_msg

    def test_validate_params_out_of_range(self):
        """Test parameter validation fails when param is out of range."""
        tool = MockTool()

        with pytest.raises(ValueError) as exc_info:
            tool.validate_params(required_param="test", optional_param=500)

        error_msg = str(exc_info.value)
        assert "mock_tool" in error_msg

    def test_execute_standard_format(self):
        """Test execute returns standard result format."""
        tool = MockTool()
        result = tool.execute(required_param="test")

        # Check all required keys present
        assert "success" in result
        assert "result" in result
        assert "error" in result
        assert "metadata" in result

        # Check types
        assert isinstance(result["success"], bool)
        assert result["error"] is None or isinstance(result["error"], str)
        assert isinstance(result["metadata"], dict) or result["metadata"] is None

    def test_execute_with_valid_params(self):
        """Test execute works with all valid parameters."""
        tool = MockTool()
        result = tool.execute(required_param="test", optional_param=25)

        assert result["success"] is True
        assert result["result"]["echo"]["required_param"] == "test"
        assert result["result"]["echo"]["optional_param"] == 25
        assert result["error"] is None

    def test_execute_error_handling(self):
        """Test tool can return error in standard format."""
        tool = FailingTool()
        result = tool.execute()

        assert result["success"] is False
        assert result["error"] == "Tool execution failed"
        assert result["result"] is None

    def test_validation_error_message_format(self):
        """Test validation error messages are helpful and well-formatted."""
        tool = MockTool()

        with pytest.raises(ValueError) as exc_info:
            tool.validate_params()  # Missing required param

        error_msg = str(exc_info.value)

        # Check error message contains helpful information
        assert tool.tool_name in error_msg
        assert "required_param" in error_msg
        assert "Required" in error_msg or "required" in error_msg

    def test_tool_with_no_required_params(self):
        """Test tool with no required parameters validates correctly."""
        tool = FailingTool()  # Has empty schema with no required fields

        # Should not raise
        tool.validate_params()
        tool.validate_params(any_param="value")  # Extra params should be OK


class TestToolAbstract:
    """Test that Tool is properly abstract."""

    def test_cannot_instantiate_base_tool(self):
        """Test that Tool base class cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Tool(tool_name="test", description="test")  # type: ignore
