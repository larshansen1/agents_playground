"""Workflow definition schema for declarative workflows."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml


@dataclass
class WorkflowStep:
    """A single step in a workflow (agent execution)."""

    agent_type: str  # e.g., "research", "assessment"
    name: str | None = None  # Optional friendly name for the step

    def __post_init__(self):
        """Validate step configuration."""
        if not self.agent_type:
            msg = "agent_type is required for WorkflowStep"
            raise ValueError(msg)


@dataclass
class WorkflowDefinition:
    """Declarative workflow definition loaded from YAML."""

    name: str
    description: str
    steps: list[WorkflowStep]
    coordination_type: Literal["sequential", "iterative_refinement"]
    max_iterations: int = 3
    convergence_check: str | None = None  # For iterative_refinement: "assessment_approved"

    def __post_init__(self):
        """Validate workflow definition."""
        if not self.name:
            msg = "Workflow name is required"
            raise ValueError(msg)
        if not self.steps:
            msg = "Workflow must have at least one step"
            raise ValueError(msg)
        if self.coordination_type == "iterative_refinement" and not self.convergence_check:
            msg = "iterative_refinement requires a convergence_check"
            raise ValueError(msg)
        if self.max_iterations < 1:
            msg = "max_iterations must be at least 1"
            raise ValueError(msg)

    @classmethod
    def from_yaml(cls, yaml_path: str | Path) -> "WorkflowDefinition":
        """
        Load workflow definition from YAML file.

        Args:
            yaml_path: Path to YAML file

        Returns:
            WorkflowDefinition instance

        Raises:
            FileNotFoundError: If YAML file doesn't exist
            ValueError: If YAML is invalid or missing required fields
        """
        path = Path(yaml_path)
        if not path.exists():
            msg = f"Workflow file not found: {yaml_path}"
            raise FileNotFoundError(msg)

        with path.open() as f:
            data = yaml.safe_load(f)

        if not isinstance(data, dict):
            msg = f"Invalid YAML format in {yaml_path}: expected dict"
            raise ValueError(msg)

        # Parse steps
        steps_data = data.get("steps", [])
        if not isinstance(steps_data, list):
            msg = "steps must be a list"
            raise ValueError(msg)

        steps = []
        for step_data in steps_data:
            if not isinstance(step_data, dict):
                msg = f"Invalid step format: {step_data}"
                raise ValueError(msg)
            steps.append(
                WorkflowStep(
                    agent_type=step_data.get("agent_type", ""),
                    name=step_data.get("name"),
                )
            )

        # Create WorkflowDefinition
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            steps=steps,
            coordination_type=data.get("coordination_type", "sequential"),
            max_iterations=data.get("max_iterations", 3),
            convergence_check=data.get("convergence_check"),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert workflow definition to dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "steps": [{"agent_type": step.agent_type, "name": step.name} for step in self.steps],
            "coordination_type": self.coordination_type,
            "max_iterations": self.max_iterations,
            "convergence_check": self.convergence_check,
        }
