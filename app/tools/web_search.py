"""Web search tool using Brave Search API."""

import os
from typing import Any

import requests
import structlog

from app.tools.base import Tool

logger = structlog.get_logger()


class WebSearchTool(Tool):
    """
    Web search tool using Brave Search API.

    Requires BRAVE_API_KEY environment variable to be set.
    """

    def __init__(self):
        super().__init__(
            tool_name="web_search",
            description="Search the web using Brave Search API",
        )
        self.api_key = os.getenv("BRAVE_API_KEY")

    def get_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query string",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results to return",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20,
                },
            },
            "required": ["query"],
        }

    def execute(self, **kwargs: Any) -> dict[str, Any]:
        """
        Execute web search.

        Args:
            **kwargs: Must contain 'query', optionally 'max_results'

        Returns:
            dict: Standard result format with search results
        """
        # Validate parameters
        self.validate_params(**kwargs)

        query = kwargs["query"]
        max_results = kwargs.get("max_results", 5)

        # Check API key
        if not self.api_key:
            logger.warning("BRAVE_API_KEY not set, returning mock results")
            return {
                "success": False,
                "result": None,
                "error": "BRAVE_API_KEY environment variable not set",
                "metadata": {"query": query},
            }

        try:
            # Call Brave Search API
            url = "https://api.search.brave.com/res/v1/web/search"
            headers = {
                "Accept": "application/json",
                "X-Subscription-Token": self.api_key,
            }
            params = {"q": query, "count": max_results}

            response = requests.get(url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Extract results
            results = []
            for item in data.get("web", {}).get("results", []):
                results.append(
                    {
                        "title": item.get("title", ""),
                        "url": item.get("url", ""),
                        "snippet": item.get("description", ""),
                    }
                )

            logger.info(
                "Web search completed",
                query=query,
                result_count=len(results),
            )

            return {
                "success": True,
                "result": {"results": results, "query": query},
                "error": None,
                "metadata": {"api": "brave", "count": len(results)},
            }

        except requests.exceptions.Timeout:
            logger.error("Web search timeout", query=query)
            return {
                "success": False,
                "result": None,
                "error": "Search request timed out",
                "metadata": {"query": query},
            }

        except requests.exceptions.HTTPError as e:
            logger.error("Web search HTTP error", query=query, error=str(e))
            return {
                "success": False,
                "result": None,
                "error": f"HTTP error: {e}",
                "metadata": {"query": query},
            }

        except Exception as e:
            logger.error("Web search failed", query=query, error=str(e))
            return {
                "success": False,
                "result": None,
                "error": f"Search failed: {e}",
                "metadata": {"query": query},
            }
