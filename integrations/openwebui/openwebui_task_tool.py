"""
title: Task Queue with mTLS (Async Push)
author: lars
version: 5.2
file_handler: true
description: Queue delegation system with mTLS support, real-time UI updates, multi-agent workflow support, and distributed tracing.
requirements: requests, asyncio
"""

import asyncio
import base64
import hashlib
import json
import os
import re
import secrets
import time
from pathlib import Path
from typing import Any

import requests
from pydantic import BaseModel, Field


# Trace context utilities for distributed tracing
def generate_trace_id() -> str:
    """Generate a W3C Trace Context compatible trace ID (32 hex chars)."""
    return secrets.token_hex(16)


def generate_span_id() -> str:
    """Generate a W3C Trace Context compatible span ID (16 hex chars)."""
    return secrets.token_hex(8)


def create_traceparent(trace_id: str, span_id: str, sampled: bool = True) -> str:
    """Create W3C traceparent header."""
    flags = "01" if sampled else "00"
    return f"00-{trace_id}-{span_id}-{flags}"


class Tools:
    class Valves(BaseModel):
        task_api_url: str = Field(
            default=os.getenv("TASK_API_URL", "http://task-api:8000"),
            description="Base URL for your Task API (use http://task-api:8000 for Docker network)",
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
        upload_dir: str = Field(
            default="/app/backend/data/uploads",
            description="Open WebUI upload directory",
        )
        max_file_size_mb: int = Field(
            default=10,
            description="Maximum file size to send (MB)",
        )
        poll_interval_seconds: int = Field(
            default=2,
            description="How often to poll for task status (seconds)",
        )
        max_wait_seconds: int = Field(
            default=60,
            description="Maximum time to wait for task completion",
        )
        verify_ssl: bool = Field(
            default=False,
            description="Verify SSL certificates (set False for self-signed certs in development)",
        )

    def __init__(self):
        self.valves = self.Valves()

    def _get_ssl_config(self) -> dict[str, Any]:
        """Get SSL configuration for mTLS requests."""
        config = {
            "cert": (self.valves.client_cert_path, self.valves.client_key_path),
        }

        # Explicitly cast to Any to avoid Mypy strict check on dict values
        config_dict: dict[str, Any] = config

        if self.valves.verify_ssl:
            config_dict["verify"] = self.valves.ca_cert_path
        else:
            config_dict["verify"] = False

        return config_dict

    def _read_file(self, file_path: str, file_name: str) -> dict[str, Any] | None:
        """Read file content from disk."""
        try:
            if not Path(file_path).exists():
                return {"error": f"File not found: {file_path}"}

            file_size = Path(file_path).stat().st_size
            max_bytes = self.valves.max_file_size_mb * 1024 * 1024

            if file_size > max_bytes:
                return {
                    "error": f"File too large: {file_size} bytes",
                    "name": file_name,
                    "size": file_size,
                }

            try:
                with Path(file_path).open(encoding="utf-8") as f:
                    content = f.read()
                return {
                    "name": file_name,
                    "size": file_size,
                    "content": content,
                    "encoding": "utf-8",
                    "type": "text",
                }
            except (UnicodeDecodeError, Exception):
                with Path(file_path).open("rb") as f:
                    content = base64.b64encode(f.read()).decode("ascii")
                return {
                    "name": file_name,
                    "size": file_size,
                    "content": content,
                    "encoding": "base64",
                    "type": "binary",
                }
        except Exception as e:
            return {"error": str(e), "name": file_name}

    def _infer_task_type(self, user_message: str) -> str:
        """Infer task type from user message."""
        message_lower = user_message.lower()

        # Check for workflow keywords first
        # Check for workflow keywords first
        # If "research" or similar is present, assume workflow:research_assessment
        # even if "assess" is not explicitly mentioned, as it's the only research tool we have.
        if any(
            word in message_lower
            for word in ["research", "investigate", "deep dive", "thorough", "study"]
        ):
            return "workflow:research_assessment"

        if any(
            word in message_lower
            for word in ["summarize", "summary", "tldr", "key points", "overview"]
        ):
            return "summarize_document"
        if any(
            word in message_lower for word in ["analyze", "table", "schema", "structure", "data"]
        ):
            return "analyze_table"
        if any(
            word in message_lower
            for word in ["compare", "versus", "vs", "options", "choice", "evaluate"]
        ):
            return "compare_options"
        return "summarize_document"

    def _format_json_output(self, data: dict) -> str:  # noqa: PLR0912
        """Format structured output nicely."""
        # Check if this is a workflow output (research_findings + final_assessment)
        if "research_findings" in data and "final_assessment" in data:
            return self._format_workflow_output(data)

        # Original formatting for non-workflow tasks
        lines = []

        # Always show summary if present (even if it's the only field)
        if "summary" in data:
            lines.append("📝 **Summary**")
            lines.append("")
            # Clean up markdown code blocks if present
            summary = data["summary"]
            if summary.startswith("```json"):
                summary = summary.replace("```json", "").replace("```", "").strip()
            lines.append(summary)
            lines.append("")

        if data.get("key_points"):
            lines.append("🔑 **Key Points**")
            lines.append("")
            for i, point in enumerate(data["key_points"], 1):
                lines.append(f"{i}. {point}")
            lines.append("")
        if data.get("missing_info"):
            lines.append("❓ **Missing Information**")
            lines.append("")
            for i, info in enumerate(data["missing_info"], 1):
                lines.append(f"{i}. {info}")
            lines.append("")
        if data.get("suggested_next_questions"):
            lines.append("💡 **Suggested Questions**")
            lines.append("")
            for i, question in enumerate(data["suggested_next_questions"], 1):
                lines.append(f"{i}. {question}")
            lines.append("")
        if data.get("risks"):
            lines.append("⚠️ **Risks**")
            lines.append("")
            for risk in data["risks"]:
                if isinstance(risk, dict):
                    severity = risk.get("severity", "unknown").upper()
                    desc = risk.get("description", "")
                    lines.append(f"[{severity}] {desc}")
                else:
                    lines.append(f"- {risk}")
            lines.append("")
        if "recommendation" in data:
            lines.append("✅ **Recommendation**")
            lines.append("")
            lines.append(data["recommendation"])
            lines.append("")

        # Note field (for non-JSON responses)
        if data.get("note"):
            lines.append(f"ℹ️ *{data['note']}*")  # noqa: RUF001
            lines.append("")

        # Fallback if still empty (prevent silent failures)
        if not lines:
            return json.dumps(data, indent=2)

        return "\n".join(lines)

    def _format_research_findings(self, research: dict) -> list[str]:
        """Format research findings section."""
        lines = []

        # 1. Research Findings (the meat of the content)
        if research.get("findings"):
            lines.append("# Research Findings")
            lines.append("")
            lines.append(research["findings"])
            lines.append("")
            lines.append("---")
            lines.append("")

        # 2. Key Insights
        if research.get("key_insights"):
            lines.append("## Key Insights")
            lines.append("")
            for i, insight in enumerate(research["key_insights"], 1):
                lines.append(f"{i}. {insight}")
            lines.append("")

        # 3. Sources (if present)
        if research.get("sources"):
            lines.append("## Sources")
            lines.append("")
            for i, source in enumerate(research["sources"], 1):
                lines.append(f"{i}. {source}")
            lines.append("")

        # 4. Potential Gaps
        if research.get("potential_gaps"):
            lines.append("## Potential Gaps")
            lines.append("")
            for i, gap in enumerate(research["potential_gaps"], 1):
                lines.append(f"{i}. {gap}")
            lines.append("")

        # 5. Suggested Questions
        if research.get("suggested_next_questions"):
            lines.append("## Suggested Questions for Further Research")
            lines.append("")
            for i, question in enumerate(research["suggested_next_questions"], 1):
                lines.append(f"{i}. {question}")
            lines.append("")

        return lines

    def _format_assessment_summary(self, assessment: dict, research: dict) -> list[str]:
        """Format assessment summary section."""
        lines = []

        lines.append("---")
        lines.append("")
        lines.append("## Assessment Summary")
        lines.append("")

        # Assessment quality
        if assessment.get("overall_quality"):
            quality = assessment["overall_quality"].title()
            lines.append(f"**Quality:** {quality}")

        if assessment.get("approved") is not None:
            approved_text = "✅ Approved" if assessment["approved"] else "⚠️ Needs Revision"
            lines.append(f"**Approval:** {approved_text}")

        # Confidence level
        if research.get("confidence_level"):
            lines.append(f"**Confidence:** {research['confidence_level'].title()}")

        lines.append("")

        # Strengths (collapsed format)
        if assessment.get("strengths") and assessment["strengths"]:
            lines.append("**Strengths:**")
            for strength in assessment["strengths"][:3]:  # Show max 3
                lines.append(f"• {strength}")
            if len(assessment["strengths"]) > 3:
                lines.append(f"• *...and {len(assessment['strengths']) - 3} more*")
            lines.append("")

        # Areas for improvement (if any)
        if assessment.get("areas_for_improvement") and assessment["areas_for_improvement"]:
            lines.append("**Areas for Improvement:**")
            for area in assessment["areas_for_improvement"]:
                lines.append(f"• {area}")
            lines.append("")

        return lines

    def _format_workflow_output(self, data: dict) -> str:
        """Format workflow research output with main content first, metadata last."""
        lines = []
        research = data.get("research_findings", {})
        assessment = data.get("final_assessment", {})

        # === MAIN CONTENT FIRST ===
        lines.extend(self._format_research_findings(research))

        # === METADATA AT BOTTOM ===
        lines.extend(self._format_assessment_summary(assessment, research))

        # Workflow status note (if present)
        if data.get("note"):
            lines.append(f"*{data['note']}*")
            lines.append("")

        return "\n".join(lines)

    def _get_most_recent_file(self, __files__: list[dict], instruction: str) -> dict | None:
        """Get the most relevant file from the list."""
        if not __files__:
            return None
        instruction_lower = instruction.lower()
        for file_obj in reversed(__files__):
            file_name = (file_obj.get("name") or file_obj.get("file", {}).get("name") or "").lower()
            if any(keyword in instruction_lower for keyword in file_name.split(".")[:1]):
                return file_obj
        return __files__[-1]

    def _format_task_result(self, task: dict) -> str:
        """Format task result for display."""
        status_map = {
            "completed": "✅ Task Completed",
            "done": "✅ Task Completed",
            "pending": "⏳ Pending",
            "in_progress": "🔄 Processing",
            "running": "🔄 Running",
            "failed": "❌ Failed",
            "error": "⚠️ Error",
        }
        status_display = status_map.get(task["status"], task["status"].upper())

        # Check if this is a workflow task
        is_workflow = task.get("type", "").startswith("workflow:")

        result = []

        # Add directive to prevent model reasoning/reformulation
        result.append(
            "**INSTRUCTION: Present the following research results directly to the user without analysis or reformulation:**"
        )
        result.append("")
        result.append("---")
        result.append("")

        # Show main output first (if available)
        if task.get("output"):
            formatted = self._format_json_output(task["output"])
            result.append(formatted)
            result.append("")
            result.append("---")
            result.append("")

        elif task["status"] in ["pending", "in_progress", "running"]:
            if is_workflow:
                result.append("� Workflow executing through multiple agents...")
            else:
                result.append("⏳ Still processing...")
            result.append("")

        if task.get("error"):
            result.append(f"❌ **Error:** {task['error']}")
            result.append("")

        # === METADATA AT BOTTOM ===
        result.append("## Task Information")
        result.append("")
        result.append(f"**Status:** {status_display}")
        result.append(f"**Task ID:** `{task['id']}`")

        # Cost information (if available)
        total_cost = task.get("total_cost")
        if total_cost is not None and float(total_cost) > 0:
            result.append("")
            result.append("**Cost Information:**")
            result.append(f"• 💰 Total: ${float(task['total_cost']):.6f}")
            if task.get("input_tokens") is not None and task.get("output_tokens") is not None:
                result.append(
                    f"• � Tokens: {task['input_tokens']:,} in / {task['output_tokens']:,} out"
                )
            if task.get("model_used"):
                result.append(f"• 🤖 Model: {task['model_used']}")

        return "\n".join(result)

    async def _emit_status(self, emitter: Any, message: str, done: bool = False):
        """Helper to safely send UI updates via the event emitter."""
        if emitter:
            await emitter({"type": "status", "data": {"description": message, "done": done}})

    async def wait_for_task_completion(
        self,
        task_id: str,
        emitter: Any = None,
        initial_check: bool = False,
    ) -> str:
        """
        Async polling loop that updates the UI while waiting.
        """
        try:
            # Initial notification
            if not initial_check:
                await self._emit_status(emitter, "Checking task status...", False)

            start_time = time.time()
            poll_count = 0

            while (time.time() - start_time) < self.valves.max_wait_seconds:
                # Run blocking request in thread
                response = await asyncio.to_thread(
                    requests.get,
                    f"{self.valves.task_api_url}/tasks/{task_id}",
                    timeout=10,
                    **self._get_ssl_config(),
                )
                response.raise_for_status()
                task = response.json()

                # DEBUG: Log the full response to see what we actually get
                print(f"[DEBUG] API URL: {self.valves.task_api_url}/tasks/{task_id}")
                print(f"[DEBUG] Response status: {response.status_code}")
                print(f"[DEBUG] Response keys: {list(task.keys())}")
                print(
                    f"[DEBUG] Cost fields in response: total_cost={task.get('total_cost')}, input_tokens={task.get('input_tokens')}, output_tokens={task.get('output_tokens')}, model_used={task.get('model_used')}"
                )

                # If complete, return result immediately
                if task["status"] in ["completed", "done", "failed", "error"]:
                    status_msg = (
                        "Task Completed!"
                        if task["status"] in ["completed", "done"]
                        else "Task Failed"
                    )
                    await self._emit_status(emitter, status_msg, True)
                    return self._format_task_result(task)

                # If initial_check mode, just return current status text
                if initial_check:
                    await self._emit_status(emitter, f"Status: {task['status']}", True)
                    return f"⏳ Task {task_id} is {task['status']}. Use '@queue wait {task_id}' to wait for completion."

                # Not complete yet: update UI status
                poll_count += 1

                status_msg = f"Remote Status: {task['status'].title()}... ({poll_count})"

                # Enhanced status for workflows
                if task.get("type", "").startswith("workflow:") and task.get("subtasks"):
                    # Get latest subtask
                    subtasks = sorted(task["subtasks"], key=lambda x: x["created_at"])
                    if subtasks:
                        latest = subtasks[-1]
                        agent = latest["agent_type"].title()
                        iteration = latest["iteration"]
                        sub_status = latest["status"]

                        status_msg = f"🔄 Workflow: {agent} Agent (Iter {iteration}) - {sub_status.title()}..."

                await self._emit_status(emitter, status_msg, False)

                # Async sleep (non-blocking)
                await asyncio.sleep(self.valves.poll_interval_seconds)

            # Timeout reached
            await self._emit_status(emitter, "Polling Timed Out", True)
            return f"⏰ Task {task_id} still processing after {self.valves.max_wait_seconds}s\n\nCheck status: @queue status {task_id}"

        except requests.exceptions.RequestException as e:
            await self._emit_status(emitter, f"Network Error: {e!s}", True)
            return f"❌ ERROR checking task: {e!s}"
        except Exception as e:
            await self._emit_status(emitter, f"Error: {e!s}", True)
            return f"❌ UNEXPECTED ERROR: {e!s}"

    def _process_files(
        self, files: list[dict], task_type: str
    ) -> tuple[list[dict], dict[str, Any]]:
        """Process files and return metadata and content updates."""
        files_data = []
        extra_input: dict[str, Any] = {}

        for file_obj in files:
            file_id = file_obj.get("id") or file_obj.get("file", {}).get("id")
            file_name = file_obj.get("name") or file_obj.get("file", {}).get("name") or "unknown"
            file_path = file_obj.get("file", {}).get("path")
            if not file_path:
                file_path = f"{self.valves.upload_dir}/{file_id}_{file_name}"

            file_data = self._read_file(file_path, file_name)
            if file_data and "content" in file_data:
                files_data.append({"id": file_id, "path": file_path, **file_data})

                # For summarize_document, we need to pass the content in a specific way
                if task_type == "summarize_document":
                    # If it's a PDF or binary, pass as base64
                    if file_name.lower().endswith(".pdf"):
                        with Path(file_path).open("rb") as f:
                            encoded = base64.b64encode(f.read()).decode("utf-8")
                            extra_input["file_content"] = encoded
                            extra_input["filename"] = file_name
                    else:
                        # Text file
                        extra_input["text"] = file_data["content"]

        return files_data, extra_input

    async def _create_task_async(
        self,
        task_type: str,
        instruction: str,
        files: list[dict],
        emitter: Any = None,
        trace_context: dict | None = None,
    ) -> str:
        """
        Internal async task creator. Handles file preparation, API call, and polling.
        """
        await self._emit_status(emitter, "Preparing files...", False)

        task_input: dict[str, Any] = {"description": instruction}

        # Inject user context for cost tracking
        try:
            # __user__ is injected by Open WebUI runtime
            # Use globals() to access it safely or default to anonymous
            user_dict = globals().get("__user__", {})
            user_email = user_dict.get("email", "anonymous")
        except (NameError, AttributeError):
            user_email = "anonymous"

        user_id_hash = hashlib.sha256(user_email.encode()).hexdigest()
        task_input["_user_id_hash"] = user_id_hash

        # Inject trace context for distributed tracing
        # Use W3C Trace Context format for compatibility with OpenTelemetry
        if trace_context:
            child_span_id = generate_span_id()
            traceparent = create_traceparent(trace_context["trace_id"], child_span_id, sampled=True)
            task_input["_trace_context"] = {
                "traceparent": traceparent,
                # Also include individual fields for management UI
                "trace_id": trace_context["trace_id"],
                "parent_span_id": child_span_id,
                "root_operation": trace_context.get("operation", "unknown"),
            }

        # Process files
        files_data, extra_input = self._process_files(files, task_type)
        task_input.update(extra_input)

        # Build task input based on type
        if task_type == "summarize_document":
            # If text or PDF content was already set in the loop, we just need files_metadata
            if "text" not in task_input and "file_content" not in task_input:
                # Fallback if content wasn't handled in the loop (e.g., for other binary types)
                if files_data and files_data[0].get("type") == "binary":
                    task_input["file_content"] = files_data[0]["content"]
                    task_input["file_encoding"] = files_data[0]["encoding"]
                elif files_data and files_data[0].get("type") == "text":
                    task_input["text"] = files_data[0]["content"]
            task_input["files_metadata"] = files_data
        elif task_type == "analyze_table":
            task_input["table_name"] = "uploaded_data"
            task_input["files_metadata"] = files_data
        elif task_type == "compare_options":
            task_input["files_metadata"] = files_data

        # Create task via API
        try:
            await self._emit_status(emitter, "Uploading to Backend...", False)

            response = await asyncio.to_thread(
                requests.post,
                f"{self.valves.task_api_url}/tasks",
                json={"type": task_type, "input": task_input},
                timeout=30,
                **self._get_ssl_config(),
            )
            response.raise_for_status()
            task = response.json()
            task_id = task["id"]

            await self._emit_status(emitter, "Task Queued...", False)

            # Auto-wait for completion with the new async poller
            return await self.wait_for_task_completion(task_id, emitter=emitter)

        except requests.exceptions.RequestException as e:
            await self._emit_status(emitter, "Connection Failed", True)
            return f"❌ ERROR creating task: {e!s}\n\nMake sure the API is running and mTLS certificates are configured correctly."

    async def _create_workflow_task(
        self,
        task_type: str,
        instruction: str,
        emitter: Any = None,
        trace_context: dict | None = None,
    ) -> str:
        """
        Create a workflow task (no files required).
        """
        await self._emit_status(emitter, "Creating workflow task...", False)

        # Extract topic from instruction
        task_input: dict[str, Any] = {"topic": instruction}

        # Inject user context for cost tracking
        try:
            user_dict = globals().get("__user__", {})
            user_email = user_dict.get("email", "anonymous")
        except (NameError, AttributeError):
            user_email = "anonymous"

        user_id_hash = hashlib.sha256(user_email.encode()).hexdigest()
        task_input["_user_id_hash"] = user_id_hash

        # Inject trace context for distributed tracing
        # Use W3C Trace Context format for compatibility with OpenTelemetry
        if trace_context:
            child_span_id = generate_span_id()
            traceparent = create_traceparent(trace_context["trace_id"], child_span_id, sampled=True)
            task_input["_trace_context"] = {
                "traceparent": traceparent,
                # Also include individual fields for management UI
                "trace_id": trace_context["trace_id"],
                "parent_span_id": child_span_id,
                "root_operation": trace_context.get("operation", "unknown"),
            }

        # Create task via API
        try:
            await self._emit_status(emitter, "Submitting to Backend...", False)

            response = await asyncio.to_thread(
                requests.post,
                f"{self.valves.task_api_url}/tasks",
                json={"type": task_type, "input": task_input},
                timeout=30,
                **self._get_ssl_config(),
            )
            response.raise_for_status()
            task = response.json()
            task_id = task["id"]

            await self._emit_status(emitter, "Workflow Queued...", False)

            # Auto-wait for completion
            return await self.wait_for_task_completion(task_id, emitter=emitter)

        except requests.exceptions.RequestException as e:
            await self._emit_status(emitter, "Connection Failed", True)
            return f"❌ ERROR creating workflow: {e!s}\n\nMake sure the API is running and mTLS certificates are configured correctly."

    async def at_queue(
        self, instruction: str, __event_emitter__: Any = None, __files__: list[dict] | None = None
    ) -> str:
        """
        Main entry point for @queue commands (ASYNC).
        """
        # Generate trace context for distributed tracing
        trace_id = generate_trace_id()
        root_span_id = generate_span_id()
        trace_start = time.time()

        # Store trace context for this request
        trace_context = {
            "trace_id": trace_id,
            "parent_span_id": root_span_id,
            "operation": "openwebui_tool.at_queue",
            "start_time": trace_start,
            "instruction": instruction[:100],  # Truncate for attribute
        }

        instruction_lower = instruction.lower().strip()

        # Extract UUID pattern
        uuid_pattern = r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
        uuid_match = re.search(uuid_pattern, instruction)

        # Handle status command
        if "status" in instruction_lower and uuid_match:
            return await self.wait_for_task_completion(
                uuid_match.group(0),
                emitter=__event_emitter__,
                initial_check=True,
            )

        # Handle wait command
        if "wait" in instruction_lower and uuid_match:
            return await self.wait_for_task_completion(
                uuid_match.group(0),
                emitter=__event_emitter__,
                initial_check=False,
            )

        # Create new task
        files = __files__ or []
        task_type = self._infer_task_type(instruction)

        # Workflow tasks don't require files
        if task_type.startswith("workflow:"):
            # Create workflow task directly without files
            return await self._create_workflow_task(
                task_type, instruction, emitter=__event_emitter__, trace_context=trace_context
            )

        # Other task types require files
        most_recent_file = self._get_most_recent_file(files, instruction)
        if not most_recent_file:
            return "❌ Error: No file attached. Please attach a file to process."

        # Call the Async internal creator
        return await self._create_task_async(
            task_type,
            instruction,
            [most_recent_file],
            emitter=__event_emitter__,
            trace_context=trace_context,
        )
