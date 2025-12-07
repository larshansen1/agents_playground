"""
title: Discover
author: lars
version: 3.0
file_handler: false
description: Explore available flows, agents, and tools. Use '@discover' to see all resources or '@discover flows/agents/tools' to filter by type. Results are cached for 60 seconds to optimize performance.
requirements: requests, asyncio
"""

import asyncio
import os
import time
from typing import Any

import requests
from pydantic import BaseModel, Field


class Tools:
    class Valves(BaseModel):
        task_api_url: str = Field(
            default=os.getenv("TASK_API_URL", "http://task-api:8000"),
            description="Base URL for Task API (use http://task-api:8000 for Docker network)",
        )
        ca_cert_path: str = Field(
            default=os.getenv("CA_CERT_PATH", "/path/to/ca-cert.pem"),
            description="Path to CA certificate for server verification",
        )
        client_cert_path: str = Field(
            default=os.getenv("CLIENT_CERT_PATH", "/path/to/client-cert.pem"),
            description="Path to client certificate for mTLS authentication",
        )
        client_key_path: str = Field(
            default=os.getenv("CLIENT_KEY_PATH", "/path/to/client-key.pem"),
            description="Path to client private key for mTLS authentication",
        )
        verify_ssl: bool = Field(
            default=False,
            description="Verify SSL certificates (set False for self-signed certs in development)",
        )
        cache_ttl_seconds: int = Field(
            default=60,
            description="Cache registry data for N seconds",
        )

    def __init__(self):
        self.valves = self.Valves()
        self._cache: dict[str, tuple[float, Any]] = {}  # key -> (timestamp, data)

    def _get_ssl_config(self) -> dict[str, Any]:
        """Get SSL configuration for mTLS requests."""
        config = {
            "cert": (self.valves.client_cert_path, self.valves.client_key_path),
        }

        config_dict: dict[str, Any] = config

        if self.valves.verify_ssl:
            config_dict["verify"] = self.valves.ca_cert_path
        else:
            config_dict["verify"] = False

        return config_dict

    async def _get_cached_or_fetch(
        self,
        cache_key: str,
        fetch_func: Any,
    ) -> Any:
        """Get from cache or fetch from API."""
        now = time.time()

        # Check cache
        if cache_key in self._cache:
            timestamp, data = self._cache[cache_key]
            if now - timestamp < self.valves.cache_ttl_seconds:
                return data

        # Cache miss - fetch from API
        data = await fetch_func()
        self._cache[cache_key] = (now, data)
        return data

    async def _fetch_agents(self) -> list[dict]:
        """Fetch agents from registry API."""
        try:
            response = await asyncio.to_thread(
                requests.get,
                f"{self.valves.task_api_url}/admin/agents",
                timeout=10,
                **self._get_ssl_config(),
            )
            response.raise_for_status()
            agents: list[dict] = response.json().get("agents", [])
            return agents
        except requests.exceptions.RequestException as e:
            msg = f"Failed to fetch agents: {e!s}"
            raise RuntimeError(msg) from e

    async def _fetch_tools(self) -> list[dict]:
        """Fetch tools from registry API."""
        try:
            response = await asyncio.to_thread(
                requests.get,
                f"{self.valves.task_api_url}/admin/tools",
                timeout=10,
                **self._get_ssl_config(),
            )
            response.raise_for_status()
            tools: list[dict] = response.json().get("tools", [])
            return tools
        except requests.exceptions.RequestException as e:
            msg = f"Failed to fetch tools: {e!s}"
            raise RuntimeError(msg) from e

    async def _fetch_workflows(self) -> list[dict]:
        """Fetch workflows from registry API."""
        try:
            response = await asyncio.to_thread(
                requests.get,
                f"{self.valves.task_api_url}/admin/workflows",
                timeout=10,
                **self._get_ssl_config(),
            )
            response.raise_for_status()
            workflows: list[dict] = response.json().get("workflows", [])
            return workflows
        except requests.exceptions.RequestException as e:
            msg = f"Failed to fetch workflows: {e!s}"
            raise RuntimeError(msg) from e

    def _format_agents(self, agents: list[dict]) -> str:
        """Format agents list with tools and config."""
        if not agents:
            return "⚠️ **No agents registered**\n"

        lines = [f"# Available Agents ({len(agents)})\n"]

        for agent in agents:
            name = agent.get("name", "unknown")
            description = agent.get("description", "No description")
            config = agent.get("config", {})
            tools = agent.get("tools", [])

            lines.append(f"**{name}**")
            lines.append(f"- Description: {description}")

            if tools:
                tools_str = ", ".join(tools)
                lines.append(f"- Tools: {tools_str}")

            if config.get("model"):
                lines.append(f"- Model: {config['model']}")
            if config.get("temperature") is not None:
                lines.append(f"- Temperature: {config['temperature']}")

            lines.append("")

        return "\n".join(lines)

    def _format_tools(self, tools: list[dict]) -> str:
        """Format tools list with parameter schemas."""
        if not tools:
            return "⚠️ **No tools registered**\n"

        lines = [f"# Available Tools ({len(tools)})\n"]

        for tool in tools:
            name = tool.get("name", "unknown")
            description = tool.get("description", "No description")
            schema = tool.get("schema", {})

            lines.append(f"**{name}**")
            lines.append(f"- Description: {description}")

            # Format parameters from schema
            if schema.get("properties"):
                lines.append("- Parameters:")
                required_params = schema.get("required", [])

                for param_name, param_info in schema["properties"].items():
                    param_type = param_info.get("type", "any")
                    param_desc = param_info.get("description", "")
                    is_required = param_name in required_params
                    required_str = "required" if is_required else "optional"
                    default = param_info.get("default")

                    param_line = f"  - {param_name} ({param_type}, {required_str})"
                    if param_desc:
                        param_line += f": {param_desc}"
                    if default is not None:
                        param_line += f" (default={default})"

                    lines.append(param_line)

            lines.append("")

        return "\n".join(lines)

    def _format_workflows(self, workflows: list[dict]) -> str:
        """Format workflows list with steps."""
        if not workflows:
            return "⚠️ **No workflows registered**\n"

        lines = [f"# Available Workflows ({len(workflows)})\n"]

        for workflow in workflows:
            name = workflow.get("name", "unknown")
            description = workflow.get("description", "No description")
            strategy = workflow.get("strategy", "unknown")
            max_iterations = workflow.get("max_iterations")
            steps = workflow.get("steps", [])

            lines.append(f"**{name}**")
            lines.append(f"- Description: {description}")
            lines.append(f"- Strategy: {strategy}")

            if max_iterations:
                lines.append(f"- Max Iterations: {max_iterations}")

            if steps:
                lines.append(f"- Steps ({len(steps)}):")
                for i, step in enumerate(steps, 1):
                    step_name = step.get("name", "unknown")
                    agent_type = step.get("agent_type", "unknown")
                    step_desc = step.get("description", "")
                    step_tools = step.get("tools", [])

                    step_line = f"  {i}. {step_name} ({agent_type} agent)"
                    if step_desc:
                        step_line += f"\n     - {step_desc}"
                    if step_tools:
                        tools_str = ", ".join(step_tools)
                        step_line += f"\n     - Tools: {tools_str}"

                    lines.append(step_line)
            lines.append("")

        return "\n".join(lines)

    def _format_all(  # noqa: PLR0912, PLR0915
        self, agents: list[dict], tools: list[dict], workflows: list[dict]
    ) -> str:
        """Format all resources together."""
        lines = ["# Available Resources\n"]

        # Summary
        lines.append(f"**Agents:** {len(agents)}")
        lines.append(f"**Tools:** {len(tools)}")
        lines.append(f"**Workflows:** {len(workflows)}\n")
        lines.append("---\n")

        # Agents section
        lines.append("## Agents\n")
        if agents:
            for agent in agents:
                name = agent.get("name", "unknown")
                description = agent.get("description", "No description")
                tools_list = agent.get("tools", [])
                config = agent.get("config", {})

                lines.append(f"- **{name}**: {description}")
                if tools_list:
                    tools_str = ", ".join(tools_list)
                    lines.append(f"  - Tools: {tools_str}")
                if config.get("model"):
                    lines.append(f"  - Model: {config['model']}")
        else:
            lines.append("⚠️ No agents registered")

        lines.append("")

        # Tools section
        lines.append("## Tools\n")
        if tools:
            for tool in tools:
                name = tool.get("name", "unknown")
                description = tool.get("description", "No description")
                schema = tool.get("schema", {})

                lines.append(f"- **{name}**: {description}")

                # Show required parameters
                if schema.get("properties"):
                    required_params = schema.get("required", [])
                    if required_params:
                        params_str = ", ".join(required_params)
                        lines.append(f"  - Parameters: {params_str}")
        else:
            lines.append("⚠️ No tools registered")

        lines.append("")

        # Workflows section
        lines.append("## Workflows\n")
        if workflows:
            for workflow in workflows:
                name = workflow.get("name", "unknown")
                description = workflow.get("description", "No description")
                strategy = workflow.get("strategy", "unknown")
                steps = workflow.get("steps", [])

                lines.append(f"- **{name}**: {description}")
                lines.append(f"  - Strategy: {strategy} ({len(steps)} steps)")
        else:
            lines.append("⚠️ No workflows registered")

        lines.append("\n---\n")
        lines.append("**Usage:**")
        lines.append('- Execute flow: `@flow <workflow_name> "topic"` or `@flow "description"`')
        lines.append('- Execute agent: `@agent <agent_name> "query"`')
        lines.append("- Execute tool: `@tool <tool_name> <args...>`")
        lines.append("")
        lines.append("**Examples:**")
        lines.append('- `@flow research_assessment "AI safety"`  # Direct workflow')
        lines.append('- `@flow "research quantum computing"`  # Smart selection')
        lines.append('- `@agent research "blockchain technology"`')
        lines.append('- `@tool calculator "2 + 2"`')

        return "\n".join(lines)

    async def _emit_status(self, emitter: Any, message: str, done: bool = False):
        """Helper to safely send UI updates via the event emitter."""
        if emitter:
            await emitter({"type": "status", "data": {"description": message, "done": done}})

    async def discover(
        self,
        query: str = "",
        __event_emitter__: Any = None,
    ) -> str:
        """
        Discover available resources in the backend system.

        Args:
            query: Optional filter - "agents", "tools", "workflows", or empty for all
            __event_emitter__: Event emitter for UI status updates

        Returns:
            Formatted markdown output with available resources
        """
        query = query.strip().lower()

        try:
            # Determine what to fetch
            fetch_agents = query in ("", "all", "agents", "agent")
            fetch_tools = query in ("", "all", "tools", "tool")
            fetch_workflows = query in ("", "all", "workflows", "workflow")

            agents: list[dict] = []
            tools: list[dict] = []
            workflows: list[dict] = []

            # Fetch agents
            if fetch_agents:
                await self._emit_status(__event_emitter__, "Fetching agents...", False)
                agents = await self._get_cached_or_fetch("registry:agents", self._fetch_agents)

            # Fetch tools
            if fetch_tools:
                await self._emit_status(__event_emitter__, "Fetching tools...", False)
                tools = await self._get_cached_or_fetch("registry:tools", self._fetch_tools)

            # Fetch workflows
            if fetch_workflows:
                await self._emit_status(__event_emitter__, "Fetching workflows...", False)
                workflows = await self._get_cached_or_fetch(
                    "registry:workflows", self._fetch_workflows
                )

            await self._emit_status(__event_emitter__, "Formatting results...", False)

            # Format output based on query
            if query in ("agents", "agent"):
                output = self._format_agents(agents)
            elif query in ("tools", "tool"):
                output = self._format_tools(tools)
            elif query in ("workflows", "workflow"):
                output = self._format_workflows(workflows)
            else:
                # All resources
                output = self._format_all(agents, tools, workflows)

            await self._emit_status(__event_emitter__, "Discovery complete!", True)
            return output

        except RuntimeError as e:
            await self._emit_status(__event_emitter__, "Discovery failed", True)
            return f"""❌ **Error: Cannot connect to backend**

The registry API is unavailable. Please check:
1. Backend service is running
2. mTLS certificates are configured correctly
3. Network connectivity

Error details: {e!s}
"""
        except Exception as e:
            await self._emit_status(__event_emitter__, "Unexpected error", True)
            return f"""❌ **Unexpected Error**

An unexpected error occurred during discovery.

Error details: {e!s}
"""
