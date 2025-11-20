import json
import logging

from fastapi import WebSocket

from app.schemas import TaskStatusUpdate

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manager for WebSocket connections.

    Handles multiple WebSocket clients and broadcasts task status updates
    to all connected clients.
    """

    def __init__(self):
        """Initialize the connection manager."""
        self.active_connections: set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """
        Accept a new WebSocket connection.

        Args:
            websocket: The WebSocket connection to accept
        """
        await websocket.accept()
        self.active_connections.add(websocket)
        logger.info(f"New WebSocket connection. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """
        Remove a WebSocket connection.

        Args:
            websocket: The WebSocket connection to remove
        """
        self.active_connections.discard(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: TaskStatusUpdate):
        """
        Broadcast a task status update to all connected clients.

        Args:
            message: The task status update to broadcast
        """
        if not self.active_connections:
            return

        # Convert message to JSON
        message_dict = {
            "task_id": str(message.task_id),
            "status": message.status,
            "type": message.type,
            "output": message.output,
            "error": message.error,
            "updated_at": message.updated_at.isoformat(),
        }
        message_json = json.dumps(message_dict)

        # Send to all connected clients
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_text(message_json)
            except Exception as e:
                logger.error(f"Error sending message to client: {e}")
                disconnected.add(connection)

        # Remove disconnected clients
        for connection in disconnected:
            self.disconnect(connection)


# Global connection manager instance
manager = ConnectionManager()
