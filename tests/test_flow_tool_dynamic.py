from unittest.mock import MagicMock, Mock, patch

import pytest
import requests

from integrations.openwebui.openwebui_flow import Tools


@pytest.fixture
def tools():
    return Tools()


@pytest.fixture
def mock_api():
    with patch("integrations.openwebui.openwebui_flow.requests.get") as mock_get:
        yield mock_get


@pytest.fixture(autouse=True)
def mock_tracer():
    with patch("integrations.openwebui.openwebui_flow.tracer") as mock:
        mock_span = MagicMock()
        mock_span.__enter__.return_value = mock_span
        mock.start_span.return_value = mock_span
        yield mock


@pytest.mark.asyncio
class TestSmartWorkflowSelection:
    async def test_exact_workflow_name_match(self, tools, mock_api):
        """Test exact workflow name in instruction."""
        # Mock workflow registry response
        mock_response = Mock()
        mock_response.json.return_value = {
            "workflows": [
                {"name": "research_assessment", "description": "Research stuff"},
                {"name": "simple_sequential", "description": "Simple stuff"},
            ]
        }
        mock_api.return_value = mock_response

        # Test exact match
        result = await tools._smart_workflow_selection("workflow:simple_sequential")
        assert result == "workflow:simple_sequential"

        # Test @flow command match
        result = await tools._smart_workflow_selection("@flow simple_sequential do something")
        assert result == "workflow:simple_sequential"

    async def test_keyword_matching(self, tools, mock_api):
        """Test keyword-based workflow matching."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "workflows": [
                {"name": "deep_research", "description": "Deep investigation into complex topics"},
                {"name": "quick_summary", "description": "Quick summary of text"},
            ]
        }
        mock_api.return_value = mock_response

        # Test keyword match
        result = await tools._smart_workflow_selection("investigation into AI safety")
        assert result == "workflow:deep_research"

    async def test_multiple_matches_best_selected(self, tools, mock_api):
        """Test best match selected with multiple options."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "workflows": [
                {"name": "research_v1", "description": "Basic research"},
                {"name": "research_v2", "description": "Advanced research with deep analysis"},
            ]
        }
        mock_api.return_value = mock_response

        # "deep analysis" should match v2 better
        result = await tools._smart_workflow_selection("do deep analysis on this")
        assert result == "workflow:research_v2"

    async def test_no_match_uses_default(self, tools, mock_api):
        """Test fallback to default workflow."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "workflows": [{"name": "custom_flow", "description": "Something unrelated"}]
        }
        mock_api.return_value = mock_response

        # Should fall back to legacy inference
        result = await tools._smart_workflow_selection("summarize this document")
        assert result == "summarize_document"

        # Should fall back to research_assessment if research keyword present but no better match
        # (Assuming legacy logic handles "research" -> "workflow:research_assessment")
        result = await tools._smart_workflow_selection("research quantum physics")
        assert result == "workflow:research_assessment"

    async def test_empty_workflow_registry(self, tools, mock_api):
        """Test behavior when no workflows registered."""
        mock_response = Mock()
        mock_response.json.return_value = {"workflows": []}
        mock_api.return_value = mock_response

        result = await tools._smart_workflow_selection("research something")
        # Should fallback to legacy logic
        assert result == "workflow:research_assessment"


@pytest.mark.asyncio
class TestBackwardCompatibility:
    async def test_summarize_task_still_works(self, tools, mock_api):
        """Test @flow summarize creates summarize_document task."""
        mock_response = Mock()
        mock_response.json.return_value = {"workflows": []}
        mock_api.return_value = mock_response

        result = await tools._smart_workflow_selection("summarize this pdf")
        assert result == "summarize_document"

    async def test_analyze_task_still_works(self, tools, mock_api):
        """Test @flow analyze creates analyze_table task."""
        mock_response = Mock()
        mock_response.json.return_value = {"workflows": []}
        mock_api.return_value = mock_response

        result = await tools._smart_workflow_selection("analyze this table")
        assert result == "analyze_table"

    async def test_compare_task_still_works(self, tools, mock_api):
        """Test @flow compare creates compare_options task."""
        mock_response = Mock()
        mock_response.json.return_value = {"workflows": []}
        mock_api.return_value = mock_response

        result = await tools._smart_workflow_selection("compare option A vs B")
        assert result == "compare_options"


@pytest.mark.asyncio
class TestQueueCaching:
    async def test_workflow_list_cached(self, tools, mock_api):
        """Test workflow list cached for performance."""
        mock_response = Mock()
        mock_response.json.return_value = {"workflows": [{"name": "cached_flow"}]}
        mock_api.return_value = mock_response

        # First call
        await tools._smart_workflow_selection("test")
        assert mock_api.call_count == 1

        # Second call (should be cached)
        await tools._smart_workflow_selection("test")
        assert mock_api.call_count == 1

    async def test_cache_ttl_respected(self, tools, mock_api):
        """Test cache expires after TTL."""
        mock_response = Mock()
        mock_response.json.return_value = {"workflows": [{"name": "cached_flow"}]}
        mock_api.return_value = mock_response

        # Set short TTL
        tools.valves.cache_ttl_seconds = 0.1

        # First call
        await tools._smart_workflow_selection("test")
        assert mock_api.call_count == 1

        # Wait for expiry
        import time

        time.sleep(0.2)

        # Second call (should fetch again)
        await tools._smart_workflow_selection("test")
        assert mock_api.call_count == 2


@pytest.mark.asyncio
class TestQueueErrorHandling:
    async def test_api_error_fallback(self, tools, mock_api):
        """Test fallback when API unavailable."""
        mock_api.side_effect = requests.exceptions.RequestException("API Error")

        # Should not raise exception, but fallback to legacy
        result = await tools._smart_workflow_selection("summarize this")
        assert result == "summarize_document"
