"""
Trading Calendar model for ProAlgoTrader FastAPI.

Stores market holidays and trading calendar dates.
Synced from Upstox API and stored in the global database.
"""

from datetime import date as date_type
from datetime import datetime
from uuid import uuid4

from sqlmodel import Field, SQLModel


class TradingCalendar(SQLModel, table=True):
    """
    Trading Calendar model - stores market holidays and trading dates.

    Each entry has:
    - date: The calendar date
    - description: Description (e.g., "Market Open", "Weekend", "Diwali")
    - closed_exchanges: Comma-separated list of exchanges closed on this date

    Stored in global database - shared across all projects.
    """

    __tablename__ = "trading_calendar"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        max_length=36,
        description="Unique identifier (UUID)",
    )

    description: str = Field(
        description="Description (e.g., 'Market Open', 'Weekend', 'Diwali')"
    )
    date: date_type = Field(description="Calendar date", unique=True)
    closed_exchanges: str = Field(
        default="",
        description="Comma-separated list of closed exchanges (e.g., 'NSE,NFO,BSE')",
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
        description="Last update timestamp",
    )

    def get_closed_exchanges(self) -> list[str]:
        """Get closed exchanges as a list."""
        if not self.closed_exchanges:
            return []
        return [e.strip() for e in self.closed_exchanges.split(",") if e.strip()]

    def set_closed_exchanges(self, value: list[str]):
        """Set closed exchanges from a list."""
        self.closed_exchanges = ",".join(value) if value else ""


# Pydantic models for API responses
class TradingCalendarRead(SQLModel):
    """Model for reading a trading calendar entry."""

    id: str
    description: str
    date: date_type
    closed_exchanges: str

    @property
    def is_trading_day(self) -> bool:
        """Check if this is a trading day."""
        return len(self.closed_exchanges) == 0

    class Config:
        from_attributes = True


class TradingCalendarList(SQLModel):
    """Model for listing trading calendar entries."""

    success: bool
    calendar: list[TradingCalendarRead]
    count: int
    last_synced: datetime | None = None
    page: int = 1
    per_page: int = 10
    total_pages: int = 1


class SyncResponse(SQLModel):
    """Model for sync response."""

    success: bool
    message: str
    count: int
    inserted: int = 0
    updated: int = 0
