from datetime import date, datetime, time, timedelta
from typing import Any, Literal

import pytz

from proalgotrader_core.project_info import ProjectInfo
from proalgotrader_core.protocols.algo_session import AlgoSessionProtocol
from proalgotrader_core.protocols.project_info import ProjectInfoProtocol


class AlgoSession(AlgoSessionProtocol):
    def __init__(self, algo_session_info: dict[str, Any]):
        self.id: int = algo_session_info["id"]

        self.mode: Literal["Paper", "Live"] = algo_session_info["mode"]

        self.backtest_start_date: str | None = algo_session_info["backtest_start_date"]

        self.backtest_end_date: str | None = algo_session_info["backtest_end_date"]

        self.tz: str = algo_session_info["tz"]

        self.tz_info = pytz.timezone(self.tz)

        self.project_info: ProjectInfoProtocol = ProjectInfo(
            algo_session_info["project"]
        )

        self.initial_capital: float = 10_00_000

        self.current_capital: float = 10_00_000

        self.market_start_time = time(9, 15)

        self.market_end_time = time(15, 30)

        self.market_start_datetime = datetime.now(tz=self.tz_info).replace(
            hour=self.market_start_time.hour,
            minute=self.market_start_time.minute,
            second=0,
            microsecond=0,
            tzinfo=None,
        )

        self.market_end_datetime = datetime.now(tz=self.tz_info).replace(
            hour=self.market_end_time.hour,
            minute=self.market_end_time.minute,
            second=0,
            microsecond=0,
            tzinfo=None,
        )

        self.pre_market_time = self.market_start_datetime - timedelta(minutes=15)

    @property
    def current_datetime(self) -> datetime:
        return datetime.now(tz=self.tz_info).replace(
            microsecond=0,
            tzinfo=None,
        )

    @property
    def current_timestamp(self) -> int:
        return int(self.current_datetime.timestamp())

    @property
    def current_date(self) -> date:
        return self.current_datetime.date()

    @property
    def current_time(self) -> time:
        return self.current_datetime.time()
