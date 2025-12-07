import json
import os
from pathlib import Path
from typing import Any

import tiktoken
import yaml
from openai import OpenAI

from app.text_utils import extract_text_from_input

PROMPTS_FILE = os.getenv("PROMPTS_FILE", str(Path(__file__).parent / "prompts.yaml"))

with Path(PROMPTS_FILE).open() as f:
    SYSTEM_PROMPTS = yaml.safe_load(f)

# Configure OpenRouter-compatible client
client = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url=os.getenv("OPENAI_API_BASE_URL", "https://openrouter.ai/api/v1"),
)

MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

# Token limits (leave buffer for prompts and output)
MAX_TOKENS = 900_000  # ~900k tokens per chunk (buffer for 1M context)
CHUNK_OVERLAP = 50_000  # Overlap to maintain context between chunks


def count_tokens(text: str, model: str = "gpt-4") -> int:
    """Count tokens in text using tiktoken."""
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback to cl100k_base (used by GPT-4, GPT-3.5-turbo, text-embedding-ada-002)
        encoding = tiktoken.get_encoding("cl100k_base")

    return len(encoding.encode(text))


def calculate_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """
    Calculate cost based on model pricing.
    Prices are per 1M tokens from OpenRouter.

    Update these prices as needed from: https://openrouter.ai/models
    """
    # Pricing structure for common models (input/output per 1M tokens)
    pricing = {
        "google/gemini-2.5-flash": (0.075, 0.30),  # $0.075/$0.30 per 1M
        "google/gemini-2.5-flash-preview-09-2025": (0.075, 0.30),
        "google/gemini-2.0-flash-exp:free": (0.0, 0.0),  # Free
        "openai/gpt-4o-mini": (0.15, 0.60),
        "openai/gpt-4o": (2.50, 10.00),
    }

    # Get pricing or use default
    input_price, output_price = pricing.get(model_name, (0.15, 0.60))

    # Calculate cost
    input_cost = (input_tokens / 1_000_000) * input_price
    output_cost = (output_tokens / 1_000_000) * output_price

    return round(input_cost + output_cost, 6)


def chunk_text(text: str, max_tokens: int = MAX_TOKENS, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """
    Split text into overlapping chunks that fit within token limit.

    Args:
        text: Input text to chunk
        max_tokens: Maximum tokens per chunk
        overlap: Number of tokens to overlap between chunks

    Returns:
        List of text chunks
    """
    # Try to get the right encoding
    try:
        encoding = tiktoken.encoding_for_model("gpt-4")
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    # Encode the entire text
    tokens = encoding.encode(text)
    total_tokens = len(tokens)

    if total_tokens <= max_tokens:
        return [text]

    # Create overlapping chunks
    chunks = []
    start = 0

    while start < total_tokens:
        end = min(start + max_tokens, total_tokens)
        chunk_tokens = tokens[start:end]
        chunk_text = encoding.decode(chunk_tokens)
        chunks.append(chunk_text)

        # Move start forward, accounting for overlap
        if end >= total_tokens:
            break
        start = end - overlap

    return chunks


def summarize_with_chunking(
    text: str, system_prompt: str, user_id_hash: str | None = None
) -> dict[str, Any]:
    """
    Summarize large text using hierarchical chunking.
    """
    token_count = count_tokens(text)

    # If text fits in context, summarize directly
    if token_count <= MAX_TOKENS:
        return _summarize_direct(text, system_prompt, user_id_hash)

    # Text is too large - use chunking
    return _summarize_hierarchical(text, system_prompt, user_id_hash, token_count)


def _summarize_direct(text: str, system_prompt: str, user_id_hash: str | None) -> dict[str, Any]:
    """Summarize text that fits within context limits."""
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": json.dumps({"text": text}, ensure_ascii=False)},
    ]

    extra_headers = {}
    if user_id_hash:
        extra_headers["X-User-ID"] = user_id_hash

    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,  # type: ignore[arg-type]
        temperature=0,
        extra_headers=extra_headers if extra_headers else None,
    )

    content = resp.choices[0].message.content
    usage = resp.usage
    total_input_tokens = usage.prompt_tokens if usage else 0
    total_output_tokens = usage.completion_tokens if usage else 0
    generation_id = resp.id

    try:
        output = json.loads(content or "{}")
    except json.JSONDecodeError:
        print(
            f"WARNING: Model returned non-JSON response. Response preview: {(content or '')[:200]}..."
        )
        output = {
            "summary": content,
            "note": "Model returned plain text instead of structured JSON",
        }

    return {
        "output": output,
        "usage": {
            "model_used": MODEL_NAME,
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "total_cost": calculate_cost(MODEL_NAME, total_input_tokens, total_output_tokens),
            "generation_id": generation_id,
        },
    }


def _summarize_hierarchical(
    text: str, system_prompt: str, user_id_hash: str | None, token_count: int
) -> dict[str, Any]:
    """Summarize large text by chunking and combining summaries."""
    chunks = chunk_text(text)
    print(f"Document too large ({token_count:,} tokens). Split into {len(chunks)} chunks.")

    # Step 1: Summarize each chunk
    chunk_summaries = []
    total_input_tokens = 0
    total_output_tokens = 0
    generation_ids = []

    extra_headers = {}
    if user_id_hash:
        extra_headers["X-User-ID"] = user_id_hash

    for i, chunk in enumerate(chunks):
        print(f"Summarizing chunk {i + 1}/{len(chunks)}...")

        messages = [
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "text": chunk,
                        "note": f"This is part {i + 1} of {len(chunks)}. Provide a detailed summary.",
                    },
                    ensure_ascii=False,
                ),
            },
        ]

        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,  # type: ignore[arg-type]
            temperature=0,
            extra_headers=extra_headers if extra_headers else None,
        )

        usage = resp.usage
        total_input_tokens += usage.prompt_tokens if usage else 0
        total_output_tokens += usage.completion_tokens if usage else 0
        generation_ids.append(resp.id)

        try:
            chunk_result = json.loads(resp.choices[0].message.content or "{}")
            chunk_summaries.append(chunk_result.get("summary", str(chunk_result)))
        except json.JSONDecodeError:
            print(f"WARNING: Chunk {i + 1} returned non-JSON, using raw content")
            chunk_summaries.append(resp.choices[0].message.content)

    # Step 2: Combine chunk summaries
    print(f"Combining {len(chunk_summaries)} chunk summaries into final summary...")

    combined_text = "\n\n".join(
        [f"=== Section {i + 1} Summary ===\n{summary}" for i, summary in enumerate(chunk_summaries)]
    )

    final_prompt = f"""{system_prompt}

IMPORTANT: The input below contains summaries of different sections of a large document.
Create a comprehensive final summary that synthesizes all sections."""

    messages = [
        {"role": "system", "content": final_prompt},
        {
            "role": "user",
            "content": json.dumps(
                {"text": combined_text, "total_chunks": len(chunks)}, ensure_ascii=False
            ),
        },
    ]

    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,  # type: ignore[arg-type]
        temperature=0,
        extra_headers=extra_headers if extra_headers else None,
    )

    usage = resp.usage
    total_input_tokens += usage.prompt_tokens if usage else 0
    total_output_tokens += usage.completion_tokens if usage else 0
    generation_ids.append(resp.id)

    try:
        final_result = json.loads(resp.choices[0].message.content or "{}")
        final_result["_chunking_info"] = {
            "original_tokens": token_count,
            "chunks_processed": len(chunks),
            "strategy": "hierarchical_summarization",
        }
        output = final_result
    except json.JSONDecodeError:
        output = {
            "summary": resp.choices[0].message.content,
            "_chunking_info": {"original_tokens": token_count, "chunks_processed": len(chunks)},
        }

    return {
        "output": output,
        "usage": {
            "model_used": MODEL_NAME,
            "input_tokens": total_input_tokens,
            "output_tokens": total_output_tokens,
            "total_cost": calculate_cost(MODEL_NAME, total_input_tokens, total_output_tokens),
            "generation_id": ", ".join(generation_ids),
        },
    }


def execute_task(
    task_type: str, task_input: dict[str, Any], user_id_hash: str | None = None
) -> dict[str, Any]:
    """
    Execute a task by:
    - looking up the system prompt for the task_type
    - handling large documents via chunking if needed
    - sending messages to the LLM
    - parsing the response as JSON
    - returning output with usage data
    """

    if task_type not in SYSTEM_PROMPTS:
        msg = f"No system prompt configured for task type: {task_type}"
        raise ValueError(msg)

    system_prompt = SYSTEM_PROMPTS[task_type]

    # Special handling for document summarization with chunking
    if task_type == "summarize_document":
        text_content = extract_text_from_input(task_input)

        # If we found text, use chunking with user tracking
        if text_content:
            print(f"Triggering chunking for {len(text_content)} character document")
            return summarize_with_chunking(text_content, system_prompt, user_id_hash)
        print(
            f"WARNING: summarize_document called but no text found. Input keys: {list(task_input.keys())}"
        )

    # Standard processing for other task types or smaller inputs
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            # pass the input as JSON so the model sees structure
            "content": json.dumps(task_input, ensure_ascii=False),
        },
    ]

    # Call OpenRouter via OpenAI-compatible client
    resp = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,  # type: ignore[arg-type]
        temperature=0,
    )

    # resp is an object with .choices[0].message.content
    content = resp.choices[0].message.content

    # We expect the model to return JSON. Try to parse it.
    try:
        output = json.loads(content or "{}")
        # Return in the standard format expected by the worker
        return {
            "output": output,
            "usage": {
                "model_used": MODEL_NAME,
                # We don't have token counts readily available in the simple response object
                # without accessing usage, so we'll default to None or 0 if needed.
                # However, the OpenAI client response usually has usage.
                "input_tokens": resp.usage.prompt_tokens if resp.usage else 0,
                "output_tokens": resp.usage.completion_tokens if resp.usage else 0,
                "total_cost": 0.0,  # Simplified for this path
            },
        }
    except json.JSONDecodeError as e:
        # If the model didn't return JSON, surface a helpful error
        msg = f"Model response was not valid JSON: {e}; content={content!r}"
        raise ValueError(msg) from e
