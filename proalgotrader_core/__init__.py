"""
ProAlgoTrader Core Library

This package provides the core functionality for algorithmic trading with ProAlgoTrader.
It includes base classes, managers, utilities, and protocol definitions.

Main Components:
- Algorithm Framework: BaseAlgorithm, Algorithm
- Session Management: AlgoSession
- Trading Infrastructure: Broker, BrokerManager
- Data Models: ProjectInfo, BrokerInfo, GithubRepositoryInfo
- Logging: AlgoLogger
- Entry Point: run_strategy function

Example Usage:
    from proalgotrader_core import Algorithm, run_strategy

    class MyStrategy(Algorithm):
        async def initialize(self):
            await self.logger.info("Initializing strategy")

        async def next(self):
            await self.logger.info("Processing next iteration")

    if __name__ == "__main__":
        run_strategy(MyStrategy)
"""

__version__ = "0.1.0"

# Core Algorithm Classes
# Session Management
from proalgotrader_core.algo_session import AlgoSession
from proalgotrader_core.algorithm import Algorithm

# API & Networking
from proalgotrader_core.api import Api

# Application Management
from proalgotrader_core.application import Application

# Configuration & Arguments
from proalgotrader_core.args_manager import ArgsManager
from proalgotrader_core.base_algorithm import BaseAlgorithm

# Broker Related
from proalgotrader_core.broker import Broker
from proalgotrader_core.broker_info import BrokerInfo
from proalgotrader_core.broker_manager import BrokerManager
from proalgotrader_core.github_repository_info import GithubRepositoryInfo

# Utilities
from proalgotrader_core.logger import AlgoLogger
from proalgotrader_core.notification_manager import NotificationManager

# Order Broker Managers
from proalgotrader_core.order_broker_managers import (
    AngelOneOrderBrokerManager,
    LiveOrderBrokerManager,
    PaperOrderBrokerManager,
)

# Data Models
from proalgotrader_core.project_info import ProjectInfo

# Protocols (for type hints)
from proalgotrader_core.protocols import (
    AlgorithmProtocol,
    AlgoSessionProtocol,
    ApiProtocol,
    ApplicationProtocol,
    ArgsManagerProtocol,
    BaseAlgorithmProtocol,
    BrokerInfoProtocol,
    BrokerManagerProtocol,
    BrokerProtocol,
    GithubRepositoryInfoProtocol,
    LoggerProtocol,
    NotificationManagerProtocol,
    ProjectInfoProtocol,
)
from proalgotrader_core.run_strategy import run_strategy

__all__ = [
    # Version
    "__version__",
    # Core Algorithm Classes
    "Algorithm",
    "BaseAlgorithm",
    # Session Management
    "AlgoSession",
    # API & Networking
    "Api",
    # Application Management
    "Application",
    "run_strategy",
    # Configuration
    "ArgsManager",
    # Broker Related
    "Broker",
    "BrokerInfo",
    "BrokerManager",
    # Data Models
    "ProjectInfo",
    "GithubRepositoryInfo",
    # Utilities
    "AlgoLogger",
    "NotificationManager",
    # Protocols (for type hints)
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
    # Order Broker Managers
    "AngelOneOrderBrokerManager",
    "LiveOrderBrokerManager",
    "PaperOrderBrokerManager",
]
