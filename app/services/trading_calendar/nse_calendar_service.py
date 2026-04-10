"""
NSE Calendar Service for ProAlgoTrader FastAPI.

Fetches market holidays from NSE India API and generates trading calendar.
Similar approach to Upstox API but using NSE's official holiday API.

NSE Holiday API: https://www.nseindia.com/api/holiday-master?type=trading&year=YYYY

Response structure:
{
    "CM": [{"tradingDate": "26-Jan-2026", "weekDay": "Monday", "description": "Republic Day", ...}],
    "FO": [...],
    "CD": [...],
    ...
}

Categories:
- CM: Capital Market (Equity)
- FO: Futures & Options
- CD: Currency Derivatives
- COM: Commodity
- etc.
"""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta

import httpx

logger = logging.getLogger(__name__)


@dataclass
class Holiday:
    """Represents a market holiday."""

    date: date
    description: str
    exchanges: list[str]  # Exchanges closed on this date


@dataclass
class TradingDay:
    """Represents a trading calendar entry."""

    date: date
    description: str
    closed_exchanges: list[str]

    @property
    def is_trading_day(self) -> bool:
        """Check if this is a trading day (market open)."""
        return len(self.closed_exchanges) == 0


class NSECalendarService:
    """Service to fetch and process trading calendar from NSE India API."""

    # NSE Holiday API endpoint
    NSE_HOLIDAYS_URL = "https://www.nseindia.com/api/holiday-master"

    # All exchanges that can be closed
    ALL_EXCHANGES = ["NSE", "NFO", "BSE", "BFO", "CDS", "BCD", "MCX"]

    # NSE category to exchange mapping
    # CM = Capital Market (NSE Equity), FO = Futures & Options
    NSE_CATEGORY_MAP = {
        "CM": ["NSE", "BSE"],  # Capital Market - Equity
        "FO": ["NFO", "BFO"],  # Futures & Options
        "CD": ["CDS", "BCD"],  # Currency Derivatives
        "COM": ["MCX"],  # Commodity
        "CMOT": ["MCX"],  # Commodity
        "CBM": ["MCX"],  # Commodity
        "IRD": [],  # Interest Rate Derivatives
        "MF": [],  # Mutual Fund
        "NDM": [],  # NDM
        "NTRP": [],  # NTRP
        "SLBS": [],  # SLBS
    }

    # Headers for NSE API requests
    NSE_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://www.nseindia.com/",
    }

    def __init__(self, timeout: float = 30.0):
        """Initialize the service.

        Args:
            timeout: Request timeout in seconds
        """
        self.timeout = timeout

    async def fetch_holidays(self, year: int) -> dict[date, Holiday]:
        """Fetch holidays from NSE API for a given year.

        Args:
            year: Year to fetch holidays for

        Returns:
            Dictionary mapping date to Holiday
        """
        holidays: dict[date, Holiday] = {}

        try:
            async with httpx.AsyncClient(
                timeout=self.timeout, follow_redirects=True
            ) as client:
                url = f"{self.NSE_HOLIDAYS_URL}?type=trading&year={year}"

                response = await client.get(url, headers=self.NSE_HEADERS)

                if response.status_code != 200:
                    logger.error(f"NSE API returned status {response.status_code}")
                    return holidays

                data = response.json()

                # Process each category (CM, FO, CD, etc.)
                for category, holiday_list in data.items():
                    if not isinstance(holiday_list, list):
                        continue

                    # Get exchanges for this category
                    exchanges_for_category = self.NSE_CATEGORY_MAP.get(category, [])

                    for holiday_data in holiday_list:
                        try:
                            # Parse date from DD-MMM-YYYY format (e.g., "26-Jan-2026")
                            date_str = holiday_data.get("tradingDate", "")
                            if not date_str:
                                continue

                            parsed_date = datetime.strptime(date_str, "%d-%b-%Y").date()
                            description = holiday_data.get("description", "Holiday")

                            # If holiday already exists, update exchanges
                            if parsed_date in holidays:
                                # Merge exchanges
                                existing = holidays[parsed_date]
                                for ex in exchanges_for_category:
                                    if ex not in existing.exchanges:
                                        existing.exchanges.append(ex)
                            else:
                                holidays[parsed_date] = Holiday(
                                    date=parsed_date,
                                    description=description,
                                    exchanges=list(exchanges_for_category),
                                )

                        except Exception as e:
                            logger.warning(
                                f"Failed to parse holiday {holiday_data}: {e}"
                            )
                            continue

                logger.info(
                    f"Fetched {len(holidays)} holidays from NSE for year {year}"
                )

        except httpx.TimeoutException:
            logger.error(f"NSE API request timed out for year {year}")
        except httpx.RequestError as e:
            logger.error(f"NSE API request failed: {e}")
        except Exception as e:
            logger.error(f"Failed to fetch holidays from NSE: {e}")

        return holidays

    async def fetch_holidays_batch(self, years: list[int]) -> dict[date, Holiday]:
        """Fetch holidays from NSE API for multiple years.

        Args:
            years: List of years to fetch holidays for

        Returns:
            Dictionary mapping date to Holiday (merged across all years)
        """
        all_holidays: dict[date, Holiday] = {}

        # Fetch holidays for current year
        current_year_holidays = await self.fetch_holidays(years[0])
        all_holidays.update(current_year_holidays)

        # Fetch holidays for previous year (if provided)
        if len(years) > 1:
            # Use a smaller timeout for previous year since it's less critical
            prev_year_holidays = await self.fetch_holidays(years[1])
            # Merge - don't overwrite if already exists (current year takes priority)
            for holiday_date, holiday in prev_year_holidays.items():
                if holiday_date not in all_holidays:
                    all_holidays[holiday_date] = holiday

        return all_holidays

    @staticmethod
    def is_weekend(d: date) -> bool:
        """Check if a date is a weekend (Saturday or Sunday).

        Args:
            d: Date to check

        Returns:
            True if weekend, False otherwise
        """
        return d.weekday() >= 5  # 5 = Saturday, 6 = Sunday

    @staticmethod
    def get_dates_in_year(year: int) -> list[date]:
        """Get all dates in a year.

        Args:
            year: Year to get dates for

        Returns:
            List of all dates in the year
        """
        start = date(year, 1, 1)
        end = date(year, 12, 31)

        dates = []
        current = start
        while current <= end:
            dates.append(current)
            current += timedelta(days=1)

        return dates

    def generate_trading_calendar(
        self, year: int, holidays: dict[date, Holiday]
    ) -> list[TradingDay]:
        """Generate complete trading calendar for a year.

        Creates an entry for every date in the year:
        - Holidays from NSE → use holiday description
        - Weekends → "Weekend", all exchanges closed
        - Regular days → "Market Open", no closed exchanges

        Args:
            year: Year to generate calendar for
            holidays: Dictionary of holidays from NSE

        Returns:
            List of TradingDay objects for each date in the year
        """
        dates = self.get_dates_in_year(year)
        calendar: list[TradingDay] = []

        for d in dates:
            if d in holidays:
                # NSE holiday
                holiday = holidays[d]
                calendar.append(
                    TradingDay(
                        date=d,
                        description=holiday.description,
                        closed_exchanges=holiday.exchanges,
                    )
                )
            elif self.is_weekend(d):
                # Weekend
                calendar.append(
                    TradingDay(
                        date=d,
                        description="Weekend",
                        closed_exchanges=list(self.ALL_EXCHANGES),
                    )
                )
            else:
                # Regular trading day
                calendar.append(
                    TradingDay(date=d, description="Market Open", closed_exchanges=[])
                )

        return calendar

    async def sync_trading_calendar(
        self, years: list[int] | None = None
    ) -> dict[str, any]:
        """Sync trading calendar from NSE API.

        Fetches holidays for specified years and generates complete calendar.

        Args:
            years: List of years to sync. Defaults to [previous_year, current_year]

        Returns:
            Dictionary with sync results
        """
        from datetime import datetime as dt

        # Default to previous and current year
        if years is None:
            current_year = dt.now().year
            years = [current_year - 1, current_year]

        logger.info(f"Starting trading calendar sync for years: {years}")

        # Fetch holidays from NSE
        holidays = await self.fetch_holidays_batch(years)

        # Generate trading calendar for each year
        all_calendar_days: list[TradingDay] = []

        for year in years:
            calendar = self.generate_trading_calendar(year, holidays)
            all_calendar_days.extend(calendar)
            logger.info(f"Generated {len(calendar)} calendar days for year {year}")

        # Calculate stats
        holidays_count = sum(
            1
            for d in all_calendar_days
            if d.description != "Market Open" and d.description != "Weekend"
        )
        weekends_count = sum(1 for d in all_calendar_days if d.description == "Weekend")
        trading_days_count = sum(
            1 for d in all_calendar_days if d.description == "Market Open"
        )

        return {
            "success": True,
            "years": years,
            "total_days": len(all_calendar_days),
            "holidays": holidays_count,
            "weekends": weekends_count,
            "trading_days": trading_days_count,
            "calendar": all_calendar_days,
        }
