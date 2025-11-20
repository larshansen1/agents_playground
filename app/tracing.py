"""
Distributed tracing configuration using OpenTelemetry.

This module sets up tracing for the application with support for:
- Console export (development)
- OTLP export to Tempo (production)
- Auto-instrumentation for FastAPI, SQLAlchemy, and requests
"""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
import logging

logger = logging.getLogger(__name__)


def setup_tracing(
    app,
    service_name: str = "task-api",
    use_console: bool = True,
    otlp_endpoint: str = None
):
    """
    Set up OpenTelemetry tracing for the application.
    
    Args:
        app: FastAPI application instance
        service_name: Name of the service for trace identification
        use_console: Whether to export traces to console (for development)
        otlp_endpoint: OTLP endpoint for Tempo (e.g., "http://tempo:4317")
    """
    # Create resource with service name
    resource = Resource.create({
        "service.name": service_name,
        "service.version": "1.0.0",
    })
    
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
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        otlp_exporter = OTLPSpanExporter(
            endpoint=otlp_endpoint,
            insecure=True  # Use insecure for internal Docker network
        )
        otlp_processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(otlp_processor)
        logger.info(f"Tracing: OTLP exporter enabled, sending to {otlp_endpoint}")
    
    # Set the global tracer provider
    trace.set_tracer_provider(provider)
    
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
    
    # Auto-instrument psycopg2 (for PostgreSQL)
    try:
        Psycopg2Instrumentor().instrument()
        logger.info("Tracing: Psycopg2 instrumented")
    except Exception as e:
        logger.warning(f"Psycopg2 instrumentation skipped: {e}")
    
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
