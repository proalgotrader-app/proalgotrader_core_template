from proalgotrader_core.protocols.algorithm import AlgorithmProtocol
from proalgotrader_core.protocols.notification_manager import (
    NotificationManagerProtocol,
)


class NotificationManager(NotificationManagerProtocol):
    def __init__(self, algorithm: AlgorithmProtocol) -> None:
        self.algorithm = algorithm
