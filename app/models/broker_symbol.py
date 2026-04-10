"""
Broker Symbol model for ProAlgoTrader FastAPI.

Stores resolved broker-specific symbols with identifiers.
Cached locally for fast resolution without API calls.
"""

from datetime import datetime
from uuid import uuid4

from sqlmodel import Field, SQLModel


class BrokerSymbol(SQLModel, table=True):
    """
    Broker Symbol model - stores resolved broker-specific symbols.

    Each broker symbol maps a base symbol to broker-specific identifiers:
    - base_symbol_id: Reference to base symbol (NIFTY_50)
    - broker_title: Broker name (angel-one, fyers, shoonya)
    - exchange: Exchange name (NSE, NFO)
    - market_type: Cash or Derivative
    - segment_type: Equity, Future, or Option
    - expiry info for derivatives
    - strike info for options
    - Broker identifiers: symbol_name, symbol_token, exchange_token

    Stored in global database - shared across all projects.
    """

    __tablename__ = "broker_symbols"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        max_length=36,
        description="Unique identifier (UUID)",
    )

    # Reference to base symbol
    base_symbol_id: str = Field(
        foreign_key="base_symbols.id", description="Reference to base symbol"
    )

    # Broker identification
    broker_title: str = Field(
        description="Broker name (e.g., 'angel-one', 'fyers', 'shoonya')"
    )

    # Classification
    exchange: str = Field(description="Exchange name (e.g., 'NSE', 'NFO')")
    market_type: str = Field(description="Market type: 'Cash' or 'Derivative'")
    segment_type: str = Field(
        description="Segment type: 'Equity', 'Future', or 'Option'"
    )

    # Derivative-specific fields
    expiry_period: str | None = Field(
        default=None, description="Expiry type: 'Weekly' or 'Monthly'"
    )
    expiry_date: str | None = Field(
        default=None, description="Expiry date in ISO format (e.g., '2024-12-26')"
    )

    # Option-specific fields
    strike_price: int | None = Field(
        default=None, description="Strike price for options (e.g., 24150)"
    )
    option_type: str | None = Field(
        default=None, description="Option type: 'CE' or 'PE'"
    )

    # Lot size
    lot_size: str = Field(default="1", description="Lot size for the instrument")

    # Broker-specific identifiers (THE RESOLVED VALUES)
    symbol_name: str = Field(
        description="Broker's symbol name (e.g., 'NIFTY24DEC24150CE')"
    )
    symbol_token: str = Field(default="", description="Broker's symbol token")
    exchange_token: str = Field(
        description="Broker's exchange token (e.g., '999260' for Angel One)"
    )

    # Soft delete support
    deleted_at: datetime | None = Field(
        default=None, description="Soft delete timestamp"
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
class BrokerSymbolRead(SQLModel):
    """Model for reading a broker symbol."""

    id: str
    base_symbol_id: str
    broker_title: str

    # Classification
    exchange: str
    market_type: str
    segment_type: str

    # Derivative details
    expiry_period: str | None
    expiry_date: str | None
    strike_price: int | None
    option_type: str | None
    lot_size: str

    # Broker identifiers
    symbol_name: str
    symbol_token: str
    exchange_token: str

    # Timestamps
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BrokerSymbolList(SQLModel):
    """Model for listing broker symbols."""

    success: bool
    broker_symbols: list[BrokerSymbolRead]
    count: int
    page: int = 1
    per_page: int = 10
    total_pages: int = 1


class BrokerSymbolCreate(SQLModel):
    """Model for creating a broker symbol."""

    base_symbol_id: str
    broker_title: str
    exchange: str
    market_type: str
    segment_type: str
    expiry_period: str | None = None
    expiry_date: str | None = None
    strike_price: int | None = None
    option_type: str | None = None
    lot_size: str = "1"
    symbol_name: str
    symbol_token: str = ""
    exchange_token: str
