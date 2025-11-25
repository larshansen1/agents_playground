"""Instance identifier utilities for stable metric labels."""

import os


def get_instance_name() -> str:
    """
    Get stable instance identifier from environment.

    Returns the HOSTNAME environment variable which Docker Compose sets to
    the container name (e.g., "task-worker-2" when scaled).

    This provides stable instance identification across container restarts
    and works seamlessly with docker-compose scaling.

    Returns:
        str: Instance name like "task-api" or "task-worker-2"
    """
    hostname = os.getenv("HOSTNAME", "unknown")
    # Split on '.' to handle FQDN if present
    return hostname.split(".")[0]
