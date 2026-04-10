"""Protocol for AlgoSession."""

from datetime import date, datetime, time
from typing import Literal, Protocol

from proalgotrader_core.protocols.project_info import ProjectInfoProtocol


class AlgoSessionProtocol(Protocol):
    """Protocol for AlgoSession functionality."""

    # Properties from concrete implementation
    id: int
    mode: Literal["Paper", "Live"]
    backtest_start_date: str | None
    backtest_end_date: str | None
    tz: str
    tz_info: object  # pytz timezone object
    initial_capital: float
    current_capital: float
    market_start_time: time
    market_end_time: time
    market_start_datetime: datetime
    market_end_datetime: datetime
    pre_market_time: datetime

    project_info: ProjectInfoProtocol

    # Computed properties
    @property
    def current_datetime(self) -> datetime: ...

    @property
    def current_timestamp(self) -> int: ...

    @property
    def current_date(self) -> date: ...

    @property
    def current_time(self) -> time: ...
