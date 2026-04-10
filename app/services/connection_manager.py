"""
WebSocket connection manager for algo session logs.
Manages active WebSocket connections and broadcasts logs to UI clients.
"""

import logging

from fastapi import WebSocket

logger = logging.getLogger(__name__)


class ConnectionManager:
    """
    Manages WebSocket connections for algorithm sessions.
    Each session can have multiple connected clients (e.g., multiple browser tabs).
    """

    def __init__(self):
        # Dictionary mapping session_id to list of WebSocket connections
        self.active_connections: dict[str, list[WebSocket]] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        """
        Accept and store a WebSocket connection for a session.

        Args:
            session_id: Algorithm session ID
            websocket: WebSocket connection
        """
        await websocket.accept()

        if session_id not in self.active_connections:
            self.active_connections[session_id] = []

        self.active_connections[session_id].append(websocket)

    def disconnect(self, session_id: str, websocket: WebSocket):
        """
        Remove a WebSocket connection for a session.

        Args:
            session_id: Algorithm session ID
            websocket: WebSocket connection to remove
        """
        if session_id in self.active_connections:
            if websocket in self.active_connections[session_id]:
                self.active_connections[session_id].remove(websocket)

            # Clean up empty session lists
            if not self.active_connections[session_id]:
                del self.active_connections[session_id]

    async def broadcast(self, session_id: str, message: dict):
        """
        Broadcast a message to all connections for a session.

        Args:
            session_id: Algorithm session ID
            message: Message to broadcast
        """
        if session_id not in self.active_connections:
            return

        # Create list of connections to remove (if send fails)
        disconnected = []

        for connection in self.active_connections[session_id]:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send message to WebSocket: {e}")
                disconnected.append(connection)

        # Remove failed connections
        for connection in disconnected:
            self.disconnect(session_id, connection)

    async def broadcast_to_all(self, message: dict):
        """
        Broadcast a message to all connections across all sessions.

        Args:
            message: Message to broadcast
        """
        for session_id in self.active_connections:
            await self.broadcast(session_id, message)

    def get_connection_count(self, session_id: str) -> int:
        """
        Get number of active connections for a session.

        Args:
            session_id: Algorithm session ID

        Returns:
            Number of active connections
        """
        return len(self.active_connections.get(session_id, []))

    def get_total_connections(self) -> int:
        """
        Get total number of active connections across all sessions.

        Returns:
            Total number of active connections
        """
        return sum(len(connections) for connections in self.active_connections.values())
