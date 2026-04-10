"""
Catalog Manager for managing broker instrument catalogs as Parquet files.

Provides functionality to:
- Load broker catalogs (Parquet files)
- Query catalogs for instrument details
- Download catalogs from broker APIs
- Manage catalog storage

Broker-specific handling:
- Strike price multipliers (Angel One ×100, Fyers ×1)
- Expiry date formats (Angel One: DDMMMYYYY, Fyers: DD MMM YY)
"""

from datetime import datetime
from pathlib import Path

import polars as pl


class CatalogManager:
    """Manages broker instrument catalogs stored as Parquet files.

    All catalogs are stored in ~/.proalgotrader/broker_catalogs/

    Catalog Structure (Parquet):
        - symbol: Broker's symbol name
        - name/ex_symbol: Base symbol identifier
        - token: Broker-specific token
        - expiry: Expiry date (broker-specific format)
        - strike: Strike price
        - exchange: Exchange name
        - opt_type: Option type (CE/PE)
        - lotsize: Lot size
        - market_type: Cash/Derivative
        - segment_type: Equity/Future/Option
    """

    CATALOG_DIR = Path.home() / ".proalgotrader" / "broker_catalogs"

    SUPPORTED_BROKERS = ["angel-one", "fyers", "shoonya"]

    # Broker-specific column mappings
    COLUMN_MAPPINGS = {
        "angel-one": {
            "symbol_col": "symbol",
            "name_col": "name",
            "token_col": "token",
        },
        "fyers": {
            "symbol_col": "symbol",
            "name_col": "ex_symbol",
            "token_col": "token",
        },
        "shoonya": {
            "symbol_col": "symbol",
            "name_col": "name",
            "token_col": "token",
        },
    }

    # Broker-specific strike multipliers
    # Angel One multiplies strike by 100 (e.g., 25000 -> 2500000)
    # Fyers uses actual strike values (e.g., 25000 -> 25000)
    STRIKE_MULTIPLIERS = {
        "angel-one": 100,
        "fyers": 1,
        "shoonya": 100,  # Same as Angel One
    }

    def __init__(self):
        """Initialize CatalogManager and ensure directory exists."""
        self.CATALOG_DIR.mkdir(parents=True, exist_ok=True)

    def get_catalog_path(self, broker: str) -> Path:
        """Get the Parquet file path for a broker.

        Args:
            broker: Broker name (e.g., 'angel-one', 'fyers')

        Returns:
            Path to the broker's Parquet catalog file
        """
        broker = self.normalize_broker(broker)
        return self.CATALOG_DIR / f"{broker}.parquet"

    def get_cache_path(self) -> Path:
        """Get the cache directory path."""
        return self.CATALOG_DIR

    def normalize_broker(self, broker: str) -> str:
        """Normalize broker name.

        Handles paper trading brokers by returning the underlying broker.

        Args:
            broker: Broker name (e.g., 'angel-one', 'paper-angel-one')

        Returns:
            Normalized broker name

        Raises:
            ValueError: If broker is not supported
        """
        broker = broker.lower().strip()

        # Paper trading uses real broker's catalog
        if broker.startswith("paper-"):
            broker = broker.replace("paper-", "")

        if broker not in self.SUPPORTED_BROKERS:
            raise ValueError(
                f"Unsupported broker: {broker}. "
                f"Supported brokers: {', '.join(self.SUPPORTED_BROKERS)}"
            )

        return broker

    def catalog_exists(self, broker: str) -> bool:
        """Check if catalog file exists for the broker.

        Args:
            broker: Broker name

        Returns:
            True if catalog exists, False otherwise
        """
        return self.get_catalog_path(broker).exists()

    def get_catalog_info(self, broker: str) -> dict | None:
        """Get information about a broker's catalog.

        Args:
            broker: Broker name

        Returns:
            Dictionary with catalog info or None if not exists
        """
        path = self.get_catalog_path(broker)

        if not path.exists():
            return None

        # Get file stats
        stat = path.stat()

        # Get row count
        try:
            df = pl.scan_parquet(path)
            row_count = df.select(pl.len()).collect().item()
        except Exception:
            row_count = 0

        return {
            "broker": broker,
            "path": str(path),
            "size_bytes": stat.st_size,
            "size_mb": round(stat.st_size / (1024 * 1024), 2),
            "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
            "row_count": row_count,
        }

    def get_catalog_age(self, broker: str) -> float | None:
        """Get the age of a broker's catalog in hours.

        Args:
            broker: Broker name

        Returns:
            Age in hours, or None if catalog doesn't exist
        """
        path = self.get_catalog_path(broker)

        if not path.exists():
            return None

        stat = path.stat()
        modified_time = datetime.fromtimestamp(stat.st_mtime)
        age = datetime.now() - modified_time

        return age.total_seconds() / 3600  # Convert to hours

    def is_catalog_fresh(self, broker: str, max_age_hours: float = 24) -> bool:
        """Check if catalog exists and is not older than max_age_hours.

        Args:
            broker: Broker name
            max_age_hours: Maximum age in hours (default 24)

        Returns:
            True if catalog exists and is fresh, False otherwise
        """
        age = self.get_catalog_age(broker)

        if age is None:
            return False

        return age <= max_age_hours

    def load_catalog(self, broker: str) -> pl.LazyFrame:
        """Load broker catalog as Polars LazyFrame for efficient filtering.

        Uses lazy evaluation for best performance on large catalogs.

        Args:
            broker: Broker name

        Returns:
            Polars LazyFrame

        Raises:
            FileNotFoundError: If catalog doesn't exist

        Note:
            Use .collect() to execute the query and get a DataFrame
        """
        path = self.get_catalog_path(broker)

        if not path.exists():
            raise FileNotFoundError(
                f"Catalog not found for {broker}. "
                f"Please sync the catalog first: POST /api/broker-symbols/{broker}/sync-catalog"
            )

        return pl.scan_parquet(path)

    # =========================================================================
    # Broker-specific formatters
    # =========================================================================

    def get_strike_multiplier(self, broker: str) -> int:
        """Get the strike price multiplier for a broker.

        Some brokers multiply strike prices (Angel One ×100),
        others use actual values (Fyers ×1).

        Args:
            broker: Broker name

        Returns:
            Strike price multiplier
        """
        broker = self.normalize_broker(broker)
        return self.STRIKE_MULTIPLIERS.get(broker, 1)

    def format_expiry(self, broker: str, expiry_date: str) -> str:
        """Convert ISO date to broker-specific expiry format.

        Args:
            broker: Broker name
            expiry_date: ISO date string "2024-12-26"

        Returns:
            Broker-specific expiry string

        Examples:
            >>> format_expiry("angel-one", "2024-12-26")
            "26DEC2024"

            >>> format_expiry("fyers", "2024-12-26")
            "26 DEC 24"
        """
        broker = self.normalize_broker(broker)
        dt = datetime.strptime(expiry_date, "%Y-%m-%d")

        if broker == "angel-one":
            # Angel One format: DDMMMYYYY (e.g., 26DEC2024)
            return dt.strftime("%d%b%Y").upper()
        elif broker == "fyers":
            # Fyers format: DD MMM YY (e.g., 26 DEC 24)
            return dt.strftime("%d %b %y").upper()
        elif broker == "shoonya":
            # Shoonya uses same format as Angel One
            return dt.strftime("%d%b%Y").upper()
        else:
            # Default to Angel One format
            return dt.strftime("%d%b%Y").upper()

    def format_strike(self, broker: str, strike_price: int) -> str:
        """Convert strike price to broker-specific format for querying.

        Args:
            broker: Broker name
            strike_price: Strike price (e.g., 22500)

        Returns:
            Broker-specific strike string for catalog query

        Examples:
            >>> format_strike("angel-one", 22500)
            "2250000.000000"

            >>> format_strike("fyers", 22500)
            "22500.0"
        """
        broker = self.normalize_broker(broker)
        multiplier = self.get_strike_multiplier(broker)
        scaled_strike = strike_price * multiplier

        if broker == "angel-one":
            # Angel One stores strike with 6 decimal places
            return f"{scaled_strike}.000000"
        elif broker == "fyers":
            # Fyers stores strike as float with 1 decimal
            return f"{float(scaled_strike)}"
        elif broker == "shoonya":
            # Shoonya uses same format as Angel One
            return f"{scaled_strike}.000000"
        else:
            # Default
            return str(scaled_strike)

    def parse_expiry_to_standard(self, broker: str, expiry_str: str) -> str | None:
        """Parse broker-specific expiry format to standard YYYY-MM-DD.

        Args:
            broker: Broker name
            expiry_str: Broker-specific expiry string

        Returns:
            Standard format YYYY-MM-DD or None if parsing fails

        Examples:
            >>> parse_expiry_to_standard("angel-one", "26DEC2024")
            "2024-12-26"

            >>> parse_expiry_to_standard("fyers", "26 DEC 24")
            "2024-12-26"
        """
        if not expiry_str:
            return None

        broker = self.normalize_broker(broker)
        expiry_str = expiry_str.strip().upper()

        # Already in standard format?
        try:
            if "-" in expiry_str and len(expiry_str) == 10:
                datetime.strptime(expiry_str, "%Y-%m-%d")
                return expiry_str
        except ValueError:
            pass

        # Broker-specific formats
        formats = []

        if broker == "angel-one":
            formats = [
                "%d%b%Y",  # 26DEC2024 (Angel One new format)
                "%d%b%y",  # 26DEC24
                "%d %b %y",  # 26 DEC 24
                "%d %b %Y",  # 26 DEC 2024
            ]
        elif broker == "fyers":
            formats = [
                "%d %b %y",  # 26 DEC 24 (Fyers format)
                "%d%b%y",  # 26DEC24
                "%d%b%Y",  # 26DEC2024
                "%d-%b-%y",  # 26-Dec-24
            ]
        else:
            # Default formats
            formats = [
                "%d%b%Y",
                "%d%b%y",
                "%d %b %y",
                "%d %b %Y",
            ]

        for fmt in formats:
            try:
                dt = datetime.strptime(expiry_str.replace(" ", " "), fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

        return None

    # =========================================================================
    # Query methods
    # =========================================================================

    def query_equity(self, broker: str, base_symbol_value: str) -> dict | None:
        """Query catalog for equity symbol.

        Args:
            broker: Broker name
            base_symbol_value: Symbol value (e.g., "NIFTY", "RELIANCE")

        Returns:
            Dictionary with symbol details or None if not found
        """
        broker = self.normalize_broker(broker)
        mapping = self.COLUMN_MAPPINGS[broker]

        df = self.load_catalog(broker)

        result = df.filter(
            (pl.col(mapping["name_col"]) == base_symbol_value)
            & (pl.col("market_type") == "Cash")
            & (pl.col("segment_type") == "Equity")
        ).collect()

        if result.is_empty():
            return None

        row = result.row(0, named=True)

        return self._extract_result(broker, row)

    def query_future(
        self, broker: str, base_symbol_value: str, expiry: str
    ) -> dict | None:
        """Query catalog for future symbol.

        Args:
            broker: Broker name
            base_symbol_value: Symbol value (e.g., "NIFTY")
            expiry: Expiry string in broker-specific format

        Returns:
            Dictionary with symbol details or None if not found
        """
        broker = self.normalize_broker(broker)
        mapping = self.COLUMN_MAPPINGS[broker]

        df = self.load_catalog(broker)

        result = df.filter(
            (pl.col(mapping["name_col"]) == base_symbol_value)
            & (pl.col("market_type") == "Derivative")
            & (pl.col("segment_type") == "Future")
            & (pl.col("expiry") == expiry)
        ).collect()

        if result.is_empty():
            return None

        row = result.row(0, named=True)

        return self._extract_result(broker, row)

    def query_option(
        self,
        broker: str,
        base_symbol_value: str,
        expiry: str,
        strike: int,
        option_type: str,
    ) -> dict | None:
        """Query catalog for option symbol.

        Uses broker-specific strike formatting.

        Args:
            broker: Broker name
            base_symbol_value: Symbol value (e.g., "NIFTY")
            expiry: Expiry string in broker-specific format
            strike: Strike price as integer (e.g., 22500)
            option_type: "CE" or "PE"

        Returns:
            Dictionary with symbol details or None if not found
        """
        broker = self.normalize_broker(broker)
        mapping = self.COLUMN_MAPPINGS[broker]

        # Format strike for broker
        strike_formatted = self.format_strike(broker, strike)

        df = self.load_catalog(broker)

        result = df.filter(
            (pl.col(mapping["name_col"]) == base_symbol_value)
            & (pl.col("market_type") == "Derivative")
            & (pl.col("segment_type") == "Option")
            & (pl.col("expiry") == expiry)
            & (pl.col("strike") == strike_formatted)
            & (pl.col("opt_type") == option_type)
        ).collect()

        if result.is_empty():
            # Try with symbol containing option type (some brokers)
            result = df.filter(
                (pl.col(mapping["name_col"]) == base_symbol_value)
                & (pl.col("market_type") == "Derivative")
                & (pl.col("segment_type") == "Option")
                & (pl.col("expiry") == expiry)
                & (pl.col("strike") == strike_formatted)
                & (pl.col("symbol").str.contains(option_type))
            ).collect()

        if result.is_empty():
            return None

        row = result.row(0, named=True)

        return self._extract_result(broker, row)

    def query_catalog(
        self,
        broker: str,
        base_symbol_value: str,
        segment_type: str,
        expiry: str | None = None,
        strike: int | None = None,
        option_type: str | None = None,
    ) -> dict | None:
        """Generic query for any instrument type.

        Automatically routes to the appropriate query method based on segment_type.

        Args:
            broker: Broker name
            base_symbol_value: Symbol value (e.g., "NIFTY")
            segment_type: "Equity", "Future", or "Option"
            expiry: Expiry string (required for Future/Option)
            strike: Strike price as integer (required for Option)
            option_type: "CE" or "PE" (required for Option)

        Returns:
            Dictionary with symbol details or None if not found
        """
        if segment_type == "Equity":
            return self.query_equity(broker, base_symbol_value)

        if segment_type == "Future":
            if not expiry:
                raise ValueError("expiry is required for Future")
            return self.query_future(broker, base_symbol_value, expiry)

        if segment_type == "Option":
            if not expiry:
                raise ValueError("expiry is required for Option")
            if strike is None:
                raise ValueError("strike is required for Option")
            if not option_type:
                raise ValueError("option_type is required for Option")
            return self.query_option(
                broker, base_symbol_value, expiry, strike, option_type
            )

        raise ValueError(f"Invalid segment_type: {segment_type}")

    def _extract_result(self, broker: str, row: dict) -> dict:
        """Extract standard result from broker-specific row.

        Args:
            broker: Broker name
            row: Row dictionary from Polars DataFrame

        Returns:
            Standardized result dictionary
        """
        mapping = self.COLUMN_MAPPINGS[broker]

        return {
            "symbol_name": row.get(mapping["symbol_col"], ""),
            "symbol_token": row.get(
                mapping["name_col"], row.get(mapping["symbol_col"], "")
            ),
            "exchange_token": str(row.get(mapping["token_col"], "")),
            # lot_size removed - will get from base_symbol (universal value)
            "exchange": row.get("exchange", "NSE"),
            "market_type": row.get("market_type", "Derivative"),
            "segment_type": row.get("segment_type", "Option"),
        }

    def list_catalogs(self) -> list[dict]:
        """List all available broker catalogs.

        Returns:
            List of catalog info dictionaries
        """
        catalogs = []

        for broker in self.SUPPORTED_BROKERS:
            info = self.get_catalog_info(broker)
            if info:
                catalogs.append(info)

        return catalogs
