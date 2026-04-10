"""Protocols package initialization."""

from proalgotrader_core.protocols.algo_session import AlgoSessionProtocol
from proalgotrader_core.protocols.algorithm import AlgorithmProtocol
from proalgotrader_core.protocols.api import ApiProtocol
from proalgotrader_core.protocols.application import ApplicationProtocol
from proalgotrader_core.protocols.args_manager import ArgsManagerProtocol
from proalgotrader_core.protocols.base_algorithm import BaseAlgorithmProtocol
from proalgotrader_core.protocols.broker import BrokerProtocol
from proalgotrader_core.protocols.broker_info import BrokerInfoProtocol
from proalgotrader_core.protocols.broker_manager import BrokerManagerProtocol
from proalgotrader_core.protocols.github_repository_info import (
    GithubRepositoryInfoProtocol,
)
from proalgotrader_core.protocols.logger import LoggerProtocol
from proalgotrader_core.protocols.notification_manager import (
    NotificationManagerProtocol,
)
from proalgotrader_core.protocols.project_info import ProjectInfoProtocol

__all__ = [
    "AlgorithmProtocol",
    "AlgoSessionProtocol",
    "ApiProtocol",
    "ApplicationProtocol",
    "ArgsManagerProtocol",
    "BaseAlgorithmProtocol",
    "BrokerInfoProtocol",
    "BrokerManagerProtocol",
    "BrokerProtocol",
    "GithubRepositoryInfoProtocol",
    "LoggerProtocol",
    "NotificationManagerProtocol",
    "ProjectInfoProtocol",
]
