"""
WebSocket endpoint for algorithm session logs.
Both subprocess and UI clients connect to receive real-time logs from running strategies.
"""

import json
import logging

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services import connection_manager

router = APIRouter(tags=["websocket"])
logger = logging.getLogger(__name__)


@router.websocket("/ws/algo-sessions/events")
async def websocket_algo_sessions_events(websocket: WebSocket):
    """
    WebSocket endpoint for algo sessions list page.
    Receives broadcasts from all session events.
    Used by the sessions listing page to update status in real-time.
    """
    session_id = "all"  # Special key for global events

    # Accept connection
    await connection_manager.connect(session_id, websocket)

    try:
        # Keep connection alive
        while True:
            try:
                data = await websocket.receive_text()
                # Just keep connection alive
                if data == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                break
    except Exception as e:
        logger.error(f"Error on global events: {e}")
    finally:
        connection_manager.disconnect(session_id, websocket)


@router.websocket("/ws/algo-sessions/{session_id}")
async def websocket_algo_session_logs(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time algorithm session logs.

    Both subprocess and UI clients connect to this endpoint.
    - Subprocess sends logs
    - Server broadcasts to all connected clients

    Args:
        websocket: WebSocket connection
        session_id: Algorithm session ID to subscribe to

    Protocol:
        - Client connects: ws://localhost:8000/ws/algo-sessions/{session_id}
        - Messages are JSON objects with log data
        - Message format: {
            "session_id": "...",
            "level": "info|warning|error|debug",
            "message": "...",
            "timestamp": "ISO8601",
            "event": "started|completed|error|stopped|...",
            "data": {...} // optional
          }

    Events:
        - started: Strategy started
        - completed: Strategy completed successfully
        - error: Strategy encountered error
        - stopped: Strategy was stopped manually
        - log: Regular log message
    """
    # Accept connection
    await connection_manager.connect(session_id, websocket)

    try:
        # Keep connection alive and handle incoming messages
        while True:
            # Receive message from client (subprocess or UI)
            try:
                data = await websocket.receive_text()

                # Parse message
                try:
                    message = json.loads(data)

                    # Broadcast to the specific session
                    await connection_manager.broadcast(session_id, message)

                    # Also broadcast to global "all" channel for listing page
                    await connection_manager.broadcast("all", message)

                except json.JSONDecodeError:
                    # If client sends "ping", respond with "pong"
                    if data == "ping":
                        await websocket.send_text("pong")

            except WebSocketDisconnect:
                break

    except Exception as e:
        logger.error(f"Error for session {session_id}: {e}")

    finally:
        # Clean up connection
        connection_manager.disconnect(session_id, websocket)
