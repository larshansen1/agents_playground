"""
title: Agent Execution Tool
author: system
version: 1.0
description: Execute a specific agent directly for a task
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
            default=300,
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

    async def _fetch_agents(self) -> list[dict]:
        """Fetch available agents from registry API."""
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

    async def _create_agent_task(
        self, agent_type: str, task_input: str, user_id: str | None = None
    ) -> dict[str, Any]:
        """Create a task for direct agent execution."""
        payload = {
            "agent_type": agent_type,
            "input": {"description": task_input},
            "user_id": user_id,
        }

        try:
            response = await asyncio.to_thread(
                requests.post,
                f"{self.valves.task_api_url}/tasks/agent",
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
                        __event_emitter__, f"Agent working... (Status: {status})", False
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

    def _format_agent_list(self, agents: list[dict]) -> str:
        """Format list of agents for display."""
        if not agents:
            return "⚠️ **No agents available**"

        lines = ["# Available Agents\n"]
        for agent in agents:
            name = agent.get("name", "unknown")
            description = agent.get("description", "No description")
            lines.append(f"**{name}**")
            lines.append(f"- Description: {description}")
            lines.append(f'- Usage: `@agent {name} "your query"`\n')

        return "\n".join(lines)

    async def agent(  # noqa: PLR0911
        self,
        command: str = "",
        __user__: dict | None = None,
        __event_emitter__: Any = None,
    ) -> str:
        """
        Execute a specific agent directly.

        Args:
            command: The command string containing agent name and task description.
                     Format: "<agent_name> <task_description>"
            __user__: User context from Open WebUI
            __event_emitter__: Event emitter for UI status updates

        Returns:
            Agent response or error message.
        """
        # Extract user ID
        user_id = __user__.get("id") if __user__ else None

        # Parse command
        parts = command.strip().split(maxsplit=1)

        # Case 1: No arguments - list agents
        if not parts or not parts[0]:
            try:
                await self._emit_status(__event_emitter__, "Fetching agents...", False)
                agents = await self._fetch_agents()
                await self._emit_status(__event_emitter__, "List retrieved", True)
                return self._format_agent_list(agents)
            except Exception as e:
                return f"❌ **Error fetching agents**: {e!s}"

        agent_name = parts[0]

        # Case 2: Agent name provided but no task - show usage/info for that agent?
        # For now, treat as missing task if we want to enforce description,
        # but maybe the user just wants to see info about a specific agent.
        # The requirements say: Command: @agent <agent_name> <task_description>
        # Let's assume if only agent name is given, we might need a prompt.
        # But for simplicity, let's require a task description.
        if len(parts) < 2:
            return f"""⚠️ **Missing Task Description**

Usage: `@agent {agent_name} "your task description"`

Example: `@agent {agent_name} "Research the history of the internet"`
"""

        task_description = parts[1]

        try:
            # 1. Create Task
            await self._emit_status(__event_emitter__, f"Starting {agent_name}...", False)

            try:
                task_response = await self._create_agent_task(agent_name, task_description, user_id)
            except RuntimeError as e:
                # Check if it's an invalid agent error
                if "Agent" in str(e) and "not found" in str(e):
                    # Fetch available agents to show helpful error
                    try:
                        agents = await self._fetch_agents()
                        agent_list = self._format_agent_list(agents)
                        return f"""❌ **Agent '{agent_name}' not found**

{agent_list}
"""
                    except Exception:  # nosec B110
                        pass  # Fallback to generic error
                raise e

            task_id = task_response["id"]

            # 2. Wait for completion
            await self._emit_status(__event_emitter__, f"Agent {agent_name} working...", False)
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
