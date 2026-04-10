from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from proalgotrader_core.protocols.algo_session import AlgoSessionProtocol
    from proalgotrader_core.protocols.algorithm import AlgorithmProtocol
    from proalgotrader_core.protocols.api import ApiProtocol
    from proalgotrader_core.protocols.notification_manager import (
        NotificationManagerProtocol,
    )


class BrokerProtocol(Protocol):
    """Protocol for Broker functionality."""

    # Properties from concrete implementation
    api: ApiProtocol
    algo_session: AlgoSessionProtocol
    notification_manager: NotificationManagerProtocol
    algorithm: AlgorithmProtocol

    async def initialize(self) -> None: ...
