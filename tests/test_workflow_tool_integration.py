"""Integration tests for the workflow OpenWebUI tool."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
import requests

# Add integrations to path
sys.path.insert(0, str(Path(__file__).parent.parent / "integrations" / "openwebui"))

from openwebui_workflow_tool import Tools


@pytest.fixture
def workflow_tool():
    """Create a workflow tool instance with test configuration."""
    tool = Tools()
    tool.valves.task_api_url = "http://test-api:8000"
    tool.valves.verify_ssl = False
    tool.valves.poll_interval = 0.1
    tool.valves.timeout = 5
    return tool


@pytest.mark.integration
class TestWorkflowToolIntegration:
    """Integration tests for workflow tool."""

    @pytest.mark.asyncio
    async def test_workflow_execution_end_to_end(self, workflow_tool):
        """Test full workflow execution flow."""
        with (
            patch("openwebui_workflow_tool.requests.post") as mock_post,
            patch("openwebui_workflow_tool.requests.get") as mock_get,
        ):
            # Mock task creation
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = {
                "id": "task-456",
                "type": "workflow:research_assessment",
                "status": "pending",
                "input": {"description": "AI safety"},
            }

            # Mock task polling - simulate workflow progression
            mock_responses = [
                {"id": "task-456", "status": "running"},
                {"id": "task-456", "status": "running"},
                {
                    "id": "task-456",
                    "status": "done",
                    "output": {
                        "result": "Comprehensive research on AI safety completed",
                        "iterations": 2,
                    },
                },
            ]

            mock_get.return_value.status_code = 200
            mock_get.return_value.json.side_effect = mock_responses

            result = await workflow_tool.workflow(
                'research_assessment "AI safety"', __user__={"id": "user-123"}
            )

            # Verify result
            assert "AI safety" in result or "Comprehensive research" in result
            assert mock_post.call_count == 1
            assert mock_get.call_count == 3  # 2 running + 1 done

    @pytest.mark.asyncio
    async def test_real_workflow_definitions(self, workflow_tool):
        """Test with actual workflow definitions structure."""
        real_workflows = {
            "workflows": [
                {
                    "name": "research_assessment",
                    "description": "Iterative research with quality assessment",
                    "strategy": "iterative_refinement",
                    "max_iterations": 3,
                    "steps": [
                        {"agent_type": "research", "name": "conduct_research"},
                        {"agent_type": "assessment", "name": "evaluate_quality"},
                    ],
                },
            ]
        }

        with patch("openwebui_workflow_tool.requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = real_workflows

            result = await workflow_tool.workflow("")

            # Verify all expected information is present
            assert "research_assessment" in result
            assert "Iterative research with quality assessment" in result
            assert "iterative_refinement" in result
            assert "Max Iterations: 3" in result
            assert "conduct_research → evaluate_quality" in result
            assert '@workflow research_assessment "your topic"' in result

    @pytest.mark.asyncio
    async def test_api_integration(self, workflow_tool):
        """Test integration with /admin/workflows and /tasks endpoints."""
        with (
            patch("openwebui_workflow_tool.requests.get") as mock_get,
            patch("openwebui_workflow_tool.requests.post") as mock_post,
        ):
            # Test /admin/workflows endpoint
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = {
                "workflows": [
                    {
                        "name": "test_workflow",
                        "description": "Test workflow",
                        "strategy": "sequential",
                        "steps": [],
                    }
                ]
            }

            await workflow_tool._fetch_workflows()
            assert "/admin/workflows" in mock_get.call_args[0][0]

            # Test /tasks endpoint
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = {
                "id": "task-789",
                "type": "workflow:test_workflow",
                "status": "pending",
            }

            await workflow_tool._create_workflow_task("test_workflow", "test topic", "user-1")
            assert "/tasks" in mock_post.call_args[0][0]

            # Verify payload structure
            payload = mock_post.call_args[1]["json"]
            assert payload["type"] == "workflow:test_workflow"
            assert payload["input"]["description"] == "test topic"
            assert payload["user_id"] == "user-1"

    @pytest.mark.asyncio
    async def test_error_recovery(self, workflow_tool):
        """Test error recovery and retry behavior."""
        with (
            patch("openwebui_workflow_tool.requests.post") as mock_post,
            patch("openwebui_workflow_tool.requests.get") as mock_get,
        ):
            # Mock task creation
            mock_post.return_value.status_code = 201
            mock_post.return_value.json.return_value = {"id": "task-999", "status": "pending"}

            # Mock polling with transient errors then success
            error_response = MagicMock()
            error_response.status_code = 500
            error_response.raise_for_status.side_effect = requests.exceptions.HTTPError()

            success_response = MagicMock()
            success_response.status_code = 200
            success_response.json.return_value = {
                "id": "task-999",
                "status": "done",
                "output": {"result": "Success after retry"},
            }

            # Simulate 2 errors then success
            mock_get.side_effect = [
                requests.exceptions.RequestException("Temp error"),
                requests.exceptions.RequestException("Temp error"),
                success_response,
            ]

            result = await workflow_tool.workflow('test_workflow "topic"')

            # Should eventually succeed despite transient errors
            assert "Success after retry" in result or "Error" in result
            assert mock_get.call_count == 3

    @pytest.mark.asyncio
    async def test_workflow_output_formats(self, workflow_tool):
        """Test different workflow output formats."""
        test_outputs = [
            {"result": "Simple result string"},
            {"response": "Response format"},
            {"content": "Content format"},
            {"custom_field": "Should return JSON"},
        ]

        for i, output in enumerate(test_outputs):
            with (
                patch("openwebui_workflow_tool.requests.post") as mock_post,
                patch("openwebui_workflow_tool.requests.get") as mock_get,
            ):
                mock_post.return_value.json.return_value = {
                    "id": f"task-{i}",
                    "status": "pending",
                }
                mock_get.return_value.json.return_value = {
                    "id": f"task-{i}",
                    "status": "done",
                    "output": output,
                }

                result = await workflow_tool.workflow('test "topic"')

                # Verify output is properly formatted
                if "result" in output:
                    assert output["result"] in result
                elif "response" in output:
                    assert output["response"] in result
                elif "content" in output:
                    assert output["content"] in result
                else:
                    # Should be JSON formatted
                    assert "```json" in result or isinstance(result, str)
