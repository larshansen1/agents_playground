"""Global agent registry initialization.

This module provides a singleton registry instance that is initialized
on first import. It attempts to load agents from YAML config, falling
back to auto-discovery if the config file is missing.

Usage:
    from app.agents.registry_init import registry

    agent = registry.get("research")
"""

import logging
from pathlib import Path

from app.agents.registry import AgentRegistry

logger = logging.getLogger(__name__)

# Module-level singleton
_registry: AgentRegistry | None = None


def get_registry() -> AgentRegistry:
    """Get the global agent registry singleton.

    Initializes on first call with the following strategy:
    1. Try loading from config/agents.yaml
    2. Fall back to auto-discovery from app/agents/
    3. Return empty registry as last resort

    Returns:
        AgentRegistry: Global registry instance
    """
    global _registry  # noqa: PLW0603

    if _registry is not None:
        return _registry

    _registry = AgentRegistry()

    # Strategy 1: Try loading from YAML
    yaml_path = Path("config/agents.yaml")
    if yaml_path.exists():
        try:
            _registry.load_from_yaml(yaml_path)
            logger.info(f"Agent Registry: Loaded agents from {yaml_path}")
            return _registry
        except Exception as e:
            logger.warning(f"Agent Registry: Failed to load YAML config: {e}")

    # Strategy 2: Fall back to auto-discovery
    try:
        discovered = _registry.discover_agents()
        if discovered:
            logger.info(f"Agent Registry: Auto-discovered {len(discovered)} agents: {discovered}")
        else:
            logger.warning("Agent Registry: No agents found via auto-discovery")
    except Exception as e:
        logger.warning(f"Agent Registry: Auto-discovery failed: {e}")

    return _registry


# Initialize on module import for convenience
registry = get_registry()
