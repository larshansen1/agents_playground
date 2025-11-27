"""Tests for workflow registry."""

import tempfile
from pathlib import Path

import pytest

from app.workflow_definition import WorkflowDefinition, WorkflowStep
from app.workflow_registry import WorkflowRegistry


class TestWorkflowRegistry:
    """Tests for WorkflowRegistry."""

    def test_register_workflow(self):
        """Test registering a workflow."""
        registry = WorkflowRegistry()
        definition = WorkflowDefinition(
            name="test",
            description="Test",
            steps=[WorkflowStep(agent_type="research")],
            coordination_type="sequential",
        )

        registry.register(definition)
        assert registry.has("test")
        assert registry.get("test") == definition

    def test_register_duplicate(self):
        """Test that registering duplicate raises error."""
        registry = WorkflowRegistry()
        definition = WorkflowDefinition(
            name="test",
            description="Test",
            steps=[WorkflowStep(agent_type="research")],
            coordination_type="sequential",
        )

        registry.register(definition)
        with pytest.raises(ValueError, match="already registered"):
            registry.register(definition)

    def test_get_nonexistent(self):
        """Test getting non-existent workflow raises error."""
        registry = WorkflowRegistry()
        with pytest.raises(KeyError, match="not found"):
            registry.get("nonexistent")

    def test_list_all(self):
        """Test listing all workflows."""
        registry = WorkflowRegistry()
        definition1 = WorkflowDefinition(
            name="workflow1",
            description="Test 1",
            steps=[WorkflowStep(agent_type="research")],
            coordination_type="sequential",
        )
        definition2 = WorkflowDefinition(
            name="workflow2",
            description="Test 2",
            steps=[WorkflowStep(agent_type="assessment")],
            coordination_type="sequential",
        )

        registry.register(definition1)
        registry.register(definition2)

        workflows = registry.list_all()
        assert len(workflows) == 2
        assert "workflow1" in workflows
        assert "workflow2" in workflows

    def test_load_from_directory(self):
        """Test loading workflows from directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create YAML files
            yaml1 = tmpdir_path / "workflow1.yaml"
            yaml1.write_text(
                """
name: workflow1
description: Test 1
coordination_type: sequential

steps:
  - agent_type: research
"""
            )

            yaml2 = tmpdir_path / "workflow2.yml"
            yaml2.write_text(
                """
name: workflow2
description: Test 2
coordination_type: sequential

steps:
  - agent_type: assessment
"""
            )

            # Load from directory
            registry = WorkflowRegistry()
            count = registry.load_from_directory(tmpdir_path)

            assert count == 2
            assert registry.has("workflow1")
            assert registry.has("workflow2")

    def test_load_from_nonexistent_directory(self):
        """Test loading from non-existent directory."""
        registry = WorkflowRegistry()
        with pytest.raises(FileNotFoundError):
            registry.load_from_directory("/nonexistent/directory")

    def test_load_with_invalid_file(self):
        """Test that loading continues even with invalid files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create valid YAML
            valid_yaml = tmpdir_path / "valid.yaml"
            valid_yaml.write_text(
                """
name: valid
description: Valid workflow
coordination_type: sequential

steps:
  - agent_type: research
"""
            )

            # Create invalid YAML
            invalid_yaml = tmpdir_path / "invalid.yaml"
            invalid_yaml.write_text("not: valid: yaml:")

            # Load from directory - should load valid and skip invalid
            registry = WorkflowRegistry()
            count = registry.load_from_directory(tmpdir_path)

            # Should load only the valid one
            assert count == 1
            assert registry.has("valid")
