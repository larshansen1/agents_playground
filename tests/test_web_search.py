"""Tests for web search tool."""

import os
from unittest.mock import MagicMock, patch

import pytest
import requests

from app.tools.web_search import WebSearchTool


class TestWebSearchTool:
    """Test suite for WebSearchTool."""

    def test_tool_initialization(self):
        """Test web search tool initializes correctly."""
        tool = WebSearchTool()
        assert tool.tool_name == "web_search"
        assert "search" in tool.description.lower()

    def test_get_schema(self):
        """Test web search schema is valid."""
        tool = WebSearchTool()
        schema = tool.get_schema()

        assert schema["type"] == "object"
        assert "query" in schema["properties"]
        assert "max_results" in schema["properties"]
        assert "query" in schema["required"]

    def test_max_results_default(self):
        """Test max_results has default value in schema."""
        tool = WebSearchTool()
        schema = tool.get_schema()

        assert schema["properties"]["max_results"]["default"] == 5
        assert schema["properties"]["max_results"]["minimum"] == 1
        assert schema["properties"]["max_results"]["maximum"] == 20

    def test_missing_api_key_returns_error(self):
        """Test execution without API key returns error."""
        with patch.dict(os.environ, {}, clear=True):
            tool = WebSearchTool()
            result = tool.execute(query="test query")

            assert result["success"] is False
            assert "BRAVE_API_KEY" in result["error"]
            assert result["result"] is None

    @patch("app.tools.web_search.requests.get")
    def test_successful_search(self, mock_get):
        """Test successful web search with mocked API."""
        # Mock API response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "web": {
                "results": [
                    {
                        "title": "Result 1",
                        "url": "https://example.com/1",
                        "description": "Description 1",
                    },
                    {
                        "title": "Result 2",
                        "url": "https://example.com/2",
                        "description": "Description 2",
                    },
                ]
            }
        }
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {"BRAVE_API_KEY": "test_key"}):
            tool = WebSearchTool()
            result = tool.execute(query="test query")

            assert result["success"] is True
            assert len(result["result"]["results"]) == 2
            assert result["result"]["results"][0]["title"] == "Result 1"
            assert result["result"]["results"][0]["url"] == "https://example.com/1"
            assert result["error"] is None

    @patch("app.tools.web_search.requests.get")
    def test_search_with_max_results(self, mock_get):
        """Test search with custom max_results."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"web": {"results": []}}
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {"BRAVE_API_KEY": "test_key"}):
            tool = WebSearchTool()
            tool.execute(query="test", max_results=10)

            # Verify API was called with correct parameters
            mock_get.assert_called_once()
            call_kwargs = mock_get.call_args.kwargs
            assert call_kwargs["params"]["count"] == 10

    @patch("app.tools.web_search.requests.get")
    def test_timeout_error(self, mock_get):
        """Test timeout error handling."""
        mock_get.side_effect = requests.exceptions.Timeout()

        with patch.dict(os.environ, {"BRAVE_API_KEY": "test_key"}):
            tool = WebSearchTool()
            result = tool.execute(query="test query")

            assert result["success"] is False
            assert "timed out" in result["error"].lower()
            assert result["result"] is None

    @patch("app.tools.web_search.requests.get")
    def test_http_error(self, mock_get):
        """Test HTTP error handling."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404")
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {"BRAVE_API_KEY": "test_key"}):
            tool = WebSearchTool()
            result = tool.execute(query="test query")

            assert result["success"] is False
            assert "HTTP error" in result["error"]
            assert result["result"] is None

    @patch("app.tools.web_search.requests.get")
    def test_general_exception(self, mock_get):
        """Test general exception handling."""
        mock_get.side_effect = Exception("Network error")

        with patch.dict(os.environ, {"BRAVE_API_KEY": "test_key"}):
            tool = WebSearchTool()
            result = tool.execute(query="test query")

            assert result["success"] is False
            assert "failed" in result["error"].lower()
            assert result["result"] is None

    def test_missing_query_parameter(self):
        """Test missing query parameter raises ValueError."""
        tool = WebSearchTool()

        with pytest.raises(ValueError):
            tool.execute()

    def test_invalid_max_results_too_high(self):
        """Test max_results above maximum raises error."""
        tool = WebSearchTool()

        with pytest.raises(ValueError):
            tool.execute(query="test", max_results=100)

    def test_invalid_max_results_too_low(self):
        """Test max_results below minimum raises error."""
        tool = WebSearchTool()

        with pytest.raises(ValueError):
            tool.execute(query="test", max_results=0)

    def test_result_format(self):
        """Test result follows standard format."""
        with patch.dict(os.environ, {}, clear=True):
            tool = WebSearchTool()
            result = tool.execute(query="test")

            assert "success" in result
            assert "result" in result
            assert "error" in result
            assert "metadata" in result

    @patch("app.tools.web_search.requests.get")
    def test_metadata_includes_query(self, mock_get):
        """Test metadata includes original query."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"web": {"results": []}}
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {"BRAVE_API_KEY": "test_key"}):
            tool = WebSearchTool()
            result = tool.execute(query="test query")

            assert result["result"]["query"] == "test query"
            assert result["metadata"]["api"] == "brave"

    @patch("app.tools.web_search.requests.get")
    def test_empty_results(self, mock_get):
        """Test handling of empty search results."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"web": {"results": []}}
        mock_get.return_value = mock_response

        with patch.dict(os.environ, {"BRAVE_API_KEY": "test_key"}):
            tool = WebSearchTool()
            result = tool.execute(query="very_specific_nonexistent_query")

            assert result["success"] is True
            assert result["result"]["results"] == []
            assert result["metadata"]["count"] == 0
