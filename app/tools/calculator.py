"""Calculator tool for safe mathematical expression evaluation."""

import ast
import operator
from typing import Any

from app.tools.base import Tool


class CalculatorTool(Tool):
    """
    Safe mathematical expression evaluator.

    Supports basic arithmetic operations: +, -, *, /, **, ().
    Prevents unsafe operations like imports, exec, file access, etc.
    """

    # Allowed operators
    _OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def __init__(self):
        super().__init__(
            tool_name="calculator",
            description="Perform safe mathematical calculations with +, -, *, /, ** operators",
        )

    def get_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '2 + 2 * 3')",
                }
            },
            "required": ["expression"],
        }

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """
        Execute calculator with safe expression evaluation.

        Args:
            **kwargs: Must contain 'expression' key with math expression string

        Returns:
            dict: Standard result format with calculated value
        """
        # Validate parameters
        self.validate_params(**kwargs)

        expression = kwargs["expression"]

        try:
            # Parse expression to AST
            tree = ast.parse(expression, mode="eval")

            # Evaluate safely
            result = self._eval_node(tree.body)

            return {
                "success": True,
                "result": result,
                "error": None,
                "metadata": {"expression": expression},
            }

        except ZeroDivisionError:
            return {
                "success": False,
                "result": None,
                "error": "Division by zero",
                "metadata": {"expression": expression},
            }

        except (SyntaxError, ValueError) as e:
            return {
                "success": False,
                "result": None,
                "error": f"Invalid expression: {e}",
                "metadata": {"expression": expression},
            }

        except Exception as e:
            return {
                "success": False,
                "result": None,
                "error": f"Calculation error: {e}",
                "metadata": {"expression": expression},
            }

    def _eval_node(self, node: ast.AST) -> float | int:
        """
        Recursively evaluate AST node safely.

        Args:
            node: AST node to evaluate

        Returns:
            float | int: Calculated result

        Raises:
            ValueError: If node type is not allowed
        """
        if isinstance(node, ast.Num):  # Number (Python < 3.8)
            # ast.Num.n can be complex, but we only support int/float
            if isinstance(node.n, int | float):
                return node.n
            msg = f"Unsupported number type: {type(node.n)}"
            raise ValueError(msg)

        if isinstance(node, ast.Constant):  # Number (Python >= 3.8)
            if isinstance(node.value, int | float):
                return node.value
            msg = f"Unsupported constant type: {type(node.value)}"
            raise ValueError(msg)

        if isinstance(node, ast.BinOp):  # Binary operation
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op_type = type(node.op)

            if op_type not in self._OPERATORS:
                msg = f"Unsupported operator: {op_type.__name__}"
                raise ValueError(msg)

            result = self._OPERATORS[op_type](left, right)  # type: ignore[operator]
            return float(result) if isinstance(result, float) else int(result)

        if isinstance(node, ast.UnaryOp):  # Unary operation
            operand = self._eval_node(node.operand)
            op_type = type(node.op)  # type: ignore[assignment]

            if op_type not in self._OPERATORS:
                msg = f"Unsupported unary operator: {op_type.__name__}"
                raise ValueError(msg)

            result = self._OPERATORS[op_type](operand)  # type: ignore[operator]
            return float(result) if isinstance(result, float) else int(result)

        msg = f"Unsupported node type: {type(node).__name__}"
        raise ValueError(msg)
