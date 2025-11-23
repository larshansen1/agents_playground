"""Orchestrator registry for multi-agent workflows."""

from app.orchestrator.base import Orchestrator
from app.orchestrator.research_assessment import ResearchAssessmentOrchestrator

# Registry mapping workflow types to orchestrator classes
ORCHESTRATOR_REGISTRY: dict[str, type[Orchestrator]] = {
    "research_assessment": ResearchAssessmentOrchestrator,
}


def get_orchestrator(workflow_type: str, **kwargs) -> Orchestrator:
    """
    Get an orchestrator instance by workflow type.

    Args:
        workflow_type: Type of workflow (e.g., 'research_assessment')
        **kwargs: Additional arguments to pass to orchestrator constructor

    Returns:
        Orchestrator instance

    Raises:
        ValueError: If workflow type is not registered
    """
    orchestrator_class = ORCHESTRATOR_REGISTRY.get(workflow_type)
    if not orchestrator_class:
        msg = f"Unknown workflow type: {workflow_type}"
        raise ValueError(msg)
    return orchestrator_class(**kwargs)


def is_workflow_task(task_type: str) -> bool:
    """
    Check if a task type is a workflow task.

    Args:
        task_type: Task type string

    Returns:
        True if this is a workflow task (starts with 'workflow:')
    """
    return task_type.startswith("workflow:")


def extract_workflow_type(task_type: str) -> str:
    """
    Extract workflow type from task type.

    Args:
        task_type: Full task type (e.g., 'workflow:research_assessment')

    Returns:
        Workflow type (e.g., 'research_assessment')

    Raises:
        ValueError: If task_type is not a workflow task
    """
    if not is_workflow_task(task_type):
        msg = f"Not a workflow task: {task_type}"
        raise ValueError(msg)

    return task_type.split(":", 1)[1]
