"""Agent registry for multi-agent workflows."""

from app.agents.assessment_agent import AssessmentAgent
from app.agents.base import Agent
from app.agents.research_agent import ResearchAgent

# Registry mapping agent types to agent classes
AGENT_REGISTRY: dict[str, type[Agent]] = {
    "research": ResearchAgent,
    "assessment": AssessmentAgent,
}


def get_agent(agent_type: str) -> Agent:
    """
    Get an agent instance by type.

    Args:
        agent_type: Type of agent to instantiate

    Returns:
        Agent instance

    Raises:
        ValueError: If agent type is not registered
    """
    agent_class = AGENT_REGISTRY.get(agent_type)
    if not agent_class:
        msg = f"Unknown agent type: {agent_type}"
        raise ValueError(msg)
    return agent_class()  # type: ignore[call-arg]
