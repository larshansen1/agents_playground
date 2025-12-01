"""
title: Workflow Execution Tool
author: system
version: 1.0
description: Execute a specific workflow directly by name
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
        cache_ttl_seconds: int = Field(
            default=60,
            description="Cache workflow data for N seconds",
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

    def _get_cached_or_fetch(
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

        # Fetch new data
        data = fetch_func()
        self._cache[cache_key] = (now, data)
        return data

    async def _fetch_workflows(self) -> list[dict]:
        """Fetch workflows from registry API."""

        def _fetch():
            response = requests.get(
                f"{self.valves.task_api_url}/admin/workflows",
                timeout=10,
                **self._get_ssl_config(),
            )
            response.raise_for_status()
            workflows: list[dict] = response.json().get("workflows", [])
            return workflows

        try:
            return await asyncio.to_thread(self._get_cached_or_fetch, "workflows", _fetch)
        except requests.exceptions.RequestException as e:
            msg = f"Failed to fetch workflows: {e!s}"
            raise RuntimeError(msg) from e

    async def _create_workflow_task(
        self, workflow_name: str, task_input: str, user_id: str | None = None
    ) -> dict[str, Any]:
        """Create a task for direct workflow execution."""
        payload = {
            "type": f"workflow:{workflow_name}",
            "input": {"description": task_input},
            "user_id": user_id,
        }

        try:
            response = await asyncio.to_thread(
                requests.post,
                f"{self.valves.task_api_url}/tasks",
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
            msg = f"Failed to create workflow task: {error_msg}"
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
                    msg = f"Workflow failed: {error_msg}"
                    raise RuntimeError(msg)

                # Emit status update if running
                if __event_emitter__:
                    await self._emit_status(
                        __event_emitter__, f"Workflow running... (Status: {status})", False
                    )

                await asyncio.sleep(self.valves.poll_interval)

            except requests.exceptions.RequestException as e:
                # Log error but continue polling (transient network issue?)
                print(f"Polling error: {e}")
                await asyncio.sleep(self.valves.poll_interval)

        msg = "Workflow timed out waiting for completion"
        raise TimeoutError(msg)

    async def _emit_status(self, emitter: Any, message: str, done: bool = False):
        """Helper to safely send UI updates via the event emitter."""
        if emitter:
            await emitter({"type": "status", "data": {"description": message, "done": done}})

    def _format_workflow_list(self, workflows: list[dict]) -> str:
        """Format list of workflows for display."""
        if not workflows:
            return "⚠️ **No workflows available**"

        lines = ["# Available Workflows\n"]
        for workflow in workflows:
            name = workflow.get("name", "unknown")
            description = workflow.get("description", "No description")
            strategy = workflow.get("strategy", "unknown")
            max_iterations = workflow.get("max_iterations")
            steps = workflow.get("steps", [])

            lines.append(f"**{name}**")
            lines.append(f"- Description: {description}")
            lines.append(
                f"- Strategy: {strategy}",
            )
            if max_iterations:
                lines.append(f"- Max Iterations: {max_iterations}")

            # Show step sequence
            if steps:
                step_names = [step.get("name", step.get("agent_type", "unknown")) for step in steps]
                lines.append(f"- Steps: {' → '.join(step_names)}")

            lines.append(f'- Usage: `@workflow {name} "your topic"`\n')

        lines.append("\n---\n")
        lines.append("**Note:** You can also use `@flow` for smart workflow selection.")

        return "\n".join(lines)

    async def workflow(  # noqa: PLR0911
        self,
        command: str = "",
        __user__: dict | None = None,
        __event_emitter__: Any = None,
    ) -> str:
        """
        Execute a specific workflow directly by name.

        Args:
            command: The command string containing workflow name and topic.
                     Format: "<workflow_name> <topic>"
            __user__: User context from Open WebUI
            __event_emitter__: Event emitter for UI status updates

        Returns:
            Workflow response or error message.
        """
        # Extract user ID
        user_id = __user__.get("id") if __user__ else None

        # Parse command
        parts = command.strip().split(maxsplit=1)

        # Case 1: No arguments - list workflows
        if not parts or not parts[0]:
            try:
                await self._emit_status(__event_emitter__, "Fetching workflows...", False)
                workflows = await self._fetch_workflows()
                await self._emit_status(__event_emitter__, "List retrieved", True)
                return self._format_workflow_list(workflows)
            except Exception as e:
                return f"❌ **Error fetching workflows**: {e!s}"

        workflow_name = parts[0]

        # Case 2: Workflow name provided but no topic
        if len(parts) < 2:
            return f"""⚠️ **Missing Topic**

Usage: `@workflow {workflow_name} "your topic"`

Example: `@workflow {workflow_name} "quantum computing applications"`
"""

        topic = parts[1]

        try:
            # 1. Create Workflow Task
            await self._emit_status(
                __event_emitter__, f"Starting workflow '{workflow_name}'...", False
            )

            try:
                task_response = await self._create_workflow_task(workflow_name, topic, user_id)
            except RuntimeError as e:
                # Check if it's an invalid workflow error
                if "Workflow" in str(e) and "not found" in str(e):
                    # Fetch available workflows to show helpful error
                    try:
                        workflows = await self._fetch_workflows()
                        workflow_list = self._format_workflow_list(workflows)
                        return f"""❌ **Workflow '{workflow_name}' not found**

{workflow_list}
"""
                    except Exception:  # nosec B110
                        pass  # Fallback to generic error
                raise e

            task_id = task_response["id"]

            # 2. Wait for completion
            await self._emit_status(
                __event_emitter__, f"Workflow '{workflow_name}' running...", False
            )
            final_task = await self._wait_for_task(task_id, __event_emitter__)

            # 3. Return result
            await self._emit_status(__event_emitter__, "Workflow complete!", True)

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
            await self._emit_status(__event_emitter__, "Workflow failed", True)
            return f"❌ **Error**: {e!s}"
