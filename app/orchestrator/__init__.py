"""Orchestrator registry for multi-agent workflows."""

from pathlib import Path

from app.logging_config import get_logger
from app.orchestrator.base import Orchestrator
from app.orchestrator.declarative_orchestrator import DeclarativeOrchestrator
from app.orchestrator.research_assessment import ResearchAssessmentOrchestrator
from app.workflow_registry import workflow_registry

logger = get_logger(__name__)

# Registry mapping workflow types to coded orchestrator classes
ORCHESTRATOR_REGISTRY: dict[str, type[Orchestrator]] = {
    "research_assessment": ResearchAssessmentOrchestrator,
}


def load_declarative_workflows() -> None:
    """
    Load all declarative workflows from app/workflows directory.

    This is called automatically on module import.
    """
    workflows_dir = Path(__file__).parent.parent / "workflows"

    if workflows_dir.exists():
        try:
            count = workflow_registry.load_from_directory(workflows_dir)
            logger.info(
                "declarative_workflows_loaded",
                count=count,
                directory=str(workflows_dir),
            )
        except Exception as e:
            logger.error(
                "declarative_workflows_load_failed",
                directory=str(workflows_dir),
                error=str(e),
            )
    else:
        logger.debug(
            "workflows_directory_not_found",
            directory=str(workflows_dir),
        )


def get_orchestrator(workflow_type: str, **kwargs) -> Orchestrator:
    """
    Get an orchestrator instance by workflow type.

    Supports both coded orchestrators and declarative workflows.

    Args:
        workflow_type: Type of workflow (e.g., 'research_assessment')
        **kwargs: Additional arguments to pass to orchestrator constructor

    Returns:
        Orchestrator instance

    Raises:
        ValueError: If workflow type is not registered
    """
    # Try coded orchestrators first (backward compatibility)
    if workflow_type in ORCHESTRATOR_REGISTRY:
        orchestrator_class = ORCHESTRATOR_REGISTRY[workflow_type]
        return orchestrator_class(**kwargs)

    # Try declarative workflows
    # Handle 'declarative:' prefix which is stored in workflow state
    lookup_type = workflow_type
    if workflow_type.startswith("declarative:"):
        lookup_type = workflow_type.split(":", 1)[1]

    if workflow_registry.has(lookup_type):
        definition = workflow_registry.get(lookup_type)
        # Note: kwargs are ignored for declarative orchestrators
        # All config comes from YAML definition
        return DeclarativeOrchestrator(definition)

    # Not found in either registry
    available = list(ORCHESTRATOR_REGISTRY.keys()) + workflow_registry.list_all()
    msg = f"Unknown workflow type: {workflow_type}. Available workflows: {', '.join(available)}"
    raise ValueError(msg)


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


def is_agent_task(task_type: str) -> bool:
    """
    Check if a task type is a direct agent execution task.

    Args:
        task_type: Task type string

    Returns:
        True if this is an agent task (starts with 'agent:')
    """
    return task_type.startswith("agent:")


def extract_agent_type(task_type: str) -> str:
    """
    Extract agent type from task type.

    Args:
        task_type: Full task type (e.g., 'agent:research')

    Returns:
        Agent type (e.g., 'research')

    Raises:
        ValueError: If task_type is not an agent task
    """
    if not is_agent_task(task_type):
        msg = f"Not an agent task: {task_type}"
        raise ValueError(msg)

    return task_type.split(":", 1)[1]


def is_tool_task(task_type: str) -> bool:
    """
    Check if a task type is a direct tool execution task.

    Args:
        task_type: Task type string

    Returns:
        True if this is a tool task (starts with 'tool:')
    """
    return task_type.startswith("tool:")


def extract_tool_type(task_type: str) -> str:
    """
    Extract tool type from task type.

    Args:
        task_type: Full task type (e.g., 'tool:calculator')

    Returns:
        Tool type (e.g., 'calculator')

    Raises:
        ValueError: If task_type is not a tool task
    """
    if not is_tool_task(task_type):
        msg = f"Not a tool task: {task_type}"
        raise ValueError(msg)

    return task_type.split(":", 1)[1]


# Load declarative workflows on module import
load_declarative_workflows()
