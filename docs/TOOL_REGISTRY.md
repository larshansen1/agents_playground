# Tool Registry Guide

The Tool Registry provides a standardized way for agents to access and execute external tools. It manages tool registration, instantiation, configuration, and discovery.

## Quick Start

```python
from app.tools.registry_init import tool_registry

# Get a tool instance (singleton)
search_tool = tool_registry.get("web_search")

# Execute the tool
result = search_tool.execute(query="Python tutorials")

if result["success"]:
    print(result["result"])
else:
    print(f"Error: {result['error']}")
```

## Available Tools

| Tool Name | Description | Parameters |
|-----------|-------------|------------|
| `calculator` | Safe mathematical expression evaluator | `expression` (str) |
| `web_search` | Search the web using Brave Search API | `query` (str), `max_results` (int) |

## Creating a New Tool

To create a custom tool, inherit from the `Tool` base class and implement the required methods.

### 1. Create Tool Class

Create a new file in `app/tools/my_tool.py`:

```python
from typing import Any
from app.tools.base import Tool

class MyTool(Tool):
    def __init__(self):
        super().__init__(
            tool_name="my_tool",
            description="Description of what my tool does"
        )

    def get_schema(self) -> dict[str, Any]:
        """Return JSON Schema for parameters."""
        return {
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "First parameter"},
                "param2": {"type": "integer", "default": 10}
            },
            "required": ["param1"]
        }

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """Execute the tool."""
        # 1. Validate parameters
        self.validate_params(**kwargs)

        # 2. Extract parameters
        param1 = kwargs["param1"]
        param2 = kwargs.get("param2", 10)

        # 3. Perform logic
        try:
            # ... your tool logic here ...
            result_data = f"Processed {param1} with {param2}"

            # 4. Return standard result
            return {
                "success": True,
                "result": result_data,
                "error": None,
                "metadata": {"processed": True}
            }
        except Exception as e:
            # Handle errors gracefully
            return {
                "success": False,
                "result": None,
                "error": str(e),
                "metadata": {}
            }
```

### 2. Register the Tool

You can register your tool in `config/tools.yaml`:

```yaml
tools:
  - name: my_tool
    class: app.tools.my_tool.MyTool
    config:
      some_config: value
    description: "My custom tool"
```

Or programmatically:

```python
from app.tools.registry_init import tool_registry
from app.tools.my_tool import MyTool

tool_registry.register("my_tool", MyTool)
```

## Using Tools in Agents

Agents can access tools via the `_execute_tool` method.

```python
from app.agents.base import Agent

class MyAgent(Agent):
    def __init__(self):
        super().__init__(
            agent_type="my_agent",
            tools=["web_search", "calculator"]  # Declare tools used
        )

    def execute(self, input_data, user_id_hash=None):
        # Execute a tool
        search_result = self._execute_tool("web_search", query="latest news")

        if search_result["success"]:
            # Process result
            pass

        return {"output": ...}
```

## Configuration

Tools are configured in `config/tools.yaml`. The registry automatically loads this file on startup.

```yaml
tools:
  - name: web_search
    class: app.tools.web_search.WebSearchTool
    config:
      api_key_env: BRAVE_API_KEY
      default_max_results: 5
```

## Auto-Discovery

The registry supports auto-discovery of tools in the `app/tools` directory. Any class inheriting from `Tool` (except `Tool` itself) can be automatically registered if `tool_registry.discover_tools()` is called.

## Error Handling

Tools always return a dictionary with the following structure, never raising exceptions for expected failures:

```python
{
    "success": bool,      # True if successful
    "result": Any,        # The output data (None on error)
    "error": str | None,  # Error message if failed
    "metadata": dict      # Optional metadata
}
```

Always check `result["success"]` before accessing `result["result"]`.
