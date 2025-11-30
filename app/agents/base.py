"""Base agent interface for multi-agent workflows."""

import json
import re
from abc import ABC, abstractmethod
from typing import Any


def extract_json(text: str) -> dict[str, Any]:
    """
    Extract JSON from text, handling markdown code blocks.
    """
    if not text:
        return {}

    # Handle SSE-like response (data: prefix)
    if text.strip().startswith("data:"):
        # Remove 'data: ' prefix and any trailing newlines/whitespace
        text = text.strip().replace("data: ", "", 1).strip()

    # Try to find JSON within markdown code blocks
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if match:
        json_str = match.group(1)
    else:
        # If no code blocks, try to find the first '{' and last '}'
        match = re.search(r"(\{.*\})", text, re.DOTALL)
        json_str = match.group(1) if match else text

    try:
        result: dict[str, Any] = json.loads(json_str)
        return result
    except json.JSONDecodeError:
        # If parsing fails, raise error to be handled by caller
        raise


class Agent(ABC):
    """
    Base abstract class for all agents.

    Agents are responsible for executing specific tasks within a workflow.
    Each agent has a type identifier and implements the execute method.
    """

    def __init__(self, agent_type: str, tools: list[str] | None = None):
        """
        Initialize the agent.

        Args:
            agent_type: Unique identifier for this agent type
            tools: Optional list of tool names this agent can use
        """
        self.agent_type = agent_type
        self.tools = tools or []
        self._tool_instances: dict[str, Any] = {}

    def _get_tool(self, tool_name: str) -> Any:
        """
        Get tool instance (lazy loading).

        Args:
            tool_name: Name of the tool to retrieve

        Returns:
            Tool instance

        Raises:
            ValueError: If tool not found in registry
        """
        if tool_name not in self._tool_instances:
            from app.tools.registry_init import tool_registry

            self._tool_instances[tool_name] = tool_registry.get(tool_name)
        return self._tool_instances[tool_name]

    def _execute_tool(self, tool_name: str, **params: Any) -> dict[str, Any]:
        """
        Execute a tool with parameters.

        Args:
            tool_name: Name of the tool to execute
            **params: Tool-specific parameters

        Returns:
            dict: Tool execution result in standard format

        Example:
            >>> result = self._execute_tool("calculator", expression="2 + 2")
            >>> assert result["success"] is True
        """
        tool = self._get_tool(tool_name)
        return tool.execute(**params)  # type: ignore[no-any-return]

    @abstractmethod
    def execute(
        self, input_data: dict[str, Any], user_id_hash: str | None = None
    ) -> dict[str, Any]:
        """
        Execute the agent's task.

        Args:
            input_data: Input data for the agent
            user_id_hash: Optional user ID hash for cost tracking

        Returns:
            Dict with 'output' and 'usage' keys:
            {
                "output": {...},  # Agent's output data
                "usage": {        # Token/cost tracking
                    "model_used": "...",
                    "input_tokens": int,
                    "output_tokens": int,
                    "total_cost": float,
                    "generation_id": "..."
                }
            }
        """
