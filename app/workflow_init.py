"""Global workflow registry initialization."""

from pathlib import Path

import structlog

from app.workflow_registry import workflow_registry

logger = structlog.get_logger()

# Auto-load workflows from app/workflows directory
workflows_dir = Path(__file__).parent / "workflows"

if workflows_dir.exists():
    logger.info("Loading workflows from directory", path=str(workflows_dir))
    workflow_registry.load_from_directory(workflows_dir)
else:
    logger.warning("Workflow directory not found", path=str(workflows_dir))
