"""
Base Symbol model for ProAlgoTrader FastAPI.

Stores the base trading symbols/instruments (e.g., NIFTY, BANKNIFTY, etc.)
These are synced from the ProAlgoTrader API and stored in the global database.

NOTE: This table is synced from external API - DO NOT add/remove columns.
Only the columns returned by the API should be stored here.
"""

from datetime import datetime
from uuid import uuid4

from sqlmodel import Field, SQLModel


class BaseSymbol(SQLModel, table=True):
    """
    Base Symbol model - stores trading instruments.

    This table is synced from broker catalog or external API.

    Columns:
    - exchange: Exchange name (NSE, NFO, BSE)
    - key: Symbol key (NIFTY_50)
    - value: Display value (NIFTY)
    - type: Symbol type (Index, Stock)
    - strike_size: Strike increment for options (50 for NIFTY)
    - lot_size: Number of shares per lot (65 for NIFTY)

    Stored in global database - shared across all projects.
    """

    __tablename__ = "base_symbols"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        max_length=36,
        description="Unique identifier (UUID)",
    )

    # Symbol details (synced from broker catalog or external API)
    exchange: str = Field(description="Exchange name (e.g., 'NSE', 'NFO')")
    key: str = Field(description="Symbol key (e.g., 'NIFTY_50')", unique=True)
    value: str = Field(description="Display value (e.g., 'NIFTY')")
    type: str = Field(description="Symbol type (e.g., 'Index', 'Stock')")
    strike_size: int = Field(
        default=0, description="Strike increment for options (e.g., 50 for NIFTY)"
    )
    lot_size: int = Field(
        default=1, description="Number of shares per lot (e.g., 65 for NIFTY)"
    )

    # Soft delete support
    deleted_at: datetime | None = Field(
        default=None, description="Soft delete timestamp"
    )

    # Sync timestamp for incremental updates
    last_synced_at: datetime | None = Field(
        default=None, description="Last sync timestamp"
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


# Pydantic models for API responses
class BaseSymbolRead(SQLModel):
    """Model for reading a base symbol."""

    id: str
    exchange: str
    key: str
    value: str
    type: str
    strike_size: int
    lot_size: int
    deleted_at: datetime | None
    last_synced_at: datetime | None
    created_at: datetime
    updated_at: datetime


class BaseSymbolList(SQLModel):
    """Model for listing base symbols."""

    success: bool
    base_symbols: list[BaseSymbolRead]
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
    base_symbols: list[BaseSymbolRead] = []
