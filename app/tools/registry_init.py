"""Global tool registry singleton."""

from pathlib import Path

import structlog

from app.tools.registry import ToolRegistry

logger = structlog.get_logger()

# Global registry singleton
tool_registry = ToolRegistry()

# Auto-load from YAML if exists
yaml_path = Path(__file__).parent.parent.parent / "config" / "tools.yaml"
if yaml_path.exists():
    logger.info("Loading tools from YAML", path=str(yaml_path))
    tool_registry.load_from_yaml(yaml_path)
else:
    logger.info("No tools.yaml found, using programmatic registration only")

# Optional: Auto-discover tools
# tool_registry.discover_tools(Path(__file__).parent)
