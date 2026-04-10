from __future__ import annotations

from asyncio import AbstractEventLoop, Protocol
from datetime import date, datetime, time, timedelta
from typing import TYPE_CHECKING

import polars as pl

if TYPE_CHECKING:
    from proalgotrader_core.protocols.algo_session import AlgoSessionProtocol
    from proalgotrader_core.protocols.broker import BrokerProtocol
    from proalgotrader_core.protocols.notification_manager import (
        NotificationManagerProtocol,
    )

from proalgotrader_core.protocols.api import ApiProtocol
from proalgotrader_core.protocols.args_manager import ArgsManagerProtocol
from proalgotrader_core.protocols.logger import LoggerProtocol


class BaseAlgorithmProtocol(Protocol):
    """Protocol for BaseAlgorithm functionality."""

    # Properties from concrete implementation
    event_loop: AbstractEventLoop
    args_manager: ArgsManagerProtocol
    api: ApiProtocol
    algo_session: AlgoSessionProtocol
    logger: LoggerProtocol
    order_broker_manager: BrokerProtocol
    notification_manager: NotificationManagerProtocol
    interval: timedelta

    # Market timing properties
    @property
    def market_start_time(self) -> time: ...

    @property
    def market_end_time(self) -> time: ...

    @property
    def market_start_datetime(self) -> datetime: ...

    @property
    def market_end_datetime(self) -> datetime: ...

    @property
    def pre_market_time(self) -> datetime: ...

    # Current time properties
    @property
    def current_datetime(self) -> datetime: ...

    @property
    def current_timestamp(self) -> int: ...

    @property
    def current_date(self) -> date: ...

    @property
    def current_time(self) -> time: ...

    # Core methods
    async def boot(self) -> None: ...
    async def run(self) -> None: ...

    # Utility methods
    async def get_market_status(self) -> str: ...
    async def get_trading_days(self) -> pl.DataFrame: ...
