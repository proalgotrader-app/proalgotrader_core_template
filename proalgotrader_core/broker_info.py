from typing import Any

from proalgotrader_core.protocols.broker_info import BrokerInfoProtocol


class BrokerInfo(BrokerInfoProtocol):
    def __init__(self, broker_info: dict[str, Any]) -> None:
        self.id: int = broker_info["id"]
        self.broker_title: str = broker_info["broker_title"]
        self.broker_name: str = broker_info["broker_name"]
        self.broker_config: dict[str, Any] = broker_info.get("broker_config", {})
