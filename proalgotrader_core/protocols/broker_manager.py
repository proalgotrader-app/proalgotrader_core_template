from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from proalgotrader_core.protocols.algo_session import AlgoSessionProtocol
    from proalgotrader_core.protocols.algorithm import AlgorithmProtocol
    from proalgotrader_core.protocols.api import ApiProtocol
    from proalgotrader_core.protocols.broker import BrokerProtocol
    from proalgotrader_core.protocols.notification_manager import (
        NotificationManagerProtocol,
    )


class BrokerManagerProtocol(Protocol):
    """Protocol for BrokerManager functionality."""

    # Public methods from concrete implementation
    @staticmethod
    def get_instance(
        api: ApiProtocol,
        algo_session: AlgoSessionProtocol,
        notification_manager: NotificationManagerProtocol,
        algorithm: AlgorithmProtocol,
    ) -> BrokerProtocol: ...
