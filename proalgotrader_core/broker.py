from proalgotrader_core.algo_session import AlgoSession
from proalgotrader_core.api import Api
from proalgotrader_core.notification_manager import NotificationManager
from proalgotrader_core.protocols.algorithm import AlgorithmProtocol
from proalgotrader_core.protocols.broker import BrokerProtocol


class Broker(BrokerProtocol):
    def __init__(
        self,
        api: Api,
        algo_session: AlgoSession,
        notification_manager: NotificationManager,
        algorithm: AlgorithmProtocol,
    ) -> None:
        self.api = api
        self.algo_session = algo_session
        self.notification_manager = notification_manager
        self.algorithm = algorithm

    async def initialize(self):
        await self.algorithm.logger.info("Intitialing broker")
