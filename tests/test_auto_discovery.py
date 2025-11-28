"""Tests for Agent Registry auto-discovery functionality."""

from app.agents.registry import AgentRegistry


def test_discover_agents():
    """Test auto-discovery of agents from filesystem."""
    registry = AgentRegistry()
    discovered = registry.discover_agents("app/agents")

    # Should find ResearchAgent and AssessmentAgent
    assert "research" in discovered
    assert "assessment" in discovered
    assert registry.has("research")
    assert registry.has("assessment")


def test_discover_with_exclusions():
    """Test discovery with exclusion patterns."""
    registry = AgentRegistry()
    discovered = registry.discover_agents(
        "app/agents", exclude_patterns=["research_*", "base.py", "__*"]
    )

    # research_agent.py should be excluded
    assert "research" not in discovered
    # assessment_agent.py should be included
    assert "assessment" in discovered


def test_discover_returns_list():
    """Test that discover_agents returns list of discovered types."""
    registry = AgentRegistry()
    discovered = registry.discover_agents("app/agents")

    assert isinstance(discovered, list)
    assert len(discovered) > 0
    assert all(isinstance(agent_type, str) for agent_type in discovered)


def test_discover_skips_already_registered():
    """Test that discovery skips already-registered agents."""
    registry = AgentRegistry()

    # Manually register research agent
    from app.agents.research_agent import ResearchAgent  # noqa: PLC0415

    registry.register("research", ResearchAgent)

    # Discover should skip it
    discovered = registry.discover_agents("app/agents")

    # research should not be in discovered list (already registered)
    assert "research" not in discovered
    # But assessment should be discovered
    assert "assessment" in discovered


def test_discover_nonexistent_path():
    """Test discovery with non-existent path."""
    registry = AgentRegistry()
    discovered = registry.discover_agents("nonexistent/path")

    # Should return empty list without crashing
    assert discovered == []


def test_discover_default_exclusions():
    """Test that default exclusions work (base.py, __*)."""
    registry = AgentRegistry()
    discovered = registry.discover_agents("app/agents")

    # Should not include 'base' (from base.py)
    assert "base" not in discovered
    # Should not include __init__ or __pycache__
    all_types = registry.list_all()
    assert not any(t.startswith("__") for t in all_types)


def test_combined_yaml_and_discovery(tmp_path):
    """Test using YAML loading and auto-discovery together."""
    # Create a YAML config
    yaml_content = """
agents:
  - name: yaml_agent
    class: app.agents.research_agent.ResearchAgent
    description: "From YAML"
"""
    yaml_file = tmp_path / "agents.yaml"
    yaml_file.write_text(yaml_content)

    registry = AgentRegistry()

    # Load from YAML
    registry.load_from_yaml(yaml_file)
    assert registry.has("yaml_agent")

    # Auto-discover (research should be skipped due to YAML registration)
    registry.discover_agents("app/agents")

    # assessment should be discovered
    assert registry.has("assessment")

    # All three methods should coexist
    from app.agents.assessment_agent import AssessmentAgent  # noqa: PLC0415

    registry.register("manual", AssessmentAgent)

    assert registry.has("yaml_agent")  # from YAML
    assert registry.has("assessment")  # from discovery
    assert registry.has("manual")  # from programmatic


def test_discover_extracts_docstring():
    """Test that discovery extracts class docstring as description."""
    registry = AgentRegistry()
    registry.discover_agents("app/agents")

    metadata = registry.get_metadata("research")
    # ResearchAgent has a docstring
    assert metadata.description
    assert len(metadata.description) > 0
