from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from proalgotrader_core.protocols.algorithm import AlgorithmProtocol


class NotificationManagerProtocol(Protocol):
    """Protocol for NotificationManager functionality."""

    # Properties from concrete implementation
    algorithm: AlgorithmProtocol
