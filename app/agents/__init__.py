"""Agent registry for multi-agent workflows."""

import logging

from app.agents.assessment_agent import AssessmentAgent
from app.agents.base import Agent
from app.agents.research_agent import ResearchAgent

# Import registry for dynamic agent lookup
try:
    from app.agents.registry_init import registry

    _USE_REGISTRY = True
except ImportError:
    _USE_REGISTRY = False
    logging.warning("Agent Registry not available, using hardcoded agent mapping")


def get_agent(agent_type: str) -> Agent:
    """Get an agent instance by type.

    Strategy:
    1. Try registry lookup (dynamic, configurable)
    2. Fall back to hardcoded mapping (backward compatibility)

    Args:
        agent_type: Type of agent to instantiate

    Returns:
        Agent instance

    Raises:
        ValueError: If agent type is unknown
    """
    # Strategy 1: Try registry (preferred)
    if _USE_REGISTRY:
        try:
            return registry.get(agent_type)
        except ValueError:
            # Registry lookup failed, fall back to hardcoded
            logging.warning(
                f"Agent '{agent_type}' not in registry, falling back to hardcoded mapping"
            )

    # Strategy 2: Hardcoded mapping (backward compatibility)
    agent_map = {
        "research": ResearchAgent,
        "assessment": AssessmentAgent,
    }

    agent_class = agent_map.get(agent_type)
    if agent_class is None:
        msg = f"Unknown agent type: '{agent_type}'. Available: {list(agent_map.keys())}"
        raise ValueError(msg)

    return agent_class()
