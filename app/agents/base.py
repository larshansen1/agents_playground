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

    def __init__(self, agent_type: str):
        """
        Initialize the agent.

        Args:
            agent_type: Unique identifier for this agent type
        """
        self.agent_type = agent_type

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
