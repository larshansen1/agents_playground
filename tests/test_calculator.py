"""Tests for calculator tool."""

import pytest

from app.tools.calculator import CalculatorTool


class TestCalculatorTool:
    """Test suite for CalculatorTool."""

    def test_tool_initialization(self):
        """Test calculator tool initializes correctly."""
        tool = CalculatorTool()
        assert tool.tool_name == "calculator"
        assert (
            "mathematical" in tool.description.lower() or "calculation" in tool.description.lower()
        )

    def test_get_schema(self):
        """Test calculator schema is valid."""
        tool = CalculatorTool()
        schema = tool.get_schema()

        assert schema["type"] == "object"
        assert "expression" in schema["properties"]
        assert "expression" in schema["required"]

    def test_simple_addition(self):
        """Test simple addition."""
        tool = CalculatorTool()
        result = tool.execute(expression="2 + 2")

        assert result["success"] is True
        assert result["result"] == 4
        assert result["error"] is None

    def test_simple_subtraction(self):
        """Test simple subtraction."""
        tool = CalculatorTool()
        result = tool.execute(expression="10 - 3")

        assert result["success"] is True
        assert result["result"] == 7

    def test_simple_multiplication(self):
        """Test simple multiplication."""
        tool = CalculatorTool()
        result = tool.execute(expression="3 * 4")

        assert result["success"] is True
        assert result["result"] == 12

    def test_simple_division(self):
        """Test simple division."""
        tool = CalculatorTool()
        result = tool.execute(expression="15 / 3")

        assert result["success"] is True
        assert result["result"] == 5.0

    def test_power_operation(self):
        """Test power operation."""
        tool = CalculatorTool()
        result = tool.execute(expression="2 ** 3")

        assert result["success"] is True
        assert result["result"] == 8

    def test_complex_expression(self):
        """Test complex expression with order of operations."""
        tool = CalculatorTool()
        result = tool.execute(expression="2 + 2 * 3")

        assert result["success"] is True
        assert result["result"] == 8  # 2 + (2 * 3)

    def test_parentheses(self):
        """Test expression with parentheses."""
        tool = CalculatorTool()
        result = tool.execute(expression="(2 + 2) * 3")

        assert result["success"] is True
        assert result["result"] == 12

    def test_negative_numbers(self):
        """Test negative numbers."""
        tool = CalculatorTool()
        result = tool.execute(expression="-5 + 3")

        assert result["success"] is True
        assert result["result"] == -2

    def test_division_by_zero(self):
        """Test division by zero returns error."""
        tool = CalculatorTool()
        result = tool.execute(expression="5 / 0")

        assert result["success"] is False
        assert "zero" in result["error"].lower()
        assert result["result"] is None

    def test_invalid_syntax(self):
        """Test invalid syntax returns error."""
        tool = CalculatorTool()
        result = tool.execute(expression="2 +")  # Incomplete expression

        assert result["success"] is False
        assert result["error"] is not None
        assert result["result"] is None

    def test_invalid_expression(self):
        """Test invalid expression returns error."""
        tool = CalculatorTool()
        result = tool.execute(expression="import os")

        assert result["success"] is False
        assert result["error"] is not None

    def test_missing_expression_parameter(self):
        """Test missing expression parameter raises ValueError."""
        tool = CalculatorTool()

        with pytest.raises(ValueError):
            tool.execute()

    def test_wrong_parameter_type(self):
        """Test wrong parameter type raises ValueError."""
        tool = CalculatorTool()

        with pytest.raises(ValueError):
            tool.execute(expression=123)  # Should be string

    def test_result_format(self):
        """Test result follows standard format."""
        tool = CalculatorTool()
        result = tool.execute(expression="1 + 1")

        assert "success" in result
        assert "result" in result
        assert "error" in result
        assert "metadata" in result
        assert isinstance(result["metadata"], dict)

    def test_metadata_includes_expression(self):
        """Test metadata includes original expression."""
        tool = CalculatorTool()
        expression = "3 + 5"
        result = tool.execute(expression=expression)

        assert result["metadata"]["expression"] == expression

    def test_float_result(self):
        """Test expressions that result in floats."""
        tool = CalculatorTool()
        result = tool.execute(expression="10 / 4")

        assert result["success"] is True
        assert result["result"] == 2.5
