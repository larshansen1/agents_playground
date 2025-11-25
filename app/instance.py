"""Instance identifier utilities for stable metric labels."""

import contextlib
import json
import os
import socket
from pathlib import Path


def get_instance_name() -> str:
    """
    Get stable instance identifier from Docker container name.

    Attempts to query the Docker API via /var/run/docker.sock to get the
    actual container name (e.g., "agents_playground-task-worker-2").
    This supports autoscaling where each replica has a unique name.

    Falls back to CONTAINER_NAME env var, then HOSTNAME.

    Returns:
        str: Instance name like "task-api" or "agents_playground-task-worker-2"
    """
    # 1. Try to query Docker API via socket
    with contextlib.suppress(Exception):
        hostname = os.getenv("HOSTNAME", "").strip()
        if hostname and hostname != "unknown" and Path("/var/run/docker.sock").exists():
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
                sock.connect("/var/run/docker.sock")
                request = f"GET /containers/{hostname}/json HTTP/1.0\r\nHost: localhost\r\n\r\n"
                sock.sendall(request.encode("utf-8"))

                response = b""
                while True:
                    chunk = sock.recv(4096)
                    if not chunk:
                        break
                    response += chunk

                # Parse HTTP response
                response_str = response.decode("utf-8")
                if "HTTP/1.0 200 OK" in response_str or "HTTP/1.1 200 OK" in response_str:
                    # Split headers and body
                    _, body = response_str.split("\r\n\r\n", 1)
                    data = json.loads(body)
                    name = data.get("Name", "")
                    # Name comes as "/container_name", remove leading slash
                    if name:
                        return str(name.lstrip("/"))

    # 2. Fallback to explicit CONTAINER_NAME (static)
    container_name = os.getenv("CONTAINER_NAME", "").strip()
    if container_name:
        return container_name

    # 3. Fallback to HOSTNAME (container ID)
    return os.getenv("HOSTNAME", "unknown")
