"""Base tool interface for agent capabilities."""

from abc import ABC, abstractmethod
from typing import Any

import jsonschema
import structlog

logger = structlog.get_logger()


class Tool(ABC):
    """
    Base abstract class for all tools.

    Tools provide external capabilities to agents (web search, calculations, etc.).
    Each tool has a name, description, and implements the execute method with
    parameter validation via JSON Schema.

    Example:
        >>> class CalculatorTool(Tool):
        ...     def __init__(self):
        ...         super().__init__(
        ...             tool_name="calculator",
        ...             description="Perform mathematical calculations"
        ...         )
        ...
        ...     def get_schema(self) -> dict:
        ...         return {
        ...             "type": "object",
        ...             "properties": {
        ...                 "expression": {"type": "string"}
        ...             },
        ...             "required": ["expression"]
        ...         }
        ...
        ...     def execute(self, **kwargs) -> dict:
        ...         self.validate_params(**kwargs)
        ...         result = eval(kwargs["expression"])  # Simplified example
        ...         return {
        ...             "success": True,
        ...             "result": result,
        ...             "error": None,
        ...             "metadata": {}
        ...         }
    """

    def __init__(self, tool_name: str, description: str = ""):
        """
        Initialize the tool.

        Args:
            tool_name: Unique identifier for this tool (e.g., "web_search")
            description: Human-readable description of what the tool does
        """
        self.tool_name = tool_name
        self.description = description

    @abstractmethod
    def get_schema(self) -> dict[str, Any]:
        """
        Return JSON Schema for tool parameters.

        The schema describes what parameters the tool accepts, their types,
        and which are required. Used for validation and documentation.

        Returns:
            dict: JSON Schema object with type, properties, and required fields

        Example:
            >>> {
            ...     "type": "object",
            ...     "properties": {
            ...         "query": {
            ...             "type": "string",
            ...             "description": "Search query"
            ...         },
            ...         "max_results": {
            ...             "type": "integer",
            ...             "default": 5,
            ...             "minimum": 1,
            ...             "maximum": 20
            ...         }
            ...     },
            ...     "required": ["query"]
            ... }
        """

    @abstractmethod
    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """
        Execute the tool's operation.

        Args:
            **kwargs: Tool-specific parameters (validated against schema)

        Returns:
            dict: Standard result format with keys:
                - success (bool): Whether execution succeeded
                - result (Any): Tool output data
                - error (str | None): Error message if failed
                - metadata (dict | None): Optional metadata about execution

        Example:
            >>> result = tool.execute(query="Python tutorials")
            >>> {
            ...     "success": True,
            ...     "result": {"results": [...]},
            ...     "error": None,
            ...     "metadata": {"api": "brave", "took_ms": 234}
            ... }

        Raises:
            ValueError: If parameter validation fails
            Exception: Tool-specific errors (should be caught and returned in error field)
        """

    def validate_params(self, **kwargs: Any) -> None:
        """
        Validate parameters against the tool's JSON Schema.

        This method should be called at the start of execute() to ensure
        all parameters are valid before processing.

        Args:
            **kwargs: Parameters to validate

        Raises:
            ValueError: If parameters don't match schema, with helpful error message

        Example:
            >>> tool.validate_params(query="test", max_results=5)  # OK
            >>> tool.validate_params(max_results=5)  # Raises ValueError: 'query' is required
        """
        schema = self.get_schema()

        try:
            jsonschema.validate(instance=kwargs, schema=schema)
            logger.debug(
                "Tool parameters validated",
                tool_name=self.tool_name,
                params=list(kwargs.keys()),
            )
        except jsonschema.ValidationError as e:
            error_msg = self._format_validation_error(e, kwargs)
            logger.warning(
                "Tool parameter validation failed",
                tool_name=self.tool_name,
                error=error_msg,
                params=kwargs,
            )
            raise ValueError(error_msg) from e

    def _format_validation_error(
        self, error: jsonschema.ValidationError, params: dict[str, Any]
    ) -> str:
        """
        Format validation error into helpful message.

        Args:
            error: JSON Schema validation error
            params: Parameters that failed validation

        Returns:
            str: Formatted error message with context
        """
        schema = self.get_schema()

        # Extract error details
        path = ".".join(str(p) for p in error.path) if error.path else "root"
        message = error.message

        # Build helpful error message
        parts = [f"Invalid parameters for tool '{self.tool_name}':"]
        parts.append(f"  Error at '{path}': {message}")

        # Add required fields if missing
        if "required" in schema:
            required = schema["required"]
            missing = [f for f in required if f not in params]
            if missing:
                parts.append(f"  Required fields: {', '.join(required)}")
                parts.append(f"  Missing fields: {', '.join(missing)}")

        # Add parameter types
        if "properties" in schema:
            parts.append("  Expected parameter types:")
            for prop, spec in schema["properties"].items():
                prop_type = spec.get("type", "any")
                required_marker = (
                    "(required)" if prop in schema.get("required", []) else "(optional)"
                )
                parts.append(f"    - {prop}: {prop_type} {required_marker}")

        return "\n".join(parts)
