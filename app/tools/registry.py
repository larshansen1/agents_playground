"""Tool registry for managing tool types, configurations, and instantiation."""

import importlib
import inspect
import threading
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import structlog
import yaml

from app.tools.base import Tool

logger = structlog.get_logger()


@dataclass
class ToolMetadata:
    """
    Metadata about a registered tool type.

    Stores configuration and metadata for a tool type, managing
    singleton instances and supporting fresh instance creation.
    """

    tool_class: type[Tool]
    config: dict = field(default_factory=dict)
    description: str = ""
    _instance: Tool | None = None

    def create_instance(self) -> Tool:
        """
        Factory method - creates configured tool instance (singleton).

        Returns the same instance on repeated calls.

        Returns:
            Tool: Singleton tool instance
        """
        if self._instance is None:
            self._instance = self.tool_class()  # type: ignore[call-arg]
        return self._instance

    def create_new_instance(self, **_override_config: Any) -> Tool:
        """
        Create fresh instance with config overrides.

        Note: Since existing tools may use no-arg constructors,
        config overrides are stored in metadata but not passed
        to the constructor in this initial implementation.

        Args:
            **_override_config: Configuration overrides (reserved for future use).
                               Prefixed with _ to indicate intentionally unused.

        Returns:
            Tool: New tool instance
        """
        # For now, create without config since tools use no-arg constructors
        # Future: pass config to tools that support it
        return self.tool_class()  # type: ignore[call-arg]


class ToolRegistry:
    """
    Central registry for all tool types.

    Manages tool registration, instantiation, and discovery with
    thread-safe operations and comprehensive error handling.

    Example:
        >>> registry = ToolRegistry()
        >>> registry.register("calculator", CalculatorTool, config={})
        >>> tool = registry.get("calculator")
        >>> result = tool.execute(expression="2 + 2")
    """

    def __init__(self):
        """Initialize the tool registry."""
        self._tools: dict[str, ToolMetadata] = {}
        self._lock = threading.Lock()

    def register(
        self,
        tool_name: str,
        tool_class: type[Tool],
        config: dict | None = None,
        description: str = "",
    ) -> None:
        """
        Register a tool type.

        Args:
            tool_name: Unique identifier for this tool type (e.g., "web_search")
            tool_class: Tool class that inherits from Tool base class
            config: Default configuration dict (stored in metadata)
            description: Human-readable description of the tool

        Raises:
            ValueError: If tool_name already registered or tool_class is invalid

        Example:
            >>> registry.register(
            ...     "calculator",
            ...     CalculatorTool,
            ...     config={},
            ...     description="Perform safe math calculations"
            ... )
        """
        with self._lock:
            # Validate tool_class
            if not inspect.isclass(tool_class):
                msg = f"tool_class must be a class, got {type(tool_class).__name__}"
                raise ValueError(msg)

            if not issubclass(tool_class, Tool):
                msg = f"Tool class {tool_class.__name__} must inherit from Tool base class"
                raise ValueError(msg)

            # Check for duplicates
            if tool_name in self._tools:
                existing_class = self._tools[tool_name].tool_class.__name__
                msg = (
                    f"Tool '{tool_name}' is already registered with class {existing_class}. "
                    f"Cannot register duplicate tool name."
                )
                raise ValueError(msg)

            # Register tool
            self._tools[tool_name] = ToolMetadata(
                tool_class=tool_class,
                config=config or {},
                description=description,
            )

            logger.info(
                "Tool registered",
                tool_name=tool_name,
                tool_class=tool_class.__name__,
                description=description,
            )

    def get(self, tool_name: str) -> Tool:
        """
        Get singleton tool instance.

        Returns the same instance on repeated calls for the same tool_name.

        Args:
            tool_name: Tool type identifier

        Returns:
            Tool: Singleton tool instance

        Raises:
            ValueError: If tool not found (includes available tools in error message)

        Example:
            >>> tool1 = registry.get("calculator")
            >>> tool2 = registry.get("calculator")
            >>> assert tool1 is tool2  # Same instance
        """
        with self._lock:
            if tool_name not in self._tools:
                available = list(self._tools.keys())
                msg = (
                    f"Unknown tool: '{tool_name}'. "
                    f"Available tools: {available if available else 'none registered'}"
                )
                raise ValueError(msg)

            metadata = self._tools[tool_name]
            tool = metadata.create_instance()

            logger.debug(
                "Tool retrieved",
                tool_name=tool_name,
                is_singleton=True,
            )

            return tool

    def create_new(self, tool_name: str, **override_config: Any) -> Tool:
        """
        Create fresh tool instance with config overrides.

        Creates a new instance every time (not a singleton).

        Args:
            tool_name: Tool type identifier
            **override_config: Configuration overrides to merge with defaults

        Returns:
            Tool: New tool instance (not cached)

        Raises:
            ValueError: If tool not found

        Example:
            >>> tool = registry.create_new("calculator", precision=10)
            >>> # New instance, not singleton
        """
        with self._lock:
            if tool_name not in self._tools:
                available = list(self._tools.keys())
                msg = (
                    f"Unknown tool: '{tool_name}'. "
                    f"Available tools: {available if available else 'none registered'}"
                )
                raise ValueError(msg)

            metadata = self._tools[tool_name]
            tool = metadata.create_new_instance(**override_config)

            logger.debug(
                "Tool instance created",
                tool_name=tool_name,
                is_singleton=False,
                config_overrides=list(override_config.keys()),
            )

            return tool

    def list_all(self) -> list[str]:
        """
        Return list of all registered tool types.

        Returns:
            List[str]: List of tool type identifiers

        Example:
            >>> registry.list_all()
            ['calculator', 'web_search']
        """
        with self._lock:
            return list(self._tools.keys())

    def has(self, tool_name: str) -> bool:
        """
        Check if tool type is registered.

        Args:
            tool_name: Tool type identifier

        Returns:
            bool: True if registered, False otherwise

        Example:
            >>> registry.has("calculator")
            True
            >>> registry.has("nonexistent")
            False
        """
        with self._lock:
            return tool_name in self._tools

    def get_metadata(self, tool_name: str) -> ToolMetadata:
        """
        Get metadata for a tool type.

        Args:
            tool_name: Tool type identifier

        Returns:
            ToolMetadata: Metadata object containing tool_class, config, and description

        Raises:
            ValueError: If tool not found

        Example:
            >>> metadata = registry.get_metadata("calculator")
            >>> assert metadata.tool_class == CalculatorTool
        """
        with self._lock:
            if tool_name not in self._tools:
                available = list(self._tools.keys())
                msg = (
                    f"Unknown tool: '{tool_name}'. "
                    f"Available tools: {available if available else 'none registered'}"
                )
                raise ValueError(msg)

            return self._tools[tool_name]

    def get_schema(self, tool_name: str) -> dict[str, Any]:
        """
        Get JSON Schema for tool parameters.

        Args:
            tool_name: Tool type identifier

        Returns:
            dict: JSON Schema describing tool parameters

        Raises:
            ValueError: If tool not found

        Example:
            >>> schema = registry.get_schema("calculator")
            >>> assert "properties" in schema
        """
        tool = self.get(tool_name)
        return tool.get_schema()

    def load_from_yaml(self, yaml_path: str | Path) -> None:
        """
        Load tool definitions from YAML file.

        Allows declarative tool configuration via YAML files instead of
        programmatic registration. Fully compatible with existing register() method.

        YAML Format:
            tools:
              - name: web_search
                class: app.tools.web_search.WebSearchTool
                config:
                  api_key_env: BRAVE_API_KEY
                description: "Search the web"

        Args:
            yaml_path: Path to YAML configuration file

        Raises:
            FileNotFoundError: If YAML file doesn't exist
            ValueError: If YAML is malformed or missing required fields
            ImportError: If tool class cannot be imported

        Example:
            >>> registry = ToolRegistry()
            >>> registry.load_from_yaml("config/tools.yaml")
            >>> tool = registry.get("web_search")
        """
        yaml_path = Path(yaml_path)

        if not yaml_path.exists():
            msg = f"YAML config file not found: {yaml_path}"
            raise FileNotFoundError(msg)

        logger.info("Loading tools from YAML", path=str(yaml_path))

        with yaml_path.open() as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                msg = f"Invalid YAML format: {e}"
                raise ValueError(msg) from e

        if not data:
            logger.warning("YAML file is empty", path=str(yaml_path))
            return

        if "tools" not in data:
            msg = "YAML file must contain 'tools' key at root level"
            raise ValueError(msg)

        tools_list = data["tools"]
        if not isinstance(tools_list, list):
            msg = "'tools' must be a list"
            raise ValueError(msg)

        # Register each tool
        for tool_def in tools_list:
            self._register_from_dict(tool_def)

        logger.info(
            "Tools loaded from YAML",
            count=len(tools_list),
            path=str(yaml_path),
        )

    def _register_from_dict(self, tool_def: dict) -> None:
        """
        Register tool from dictionary definition.

        Internal helper for YAML loading and future JSON/dict-based config.

        Args:
            tool_def: Dictionary with keys: name, class, config, description

        Raises:
            ValueError: If required fields are missing
            ImportError: If tool class cannot be imported
        """
        # Validate required fields
        if "name" not in tool_def:
            msg = "Tool definition missing required field: 'name'"
            raise ValueError(msg)

        if "class" not in tool_def:
            msg = f"Tool definition for '{tool_def['name']}' missing required field: 'class'"
            raise ValueError(msg)

        tool_name = tool_def["name"]
        class_path = tool_def["class"]
        config = tool_def.get("config", {})
        description = tool_def.get("description", "")

        # Import tool class
        try:
            module_path, class_name = class_path.rsplit(".", 1)
            module = importlib.import_module(module_path)
            tool_class = getattr(module, class_name)
        except (ValueError, ImportError, AttributeError) as e:
            msg = f"Failed to import tool class '{class_path}' for tool '{tool_name}': {e}"
            raise ImportError(msg) from e

        # Register tool
        self.register(
            tool_name=tool_name,
            tool_class=tool_class,
            config=config,
            description=description,
        )

    def discover_tools(self, search_path: str | Path) -> None:
        """
        Auto-discover tool classes in a directory.

        Scans Python files for Tool subclasses and auto-registers them.
        Excludes the Tool base class itself and test files.

        Args:
            search_path: Directory to search for tool classes

        Example:
            >>> registry.discover_tools("app/tools")
            >>> # All tool classes in app/tools/ now registered
        """
        search_path = Path(search_path)

        if not search_path.exists():
            logger.warning("Search path does not exist", path=str(search_path))
            return

        logger.info("Discovering tools", path=str(search_path))

        discovered_count = 0

        # Find all Python files
        for py_file in search_path.glob("*.py"):
            # Skip __init__.py, base.py, and test files
            if py_file.name in ("__init__.py", "base.py") or py_file.name.startswith("test_"):
                continue

            # Import module
            try:
                module_name = f"app.tools.{py_file.stem}"
                module = importlib.import_module(module_name)
            except ImportError as e:
                logger.warning(
                    "Failed to import module",
                    file=str(py_file),
                    error=str(e),
                )
                continue

            # Find Tool subclasses
            for name, obj in inspect.getmembers(module, inspect.isclass):
                # Skip if not a Tool subclass or is the Tool base class itself
                if not issubclass(obj, Tool) or obj is Tool:
                    continue

                # Generate tool name from class name
                # e.g., "WebSearchTool" -> "web_search"
                tool_name = self._class_name_to_tool_name(name)

                # Skip if already registered
                if self.has(tool_name):
                    logger.debug(
                        "Tool already registered, skipping",
                        tool_name=tool_name,
                        class_name=name,
                    )
                    continue

                # Register tool
                try:
                    self.register(
                        tool_name=tool_name,
                        tool_class=obj,
                        config={},
                        description=obj.__doc__ or "",
                    )
                    discovered_count += 1
                except ValueError as e:
                    logger.warning(
                        "Failed to register discovered tool",
                        tool_name=tool_name,
                        class_name=name,
                        error=str(e),
                    )

        logger.info("Tool discovery complete", discovered_count=discovered_count)

    def _class_name_to_tool_name(self, class_name: str) -> str:
        """
        Convert class name to tool name.

        Examples:
            "WebSearchTool" -> "web_search"
            "Calculator" -> "calculator"
            "DocumentReaderTool" -> "document_reader"

        Args:
            class_name: Class name

        Returns:
            str: Tool name in snake_case
        """
        # Remove "Tool" suffix if present
        if class_name.endswith("Tool"):
            class_name = class_name[:-4]

        # Convert CamelCase to snake_case
        result = []
        for i, char in enumerate(class_name):
            if char.isupper() and i > 0:
                result.append("_")
            result.append(char.lower())

        return "".join(result)
