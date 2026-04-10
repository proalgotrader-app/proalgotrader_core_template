import asyncio
from abc import ABC, abstractmethod
from asyncio import AbstractEventLoop
from datetime import date, datetime, time, timedelta
from typing import Any

import polars as pl

from proalgotrader_core.algo_session import AlgoSession
from proalgotrader_core.broker_manager import BrokerManager
from proalgotrader_core.logger import AlgoLogger
from proalgotrader_core.notification_manager import NotificationManager
from proalgotrader_core.protocols.api import ApiProtocol
from proalgotrader_core.protocols.args_manager import ArgsManagerProtocol


class BaseAlgorithm(ABC):
    def __init__(
        self,
        event_loop: AbstractEventLoop,
        args_manager: ArgsManagerProtocol,
        api: ApiProtocol,
        algo_session_info: dict[str, Any],
    ) -> None:
        self.event_loop = event_loop

        self.args_manager = args_manager

        self.api = api

        self.algo_session = AlgoSession(
            algo_session_info=algo_session_info["algo_session"],
        )

        self.notification_manager = NotificationManager(algorithm=self)

        self.order_broker_manager = BrokerManager.get_instance(
            algorithm=self,
            api=api,
            algo_session=self.algo_session,
            notification_manager=self.notification_manager,
        )

        self.logger = AlgoLogger(
            api_url=self.args_manager.local_api_url,
            session_id=self.args_manager.algo_session_id,
            enabled=True,
        )

        self.interval = timedelta(seconds=1)

        self.__trading_days: pl.DataFrame | None = None

        self.__booted = False

    @property
    def market_start_time(self) -> time:
        return self.algo_session.market_start_time

    @property
    def market_end_time(self) -> time:
        return self.algo_session.market_end_time

    @property
    def market_start_datetime(self) -> datetime:
        return self.algo_session.market_start_datetime

    @property
    def market_end_datetime(self) -> datetime:
        return self.algo_session.market_end_datetime

    @property
    def pre_market_time(self) -> datetime:
        return self.algo_session.pre_market_time

    @property
    def current_datetime(self) -> datetime:
        return self.algo_session.current_datetime

    @property
    def current_timestamp(self) -> int:
        return self.algo_session.current_timestamp

    @property
    def current_date(self) -> date:
        return self.algo_session.current_date

    @property
    def current_time(self) -> time:
        return self.algo_session.current_time

    async def boot(self) -> None:
        try:
            if self.__booted:
                raise Exception("Algorithm already booted")

            await self.logger.info("booting algorithm")

            await self.__validate_market_status()

            await self.order_broker_manager.initialize()
        except:
            raise

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the algorithm. Must be implemented by subclass.

        Called once after boot() completes and before the main loop starts.
        Use this to set up strategy-specific state, fetch initial data, etc.
        """
        ...

    @abstractmethod
    async def next(self) -> None:
        """Execute one iteration of the algorithm. Must be implemented by subclass.

        Called repeatedly in a loop while market is open.
        Use this to implement trading logic, check conditions, place orders, etc.
        """
        ...

    async def run(self) -> None:
        try:
            if self.__booted:
                raise Exception("Algorithm already booted")

            await self.logger.info("Market is Opened")

            await self.__initialize()

            await self.__next()
        except:
            raise

    async def __initialize(self) -> None:
        try:
            await self.logger.info("Initialize Algorithm")
            await self.initialize()
        except:
            raise

    async def __next(self) -> None:
        try:
            self.__booted = True

            await self.logger.info("Next Algorithm")

            market_status = await self.get_market_status()

            while market_status == "market_opened":
                await self.next()

                await asyncio.sleep(self.interval.seconds)
        except:
            raise

    async def __validate_market_status(self) -> None:
        try:
            await self.logger.info("validating market status")

            while True:
                market_status = await self.get_market_status()

                if market_status == "trading_closed":
                    raise Exception("trading is closed")
                elif market_status == "after_market_closed":
                    raise Exception("market is closed")
                elif market_status == "before_market_opened":
                    raise Exception("market is not opened yet")
                elif market_status == "pre_market_opened":
                    await self.logger.info("market will be opened soon")
                    await asyncio.sleep(1)
                elif market_status == "market_opened":
                    break
                else:
                    raise Exception("Invalid market status")
        except:
            raise

    async def get_market_status(self) -> str:
        try:
            trading_days = await self.get_trading_days()

            # Convert current date to string for comparison
            today = self.current_datetime.strftime("%Y-%m-%d")
            trading_dates = trading_days["date"].to_list()

            if today not in trading_dates:
                return "trading_closed"

            if self.current_datetime < self.pre_market_time:
                return "before_market_opened"

            if (self.current_datetime >= self.pre_market_time) and (
                self.current_datetime < self.market_start_datetime
            ):
                return "pre_market_opened"

            if self.current_datetime > self.market_end_datetime:
                return "after_market_closed"

            return "market_opened"
        except:
            raise

    async def get_trading_days(self) -> pl.DataFrame:
        try:
            """Get trading days DataFrame (cached in memory after first fetch)."""
            if self.__trading_days is None:
                self.__trading_days = await self.__fetch_trading_days()

            return self.__trading_days
        except:
            raise

    async def __fetch_trading_days(self) -> pl.DataFrame:
        """Fetch trading days from API and convert to Polars DataFrame.

        Matches the structure from proalgotrader_core repo:
        - date: Date string (YYYY-MM-DD)
        - day: Day name (Monday, Tuesday, etc.)
        - year: Year as integer

        Returns:
            pl.DataFrame: DataFrame containing trading calendar data
        """
        # Get current and previous year
        current_year = self.current_date.year
        years = f"{current_year - 1},{current_year}"

        result = await self.api.get_trading_days(years=years)

        calendar = result.get("calendar", [])

        if not calendar:
            return pl.DataFrame(
                {
                    "date": [],
                    "day": [],
                    "year": [],
                }
            )

        def get_json(trading_day: dict[str, Any]) -> dict[str, Any]:
            date = trading_day["date"]

            dt = datetime.strptime(date, "%Y-%m-%d")

            return {
                "date": dt.strftime("%Y-%m-%d"),
                "day": dt.strftime("%A"),
                "year": dt.year,
            }

        df = pl.DataFrame(
            data=[
                get_json(trading_day)
                for trading_day in calendar
                if trading_day["description"] == "Market Open"
            ],
        )

        return df
