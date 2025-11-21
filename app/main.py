from fastapi import FastAPI, Response, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import CONTENT_TYPE_LATEST, REGISTRY, generate_latest
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import settings
from app.database import engine
from app.logging_config import configure_logging, get_logger
from app.metrics import (
    app_info,
    websocket_connections_active,
    websocket_messages_sent,
)
from app.middleware.mtls import MTLSMiddleware
from app.routers import tasks
from app.tracing import setup_tracing
from app.websocket import manager

# Configure structured logging
configure_logging(log_level="INFO", json_logs=True)
logger = get_logger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Task Management API",
    description="Async task management with WebSocket support",
    version="1.0.0",
)

# Set up distributed tracing
setup_tracing(
    app,
    service_name="task-api",
    use_console=True,  # Keep console for debugging
    otlp_endpoint=settings.otlp_endpoint,  # Send to Tempo if configured
)
logger.info("Distributed tracing enabled: console + Tempo")

# Set up Prometheus metrics
instrumentator = Instrumentator(
    should_group_status_codes=False,
    should_ignore_untemplated=True,
    should_respect_env_var=False,  # Always enable metrics
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics"],
)

# Instrument the app
instrumentator.instrument(app)

# Set application info
app_info.info({"version": "1.0.0", "name": "task-api", "description": "Async task management API"})

# Add CORS middleware (configure as needed for your use case)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add mTLS middleware
# Note: The actual certificate verification is handled by uvicorn's SSL configuration
# This middleware can be used for additional validation or logging
app.add_middleware(MTLSMiddleware)

# Include routers
app.include_router(tasks.router)


@app.on_event("startup")
async def startup_event():
    """Application startup."""
    logger.info(
        "application_startup",
        database=settings.database_url.split("@")[-1]
        if "@" in settings.database_url
        else "postgres",
        websocket_manager="initialized",
        metrics_endpoint="/metrics",
    )


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown."""
    logger.info("application_shutdown")
    await engine.dispose()


@app.get("/")
async def root():
    """Root endpoint."""
    logger.debug("root_endpoint_accessed")
    return {
        "status": "healthy",
        "message": "Task Management API is running",
        "version": "1.0.0",
    }


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


@app.get("/health")
async def health():
    """Health check endpoint."""
    ws_count = len(manager.active_connections)
    websocket_connections_active.set(ws_count)

    logger.debug(
        "health_check",
        database="connected",
        websocket_connections=ws_count,
    )

    return {
        "status": "healthy",
        "database": "connected",
        "websocket_connections": ws_count,
    }


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time task updates."""
    await manager.connect(websocket)
    websocket_connections_active.inc()

    logger.info(
        "websocket_connected",
        client=websocket.client.host if websocket.client else "unknown",
        total_connections=len(manager.active_connections),
    )

    try:
        while True:
            # Keep connection alive and handle ping/pong
            data = await websocket.receive_text()

            # Simple ping/pong for connection testing
            if data == "ping":
                await websocket.send_text("pong")
                websocket_messages_sent.labels(message_type="pong").inc()

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        websocket_connections_active.dec()
        logger.info(
            "websocket_disconnected",
            total_connections=len(manager.active_connections),
        )
        logger.info("Client disconnected from WebSocket")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)
