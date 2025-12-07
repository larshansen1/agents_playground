"""
title: Tool
author: system
version: 1.0
description: Execute a specific tool directly
requirements: requests, asyncio
"""

import asyncio
import json
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
        poll_interval: float = Field(
            default=2.0,
            description="Interval in seconds to poll for task completion",
        )
        timeout: int = Field(
            default=60,
            description="Maximum time in seconds to wait for task completion",
        )

    def __init__(self):
        self.valves = self.Valves()

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

    async def _fetch_tools(self) -> list[dict]:
        """Fetch available tools from registry API."""
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

    async def _create_tool_task(
        self, tool_name: str, tool_input: dict, user_id: str | None = None
    ) -> dict[str, Any]:
        """Create a task for direct tool execution."""
        payload = {
            "tool_name": tool_name,
            "input": tool_input,
            "user_id": user_id,
        }

        try:
            response = await asyncio.to_thread(
                requests.post,
                f"{self.valves.task_api_url}/tasks/tool",
                json=payload,
                timeout=10,
                **self._get_ssl_config(),
            )
            response.raise_for_status()
            task_data: dict[str, Any] = response.json()
            return task_data
        except requests.exceptions.RequestException as e:
            # Try to extract error message from response
            error_msg = str(e)
            if hasattr(e, "response") and e.response is not None:
                try:
                    error_detail = e.response.json().get("detail")
                    if error_detail:
                        error_msg = error_detail
                except ValueError:
                    pass
            msg = f"Failed to create task: {error_msg}"
            raise RuntimeError(msg) from e

    async def _wait_for_task(self, task_id: str, __event_emitter__: Any = None) -> dict[str, Any]:
        """Wait for task completion with polling."""
        start_time = time.time()

        while time.time() - start_time < self.valves.timeout:
            try:
                response = await asyncio.to_thread(
                    requests.get,
                    f"{self.valves.task_api_url}/tasks/{task_id}",
                    timeout=10,
                    **self._get_ssl_config(),
                )
                response.raise_for_status()
                task: dict[str, Any] = response.json()
                status = task.get("status")

                if status == "done":
                    return task
                if status == "error":
                    error_msg = task.get("error", "Unknown error")
                    msg = f"Task failed: {error_msg}"
                    raise RuntimeError(msg)

                # Emit status update if running
                if __event_emitter__:
                    await self._emit_status(
                        __event_emitter__, f"Tool executing... (Status: {status})", False
                    )

                await asyncio.sleep(self.valves.poll_interval)

            except requests.exceptions.RequestException as e:
                # Log error but continue polling (transient network issue?)
                print(f"Polling error: {e}")
                await asyncio.sleep(self.valves.poll_interval)

        msg = "Task timed out waiting for completion"
        raise TimeoutError(msg)

    async def _emit_status(self, emitter: Any, message: str, done: bool = False):
        """Helper to safely send UI updates via the event emitter."""
        if emitter:
            await emitter({"type": "status", "data": {"description": message, "done": done}})

    def _format_tool_list(self, tools: list[dict]) -> str:
        """Format list of tools for display."""
        if not tools:
            return "⚠️ **No tools available**"

        lines = ["# Available Tools\n"]
        for tool in tools:
            name = tool.get("name", "unknown")
            description = tool.get("description", "No description")
            schema = tool.get("schema", {})

            lines.append(f"**{name}**")
            lines.append(f"- Description: {description}")

            # Show parameters
            if schema.get("properties"):
                required_params = schema.get("required", [])
                params = []
                for param_name in required_params:
                    params.append(param_name)
                if params:
                    lines.append(f"- Parameters: {', '.join(params)}")

            lines.append(f"- Usage: `@tool {name} <args>`\n")

        return "\n".join(lines)

    async def tool(  # noqa: PLR0911, PLR0912, PLR0915
        self,
        command: str = "",
        __user__: dict | None = None,
        __event_emitter__: Any = None,
    ) -> str:
        """
        Execute a specific tool directly.

        Args:
            command: The command string containing tool name and arguments.
                     Format: "<tool_name> <args...>"
            __user__: User context from Open WebUI
            __event_emitter__: Event emitter for UI status updates

        Returns:
            Tool response or error message.

        Examples:
            @tool calculator "2 + 2"
            @tool web_search "Python tutorials"
        """
        # Extract user ID
        user_id = __user__.get("id") if __user__ else None

        # Parse command
        parts = command.strip().split(maxsplit=1)

        # Case 1: No arguments - list tools
        if not parts or not parts[0]:
            try:
                await self._emit_status(__event_emitter__, "Fetching tools...", False)
                tools = await self._fetch_tools()
                await self._emit_status(__event_emitter__, "List retrieved", True)
                return self._format_tool_list(tools)
            except Exception as e:
                return f"❌ **Error fetching tools**: {e!s}"

        tool_name = parts[0]

        # Case 2: Tool name provided but no args
        if len(parts) < 2:
            return f"""⚠️ **Missing Arguments**

Usage: `@tool {tool_name} <args...>`

Example: `@tool {tool_name} "your input"`
"""

        tool_args = parts[1]

        # Strip surrounding quotes if present (from command like: @tool calculator "2+2")
        if (tool_args.startswith('"') and tool_args.endswith('"')) or (
            tool_args.startswith("'") and tool_args.endswith("'")
        ):
            tool_args = tool_args[1:-1]

        try:
            # Fetch tool info to get schema
            await self._emit_status(__event_emitter__, f"Preparing {tool_name}...", False)
            tools = await self._fetch_tools()
            tool_info = next((t for t in tools if t.get("name") == tool_name), None)

            # Parse tool arguments based on schema
            if tool_info and tool_info.get("schema"):
                schema = tool_info["schema"]
                required = schema.get("required", [])

                # Simple mapping: if tool has one required parameter, use that
                if len(required) == 1:
                    param_name = required[0]
                    tool_input = {param_name: tool_args}
                else:
                    # Multiple parameters - try to parse as JSON, fallback to first required param
                    try:
                        tool_input = json.loads(tool_args)
                    except (json.JSONDecodeError, ValueError):
                        # Not JSON, use first required parameter if available
                        if required:
                            tool_input = {required[0]: tool_args}
                        else:
                            # No required params, try generic 'description'
                            tool_input = {"description": tool_args}
            else:
                # No schema info, fallback to generic description
                tool_input = {"description": tool_args}

            # 1. Create Task
            await self._emit_status(__event_emitter__, f"Executing {tool_name}...", False)

            try:
                task_response = await self._create_tool_task(tool_name, tool_input, user_id)
            except RuntimeError as e:
                # Check if it's an invalid tool error
                if "Tool" in str(e) and "not found" in str(e):
                    # Fetch available tools to show helpful error
                    try:
                        tools = await self._fetch_tools()
                        tool_list = self._format_tool_list(tools)
                        return f"""❌ **Tool '{tool_name}' not found**

{tool_list}
"""
                    except Exception:  # nosec B110
                        pass  # Fallback to generic error
                raise e

            task_id = task_response["id"]

            # 2. Wait for completion
            await self._emit_status(__event_emitter__, f"Tool {tool_name} running...", False)
            final_task = await self._wait_for_task(task_id, __event_emitter__)

            # 3. Return result
            await self._emit_status(__event_emitter__, "Task complete!", True)

            output = final_task.get("output", {})
            # If output is a dict with 'result' or 'response', use that.
            # Otherwise dump the whole thing formatted.

            if isinstance(output, dict):
                if "result" in output:
                    return str(output["result"])
                if "response" in output:
                    return str(output["response"])
                if "content" in output:
                    return str(output["content"])

            # Fallback: formatted JSON
            return f"```json\n{json.dumps(output, indent=2)}\n```"

        except Exception as e:
            await self._emit_status(__event_emitter__, "Task failed", True)
            return f"❌ **Error**: {e!s}"
