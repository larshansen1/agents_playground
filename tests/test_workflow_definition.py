"""Tests for declarative workflow definitions."""

import tempfile
from pathlib import Path

import pytest

from app.workflow_definition import WorkflowDefinition, WorkflowStep


class TestWorkflowStep:
    """Tests for WorkflowStep dataclass."""

    def test_valid_step(self):
        """Test creating valid workflow step."""
        step = WorkflowStep(agent_type="research", name="conduct_research")
        assert step.agent_type == "research"
        assert step.name == "conduct_research"

    def test_missing_agent_type(self):
        """Test that empty agent_type raises error."""
        with pytest.raises(ValueError, match="agent_type is required"):
            WorkflowStep(agent_type="", name="test")


class TestWorkflowDefinition:
    """Tests for WorkflowDefinition dataclass."""

    def test_valid_definition(self):
        """Test creating valid workflow definition."""
        definition = WorkflowDefinition(
            name="test_workflow",
            description="Test workflow",
            steps=[WorkflowStep(agent_type="research")],
            coordination_type="sequential",
        )
        assert definition.name == "test_workflow"
        assert len(definition.steps) == 1
        assert definition.coordination_type == "sequential"

    def test_missing_name(self):
        """Test that missing name raises error."""
        with pytest.raises(ValueError, match="name is required"):
            WorkflowDefinition(
                name="",
                description="Test",
                steps=[WorkflowStep(agent_type="research")],
                coordination_type="sequential",
            )

    def test_missing_steps(self):
        """Test that empty steps raises error."""
        with pytest.raises(ValueError, match="at least one step"):
            WorkflowDefinition(
                name="test",
                description="Test",
                steps=[],
                coordination_type="sequential",
            )

    def test_iterative_without_convergence_check(self):
        """Test that iterative_refinement requires convergence_check."""
        with pytest.raises(ValueError, match="requires a convergence_check"):
            WorkflowDefinition(
                name="test",
                description="Test",
                steps=[WorkflowStep(agent_type="research")],
                coordination_type="iterative_refinement",
            )

    def test_invalid_max_iterations(self):
        """Test that max_iterations must be at least 1."""
        with pytest.raises(ValueError, match="at least 1"):
            WorkflowDefinition(
                name="test",
                description="Test",
                steps=[WorkflowStep(agent_type="research")],
                coordination_type="sequential",
                max_iterations=0,
            )


class TestYAMLParsing:
    """Tests for YAML parsing functionality."""

    def test_load_valid_yaml(self):
        """Test loading valid YAML workflow."""
        yaml_content = """
name: test_workflow
description: Test workflow
coordination_type: sequential
max_iterations: 2

steps:
  - agent_type: research
    name: do_research
  - agent_type: assessment
    name: assess_quality
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            definition = WorkflowDefinition.from_yaml(temp_path)
            assert definition.name == "test_workflow"
            assert definition.description == "Test workflow"
            assert definition.coordination_type == "sequential"
            assert definition.max_iterations == 2
            assert len(definition.steps) == 2
            assert definition.steps[0].agent_type == "research"
            assert definition.steps[0].name == "do_research"
        finally:
            Path(temp_path).unlink()

    def test_load_iterative_yaml(self):
        """Test loading iterative refinement workflow."""
        yaml_content = """
name: iterative_workflow
description: Iterative test
coordination_type: iterative_refinement
max_iterations: 3
convergence_check: assessment_approved

steps:
  - agent_type: research
  - agent_type: assessment
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            definition = WorkflowDefinition.from_yaml(temp_path)
            assert definition.coordination_type == "iterative_refinement"
            assert definition.convergence_check == "assessment_approved"
            assert definition.max_iterations == 3
        finally:
            Path(temp_path).unlink()

    def test_load_nonexistent_file(self):
        """Test loading non-existent YAML file."""
        with pytest.raises(FileNotFoundError):
            WorkflowDefinition.from_yaml("/nonexistent/file.yaml")

    def test_load_invalid_yaml(self):
        """Test loading invalid YAML format."""
        yaml_content = "just a string, not a dict"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write(yaml_content)
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="Invalid YAML format"):
                WorkflowDefinition.from_yaml(temp_path)
        finally:
            Path(temp_path).unlink()

    def test_to_dict(self):
        """Test converting definition to dictionary."""
        definition = WorkflowDefinition(
            name="test",
            description="Test workflow",
            steps=[
                WorkflowStep(agent_type="research", name="r1"),
                WorkflowStep(agent_type="assessment"),
            ],
            coordination_type="sequential",
            max_iterations=5,
        )

        result = definition.to_dict()
        assert result["name"] == "test"
        assert result["description"] == "Test workflow"
        assert len(result["steps"]) == 2
        assert result["steps"][0]["agent_type"] == "research"
        assert result["steps"][0]["name"] == "r1"
        assert result["coordination_type"] == "sequential"
        assert result["max_iterations"] == 5
