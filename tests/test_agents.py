"""Unit tests for agents with mocked LLM calls."""

import json
from unittest.mock import MagicMock, patch

import pytest

from app.agents.assessment_agent import AssessmentAgent
from app.agents.research_agent import ResearchAgent
from app.tasks import calculate_cost


class TestResearchAgent:
    """Tests for ResearchAgent execution."""

    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client."""
        with patch("app.agents.research_agent.client") as mock_client:
            yield mock_client

    def test_prompt_construction_initial(self, mock_openai_client):
        """Verify prompt construction for initial research."""
        agent = ResearchAgent()
        input_data = {"topic": "Quantum Computing"}

        # Setup mock response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({"findings": "test"})
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 20
        mock_openai_client.chat.completions.create.return_value = mock_response

        agent.execute(input_data)

        # Verify call arguments
        call_args = mock_openai_client.chat.completions.create.call_args
        assert call_args is not None
        messages = call_args.kwargs["messages"]

        # Check system prompt
        assert messages[0]["role"] == "system"
        assert "research" in messages[0]["content"].lower()

        # Check user content
        assert messages[1]["role"] == "user"
        content = json.loads(messages[1]["content"])
        assert content["topic"] == "Quantum Computing"
        assert "previous_feedback" not in content

    def test_prompt_construction_revision(self, mock_openai_client):
        """Verify prompt construction for revision iteration."""
        agent = ResearchAgent()
        input_data = {
            "topic": "Quantum Computing",
            "previous_feedback": "Add more details on qubits",
        }

        # Setup mock response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({"findings": "test"})
        mock_openai_client.chat.completions.create.return_value = mock_response

        agent.execute(input_data)

        # Verify call arguments
        call_args = mock_openai_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]

        # Check user content includes feedback
        content = json.loads(messages[1]["content"])
        assert content["topic"] == "Quantum Computing"
        assert content["previous_feedback"] == "Add more details on qubits"
        assert "note" in content  # Should have the revision note

    def test_response_parsing_valid_json(self, mock_openai_client):
        """Verify parsing of valid JSON response."""
        agent = ResearchAgent()
        expected_output = {
            "findings": "Quantum computers use qubits.",
            "sources": ["nature.com"],
            "key_insights": ["Superposition is key"],
            "confidence_level": "high",
        }

        # Setup mock response
        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps(expected_output)
        mock_openai_client.chat.completions.create.return_value = mock_response

        result = agent.execute({"topic": "test"})

        assert result["output"] == expected_output

    def test_response_parsing_invalid_json(self, mock_openai_client):
        """Verify fallback handling for invalid JSON response."""
        agent = ResearchAgent()
        raw_text = "Here are the findings: Quantum computers are fast."

        # Setup mock response with plain text
        mock_response = MagicMock()
        mock_response.choices[0].message.content = raw_text
        mock_openai_client.chat.completions.create.return_value = mock_response

        result = agent.execute({"topic": "test"})

        # Should wrap text in structured output
        assert result["output"]["findings"] == raw_text
        assert result["output"]["note"] == "Model returned plain text instead of JSON"
        assert result["output"]["confidence_level"] == "unknown"

    def test_cost_calculation(self, mock_openai_client):
        """Verify cost calculation based on token usage."""
        agent = ResearchAgent()

        # Setup mock usage
        input_tokens = 150
        output_tokens = 250
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "{}"
        mock_response.usage.prompt_tokens = input_tokens
        mock_response.usage.completion_tokens = output_tokens
        mock_response.id = "gen-123"
        mock_openai_client.chat.completions.create.return_value = mock_response

        result = agent.execute({"topic": "test"})

        usage = result["usage"]
        assert usage["input_tokens"] == input_tokens
        assert usage["output_tokens"] == output_tokens
        assert usage["generation_id"] == "gen-123"

        # Verify cost matches utility calculation
        expected_cost = calculate_cost("gpt-4o-mini", input_tokens, output_tokens)
        assert usage["total_cost"] == expected_cost

    def test_user_id_header(self, mock_openai_client):
        """Verify X-User-ID header is passed."""
        agent = ResearchAgent()
        user_id_hash = "user-123-hash"

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "{}"
        mock_openai_client.chat.completions.create.return_value = mock_response

        agent.execute({"topic": "test"}, user_id_hash=user_id_hash)

        call_args = mock_openai_client.chat.completions.create.call_args
        extra_headers = call_args.kwargs["extra_headers"]
        assert extra_headers["X-User-ID"] == user_id_hash


class TestAssessmentAgent:
    """Tests for AssessmentAgent execution."""

    @pytest.fixture
    def mock_openai_client(self):
        """Mock OpenAI client."""
        with patch("app.agents.assessment_agent.client") as mock_client:
            yield mock_client

    def test_prompt_construction(self, mock_openai_client):
        """Verify prompt construction for assessment."""
        agent = AssessmentAgent()
        input_data = {"research_findings": {"findings": "content"}, "original_topic": "Topic A"}

        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps({"approved": True})
        mock_openai_client.chat.completions.create.return_value = mock_response

        agent.execute(input_data)

        call_args = mock_openai_client.chat.completions.create.call_args
        messages = call_args.kwargs["messages"]

        # Check system prompt
        assert messages[0]["role"] == "system"
        assert "assess" in messages[0]["content"].lower()

        # Check user content
        content = json.loads(messages[1]["content"])
        assert content["original_topic"] == "Topic A"
        assert content["research_findings"] == {"findings": "content"}

    def test_response_parsing_approval(self, mock_openai_client):
        """Verify parsing of approval response."""
        agent = AssessmentAgent()
        expected_output = {"approved": True, "feedback": "Great job", "quality_score": 90}

        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps(expected_output)
        mock_openai_client.chat.completions.create.return_value = mock_response

        result = agent.execute({"research_findings": {}, "original_topic": "test"})

        assert result["output"] == expected_output
        assert result["output"]["approved"] is True

    def test_response_parsing_rejection(self, mock_openai_client):
        """Verify parsing of rejection response."""
        agent = AssessmentAgent()
        expected_output = {
            "approved": False,
            "feedback": "Missing sources",
            "areas_for_improvement": ["Add citations"],
        }

        mock_response = MagicMock()
        mock_response.choices[0].message.content = json.dumps(expected_output)
        mock_openai_client.chat.completions.create.return_value = mock_response

        result = agent.execute({"research_findings": {}, "original_topic": "test"})

        assert result["output"] == expected_output
        assert result["output"]["approved"] is False

    def test_error_handling_fallback(self, mock_openai_client):
        """Verify fallback when model returns invalid JSON."""
        agent = AssessmentAgent()

        mock_response = MagicMock()
        mock_response.choices[0].message.content = "I cannot approve this."
        mock_openai_client.chat.completions.create.return_value = mock_response

        result = agent.execute({"research_findings": {}, "original_topic": "test"})

        # Should default to rejected
        assert result["output"]["approved"] is False
        assert "Assessment agent error" in result["output"]["feedback"]
