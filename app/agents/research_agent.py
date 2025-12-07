"""Research agent for conducting deep investigations."""

import json
import os
from typing import Any

from openai import OpenAI

from app.agents.base import Agent, extract_json
from app.tasks import SYSTEM_PROMPTS, calculate_cost

# Configure OpenRouter-compatible client
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE_URL", "https://openrouter.ai/api/v1"),
)

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


class ResearchAgent(Agent):
    """Agent that conducts deep research on a topic."""

    def __init__(self):
        super().__init__(agent_type="research")

    def execute(
        self, input_data: dict[str, Any], user_id_hash: str | None = None
    ) -> dict[str, Any]:
        """
        Execute research task.

        Input format:
        {
            "topic": "Research topic or question",
            "previous_feedback": "Feedback from previous iteration (optional)"
        }

        Returns:
            Dict with research findings and usage data
        """
        system_prompt = SYSTEM_PROMPTS["research_deep"]

        # Build message content
        if "previous_feedback" in input_data:
            # This is a revision iteration
            content = json.dumps(
                {
                    "topic": input_data.get("topic", ""),
                    "previous_feedback": input_data["previous_feedback"],
                    "note": "This is a revision. Please address the feedback carefully.",
                },
                ensure_ascii=False,
            )
        else:
            # First iteration
            content = json.dumps(input_data, ensure_ascii=False)

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": content},
        ]

        # Prepare headers with user tracking
        extra_headers = {}
        if user_id_hash:
            extra_headers["X-User-ID"] = user_id_hash

        # Call LLM
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=0.3,  # Slightly higher for creative research
            extra_headers=extra_headers if extra_headers else None,
        )

        content_str = resp.choices[0].message.content
        usage = resp.usage

        # Parse response
        try:
            content_to_parse = content_str if content_str else "{}"
            output = extract_json(content_to_parse)
        except (json.JSONDecodeError, ImportError):
            # Fallback if model doesn't return JSON
            output = {
                "findings": content_str,
                "note": "Model returned plain text instead of JSON",
                "sources": [],
                "key_insights": [],
                "confidence_level": "unknown",
            }

        # Calculate costs
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0

        return {
            "output": output,
            "usage": {
                "model_used": MODEL_NAME,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_cost": calculate_cost(MODEL_NAME, input_tokens, output_tokens),
                "generation_id": resp.id,
            },
        }
