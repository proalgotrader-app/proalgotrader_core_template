from typing import Any

from proalgotrader_core.broker import Broker
from proalgotrader_core.order_broker_managers.angel_one_order_broker_manager import (
    AngelOneOrderBrokerManager,
)
from proalgotrader_core.order_broker_managers.live_order_broker_manager import (
    LiveOrderBrokerManager,
)
from proalgotrader_core.order_broker_managers.paper_order_broker_manager import (
    PaperOrderBrokerManager,
)
from proalgotrader_core.protocols.algo_session import AlgoSessionProtocol
from proalgotrader_core.protocols.algorithm import AlgorithmProtocol
from proalgotrader_core.protocols.api import ApiProtocol
from proalgotrader_core.protocols.broker import BrokerProtocol
from proalgotrader_core.protocols.notification_manager import (
    NotificationManagerProtocol,
)

modes: dict[str, Any] = {
    "paper": PaperOrderBrokerManager,
    "live": LiveOrderBrokerManager,
}

brokers: dict[str, Any] = {
    "angel-one": AngelOneOrderBrokerManager,
}


class BrokerManager:
    @staticmethod
    def get_instance(
        api: ApiProtocol,
        algo_session: AlgoSessionProtocol,
        notification_manager: NotificationManagerProtocol,
        algorithm: AlgorithmProtocol,
    ) -> BrokerProtocol:
        broker_mode = algo_session.mode.lower()

        mode_class: type[Broker] = modes[broker_mode]

        broker_title = algo_session.project_info.broker_info.broker_title.lower()

        broker_class: type[Broker] = brokers[broker_title]

        mode_class.__bases__ = (broker_class,)

        broker: Broker = mode_class(
            api=api,
            algo_session=algo_session,
            notification_manager=notification_manager,
            algorithm=algorithm,
        )

        return broker
