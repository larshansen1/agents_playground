import os
import socket
from pathlib import Path

import requests  # noqa: F401 - Used in tests for mocking
import urllib3
from opentelemetry import trace

from app.instance import get_instance_name
from app.logging_config import configure_logging, get_logger
from app.tracing import setup_tracing

# Suppress InsecureRequestWarning since we're using self-signed certs internally
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure structured logging
configure_logging(log_level="INFO", json_logs=True)
logger = get_logger(__name__)

# API endpoint (internal Docker network) - Moved to api_client.py
# Worker Identity (hostname:pid)
WORKER_ID = f"{socket.gethostname()}:{os.getpid()}"

# Configure Prometheus multiprocess directory per instance to avoid PID collisions
# All Docker containers have PID 1, so they would overwrite each other's metrics
# Using separate subdirectories ensures each container writes to unique files
if "PROMETHEUS_MULTIPROC_DIR" in os.environ:
    base_dir = Path(os.environ["PROMETHEUS_MULTIPROC_DIR"])
    instance_dir = base_dir / get_instance_name()
    instance_dir.mkdir(parents=True, exist_ok=True)
    os.environ["PROMETHEUS_MULTIPROC_DIR"] = str(instance_dir)
    logger.info(f"Prometheus multiprocess directory: {instance_dir}")

# Set up tracing for worker
setup_tracing(
    app=None,  # No FastAPI app in worker
    service_name="task-worker",
    use_console=True,  # Keep console for debugging
    otlp_endpoint="tempo:4317",  # Send to Tempo
    instrument_sql=False,  # Disable SQL tracing to reduce noise from lease queries
)
tracer = trace.get_tracer(__name__)


def run_worker() -> None:
    """Main entry point for worker process."""
    from app.worker_state import WorkerStateMachine

    worker_id = get_instance_name()
    state_machine = WorkerStateMachine(worker_id=worker_id)
    state_machine.run()


if __name__ == "__main__":
    run_worker()
