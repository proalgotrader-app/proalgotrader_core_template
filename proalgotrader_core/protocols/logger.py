"""Protocol for AlgoLogger."""

from typing import Any, Protocol


class LoggerProtocol(Protocol):
    """Protocol for algorithm logger."""

    # Properties from concrete implementation
    ws_url: str
    session_id: str
    enabled: bool
    websocket: Any  # websockets connection object

    async def connect(self) -> None:
        """Establish WebSocket connection."""
        ...

    async def info(
        self,
        message: str,
        event: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Log info message."""
        ...

    async def warning(
        self,
        message: str,
        event: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Log warning message."""
        ...

    async def error(
        self,
        message: str,
        event: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Log error message."""
        ...

    async def debug(
        self,
        message: str,
        event: str | None = None,
        data: dict[str, Any] | None = None,
    ) -> None:
        """Log debug message."""
        ...

    async def close(self) -> None:
        """Close WebSocket connection."""
        ...
