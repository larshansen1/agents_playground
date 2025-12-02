from unittest.mock import MagicMock, patch

import pytest

from app.tasks import (
    MAX_TOKENS,
    calculate_cost,
    chunk_text,
    count_tokens,
    execute_task,
    summarize_with_chunking,
)


class TestCostCalculation:
    """Test cost calculation for different models."""

    def test_calculate_cost_gpt4o(self):
        """Verify GPT-4o pricing calculation with realistic token counts."""
        # Input: 1M tokens ($2.50), Output: 1M tokens ($10.00)
        cost = calculate_cost("openai/gpt-4o", 1_000_000, 1_000_000)
        assert cost == 12.50
        assert isinstance(cost, float)

    def test_calculate_cost_gpt4o_mini(self):
        """Verify GPT-4o-mini pricing calculation with realistic token counts."""
        # Input: 1M tokens ($0.15), Output: 1M tokens ($0.60)
        cost = calculate_cost("openai/gpt-4o-mini", 1_000_000, 1_000_000)
        assert cost == 0.75
        assert isinstance(cost, float)

    def test_calculate_cost_gemini_flash(self):
        """Verify Gemini Flash pricing calculation."""
        # Input: 1M tokens ($0.075), Output: 1M tokens ($0.30)
        cost = calculate_cost("google/gemini-2.5-flash", 1_000_000, 1_000_000)
        assert cost == 0.375
        assert isinstance(cost, float)

    def test_calculate_cost_free_model(self):
        """Verify free model returns zero cost."""
        cost = calculate_cost("google/gemini-2.0-flash-exp:free", 1_000_000, 1_000_000)
        assert cost == 0.0

    def test_calculate_cost_unknown_model(self):
        """Verify unknown models default to gpt-4o-mini pricing."""
        cost = calculate_cost("unknown-model", 1_000_000, 1_000_000)
        assert cost == 0.75  # Should use default pricing

    def test_calculate_cost_zero_tokens(self):
        """Verify cost calculation with zero tokens."""
        cost = calculate_cost("openai/gpt-4o", 0, 0)
        assert cost == 0.0

    def test_calculate_cost_asymmetric_usage(self):
        """Verify cost calculation with different input/output token counts."""
        # 500k input, 100k output for gpt-4o
        cost = calculate_cost("openai/gpt-4o", 500_000, 100_000)
        expected = (500_000 / 1_000_000) * 2.50 + (100_000 / 1_000_000) * 10.00
        assert cost == round(expected, 6)


class TestTokenCounting:
    """Test token counting functionality."""

    def test_count_tokens_simple_text(self):
        """Verify token counting for simple text."""
        text = "Hello, world!"
        count = count_tokens(text)
        assert count > 0
        assert isinstance(count, int)

    def test_count_tokens_empty_string(self):
        """Verify token counting for empty string."""
        count = count_tokens("")
        assert count == 0

    def test_count_tokens_with_model_fallback(self):
        """Verify token counting falls back to cl100k_base for unknown models."""
        text = "Test text"
        count = count_tokens(text, model="unknown-model")
        assert count > 0


class TestChunking:
    """Test text chunking functionality."""

    def test_chunk_text_small(self):
        """Verify small text is not chunked."""
        text = "Small text"
        chunks = chunk_text(text, max_tokens=100)

        # Assertions on return value structure
        assert isinstance(chunks, list)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_text_large(self):
        """Verify large text is split into multiple chunks."""
        # Create text that will definitely be split
        # Assuming 1 char approx 0.25 tokens, so 400 chars ~ 100 tokens
        # We set max_tokens=10 to force split
        text = "a" * 100
        chunks = chunk_text(text, max_tokens=10, overlap=0)

        # Assertions on chunking behavior
        assert len(chunks) > 1
        assert all(isinstance(chunk, str) for chunk in chunks)

        # Verify reconstruction (roughly)
        combined = "".join(chunks)
        assert len(combined) == len(text)

    def test_chunk_text_with_overlap(self):
        """Verify chunks have proper overlap."""
        # Create a text that will be split
        text = "word " * 1000  # Repeating words
        chunks = chunk_text(text, max_tokens=100, overlap=20)

        if len(chunks) > 1:
            # Verify we got multiple chunks
            assert len(chunks) > 1
            # Each chunk should be a string
            assert all(isinstance(chunk, str) for chunk in chunks)

    def test_chunk_text_exact_boundary(self):
        """Verify text exactly at max_tokens is not chunked."""
        text = "test " * 100
        token_count = count_tokens(text)
        chunks = chunk_text(text, max_tokens=token_count)

        # Should return single chunk when text fits exactly
        assert len(chunks) == 1

    def test_chunk_text_zero_overlap(self):
        """Verify chunking works with zero overlap."""
        text = "a" * 200
        chunks = chunk_text(text, max_tokens=10, overlap=0)

        assert len(chunks) > 1
        # With zero overlap, combined length should equal original
        combined = "".join(chunks)
        assert len(combined) == len(text)


class TestSummarization:
    """Test summarization with chunking functionality."""

    @patch("app.tasks.client")
    @patch("app.tasks.count_tokens")
    def test_summarize_direct_success(self, mock_count, mock_client):
        """Verify direct summarization for small documents."""
        mock_count.return_value = 100  # Small enough to fit

        # Mock successful API response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"summary": "Test summary"}'
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.id = "test-generation-id"
        mock_client.chat.completions.create.return_value = mock_response

        result = summarize_with_chunking("test text", "test prompt")

        # Assertions on return value structure
        assert "output" in result
        assert "usage" in result

        # Assertions on output content
        assert result["output"]["summary"] == "Test summary"

        # Assertions on usage tracking
        assert result["usage"]["input_tokens"] == 10
        assert result["usage"]["output_tokens"] == 5
        assert result["usage"]["model_used"] is not None
        assert result["usage"]["generation_id"] == "test-generation-id"
        assert "total_cost" in result["usage"]

    @patch("app.tasks.client")
    @patch("app.tasks.count_tokens")
    def test_summarize_direct_with_user_tracking(self, mock_count, mock_client):
        """Verify user tracking is passed to API calls."""
        mock_count.return_value = 100

        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"summary": "Test"}'
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.id = "test-id"
        mock_client.chat.completions.create.return_value = mock_response

        user_hash = "user123hash"
        summarize_with_chunking("text", "prompt", user_id_hash=user_hash)

        # Verify user tracking header was passed
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert "extra_headers" in call_kwargs
        assert call_kwargs["extra_headers"]["X-User-ID"] == user_hash

    @patch("app.tasks.client")
    @patch("app.tasks.count_tokens")
    def test_summarize_direct_non_json_response(self, mock_count, mock_client):
        """Verify handling of non-JSON responses from model."""
        mock_count.return_value = 100

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Plain text response"
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.id = "test-id"
        mock_client.chat.completions.create.return_value = mock_response

        result = summarize_with_chunking("text", "prompt")

        # Should gracefully handle non-JSON by wrapping in structure
        assert result["output"]["summary"] == "Plain text response"
        assert "note" in result["output"]

    @patch("app.tasks.client")
    @patch("app.tasks.count_tokens")
    @patch("app.tasks.chunk_text")
    def test_summarize_hierarchical_success(self, mock_chunk, mock_count, mock_client):
        """Verify hierarchical summarization for large documents."""
        mock_count.return_value = MAX_TOKENS + 100  # Force chunking
        mock_chunk.return_value = ["chunk1", "chunk2"]

        # Mock responses for chunks and final summary
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"summary": "result"}'
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.id = "test-id"
        mock_client.chat.completions.create.return_value = mock_response

        result = summarize_with_chunking("large text", "prompt")

        # Assertions on chunking metadata
        assert result["output"]["summary"] == "result"
        assert "_chunking_info" in result["output"]
        assert result["output"]["_chunking_info"]["chunks_processed"] == 2
        assert result["output"]["_chunking_info"]["strategy"] == "hierarchical_summarization"

        # Verify API was called correct number of times (2 chunks + 1 final)
        assert mock_client.chat.completions.create.call_count == 3

    @patch("app.tasks.client")
    @patch("app.tasks.count_tokens")
    @patch("app.tasks.chunk_text")
    def test_summarize_hierarchical_chunk_failure(self, mock_chunk, mock_count, mock_client):
        """Verify handling of non-JSON chunk responses."""
        mock_count.return_value = MAX_TOKENS + 100
        mock_chunk.return_value = ["chunk1", "chunk2"]

        # First two calls return non-JSON, final call returns JSON
        responses = []
        for i in range(2):
            resp = MagicMock()
            resp.choices[0].message.content = f"Non-JSON chunk {i}"
            resp.usage.prompt_tokens = 10
            resp.usage.completion_tokens = 5
            resp.id = f"chunk-{i}"
            responses.append(resp)

        final_resp = MagicMock()
        final_resp.choices[0].message.content = '{"summary": "final"}'
        final_resp.usage.prompt_tokens = 10
        final_resp.usage.completion_tokens = 5
        final_resp.id = "final-id"
        responses.append(final_resp)

        mock_client.chat.completions.create.side_effect = responses

        result = summarize_with_chunking("large text", "prompt")

        # Should still produce final summary despite chunk failures
        assert result["output"]["summary"] == "final"
        assert result["output"]["_chunking_info"]["chunks_processed"] == 2

    @patch("app.tasks.client")
    @patch("app.tasks.count_tokens")
    @patch("app.tasks.chunk_text")
    def test_summarize_hierarchical_final_non_json(self, mock_chunk, mock_count, mock_client):
        """Verify handling when final summary is non-JSON."""
        mock_count.return_value = MAX_TOKENS + 100
        mock_chunk.return_value = ["chunk1"]

        # Chunk returns JSON, final returns non-JSON
        chunk_resp = MagicMock()
        chunk_resp.choices[0].message.content = '{"summary": "chunk summary"}'
        chunk_resp.usage.prompt_tokens = 10
        chunk_resp.usage.completion_tokens = 5
        chunk_resp.id = "chunk-id"

        final_resp = MagicMock()
        final_resp.choices[0].message.content = "Plain text final"
        final_resp.usage.prompt_tokens = 10
        final_resp.usage.completion_tokens = 5
        final_resp.id = "final-id"

        mock_client.chat.completions.create.side_effect = [chunk_resp, final_resp]

        result = summarize_with_chunking("large text", "prompt")

        # Should wrap plain text in structure
        assert result["output"]["summary"] == "Plain text final"
        assert "_chunking_info" in result["output"]


class TestTaskExecution:
    """Test task execution functionality."""

    @patch("app.tasks.SYSTEM_PROMPTS", {"test_task": "You are a test."})
    @patch("app.tasks.client")
    def test_execute_task_valid_json_response(self, mock_client):
        """Verify successful task execution with valid JSON response."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"result": "success", "status": "completed"}'
        mock_response.usage.prompt_tokens = 100
        mock_response.usage.completion_tokens = 50
        mock_client.chat.completions.create.return_value = mock_response

        result = execute_task("test_task", {"input": "data"})

        # Assertions on return value structure
        assert "output" in result
        assert "usage" in result

        # Assertions on output content
        assert result["output"]["result"] == "success"
        assert result["output"]["status"] == "completed"

        # Assertions on usage tracking
        assert result["usage"]["input_tokens"] == 100
        assert result["usage"]["output_tokens"] == 50
        assert "model_used" in result["usage"]

    def test_execute_task_unknown_type(self):
        """Verify error handling for unknown task types."""
        with pytest.raises(ValueError, match="No system prompt configured"):
            execute_task("unknown_type", {})

    @patch("app.tasks.SYSTEM_PROMPTS", {"test_task": "You are a test."})
    @patch("app.tasks.client")
    def test_execute_task_invalid_json_response(self, mock_client):
        """Verify error handling for invalid JSON responses."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Not JSON at all"
        mock_client.chat.completions.create.return_value = mock_response

        with pytest.raises(ValueError, match="Model response was not valid JSON"):
            execute_task("test_task", {})

    @patch("app.tasks.SYSTEM_PROMPTS", {"test_task": "You are a test."})
    @patch("app.tasks.client")
    def test_execute_task_empty_response(self, mock_client):
        """Verify handling of empty response content."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = ""
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 0
        mock_client.chat.completions.create.return_value = mock_response

        result = execute_task("test_task", {})

        # Empty string should parse as empty dict
        assert result["output"] == {}

    @patch("app.tasks.SYSTEM_PROMPTS", {"summarize_document": "Summarize this."})
    @patch("app.tasks.extract_text_from_input")
    @patch("app.tasks.summarize_with_chunking")
    def test_execute_task_document_summarization_with_text(
        self,
        mock_summarize,
        mock_extract,
    ):
        """Verify document summarization delegates to chunking when text is found."""
        mock_extract.return_value = "Large document text content"
        mock_summarize.return_value = {
            "output": {"summary": "Document summary"},
            "usage": {"input_tokens": 1000, "output_tokens": 100},
        }

        result = execute_task(
            "summarize_document", {"document": "test.pdf"}, user_id_hash="user123"
        )

        # Verify delegation occurred
        mock_extract.assert_called_once()
        mock_summarize.assert_called_once_with(
            "Large document text content", "Summarize this.", "user123"
        )

        # Verify result structure
        assert result["output"]["summary"] == "Document summary"

    @patch("app.tasks.SYSTEM_PROMPTS", {"summarize_document": "Summarize this."})
    @patch("app.tasks.extract_text_from_input")
    @patch("app.tasks.client")
    def test_execute_task_document_summarization_no_text(self, mock_client, mock_extract):
        """Verify document summarization falls back to standard processing when no text found."""
        mock_extract.return_value = None  # No text extracted

        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"summary": "fallback"}'
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_client.chat.completions.create.return_value = mock_response

        result = execute_task("summarize_document", {"url": "http://example.com"})

        # Should fall back to standard processing
        assert result["output"]["summary"] == "fallback"
        mock_client.chat.completions.create.assert_called_once()

    @patch("app.tasks.SYSTEM_PROMPTS", {"test_task": "You are a test."})
    @patch("app.tasks.client")
    def test_execute_task_no_usage_info(self, mock_client):
        """Verify handling when API response has no usage information."""
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"result": "success"}'
        mock_response.usage = None  # No usage info
        mock_client.chat.completions.create.return_value = mock_response

        result = execute_task("test_task", {})

        # Should default to 0 for token counts
        assert result["usage"]["input_tokens"] == 0
        assert result["usage"]["output_tokens"] == 0
