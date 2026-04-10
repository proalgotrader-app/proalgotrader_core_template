from __future__ import annotations

from typing import Any, Protocol


class BrokerInfoProtocol(Protocol):
    """Protocol for BrokerInfo functionality."""

    # Properties from concrete implementation
    id: int
    broker_title: str
    broker_name: str
    broker_config: dict[str, Any]
