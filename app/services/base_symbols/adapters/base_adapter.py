"""
Base adapter interface for extracting base symbols from broker catalogs.

All broker adapters must implement this interface.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum


class SymbolType(str, Enum):
    """Symbol type enumeration."""

    INDEX = "Index"
    STOCK = "Stock"


@dataclass
class ExtractedBaseSymbol:
    """
    Base symbol extracted from broker catalog.

    Universal values (same across brokers):
    - exchange: NSE, BSE (set by exchange)
    - key: NIFTY_50, RELIANCE (standardized)
    - value: NIFTY, RELIANCE (display name)
    - type: Index or Stock (classification)
    - strike_size: Inferred from NSE strike intervals (UNIVERSAL!)
    - lot_size: Number of shares per lot (UNIVERSAL!)

    Broker-specific:
    - broker: Which catalog this came from
    """

    # Universal values (same across brokers)
    exchange: str
    key: str
    value: str
    type: SymbolType
    strike_size: int  # From NSE standard
    lot_size: int  # From NSE standard

    # Metadata
    has_derivatives: bool  # Has F&O
    broker: str
    confidence: str  # High, Medium, Low


class BaseSymbolAdapter(ABC):
    """
    Abstract adapter for extracting base symbols from broker catalog.

    All brokers will produce SAME strike_size and lot_size because:
    - Strike sizes are set by NSE (universal)
    - Lot sizes are set by NSE (universal)
    - Only representation differs (×1 for Fyers, ×100 for Angel One)
    - Adapter normalizes representation to get universal values
    """

    @abstractmethod
    def get_column_mappings(self) -> dict[str, str]:
        """
        Get broker-specific column name mappings.

        Returns:
            Dict mapping standard names to broker column names

        Example:
            >>> angel_one_adapter.get_column_mappings()
            {'symbol': 'name', 'strike': 'strike', 'lotsize': 'lotsize'}

            >>> fyers_adapter.get_column_mappings()
            {'symbol': 'ex_symbol', 'strike': 'strike', 'lotsize': 'lotsize'}
        """
        pass

    @abstractmethod
    def get_strike_multiplier(self) -> int:
        """
        Get strike price multiplier to normalize to rupees.

        Returns:
            Multiplier to divide catalog strike by

        Example:
            >>> angel_one_adapter.get_strike_multiplier()
            100  # Angel One stores strikes as paisa (×100)

            >>> fyers_adapter.get_strike_multiplier()
            1    # Fyers stores strikes as rupees (×1)
        """
        pass

    @abstractmethod
    def get_exchange_filter(self) -> dict[str, str]:
        """
        Get exchange filter for NSE symbols.

        Returns:
            Dict with exchange column and value for filtering

        Example:
            >>> angel_one_adapter.get_exchange_filter()
            {'exchange': 'NFO'}  # NSE F&O exchange code

            >>> fyers_adapter.get_exchange_filter()
            {'ex_segment': 'NFO'}  # Fyers uses different column
        """
        pass
