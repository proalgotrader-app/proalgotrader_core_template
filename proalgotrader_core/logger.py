"""
Custom logger for ProAlgoTrader Core.
Sends logs to both terminal and FastAPI WebSocket endpoint.
"""

import json
from datetime import datetime
from typing import Any

import websockets


class AlgoLogger:
    """
    WebSocket-based logger that prints to terminal and sends logs to FastAPI.
    Used by subprocess to communicate status back to parent process via WebSocket.
    """

    def __init__(self, api_url: str, session_id: str, enabled: bool = True):
        """
        Initialize the WebSocket logger.

        Args:
            api_url: Base URL of the FastAPI server (e.g., http://localhost:8000)
            session_id: Algorithm session ID
            enabled: Whether to send logs to API (default True)
        """
        # Convert HTTP URL to WebSocket URL
        self.ws_url = api_url.replace("http://", "ws://").replace("https://", "wss://")
        self.session_id = session_id
        self.enabled = enabled
        self.websocket = None

    def _print(self, message: str, level: str = "info"):
        """Print to terminal with timestamp and level."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}][{level.upper()}] {message}")

    async def connect(self):
        """Establish WebSocket connection to FastAPI."""
        if not self.enabled:
            return

        try:
            ws_endpoint = f"{self.ws_url}/ws/algo-sessions/{self.session_id}"
            self.websocket = await websockets.connect(ws_endpoint)
            self._print("WebSocket connected", "info")
        except Exception as e:
            self._print(f"Failed to connect WebSocket: {e}", "error")
            # Don't fail if WebSocket connection fails

    async def _send(
        self,
        level: str,
        message: str,
        event: str | None = None,
        data: dict[str, Any] | None = None,
    ):
        """Send log message via WebSocket."""
        if not self.enabled or not self.websocket:
            return

        try:
            payload = {
                "level": level,
                "message": message,
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
            }

            if event:
                payload["event"] = event

            if data:
                payload["data"] = data

            await self.websocket.send(json.dumps(payload))
        except Exception as e:
            self._print(f"Failed to send: {e}", "error")

    async def info(
        self,
        message: str,
        event: str | None = None,
        data: dict[str, Any] | None = None,
    ):
        """Log info message."""
        self._print(message, "info")
        await self._send("info", message, event, data)

    async def warning(
        self,
        message: str,
        event: str | None = None,
        data: dict[str, Any] | None = None,
    ):
        """Log warning message."""
        self._print(message, "warning")
        await self._send("warning", message, event, data)

    async def error(
        self,
        message: str,
        event: str | None = None,
        data: dict[str, Any] | None = None,
    ):
        """Log error message."""
        self._print(message, "error")
        await self._send("error", message, event, data)

    async def debug(
        self,
        message: str,
        event: str | None = None,
        data: dict[str, Any] | None = None,
    ):
        """Log debug message."""
        self._print(message, "debug")
        await self._send("debug", message, event, data)

    async def close(self):
        """Close the WebSocket connection."""
        if self.websocket:
            try:
                await self.websocket.close()
            except:
                pass
            finally:
                self.websocket = None
