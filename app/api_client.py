"""API Client for worker communication."""

import os
import socket
from typing import Any

import requests
import urllib3

from app.logging_config import get_logger

# Suppress InsecureRequestWarning since we're using self-signed certs internally
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

logger = get_logger(__name__)

# API endpoint (internal Docker network)
API_URL = "https://task-api:8443"

# Worker Identity (hostname:pid)
WORKER_ID = f"{socket.gethostname()}:{os.getpid()}"


def notify_api_async(
    task_id: str, status: str, output: dict | None = None, error: str | None = None
) -> None:
    """
    Notify API of task update (best-effort, non-blocking).
    This triggers metrics recording and WebSocket broadcasting.
    Failures are logged but don't affect task completion.

    Args:
        task_id: UUID of the task
        status: Task status
        output: Task output dict (optional)
        error: Error message (optional)
    """
    url = f"{API_URL}/tasks/{task_id}"
    payload: dict[str, Any] = {"status": status}

    if output is not None:
        payload["output"] = output
    if error is not None:
        payload["error"] = error

    try:
        # Use verify=False for internal communication with self-signed certs
        response = requests.patch(url, json=payload, timeout=5, verify=False)  # nosec B501
        response.raise_for_status()
        logger.debug("api_notified", task_id=task_id, status=status)
    except Exception as e:
        # Log but don't fail - DB already updated
        logger.warning("api_notification_failed", task_id=task_id, error=str(e)[:100])
