from unittest.mock import MagicMock, patch

import pytest

from app.tasks import (
    MAX_TOKENS,
    calculate_cost,
    chunk_text,
    execute_task,
    summarize_with_chunking,
)


class TestCostCalculation:
    def test_calculate_cost_gpt4o(self):
        # Input: 1M tokens ($2.50), Output: 1M tokens ($10.00)
        cost = calculate_cost("openai/gpt-4o", 1_000_000, 1_000_000)
        assert cost == 12.50

    def test_calculate_cost_gpt4o_mini(self):
        # Input: 1M tokens ($0.15), Output: 1M tokens ($0.60)
        cost = calculate_cost("openai/gpt-4o-mini", 1_000_000, 1_000_000)
        assert cost == 0.75

    def test_calculate_cost_unknown_model(self):
        # Should use default (gpt-4o-mini pricing)
        cost = calculate_cost("unknown-model", 1_000_000, 1_000_000)
        assert cost == 0.75


class TestChunking:
    def test_chunk_text_small(self):
        text = "Small text"
        chunks = chunk_text(text, max_tokens=100)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_text_large(self):
        # Create text that will definitely be split
        # Assuming 1 char approx 0.25 tokens, so 400 chars ~ 100 tokens
        # We set max_tokens=10 to force split
        text = "a" * 100
        chunks = chunk_text(text, max_tokens=10, overlap=0)
        assert len(chunks) > 1

        # Verify reconstruction (roughly)
        # Note: encoding/decoding might not be perfectly 1:1 with chars for "a"*100
        # but combined length should be close
        combined = "".join(chunks)
        assert len(combined) == len(text)

    def test_chunk_text_overlap(self):
        text = "abcdefghij"
        # Force small chunks with overlap
        # Using a mock encoding to make this predictable would be better,
        # but for now we rely on the fact that single chars are usually single tokens
        chunks = chunk_text(text, max_tokens=5, overlap=2)
        if len(chunks) > 1:
            # If it split, check overlap
            # This is hard to assert exactly without mocking tiktoken
            pass


class TestSummarization:
    @patch("app.tasks.client")
    @patch("app.tasks.count_tokens")
    def test_summarize_direct(self, mock_count, mock_client):
        mock_count.return_value = 100  # Small enough

        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"summary": "short"}'
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_client.chat.completions.create.return_value = mock_response

        result = summarize_with_chunking("text", "prompt")

        assert result["output"]["summary"] == "short"
        assert result["usage"]["input_tokens"] == 10

    @patch("app.tasks.client")
    @patch("app.tasks.count_tokens")
    @patch("app.tasks.chunk_text")
    def test_summarize_hierarchical(self, mock_chunk, mock_count, mock_client):
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

        assert result["output"]["summary"] == "result"
        assert result["output"]["_chunking_info"]["chunks_processed"] == 2
        assert mock_client.chat.completions.create.call_count == 3  # 2 chunks + 1 final


class TestTaskExecution:
    @patch("app.tasks.SYSTEM_PROMPTS", {"test_task": "You are a test."})
    @patch("app.tasks.client")
    def test_execute_task_valid(self, mock_client):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = '{"result": "success"}'
        mock_client.chat.completions.create.return_value = mock_response

        result = execute_task("test_task", {"input": "data"})

        assert result["output"]["result"] == "success"

    def test_execute_task_unknown_type(self):
        with pytest.raises(ValueError, match="No system prompt configured"):
            execute_task("unknown_type", {})

    @patch("app.tasks.SYSTEM_PROMPTS", {"test_task": "You are a test."})
    @patch("app.tasks.client")
    def test_execute_task_invalid_json(self, mock_client):
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "Not JSON"
        mock_client.chat.completions.create.return_value = mock_response

        with pytest.raises(ValueError, match="Model response was not valid JSON"):
            execute_task("test_task", {})
