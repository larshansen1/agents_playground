"""Tests for Agent Registry YAML loading functionality."""

from pathlib import Path

import pytest

from app.agents.assessment_agent import AssessmentAgent
from app.agents.registry import AgentRegistry


def test_load_valid_yaml(tmp_path):
    """Test loading valid YAML configuration."""
    yaml_content = """
agents:
  - name: test_research
    class: app.agents.research_agent.ResearchAgent
    tools:
      - web_search
    description: "Test research agent"
"""
    yaml_file = tmp_path / "agents.yaml"
    yaml_file.write_text(yaml_content)

    registry = AgentRegistry()
    registry.load_from_yaml(yaml_file)

    assert registry.has("test_research")
    metadata = registry.get_metadata("test_research")
    assert "web_search" in metadata.tools
    assert metadata.description == "Test research agent"


def test_load_yaml_with_config(tmp_path):
    """Test loading YAML with agent configuration."""
    yaml_content = """
agents:
  - name: configured_agent
    class: app.agents.research_agent.ResearchAgent
    config:
      model: gpt-4-turbo
      temperature: 0.7
    tools:
      - web_search
      - document_reader
"""
    yaml_file = tmp_path / "agents.yaml"
    yaml_file.write_text(yaml_content)

    registry = AgentRegistry()
    registry.load_from_yaml(yaml_file)

    metadata = registry.get_metadata("configured_agent")
    assert metadata.config == {"model": "gpt-4-turbo", "temperature": 0.7}
    assert len(metadata.tools) == 2


def test_load_yaml_multiple_agents(tmp_path):
    """Test loading multiple agents from YAML."""
    yaml_content = """
agents:
  - name: research
    class: app.agents.research_agent.ResearchAgent
  - name: assessment
    class: app.agents.assessment_agent.AssessmentAgent
"""
    yaml_file = tmp_path / "agents.yaml"
    yaml_file.write_text(yaml_content)

    registry = AgentRegistry()
    registry.load_from_yaml(yaml_file)

    assert registry.has("research")
    assert registry.has("assessment")
    assert len(registry.list_all()) == 2


def test_load_yaml_missing_file():
    """Test error handling for missing YAML file."""
    registry = AgentRegistry()

    with pytest.raises(FileNotFoundError, match="YAML file not found"):
        registry.load_from_yaml("nonexistent.yaml")


def test_load_yaml_invalid_syntax(tmp_path):
    """Test error handling for invalid YAML syntax."""
    yaml_file = tmp_path / "bad.yaml"
    yaml_file.write_text("not: valid: yaml: [unclosed")

    registry = AgentRegistry()

    with pytest.raises(ValueError, match="Invalid YAML syntax"):
        registry.load_from_yaml(yaml_file)


def test_load_yaml_missing_agents_key(tmp_path):
    """Test error for YAML missing 'agents' key."""
    yaml_file = tmp_path / "no_agents.yaml"
    yaml_file.write_text("other_key: value")

    registry = AgentRegistry()

    with pytest.raises(ValueError, match="must contain 'agents' key"):
        registry.load_from_yaml(yaml_file)


def test_load_yaml_missing_name_field(tmp_path):
    """Test error for agent missing 'name' field."""
    yaml_content = """
agents:
  - class: app.agents.research_agent.ResearchAgent
"""
    yaml_file = tmp_path / "missing_name.yaml"
    yaml_file.write_text(yaml_content)

    registry = AgentRegistry()

    with pytest.raises(ValueError, match="missing required 'name' field"):
        registry.load_from_yaml(yaml_file)


def test_load_yaml_missing_class_field(tmp_path):
    """Test error for agent missing 'class' field."""
    yaml_content = """
agents:
  - name: no_class_agent
"""
    yaml_file = tmp_path / "missing_class.yaml"
    yaml_file.write_text(yaml_content)

    registry = AgentRegistry()

    with pytest.raises(ValueError, match="missing required 'class' field"):
        registry.load_from_yaml(yaml_file)


def test_load_yaml_invalid_class_path(tmp_path):
    """Test error for invalid class path."""
    yaml_content = """
agents:
  - name: bad_class
    class: InvalidClassName
"""
    yaml_file = tmp_path / "bad_class.yaml"
    yaml_file.write_text(yaml_content)

    registry = AgentRegistry()

    with pytest.raises(ValueError, match="must be fully qualified"):
        registry.load_from_yaml(yaml_file)


def test_load_yaml_nonexistent_module(tmp_path):
    """Test error for non-existent module."""
    yaml_content = """
agents:
  - name: bad_module
    class: nonexistent.module.ClassName
"""
    yaml_file = tmp_path / "bad_module.yaml"
    yaml_file.write_text(yaml_content)

    registry = AgentRegistry()

    with pytest.raises(ImportError, match="Cannot import module"):
        registry.load_from_yaml(yaml_file)


def test_load_yaml_nonexistent_class(tmp_path):
    """Test error for non-existent class in valid module."""
    yaml_content = """
agents:
  - name: bad_class_name
    class: app.agents.research_agent.NonExistentClass
"""
    yaml_file = tmp_path / "bad_class_name.yaml"
    yaml_file.write_text(yaml_content)

    registry = AgentRegistry()

    with pytest.raises(ImportError, match=r"Class .* not found"):
        registry.load_from_yaml(yaml_file)


def test_load_yaml_with_defaults(tmp_path):
    """Test loading YAML with default values for optional fields."""
    yaml_content = """
agents:
  - name: minimal_agent
    class: app.agents.research_agent.ResearchAgent
"""
    yaml_file = tmp_path / "minimal.yaml"
    yaml_file.write_text(yaml_content)

    registry = AgentRegistry()
    registry.load_from_yaml(yaml_file)

    metadata = registry.get_metadata("minimal_agent")
    assert metadata.config == {}
    assert metadata.tools == []
    assert metadata.description == ""


def test_yaml_and_programmatic_registration(tmp_path):
    """Test that YAML loading and programmatic registration can coexist."""
    yaml_content = """
agents:
  - name: yaml_agent
    class: app.agents.research_agent.ResearchAgent
"""
    yaml_file = tmp_path / "agents.yaml"
    yaml_file.write_text(yaml_content)

    registry = AgentRegistry()

    # Load from YAML
    registry.load_from_yaml(yaml_file)

    # Register programmatically
    registry.register("manual_agent", AssessmentAgent)

    # Both should exist
    assert registry.has("yaml_agent")
    assert registry.has("manual_agent")
    assert len(registry.list_all()) == 2


def test_load_production_config():
    """Test loading the actual production config/agents.yaml file."""
    config_file = Path("config/agents.yaml")

    if not config_file.exists():
        pytest.skip("Production config file not found")

    registry = AgentRegistry()
    registry.load_from_yaml(config_file)

    # Should have loaded research and assessment agents
    assert registry.has("research")
    assert registry.has("assessment")
