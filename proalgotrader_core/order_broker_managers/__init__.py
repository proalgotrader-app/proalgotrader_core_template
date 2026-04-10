"""
Order Broker Managers for ProAlgoTrader Core.

This package provides different broker implementations for order execution
in trading algorithms.

Available Broker Managers:
- PaperOrderBrokerManager: Simulates trading without real orders
- LiveOrderBrokerManager: Executes live orders (base implementation)
- AngelOneOrderBrokerManager: Angel One broker specific implementation

Example Usage:
    # Used internally by BrokerManager based on mode and broker selection
    # Users typically don't instantiate these directly
    from proalgotrader_core.order_broker_managers import AngelOneOrderBrokerManager
"""

from proalgotrader_core.order_broker_managers.angel_one_order_broker_manager import (
    AngelOneOrderBrokerManager,
)
from proalgotrader_core.order_broker_managers.live_order_broker_manager import (
    LiveOrderBrokerManager,
)
from proalgotrader_core.order_broker_managers.paper_order_broker_manager import (
    PaperOrderBrokerManager,
)

__all__ = [
    "AngelOneOrderBrokerManager",
    "LiveOrderBrokerManager",
    "PaperOrderBrokerManager",
]
