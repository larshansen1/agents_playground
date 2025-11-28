"""Distributed tracing configuration using OpenTelemetry.

Provides tracing setup for FastAPI backend and task workers.
"""

from __future__ import annotations

import atexit
import contextlib
import logging
import os

from opentelemetry import trace

# from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter

logger = logging.getLogger(__name__)


def setup_tracing(
    app=None,
    service_name: str = "task-api",
    use_console: bool = False,
    otlp_endpoint: str | None = None,
    instrument_sql: bool = True,  # New parameter to control SQL instrumentation
) -> None:
    """
    Set up OpenTelemetry tracing for the application.

    Args:
        app: FastAPI application instance
        service_name: Name of the service for trace identification
        use_console: Whether to export traces to console (for development)
        otlp_endpoint: OTLP endpoint for Tempo (e.g., "http://tempo:4317")
    """
    # Enable OpenTelemetry debug logging
    os.environ["OTEL_LOG_LEVEL"] = "debug"

    # Create resource with service name
    resource = Resource.create(
        {
            "service.name": service_name,
            "service.version": "1.0.0",
        }
    )

    # Set up tracer provider
    provider = TracerProvider(resource=resource)

    # Add console exporter for development
    if use_console:
        console_exporter = ConsoleSpanExporter()
        console_processor = BatchSpanProcessor(console_exporter)
        provider.add_span_processor(console_processor)
        logger.info(f"Tracing: Console exporter enabled for {service_name}")

    # Add OTLP exporter for production (Tempo)
    if otlp_endpoint:
        # Switch to HTTP exporter for better reliability
        # Ensure endpoint uses HTTP port if not specified
        if "4317" in otlp_endpoint:
            otlp_endpoint = otlp_endpoint.replace("4317", "4318")

        if not otlp_endpoint.startswith("http"):
            otlp_endpoint = f"http://{otlp_endpoint}/v1/traces"
        elif not otlp_endpoint.endswith("/v1/traces"):
            otlp_endpoint = f"{otlp_endpoint}/v1/traces"

        otlp_exporter = OTLPSpanExporter(
            endpoint=otlp_endpoint,
        )
        # Use BatchSpanProcessor with aggressive flushing to ensure spans are sent
        # even for short-lived operations
        otlp_processor = BatchSpanProcessor(
            otlp_exporter,
            max_queue_size=2048,
            schedule_delay_millis=1000,  # Flush every 1 second (default is 5s)
            export_timeout_millis=30000,  # 30 second timeout
            max_export_batch_size=512,
        )
        provider.add_span_processor(otlp_processor)
        logger.info(f"Tracing: OTLP HTTP exporter enabled, sending to {otlp_endpoint}")

    # Set the global tracer provider
    trace.set_tracer_provider(provider)

    # Register shutdown handler to flush spans on exit
    def shutdown_tracing():
        """Flush and shutdown all span processors."""
        try:
            provider.force_flush(timeout_millis=10000)  # Wait up to 10s for flush
            provider.shutdown()
        except Exception as e:
            # Prevent shutdown errors from crashing the app/tests
            with contextlib.suppress(ValueError):
                logger.warning(f"Tracing: Shutdown error: {e}")

    atexit.register(shutdown_tracing)

    # Auto-instrument FastAPI (only if app is provided)
    if app is not None:
        FastAPIInstrumentor.instrument_app(app)
        logger.info("Tracing: FastAPI instrumented")

    # Auto-instrument SQLAlchemy
    try:
        SQLAlchemyInstrumentor().instrument()
        logger.info("Tracing: SQLAlchemy instrumented")
    except Exception as e:
        logger.warning(f"SQLAlchemy instrumentation skipped: {e}")

    # Auto-instrument requests library (for HTTP calls)
    try:
        RequestsInstrumentor().instrument()
        logger.info("Tracing: Requests library instrumented")
    except Exception as e:
        logger.warning(f"Requests instrumentation skipped: {e}")

    # Auto-instrument psycopg2 (for PostgreSQL) - optional for workers
    if instrument_sql:
        try:
            Psycopg2Instrumentor().instrument()
            logger.info("Tracing: Psycopg2 instrumented")
        except Exception as e:
            logger.warning(f"Psycopg2 instrumentation skipped: {e}")
    else:
        logger.info("Tracing: SQL instrumentation disabled (reduces trace noise)")

    logger.info(f"✅ Tracing setup complete for {service_name}")


def get_tracer(name: str = __name__):
    """
    Get a tracer instance for manual span creation.

    Args:
        name: Name of the tracer (usually __name__)

    Returns:
        Tracer instance
    """
    return trace.get_tracer(name)
