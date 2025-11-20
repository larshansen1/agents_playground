"""
Mutual TLS (mTLS) authentication middleware for FastAPI.

This middleware validates client certificates for external traffic
while allowing internal Docker network traffic without certificates.
"""

import ipaddress
import logging
from collections.abc import Callable
from typing import cast

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)


def is_internal_ip(ip: str) -> bool:
    """
    Check if an IP address is from an internal/private network.

    Args:
        ip: IP address string

    Returns:
        True if IP is from internal network
    """
    try:
        ip_obj = ipaddress.ip_address(ip)
        # Check if IP is in private ranges (Docker networks, localhost)
        return ip_obj.is_private or ip_obj.is_loopback
    except ValueError:
        return False


class MTLSMiddleware(BaseHTTPMiddleware):
    """
    Middleware to handle mTLS authentication.

    - External traffic: Requires valid client certificate
    - Internal Docker network traffic: Certificate optional
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and validate mTLS if from external client.

        Args:
            request: The incoming request
            call_next: The next middleware/route handler

        Returns:
            Response from the application
        """
        # Get client IP
        client_ip = request.client.host if request.client else None

        # Skip mTLS validation for internal traffic
        if client_ip and is_internal_ip(client_ip):
            logger.debug(f"Internal request from {client_ip}, skipping mTLS")
            response = cast(Response, await call_next(request))
            return response  # noqa: RET504

        # For external traffic, check for client certificate
        peercert = request.scope.get("peercert")

        if peercert:
            # Log successful mTLS authentication
            subject = dict(x[0] for x in peercert.get("subject", ()))
            logger.info(
                f"mTLS authenticated: {subject.get('commonName', 'Unknown')} from {client_ip}"
            )
        else:
            # External request without certificate - log warning
            logger.warning(f"External request from {client_ip} without client certificate")

        response = cast(Response, await call_next(request))
        return response  # noqa: RET504
