"""Instance identifier utilities for stable metric labels."""

import os


def get_instance_name() -> str:
    """
    Get stable instance identifier from environment.

    Returns the CONTAINER_NAME environment variable which we set in docker-compose.yml.
    Falls back to HOSTNAME if not set.

    When using docker-compose scale, the replica index is appended automatically
    to the container name (e.g., "task-worker-2").

    Returns:
        str: Instance name like "task-api" or "task-worker-2"
    """
    # Use explicit CONTAINER_NAME if set in docker-compose
    container_name = os.getenv("CONTAINER_NAME", "").strip()
    if container_name:
        return container_name

    # Fallback to HOSTNAME (will be container ID in Docker)
    return os.getenv("HOSTNAME", "unknown")
