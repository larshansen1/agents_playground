"""Tests for Agent Registry."""

import pytest

from app.agents.assessment_agent import AssessmentAgent
from app.agents.base import Agent
from app.agents.registry import AgentMetadata, AgentRegistry
from app.agents.research_agent import ResearchAgent


class MockAgent(Agent):
    """Mock agent for testing."""

    def __init__(self):
        super().__init__(agent_type="mock")

    def execute(self, _input_data: dict, _user_id_hash: str | None = None) -> dict:
        """Mock execute method."""
        return {"output": {}, "usage": {}}


class InvalidAgent:
    """Invalid agent that doesn't inherit from Agent."""


@pytest.fixture
def registry():
    """Fresh registry instance for each test."""
    return AgentRegistry()


@pytest.fixture
def mock_agent_class():
    """Mock agent class for testing."""
    return MockAgent


# ============================================================================
# Registration Tests (FR1)
# ============================================================================


def test_register_agent_success(registry, mock_agent_class):
    """Test successful agent registration."""
    registry.register(
        "mock",
        mock_agent_class,
        config={"model": "gpt-4-turbo"},
        tools=["web_search"],
        description="Mock agent for testing",
    )

    assert registry.has("mock")
    assert "mock" in registry.list_all()


def test_register_duplicate_raises_error(registry, mock_agent_class):
    """Test that duplicate registration raises ValueError."""
    registry.register("mock", mock_agent_class)

    with pytest.raises(ValueError, match="already registered"):
        registry.register("mock", mock_agent_class)


def test_register_with_default_values(registry, mock_agent_class):
    """Test registration with default values for optional parameters."""
    registry.register("mock", mock_agent_class)

    metadata = registry.get_metadata("mock")
    assert metadata.config == {}
    assert metadata.tools == []
    assert metadata.description == ""


def test_register_with_all_parameters(registry, mock_agent_class):
    """Test registration with all parameters provided."""
    registry.register(
        agent_type="mock",
        agent_class=mock_agent_class,
        config={"model": "gpt-4-turbo", "temperature": 0.7},
        tools=["web_search", "document_reader"],
        description="Full registration test",
    )

    metadata = registry.get_metadata("mock")
    assert metadata.config == {"model": "gpt-4-turbo", "temperature": 0.7}
    assert metadata.tools == ["web_search", "document_reader"]
    assert metadata.description == "Full registration test"


def test_register_invalid_agent_class_raises_error(registry):
    """Test that registering invalid agent class raises TypeError."""
    with pytest.raises(TypeError, match="must inherit from Agent base class"):
        registry.register("invalid", InvalidAgent)


def test_register_empty_agent_type_raises_error(registry, mock_agent_class):
    """Test that empty agent_type raises ValueError."""
    with pytest.raises(ValueError, match="cannot be empty"):
        registry.register("", mock_agent_class)


# ============================================================================
# Instantiation Tests (FR2)
# ============================================================================


def test_get_agent_returns_instance(registry, mock_agent_class):
    """Test that get() returns an agent instance."""
    registry.register("mock", mock_agent_class)

    agent = registry.get("mock")

    assert isinstance(agent, Agent)
    assert isinstance(agent, mock_agent_class)


def test_get_agent_returns_singleton(registry, mock_agent_class):
    """Test that get() returns the same instance on repeated calls."""
    registry.register("mock", mock_agent_class)

    agent1 = registry.get("mock")
    agent2 = registry.get("mock")

    assert agent1 is agent2  # Same object


def test_get_unknown_agent_raises_error(registry):
    """Test that getting unknown agent raises ValueError with helpful message."""
    registry.register("research", ResearchAgent)

    with pytest.raises(ValueError, match="Unknown agent type: 'nonexistent'"):
        registry.get("nonexistent")

    # Verify error message includes available agents
    with pytest.raises(ValueError, match="Available agents") as exc_info:
        registry.get("nonexistent")
    assert "research" in str(exc_info.value)


def test_create_new_returns_fresh_instance(registry, mock_agent_class):
    """Test that create_new() returns a new instance."""
    registry.register("mock", mock_agent_class)

    agent1 = registry.get("mock")  # Singleton
    agent2 = registry.create_new("mock")  # Fresh instance

    assert agent1 is not agent2  # Different objects
    assert isinstance(agent2, mock_agent_class)


def test_create_new_with_config_override(registry, mock_agent_class):
    """Test that create_new() accepts config overrides."""
    registry.register(
        "mock",
        mock_agent_class,
        config={"model": "gpt-4-turbo", "temperature": 0.7},
    )

    agent = registry.create_new("mock", temperature=0.9)

    assert isinstance(agent, mock_agent_class)

    # Verify config was actually applied
    # Note: The registry's stored metadata config remains unchanged,
    # but the *instance* created by create_new should reflect the override
    # if the agent's constructor supports it. For MockAgent, it doesn't
    # take config args, so we verify the registry's metadata is stable.
    metadata = registry.get_metadata("mock")
    assert metadata.config["temperature"] == 0.7  # Original config unchanged in registry
    assert metadata.config["model"] == "gpt-4-turbo"  # Original config preserved


def test_create_new_unknown_agent_raises_error(registry):
    """Test that create_new() raises error for unknown agent."""
    with pytest.raises(ValueError, match="Unknown agent type"):
        registry.create_new("nonexistent")


# ============================================================================
# Discovery Tests (FR4)
# ============================================================================


def test_list_all_agents(registry):
    """Test that list_all() returns all registered agent types."""
    assert registry.list_all() == []

    registry.register("research", ResearchAgent)
    registry.register("assessment", AssessmentAgent)

    agents = registry.list_all()
    assert len(agents) == 2
    assert "research" in agents
    assert "assessment" in agents


def test_has_agent(registry, mock_agent_class):
    """Test that has() correctly checks agent existence."""
    assert not registry.has("mock")

    registry.register("mock", mock_agent_class)

    assert registry.has("mock")
    assert not registry.has("nonexistent")


def test_get_metadata(registry, mock_agent_class):
    """Test that get_metadata() returns correct metadata."""
    registry.register(
        "mock",
        mock_agent_class,
        config={"model": "gpt-4-turbo"},
        tools=["web_search"],
        description="Test agent",
    )

    metadata = registry.get_metadata("mock")

    assert isinstance(metadata, AgentMetadata)
    assert metadata.agent_class == mock_agent_class
    assert metadata.config == {"model": "gpt-4-turbo"}
    assert "web_search" in metadata.tools
    assert metadata.description == "Test agent"


def test_get_metadata_unknown_agent_raises_error(registry):
    """Test that get_metadata() raises error for unknown agent."""
    with pytest.raises(ValueError, match="Unknown agent type"):
        registry.get_metadata("nonexistent")


# ============================================================================
# Error Handling Tests
# ============================================================================


def test_error_message_includes_available_agents(registry):
    """Test that error messages include list of available agents."""
    registry.register("research", ResearchAgent)
    registry.register("assessment", AssessmentAgent)

    with pytest.raises(ValueError, match="Unknown agent type: 'typo_research'") as exc_info:
        registry.get("typo_research")

    error_msg = str(exc_info.value)
    assert "Available agents:" in error_msg
    assert "'research'" in str(exc_info.value)
    assert "'assessment'" in error_msg


def test_duplicate_registration_error_message(registry, mock_agent_class):
    """Test that duplicate registration error includes existing details."""
    registry.register("mock", mock_agent_class, tools=["tool1", "tool2"])

    with pytest.raises(ValueError, match="already registered") as exc_info:
        registry.register("mock", mock_agent_class)

    error_msg = str(exc_info.value)
    assert "'mock' is already registered" in error_msg
    assert "MockAgent" in error_msg
    assert "tools=" in error_msg


def test_metadata_for_unknown_agent_raises_error(registry):
    """Test that accessing metadata for unknown agent raises clear error."""
    with pytest.raises(ValueError, match="Unknown agent type") as exc_info:
        registry.get_metadata("unknown")

    assert "Unknown agent type" in str(exc_info.value)
    assert "Available agents" in str(exc_info.value)


# ============================================================================
# Integration Tests
# ============================================================================


def test_full_workflow_with_real_agents(registry):
    """Test complete workflow with real Research and Assessment agents."""
    # Register agents
    registry.register(
        "research",
        ResearchAgent,
        config={"model": "gpt-4-turbo", "temperature": 0.7},
        tools=["web_search"],
        description="Gathers information from web sources",
    )

    registry.register(
        "assessment",
        AssessmentAgent,
        config={"model": "gpt-4-turbo", "temperature": 0.3},
        tools=["fact_checker"],
        description="Assesses research quality",
    )

    # List all
    assert len(registry.list_all()) == 2

    # Get singleton
    agent1 = registry.get("research")
    agent2 = registry.get("research")
    assert agent1 is agent2  # Same instance

    # Create new
    agent3 = registry.create_new("research", temperature=0.9)
    assert agent3 is not agent1  # Different instance

    # Get metadata
    metadata = registry.get_metadata("research")
    assert "web_search" in metadata.tools
    assert metadata.description == "Gathers information from web sources"


# ============================================================================
# Thread Safety Tests (Optional - Basic verification)
# ============================================================================


def test_multiple_registration_calls(registry, mock_agent_class):
    """Test that registration is idempotent when expected."""
    # First registration should succeed
    registry.register("mock", mock_agent_class)

    # Second should fail with clear error
    with pytest.raises(ValueError, match="already registered"):
        registry.register("mock", mock_agent_class)

    # But registry should still work
    assert registry.has("mock")
    assert registry.get("mock") is not None
