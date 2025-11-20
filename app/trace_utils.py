"""
Helper utilities for trace context propagation.

This module provides utilities to inject and extract trace context
for distributed tracing across services (API -> Worker).
"""

from typing import Any

from opentelemetry import trace
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator


def inject_trace_context(data: dict[str, Any]) -> dict[str, Any]:
    """
    Inject current trace context into a dictionary.

    This is typically called when creating a task in the API to propagate
    the trace context to the worker.

    Args:
        data: Dictionary to inject trace context into (e.g., task.input)

    Returns:
        Dictionary with _trace_context added
    """
    carrier: dict[str, str] = {}
    TraceContextTextMapPropagator().inject(carrier)

    # Add trace context as a special key
    data_with_context = data.copy()
    if carrier:
        data_with_context["_trace_context"] = carrier

    return data_with_context


def extract_trace_context(data: dict[str, Any]) -> Any:
    """
    Extract trace context from a dictionary and return the context.
    Also returns cleaned data without the trace context.

    Args:
        data: Dictionary containing _trace_context

    Returns:
        Tuple of (context, cleaned_data)
    """
    if not data or "_trace_context" not in data:
        return None, data

    # Extract trace context
    carrier = data.get("_trace_context", {})
    ctx = TraceContextTextMapPropagator().extract(carrier)

    # Remove trace context from data
    cleaned_data = {k: v for k, v in data.items() if k != "_trace_context"}

    return ctx, cleaned_data


def get_current_trace_id() -> str:
    """
    Get the current trace ID as a hex string.

    Returns:
        Trace ID hex string or empty string if no active trace
    """
    span = trace.get_current_span()
    if span and span.get_span_context().is_valid:
        return format(span.get_span_context().trace_id, "032x")
    return ""
