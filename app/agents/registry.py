"""Agent registry for managing agent types, configurations, and instantiation."""

import importlib
import inspect
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog
import yaml

from app.agents.base import Agent

logger = structlog.get_logger()


@dataclass
class AgentMetadata:
    """Metadata about a registered agent type.

    Stores configuration and metadata for an agent type, managing
    singleton instances and supporting fresh instance creation.
    """

    agent_class: type[Agent]
    config: dict
    tools: list[str]
    description: str
    _instance: Agent | None = field(default=None, init=False, repr=False)

    def create_instance(self) -> Agent:
        """Factory method - creates configured agent instance (singleton).

        Returns the same instance on repeated calls.

        Returns:
            Agent: Singleton agent instance
        """
        if self._instance is None:
            # Option 1 approach: Call no-arg constructor
            # Config is stored in metadata but not passed during instantiation
            self._instance = self.agent_class()  # type: ignore[call-arg]
        return self._instance

    def create_new_instance(self, **_override_config) -> Agent:
        """Create fresh instance with config overrides.

        Note: Since existing agents use no-arg constructors,
        config overrides are stored in metadata but not passed
        to the constructor. This supports future agents that
        may accept config parameters.

        Args:
            **_override_config: Configuration overrides (stored but not used
                               with current no-arg constructor agents)
                               Prefixed with _ to indicate intentionally unused.

        Returns:
            Agent: New agent instance
        """
        # Option 1 approach: Call no-arg constructor
        # Future enhancement: Detect constructor signature and pass config if supported
        # Note: Config merging would be: {**self.config, **_override_config}
        return self.agent_class()  # type: ignore[call-arg]


class AgentRegistry:
    """
    Central registry for all agent types.

    Manages agent registration, instantiation, and discovery with
    thread-safe operations and comprehensive error handling.

    Example:
        >>> registry = AgentRegistry()
        >>> registry.register(
        ...     "research",
        ...     ResearchAgent,
        ...     config={"model": "gpt-4-turbo"},
        ...     tools=["web_search"]
        ... )
        >>> agent = registry.get("research")
    """

    def __init__(self):
        """Initialize the agent registry."""
        self._agents: dict[str, AgentMetadata] = {}
        self._initialized = False
        self._lock = threading.RLock()

    def register(
        self,
        agent_type: str,
        agent_class: type[Agent],
        config: dict | None = None,
        tools: list[str] | None = None,
        description: str = "",
    ) -> None:
        """Register an agent type.

        Args:
            agent_type: Unique identifier for this agent type (e.g., "research")
            agent_class: Agent class that inherits from Agent base class
            config: Default configuration dict (stored in metadata)
            tools: List of tool names the agent can use
            description: Human-readable description of the agent

        Raises:
            ValueError: If agent_type already registered
            TypeError: If agent_class doesn't inherit from Agent

        Example:
            >>> registry.register(
            ...     "research",
            ...     ResearchAgent,
            ...     config={"model": "gpt-4-turbo", "temperature": 0.7},
            ...     tools=["web_search", "document_reader"],
            ...     description="Gathers information from web sources"
            ... )
        """
        with self._lock:
            # Validate inputs
            if not agent_type:
                msg = "agent_type cannot be empty"
                raise ValueError(msg)

            if agent_type in self._agents:
                existing = self._agents[agent_type]
                logger.warning(
                    "agent_registration_duplicate_attempt",
                    agent_type=agent_type,
                )
                msg = (
                    f"Agent type '{agent_type}' is already registered.\n"
                    f"Existing: {existing.agent_class.__name__} with "
                    f"tools={existing.tools}"
                )
                raise ValueError(msg)

            # Validate agent class inheritance
            if not (isinstance(agent_class, type) and issubclass(agent_class, Agent)):
                msg = f"Agent class must inherit from Agent base class.\nGot: {type(agent_class)}"
                raise TypeError(msg)

            # Set defaults
            config = config or {}
            tools = tools or []

            # Create and store metadata
            metadata = AgentMetadata(
                agent_class=agent_class,
                config=config,
                tools=tools,
                description=description,
            )
            self._agents[agent_type] = metadata

            logger.info(
                "agent_registered",
                agent_type=agent_type,
                class_name=agent_class.__name__,
                tools=tools,
                description=description,
            )

    def get(self, agent_type: str) -> Agent:
        """Get singleton agent instance.

        Returns the same instance on repeated calls for the same agent_type.

        Args:
            agent_type: Agent type identifier

        Returns:
            Agent: Singleton agent instance

        Raises:
            ValueError: If agent type is not registered

        Example:
            >>> agent1 = registry.get("research")
            >>> agent2 = registry.get("research")
            >>> assert agent1 is agent2  # Same instance
        """
        if agent_type not in self._agents:
            available = list(self._agents.keys())
            msg = f"Unknown agent type: '{agent_type}'.\nAvailable agents: {available}"
            raise ValueError(msg)

        metadata = self._agents[agent_type]
        instance = metadata.create_instance()

        logger.info(
            "agent_instantiated",
            agent_type=agent_type,
            instance_id=id(instance),
            is_singleton=True,
        )

        return instance

    def create_new(self, agent_type: str, **override_config: Any) -> Agent:
        """Create fresh agent instance with config overrides.

        Creates a new instance every time (not a singleton).

        Args:
            agent_type: Agent type identifier
            **override_config: Configuration overrides to merge with defaults

        Returns:
            Agent: New agent instance

        Raises:
            ValueError: If agent type is not registered

        Example:
            >>> agent = registry.create_new("research", temperature=0.9)
            >>> # New instance, not singleton
        """
        if agent_type not in self._agents:
            available = list(self._agents.keys())
            msg = f"Unknown agent type: '{agent_type}'.\nAvailable agents: {available}"
            raise ValueError(msg)

        metadata = self._agents[agent_type]
        instance = metadata.create_new_instance(**override_config)

        logger.info(
            "agent_instantiated",
            agent_type=agent_type,
            instance_id=id(instance),
            is_singleton=False,
            config_overrides=override_config,
        )

        return instance

    def list_all(self) -> list[str]:
        """Return list of all registered agent types.

        Returns:
            List[str]: List of agent type identifiers

        Example:
            >>> registry.list_all()
            ['research', 'assessment']
        """
        return list(self._agents.keys())

    def has(self, agent_type: str) -> bool:
        """Check if agent type is registered.

        Args:
            agent_type: Agent type identifier

        Returns:
            bool: True if registered, False otherwise

        Example:
            >>> registry.has("research")
            True
            >>> registry.has("nonexistent")
            False
        """
        return agent_type in self._agents

    def get_metadata(self, agent_type: str) -> AgentMetadata:
        """Get metadata for an agent type.

        Args:
            agent_type: Agent type identifier

        Returns:
            AgentMetadata: Metadata object containing agent_class, config,
                          tools, and description

        Raises:
            ValueError: If agent type is not registered

        Example:
            >>> metadata = registry.get_metadata("research")
            >>> assert metadata.agent_class == ResearchAgent
            >>> assert "web_search" in metadata.tools
        """
        if agent_type not in self._agents:
            available = list(self._agents.keys())
            msg = f"Unknown agent type: '{agent_type}'.\nAvailable agents: {available}"
            raise ValueError(msg)

        return self._agents[agent_type]

    def load_from_yaml(self, yaml_path: str | Path) -> None:
        """Load agent definitions from YAML file.

        Allows declarative agent configuration via YAML files instead of
        programmatic registration. Fully compatible with existing register() method.

        YAML Format:
            agents:
              - name: research
                class: app.agents.research_agent.ResearchAgent
                config:
                  model: gpt-4-turbo
                  temperature: 0.7
                tools:
                  - web_search
                description: "Conducts research"

        Args:
            yaml_path: Path to YAML configuration file

        Raises:
            FileNotFoundError: If YAML file doesn't exist
            ValueError: If YAML is malformed or missing required fields
            ImportError: If agent class cannot be imported

        Example:
            >>> registry = AgentRegistry()
            >>> registry.load_from_yaml("config/agents.yaml")
            >>> agent = registry.get("research")
        """
        yaml_path = Path(yaml_path)

        if not yaml_path.exists():
            msg = f"YAML file not found: {yaml_path}"
            raise FileNotFoundError(msg)

        try:
            with yaml_path.open() as f:
                data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            msg = f"Invalid YAML syntax in {yaml_path}: {e}"
            raise ValueError(msg) from e

        if not data or "agents" not in data:
            msg = f"YAML file must contain 'agents' key: {yaml_path}"
            raise ValueError(msg)

        agents_loaded = []
        for agent_def in data["agents"]:
            try:
                self._register_from_dict(agent_def)
                agents_loaded.append(agent_def.get("name", "unknown"))
            except (ValueError, ImportError) as e:
                logger.error(
                    "yaml_agent_registration_failed",
                    agent_def=agent_def,
                    error=str(e),
                )
                raise

        logger.info(
            "yaml_agents_loaded",
            yaml_path=str(yaml_path),
            count=len(agents_loaded),
            agent_types=agents_loaded,
        )

    def _register_from_dict(self, agent_def: dict) -> None:
        """Register agent from dictionary definition.

        Internal helper for YAML loading and future JSON/dict-based config.

        Args:
            agent_def: Dictionary with keys: name, class, config, tools, description

        Raises:
            ValueError: If required fields are missing
            ImportError: If agent class cannot be imported
        """
        # Validate required fields
        if "name" not in agent_def:
            msg = "Agent definition missing required 'name' field"
            raise ValueError(msg)

        if "class" not in agent_def:
            msg = f"Agent '{agent_def['name']}' missing required 'class' field"
            raise ValueError(msg)

        # Import agent class dynamically
        class_path = agent_def["class"]
        try:
            module_path, class_name = class_path.rsplit(".", 1)
        except ValueError as e:
            msg = f"Invalid class path '{class_path}': must be fully qualified (e.g., 'module.ClassName')"
            raise ValueError(msg) from e

        try:
            module = importlib.import_module(module_path)
            agent_class = getattr(module, class_name)
        except ImportError as e:
            msg = f"Cannot import module '{module_path}' for agent '{agent_def['name']}': {e}"
            raise ImportError(msg) from e
        except AttributeError as e:
            msg = f"Class '{class_name}' not found in module '{module_path}': {e}"
            raise ImportError(msg) from e

        # Register with extracted values
        self.register(
            agent_type=agent_def["name"],
            agent_class=agent_class,
            config=agent_def.get("config", {}),
            tools=agent_def.get("tools", []),
            description=agent_def.get("description", ""),
        )

    def discover_agents(
        self,
        search_path: str | Path = "app/agents",
        exclude_patterns: list[str] | None = None,
    ) -> list[str]:
        """Auto-discover and register agents from filesystem.

        Scans the specified directory for Agent subclasses and automatically
        registers them. Useful for plugin-style agent discovery.

        Args:
            search_path: Directory to search for agent modules (default: "app/agents")
            exclude_patterns: File patterns to exclude (default: ["base.py", "__*"])

        Returns:
            List of discovered agent type names

        Example:
            >>> registry = AgentRegistry()
            >>> discovered = registry.discover_agents()
            >>> print(f"Found {len(discovered)} agents: {discovered}")
        """
        search_path = Path(search_path)
        exclude_patterns = exclude_patterns or ["base.py", "__*"]

        discovered: list[str] = []

        if not search_path.exists():
            logger.warning("discovery_path_not_found", path=str(search_path))
            return discovered

        for py_file in search_path.glob("*.py"):
            # Skip excluded files
            if any(py_file.match(pattern) for pattern in exclude_patterns):
                continue

            # Build module name from path
            # e.g., "app/agents/research_agent.py" -> "app.agents.research_agent"
            # Resolve to absolute paths first to avoid relative_to issues
            abs_file = py_file.resolve()
            abs_cwd = Path.cwd().resolve()

            try:
                relative_parts = abs_file.relative_to(abs_cwd).with_suffix("").parts
                module_name = ".".join(relative_parts)
            except ValueError:
                # If file is outside cwd, try simple module construction
                logger.warning(
                    "discovery_path_resolution_failed",
                    file=str(py_file),
                    cwd=str(abs_cwd),
                )
                continue

            try:
                module = importlib.import_module(module_name)
            except ImportError as e:
                logger.warning("discovery_import_failed", module=module_name, error=str(e))
                continue

            # Find Agent subclasses in the module
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Check if it's an Agent subclass (but not Agent itself)
                # and defined in this module (not imported from elsewhere)
                if (
                    issubclass(obj, Agent)
                    and obj is not Agent
                    and obj.__module__ == module.__name__
                ):
                    # Derive agent type from filename
                    # e.g., "research_agent.py" -> "research"
                    agent_type = py_file.stem.replace("_agent", "")

                    # Auto-register if not already registered
                    if not self.has(agent_type):
                        self.register(
                            agent_type=agent_type,
                            agent_class=obj,
                            description=obj.__doc__ or "",
                        )
                        discovered.append(agent_type)
                        logger.debug(
                            "agent_discovered",
                            agent_type=agent_type,
                            class_name=name,
                            module=module_name,
                        )

        logger.info(
            "agents_discovered",
            path=str(search_path),
            count=len(discovered),
            agent_types=discovered,
        )

        return discovered
