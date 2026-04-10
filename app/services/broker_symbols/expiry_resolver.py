"""
Expiry Resolver - Derives expiry dates from broker catalog.

Data-driven approach matching proalgotrader_core main branch:
- Queries broker catalog for actual expiry dates
- Determines monthly expiry as the last expiry in each month
- All other expiries in the month are weekly

No hard-coded expiry days needed - works for any broker/symbol.
"""

from collections import defaultdict
from datetime import datetime

import polars as pl

from app.services.broker_symbols.catalog_manager import CatalogManager


class ExpiryResolver:
    """Resolves expiry dates from broker catalog.

    Uses data-driven approach from broker catalog:
    1. Query catalog for unique expiries for symbol
    2. Group by year-month
    3. Monthly = last expiry in month (closest to month-end)
    4. All other expiries = weekly

    This matches proalgotrader_core main branch's get_filtered_expiry_dates().
    """

    def __init__(self):
        """Initialize ExpiryResolver."""
        self.catalog_manager = CatalogManager()

    def get_expiry_dates(
        self,
        broker: str,
        base_symbol: str,
        segment_type: str = "Option",
    ) -> tuple[list[str], list[str]]:
        """Get weekly and monthly expiry dates from broker catalog.

        Args:
            broker: Broker name (e.g., 'angel-one', 'fyers')
            base_symbol: Symbol value (e.g., 'NIFTY')
            segment_type: Segment type ('Future' or 'Option')

        Returns:
            Tuple of (weekly_dates, monthly_dates) in YYYY-MM-DD format

        Raises:
            FileNotFoundError: If catalog not synced
            ValueError: If no expiries found
        """
        broker = self.catalog_manager.normalize_broker(broker)
        mapping = self.catalog_manager.COLUMN_MAPPINGS[broker]

        df = self.catalog_manager.load_catalog(broker)

        # Filter for symbol and get unique expiries
        filtered = (
            df.filter(
                (pl.col(mapping["name_col"]) == base_symbol)
                & (pl.col("segment_type") == segment_type)
            )
            .select("expiry")
            .unique()
            .sort("expiry")
            .collect()
        )

        if filtered.is_empty():
            raise ValueError(f"No expiry dates found for {base_symbol}")

        # Parse expiry dates and group by year-month
        expiry_by_month = defaultdict(list)
        all_dates = []

        for row in filtered.iter_rows(named=True):
            expiry_str = row.get("expiry", "")
            if not expiry_str:
                continue

            # Parse to standard format
            standard_date = self._parse_expiry(broker, expiry_str)
            if not standard_date:
                continue

            expiry_dt = datetime.strptime(standard_date, "%Y-%m-%d")
            year_month = (expiry_dt.year, expiry_dt.month)

            expiry_by_month[year_month].append((expiry_dt, standard_date))
            all_dates.append(standard_date)

        if not all_dates:
            raise ValueError(f"No valid expiry dates found for {base_symbol}")

        # For each month, find the monthly expiry (last/ closest to month-end)
        monthly_dates = set()
        for _year_month, expiries in expiry_by_month.items():
            # Sort by date descending (latest first)
            sorted_expiries = sorted(expiries, key=lambda x: x[0], reverse=True)

            # The expiry closest to the end of the month is the monthly expiry
            if sorted_expiries:
                monthly_dates.add(sorted_expiries[0][1])

        # Separate weekly and monthly
        weekly_dates = [d for d in sorted(all_dates) if d not in monthly_dates]
        monthly_dates_list = sorted(monthly_dates)

        return weekly_dates, monthly_dates_list

    def get_filtered_expiry_dates(
        self,
        broker: str,
        base_symbol: str,
        expiry_period: str,
        segment_type: str = "Option",
    ) -> list[str]:
        """Get filtered expiry dates (weekly or monthly) from catalog.

        Main entry point matching proalgotrader_core's get_filtered_expiry_dates().

        Args:
            broker: Broker name
            base_symbol: Symbol value
            expiry_period: 'Weekly' or 'Monthly'
            segment_type: 'Future' or 'Option'

        Returns:
            List of expiry dates in YYYY-MM-DD format, sorted ascending
        """
        if expiry_period not in ["Weekly", "Monthly"]:
            raise ValueError(
                f"expiry_period must be 'Weekly' or 'Monthly', got '{expiry_period}'"
            )

        # For futures, all are monthly
        if segment_type == "Future":
            weekly, monthly = self.get_expiry_dates(broker, base_symbol, segment_type)
            return monthly

        weekly_dates, monthly_dates = self.get_expiry_dates(
            broker, base_symbol, segment_type
        )

        if expiry_period == "Weekly":
            return weekly_dates
        else:
            return monthly_dates

    def resolve_expiry(
        self,
        broker: str,
        base_symbol: str,
        expiry_input: tuple[str, int],
        segment_type: str = "Option",
    ) -> str | None:
        """Resolve expiry_input to actual expiry date string.

        Args:
            broker: Broker name
            base_symbol: Symbol value (e.g., 'NIFTY')
            expiry_input: ('Weekly', index) or ('Monthly', index)
                          e.g., ('Weekly', 0) = current weekly
                          e.g., ('Monthly', 1) = next monthly
            segment_type: 'Future' or 'Option'

        Returns:
            Broker-specific expiry string (e.g., '30JAN25') or None
        """
        period, index = expiry_input

        try:
            dates = self.get_filtered_expiry_dates(
                broker=broker,
                base_symbol=base_symbol,
                expiry_period=period,
                segment_type=segment_type,
            )

            if index < len(dates):
                # Filter to today or later
                today = datetime.now().strftime("%Y-%m-%d")
                future_dates = [d for d in dates if d >= today]

                if index < len(future_dates):
                    return future_dates[index]

            return None
        except (FileNotFoundError, ValueError):
            return None

    def get_expiry_with_broker_format(
        self,
        broker: str,
        base_symbol: str,
        expiry_input: tuple[str, int],
        segment_type: str = "Option",
    ) -> str | None:
        """Get expiry in broker-specific format.

        Returns expiry in the format stored in the broker's catalog,
        which may differ from YYYY-MM-DD.

        Args:
            broker: Broker name
            base_symbol: Symbol value
            expiry_input: ('Weekly', index) or ('Monthly', index)
            segment_type: 'Future' or 'Option'

        Returns:
            Broker-specific expiry string or None
        """
        period, index = expiry_input
        broker = self.catalog_manager.normalize_broker(broker)
        mapping = self.catalog_manager.COLUMN_MAPPINGS[broker]

        try:
            df = self.catalog_manager.load_catalog(broker)

            # Get unique expiries for symbol
            filtered = (
                df.filter(
                    (pl.col(mapping["name_col"]) == base_symbol)
                    & (pl.col("segment_type") == segment_type)
                )
                .select("expiry")
                .unique()
                .sort("expiry")
                .collect()
            )

            if filtered.is_empty():
                return None

            # Get all expiries with their original and parsed formats
            expiries = []
            for row in filtered.iter_rows(named=True):
                expiry_str = row.get("expiry", "")
                if expiry_str:
                    standard = self._parse_expiry(broker, expiry_str)
                    if standard:
                        expiries.append((standard, expiry_str))

            # Sort by standard date
            expiries.sort(key=lambda x: x[0])

            # Filter to today or later
            today = datetime.now().strftime("%Y-%m-%d")
            future_expiries = [(s, o) for s, o in expiries if s >= today]

            # Get weekly/monthly classification
            weekly_dates, monthly_dates = self.get_expiry_dates(
                broker, base_symbol, segment_type
            )

            if period == "Weekly":
                target_dates = [d for d in future_expiries if d[0] in weekly_dates]
            else:
                target_dates = [d for d in future_expiries if d[0] in monthly_dates]

            if index < len(target_dates):
                return target_dates[index][1]  # Return broker format

            return None

        except FileNotFoundError:
            return None

    def _parse_expiry(self, broker: str, expiry_str: str) -> str | None:
        """Parse broker-specific expiry format to standard YYYY-MM-DD.

        Args:
            broker: Broker name
            expiry_str: Broker-specific expiry string

        Returns:
            Standard format YYYY-MM-DD or None if parsing fails

        Formats:
            Angel One: "05MAY2026" or "25JAN25" or "30 JAN 25" → "2025-01-30"
            Fyers: "30-Jan-25" or "2025-01-30" → "2025-01-30"
        """
        if not expiry_str:
            return None

        expiry_str = expiry_str.strip().upper()

        # Already in standard format?
        try:
            if "-" in expiry_str and len(expiry_str) == 10:
                datetime.strptime(expiry_str, "%Y-%m-%d")
                return expiry_str
        except ValueError:
            pass

        # Try various formats
        patterns = [
            (
                "%d%b%Y",
                expiry_str.replace(" ", ""),
            ),  # "05MAY2026" - Angel One new format
            ("%d%b%y", expiry_str.replace(" ", "")),  # "25JAN25"
            ("%d %b %y", expiry_str),  # "30 JAN 25"
            ("%d-%b-%y", expiry_str),  # "30-Jan-25"
            ("%d-%b-%Y", expiry_str),  # "30-Jan-2025"
            ("%d %b %Y", expiry_str),  # "30 JAN 2025"
        ]

        for fmt, s in patterns:
            try:
                dt = datetime.strptime(s, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        return None
