"""Assessment agent for evaluating research quality."""

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


class AssessmentAgent(Agent):
    """Agent that evaluates research findings quality."""

    def __init__(self):
        super().__init__(agent_type="assessment")

    def execute(
        self, input_data: dict[str, Any], user_id_hash: str | None = None
    ) -> dict[str, Any]:
        """
        Execute assessment task.

        Input format:
        {
            "research_findings": {...},  # Output from ResearchAgent
            "original_topic": "..."       # Original research question
        }

        Returns:
            Dict with approval decision, feedback, and usage data
        """
        system_prompt = SYSTEM_PROMPTS["assessment_quality"]

        # Build message content
        content = json.dumps(
            {
                "original_topic": input_data.get("original_topic", ""),
                "research_findings": input_data.get("research_findings", {}),
            },
            ensure_ascii=False,
        )

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
            temperature=0,  # Deterministic evaluation
            extra_headers=extra_headers if extra_headers else None,
        )

        content_str = resp.choices[0].message.content
        usage = resp.usage

        # Parse response
        try:
            output = extract_json(content_str)
        except (json.JSONDecodeError, ImportError):
            # Fallback if model doesn't return JSON
            output = {
                "approved": False,
                "feedback": f"Assessment agent error: {content_str}",
                "strengths": [],
                "areas_for_improvement": [],
                "overall_quality": "unknown",
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
