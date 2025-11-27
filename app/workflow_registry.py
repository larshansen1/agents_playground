"""Workflow registry for managing declarative workflows."""

from collections.abc import Iterator
from pathlib import Path

from app.logging_config import get_logger
from app.workflow_definition import WorkflowDefinition

logger = get_logger(__name__)


class WorkflowRegistry:
    """Registry for declarative workflow definitions."""

    def __init__(self):
        """Initialize empty registry."""
        self._workflows: dict[str, WorkflowDefinition] = {}

    def register(self, definition: WorkflowDefinition) -> None:
        """
        Register a workflow definition.

        Args:
            definition: WorkflowDefinition to register

        Raises:
            ValueError: If workflow with same name already registered
        """
        if definition.name in self._workflows:
            msg = f"Workflow '{definition.name}' is already registered"
            raise ValueError(msg)

        self._workflows[definition.name] = definition
        logger.info("workflow_registered", workflow_name=definition.name)

    def get(self, name: str) -> WorkflowDefinition:
        """
        Get workflow definition by name.

        Args:
            name: Workflow name

        Returns:
            WorkflowDefinition instance

        Raises:
            KeyError: If workflow not found
        """
        if name not in self._workflows:
            msg = f"Workflow '{name}' not found in registry"
            raise KeyError(msg)
        return self._workflows[name]

    def has(self, name: str) -> bool:
        """
        Check if workflow is registered.

        Args:
            name: Workflow name

        Returns:
            True if workflow is registered
        """
        return name in self._workflows

    def list_all(self) -> list[str]:
        """
        List all registered workflow names.

        Returns:
            List of workflow names
        """
        return list(self._workflows.keys())

    def load_from_directory(self, directory: str | Path) -> int:
        """
        Load all YAML workflow files from a directory.

        Args:
            directory: Path to directory containing .yaml/.yml files

        Returns:
            Number of workflows loaded

        Raises:
            FileNotFoundError: If directory doesn't exist
        """
        dir_path = Path(directory)
        if not dir_path.exists():
            msg = f"Workflow directory not found: {directory}"
            raise FileNotFoundError(msg)

        if not dir_path.is_dir():
            msg = f"Not a directory: {directory}"
            raise ValueError(msg)

        count = 0
        for yaml_file in self._find_yaml_files(dir_path):
            try:
                definition = WorkflowDefinition.from_yaml(yaml_file)
                self.register(definition)
                count += 1
                logger.info(
                    "workflow_loaded",
                    workflow_name=definition.name,
                    file=str(yaml_file),
                )
            except Exception as e:
                logger.error(
                    "workflow_load_failed",
                    file=str(yaml_file),
                    error=str(e),
                )
                # Continue loading other workflows

        logger.info("workflows_loaded", count=count, directory=str(directory))
        return count

    def _find_yaml_files(self, directory: Path) -> Iterator[Path]:
        """Find all YAML files in directory (non-recursive)."""
        for pattern in ["*.yaml", "*.yml"]:
            yield from directory.glob(pattern)


# Global registry instance
workflow_registry = WorkflowRegistry()
