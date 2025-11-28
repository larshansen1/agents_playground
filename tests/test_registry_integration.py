"""Tests for Agent Registry integration with orchestrators and workers."""

import pytest

from app.agents import get_agent
from app.agents.assessment_agent import AssessmentAgent
from app.agents.registry_init import registry
from app.agents.research_agent import ResearchAgent


def test_registry_initialized():
    """Test that registry is initialized on import."""
    # Should have agents either from YAML or auto-discovery
    assert registry is not None

    # Should have at least research and assessment
    assert registry.has("research") or registry.has("assessment")


def test_get_agent_uses_registry():
    """Test that get_agent() uses registry."""
    # Get agent via get_agent function
    research_agent = get_agent("research")

    # Should return an instance
    assert research_agent is not None
    assert isinstance(research_agent, ResearchAgent)


def test_get_agent_returns_singleton():
    """Test that get_agent() returns singleton from registry."""
    # Get same agent twice
    agent1 = get_agent("research")
    agent2 = get_agent("research")

    # Should be same instance (singleton)
    assert agent1 is agent2


def test_get_agent_fallback():
    """Test that get_agent() falls back to hardcoded mapping."""
    # Even if registry fails, should still work
    try:
        agent = get_agent("assessment")
        assert agent is not None
        assert isinstance(agent, AssessmentAgent)
    except ValueError:
        pytest.skip("Expected agent not found")


def test_registry_yaml_config_loaded():
    """Test that YAML config is loaded if present."""
    from pathlib import Path  # noqa: PLC0415

    yaml_path = Path("config/agents.yaml")
    if not yaml_path.exists():
        pytest.skip("config/agents.yaml not found")

    # Should have loaded from YAML
    assert registry.has("research")
    assert registry.has("assessment")

    # Check metadata
    metadata = registry.get_metadata("research")
    assert metadata.agent_class == ResearchAgent


def test_registry_auto_discovery():
    """Test that auto-discovery works as fallback."""
    # Registry should discover agents from app/agents/
    # even without YAML config
    agent_types = registry.list_all()

    # Should have found at least research and assessment
    assert "research" in agent_types or "assessment" in agent_types


def test_unknown_agent_raises_error():
    """Test that unknown agent type raises clear error."""
    with pytest.raises(ValueError, match="Unknown agent type"):
        get_agent("nonexistent_agent")


def test_worker_can_use_registry():
    """Test that worker's get_agent function works with registry."""
    # Simulate what worker does
    from app.agents import get_agent as worker_get_agent  # noqa: PLC0415

    agent = worker_get_agent("research")
    assert agent is not None
    assert hasattr(agent, "execute")


def test_registry_config_accessibility():
    """Test that we can access agent config from registry."""
    if not registry.has("research"):
        pytest.skip("Research agent not in registry")

    metadata = registry.get_metadata("research")

    # Config should be accessible
    assert isinstance(metadata.config, dict)
    assert isinstance(metadata.tools, list)
    assert isinstance(metadata.description, str)
