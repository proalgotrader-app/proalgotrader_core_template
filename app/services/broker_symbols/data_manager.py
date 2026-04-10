"""
Data Manager for managing trading days and expiry data using Polars.

Provides functionality to:
- Load trading days from local SQLite database
- Generate weekly/monthly expiry files
- Resolve expiry input to actual dates
"""

from datetime import date, datetime
from pathlib import Path

import polars as pl
from sqlmodel import Session, select

from app.models.trading_calendar import TradingCalendar


class DataManager:
    """Manages all local data using Polars - NO external API calls at runtime.

    Data Flow:
    1. TradingCalendar (SQLite) → trading_days.csv (Polars)
    2. trading_days.csv → Weekly_{day}.csv (cached)
    3. trading_days.csv → Monthly_{day}.csv (cached)

    Directory:
        ~/.proalgotrader/trading_info/{year}/
        - trading_days.csv
        - Weekly_Thursday.csv
        - Monthly_Thursday.csv
        - Weekly_Wednesday.csv (for BANKNIFTY)
        - Monthly_Wednesday.csv (for BANKNIFTY)
    """

    def __init__(self, data_path: Path | None = None):
        """Initialize DataManager with optional custom data path.

        Args:
            data_path: Custom path for storing data files.
                      Defaults to ~/.proalgotrader/trading_info/{year}/
        """
        if data_path is None:
            # Default to ~/.proalgotrader/trading_info/{year}/
            home = Path.home()
            year = datetime.now().year
            data_path = home / ".proalgotrader" / "trading_info" / str(year)

        self.data_path = data_path
        self.data_path.mkdir(parents=True, exist_ok=True)

        # Cache for trading days DataFrame
        self._trading_days: pl.DataFrame | None = None

    def load_trading_days_from_db(self, session: Session) -> pl.DataFrame:
        """Load trading days from local SQLite database.

        Trading days are entries where closed_exchanges is empty
        (meaning market is open).

        Args:
            session: SQLModel session for database access

        Returns:
            Polars DataFrame with columns: date, day, year, month
        """
        # Get all trading days (where closed_exchanges is empty = market open)
        entries = session.exec(
            select(TradingCalendar)
            .where(TradingCalendar.closed_exchanges == "")
            .order_by(TradingCalendar.date)
        ).all()

        if not entries:
            raise ValueError(
                "No trading days found in database. "
                "Please sync trading calendar first: POST /api/trading-calendar/sync"
            )

        # Convert to Polars DataFrame with computed columns
        rows = []
        for entry in entries:
            dt = entry.date
            rows.append(
                {
                    "date": dt,
                    "day": dt.strftime("%A"),  # Monday, Tuesday, etc.
                    "year": dt.year,
                    "month": dt.month,
                }
            )

        df = pl.DataFrame(rows)

        # Cache to file for faster subsequent loads
        df.write_csv(self.data_path / "trading_days.csv")

        return df

    def get_trading_days(self, session: Session) -> pl.DataFrame:
        """Get trading days - try cache first, then DB.

        Args:
            session: SQLModel session for database access

        Returns:
            Polars DataFrame with columns: date, day, year, month
        """
        # Return cached if available
        if self._trading_days is not None:
            return self._trading_days

        file = self.data_path / "trading_days.csv"

        try:
            # Try to load from cache file
            df = pl.read_csv(file, try_parse_dates=True)
            self._trading_days = df
            return df
        except FileNotFoundError:
            # Load from database and cache
            df = self.load_trading_days_from_db(session)
            self._trading_days = df
            return df

    def get_weekly_expiries(self, expiry_day: str, session: Session) -> pl.DataFrame:
        """Get all weekly expiries for a given day.

        Weekly expiries are all {expiry_day}s from trading days.
        For example, all Thursdays for NIFTY weekly expiry.

        Args:
            expiry_day: Day name like "Thursday" or "Wednesday"
            session: SQLModel session for database access

        Returns:
            Polars DataFrame with columns: date, day, year, month
        """
        file = self.data_path / f"Weekly_{expiry_day}.csv"

        try:
            # Try to load from cache
            return pl.read_csv(file, try_parse_dates=True)
        except FileNotFoundError:
            # Derive from trading days
            trading_days = self.get_trading_days(session)

            # Filter to get all {expiry_day}s
            df = trading_days.filter(pl.col("day") == expiry_day).sort("date")

            # Cache for future use
            df.write_csv(file)

            return df

    def get_monthly_expiries(self, expiry_day: str, session: Session) -> pl.DataFrame:
        """Get last expiry of each month for a given day.

        Monthly expiries are the last {expiry_day} of each month.
        For example, last Thursday of each month for NIFTY monthly expiry.

        Args:
            expiry_day: Day name like "Thursday"
            session: SQLModel session for database access

        Returns:
            Polars DataFrame with columns: date, day, year, month
        """
        file = self.data_path / f"Monthly_{expiry_day}.csv"

        try:
            # Try to load from cache
            return pl.read_csv(file, try_parse_dates=True)
        except FileNotFoundError:
            # Derive from trading days
            trading_days = self.get_trading_days(session)

            # Get all {expiry_day}s
            df = trading_days.filter(pl.col("day") == expiry_day)

            # Get last one of each month
            df = df.group_by(["year", "month"]).agg(pl.col("date").max().alias("date"))

            # Join back to get day name
            df = (
                df.join(trading_days, on="date", how="left")
                .select(["date", "day", "year", "month"])
                .sort("date")
            )

            # Cache for future use
            df.write_csv(file)

            return df

    def resolve_expiry(
        self,
        expiry_day: str,
        expiry_input: tuple[str, int],
        session: Session,
        current_date: date | None = None,
    ) -> tuple[str, str]:
        """Convert expiry_input to actual expiry date.

        Args:
            expiry_day: Day name from base_symbol (e.g., "Thursday")
            expiry_input: Tuple of (period, index) where:
                         - period: "Weekly" or "Monthly"
                         - index: 0 (current), 1 (next), 2 (next+1), etc.
                         Example: ("Weekly", 0), ("Monthly", 1)
            session: SQLModel session for database access
            current_date: Current date for filtering (defaults to today)

        Returns:
            Tuple of (expiry_period, expiry_date)
            - expiry_period: "Weekly" or "Monthly" (may change from input)
            - expiry_date: ISO date string like "2024-12-26"

        Example:
            >>> dm = DataManager()
            >>> dm.resolve_expiry("Thursday", ("Weekly", 0), session)
            ("Weekly", "2024-12-26")

            >>> dm.resolve_expiry("Thursday", ("Monthly", 0), session)
            ("Monthly", "2024-12-26")  # If 26th is last Thursday of month

        Raises:
            ValueError: If no expiries found or index out of range
        """
        if current_date is None:
            current_date = date.today()

        expiry_period, expiry_number = expiry_input

        # Get the appropriate expiry DataFrame
        if expiry_period == "Weekly":
            expiries = self.get_weekly_expiries(expiry_day, session)
        else:
            expiries = self.get_monthly_expiries(expiry_day, session)

        # Filter to upcoming expiries (today or later)
        upcoming = expiries.filter(pl.col("date").dt.date() >= current_date).sort(
            "date"
        )

        if len(upcoming) == 0:
            raise ValueError(
                f"No {expiry_period} expiries found for {expiry_day}. "
                f"Please sync trading calendar first."
            )

        if expiry_number >= len(upcoming):
            raise ValueError(
                f"Expiry index {expiry_number} out of range. "
                f"Only {len(upcoming)} expiries available."
            )

        # Get the requested expiry
        expiry_row = upcoming.row(expiry_number, named=True)
        expiry_date = expiry_row["date"]

        # Special case: weekly expiry can become monthly
        # If this weekly is the last one of the month, it's also monthly
        if expiry_period == "Weekly" and expiry_number + 1 < len(upcoming):
            next_row = upcoming.row(expiry_number + 1, named=True)
            current_month = expiry_row["month"]
            next_month = next_row["month"]
            if current_month != next_month:
                # This is the last weekly of the month = monthly expiry
                expiry_period = "Monthly"

        return (expiry_period, expiry_date.strftime("%Y-%m-%d"))

    def resolve_expiry_from_date(
        self,
        expiry_day: str,
        expiry_date_str: str,
        session: Session,
    ) -> tuple[str, str]:
        """Determine expiry period from a given date.

        Used when user provides expiry_date directly instead of expiry_input.

        Args:
            expiry_day: Day name from base_symbol (e.g., "Thursday")
            expiry_date_str: ISO date string like "2024-12-26"
            session: SQLModel session for database access

        Returns:
            Tuple of (expiry_period, expiry_date)
        """
        # Parse the date
        expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()

        # Get weekly expiries
        weekly_expiries = self.get_weekly_expiries(expiry_day, session)

        # Filter to the month containing this expiry
        month_expiries = weekly_expiries.filter(
            (pl.col("year") == expiry_date.year)
            & (pl.col("month") == expiry_date.month)
        )

        # If this is the last one, it's monthly
        if len(month_expiries) > 0:
            last_expiry_date = month_expiries["date"][-1]
            if last_expiry_date == expiry_date:
                return ("Monthly", expiry_date_str)

        return ("Weekly", expiry_date_str)

    def clear_cache(self) -> None:
        """Clear cached trading days DataFrame."""
        self._trading_days = None
