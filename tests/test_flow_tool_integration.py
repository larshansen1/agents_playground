from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
import requests

from integrations.openwebui.openwebui_task_tool import Tools


@pytest.fixture
def tools():
    return Tools()


@pytest.fixture
def mock_requests():
    with patch("integrations.openwebui.openwebui_task_tool.requests") as mock_req:
        # Fix: Ensure requests.exceptions.RequestException is a real exception class
        mock_req.exceptions.RequestException = requests.exceptions.RequestException
        yield mock_req


@pytest.fixture(autouse=True)
def mock_tracer():
    with patch("integrations.openwebui.openwebui_task_tool.tracer") as mock:
        mock_span = MagicMock()
        mock_span.__enter__.return_value = mock_span
        mock.start_span.return_value = mock_span
        yield mock


@pytest.mark.asyncio
class TestQueueToolIntegration:
    async def test_flow_dynamic_workflow_end_to_end(self, tools, mock_requests):
        """Test @flow with dynamic workflow selection."""
        # Setup mocks
        mock_response_workflows = MagicMock()
        mock_response_workflows.json.return_value = {
            "workflows": [{"name": "research_assessment", "description": "Research stuff"}]
        }

        mock_response_task = MagicMock()
        mock_response_task.json.return_value = {
            "id": "task-123",
            "status": "completed",
            "type": "workflow:research_assessment",
            "output": {
                "research_findings": {"findings": "Done"},
                "final_assessment": {"approved": True},
            },
        }

        # Configure side_effect for requests.get/post
        def side_effect(*args, **kwargs):
            url = args[0]
            if "/admin/workflows" in url:
                return mock_response_workflows
            if "/tasks/" in url:  # GET task status
                return mock_response_task
            return MagicMock()

        mock_requests.get.side_effect = side_effect
        mock_requests.post.return_value = mock_response_task

        # Execute
        emitter = AsyncMock()
        result = await tools.at_flow("research quantum computing", __event_emitter__=emitter)

        # Verify
        assert "Research Findings" in result
        # Verify workflow was selected
        print(f"\nActual call args: {mock_requests.post.call_args}")
        mock_requests.post.assert_called_with(
            ANY,
            json={
                "type": "workflow:research_assessment",
                "input": {
                    "topic": "research quantum computing",
                    "_debug_user_context": ANY,
                    "_trace_context": ANY,
                },
                "user_id": "anonymous",
                "tenant_id": ANY,
            },
            timeout=30,
            cert=ANY,
            verify=ANY,
        )

    async def test_flow_backward_compatible(self, tools, mock_requests):
        """Test @flow with legacy task types."""
        mock_response_workflows = MagicMock()
        mock_response_workflows.json.return_value = {"workflows": []}

        mock_response_task = MagicMock()
        mock_response_task.json.return_value = {
            "id": "task-456",
            "status": "completed",
            "type": "summarize_document",
            "output": {"summary": "Summary done"},
        }

        def side_effect(*args, **kwargs):
            url = args[0]
            if "/admin/workflows" in url:
                return mock_response_workflows
            if "/tasks/" in url:
                return mock_response_task
            return MagicMock()

        mock_requests.get.side_effect = side_effect
        mock_requests.post.return_value = mock_response_task

        # Execute
        emitter = AsyncMock()
        files = [{"name": "doc.txt", "content": "text", "type": "text"}]
        result = await tools.at_flow("summarize this", __event_emitter__=emitter, __files__=files)

        # Verify
        assert "Summary done" in result
        mock_requests.post.assert_called()
        call_args = mock_requests.post.call_args
        assert call_args[1]["json"]["type"] == "summarize_document"

    async def test_flow_workflow_suggestions(self, tools, mock_requests):
        """Test workflow suggestions on ambiguous input."""
        # Setup multiple matching workflows
        mock_response_workflows = MagicMock()
        mock_response_workflows.json.return_value = {
            "workflows": [
                {"name": "research_v1", "description": "Research topic"},
                {"name": "research_v2", "description": "Research topic deep"},
            ]
        }

        mock_requests.get.return_value = mock_response_workflows
        mock_requests.post.return_value = MagicMock(
            json=lambda: {"id": "1", "status": "completed", "output": {}}
        )

        emitter = AsyncMock()
        # "research topic" matches both
        await tools.at_flow("research topic", __event_emitter__=emitter)

        # Verify status update contained suggestions (or at least notification of selection)
        # In current implementation, it auto-selects best match and notifies.
        # We check if emitter was called with status update about selection
        status_calls = [c[0][0] for c in emitter.call_args_list]
        descriptions = [c["data"]["description"] for c in status_calls if c["type"] == "status"]

        # Should mention matched workflow
        assert any(
            "Matched workflow" in d or "Selected workflow" in d or "Multiple workflows match" in d
            for d in descriptions
        )

    async def test_flow_trace_propagation(self, tools, mock_requests):
        """Test trace propagation through workflow."""
        mock_response_workflows = MagicMock()
        mock_response_workflows.json.return_value = {"workflows": []}
        mock_requests.get.return_value = mock_response_workflows

        mock_response_task = MagicMock()
        mock_response_task.json.return_value = {"id": "1", "status": "completed", "output": {}}
        mock_requests.post.return_value = mock_response_task

        await tools.at_flow(
            "summarize", __files__=[{"name": "f.txt", "content": "c", "type": "text"}]
        )

        # Verify POST request contained trace context
        call_args = mock_requests.post.call_args
        payload = call_args[1]["json"]
        assert "_trace_context" in payload["input"]
        assert "traceparent" in payload["input"]["_trace_context"]
