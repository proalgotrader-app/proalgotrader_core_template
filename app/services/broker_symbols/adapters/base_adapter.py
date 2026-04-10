"""
Base Adapter - Abstract interface for broker catalog adapters.

Each broker (Angel One, Fyers, Shoonya) implements this interface
to download and process their specific catalog format.
"""

from abc import ABC, abstractmethod

import polars as pl


class BaseAdapter(ABC):
    """Abstract base class for broker catalog adapters.

    Each broker has a different API and catalog format. This interface
    provides a standardized way to:
    - Download broker instrument catalogs
    - Convert to standardized Parquet format
    - Query for specific instruments

    Implementations:
        - AngelOneAdapter
        - FyersAdapter
        - ShoonyaAdapter
    """

    @property
    @abstractmethod
    def broker_title(self) -> str:
        """Return broker identifier.

        Returns:
            Broker title (e.g., 'angel-one', 'fyers', 'shoonya')
        """
        pass

    @property
    @abstractmethod
    def catalog_url(self) -> str:
        """Return URL to download catalog.

        Returns:
            URL string for the broker's instrument catalog
        """
        pass

    @abstractmethod
    async def download_catalog(self) -> pl.DataFrame:
        """Download and process broker catalog.

        This method:
        1. Downloads raw catalog from broker's API
        2. Processes and standardizes the data
        3. Returns a Polars DataFrame in standard format

        Returns:
            Polars DataFrame with standardized columns

        Standard Columns:
            - symbol: Broker's symbol name
            - name/ex_symbol: Base symbol identifier
            - token: Broker-specific token
            - expiry: Expiry date (broker format)
            - strike: Strike price
            - exchange: Exchange name
            - opt_type: Option type (CE/PE)
            - lotsize: Lot size
            - market_type: Cash/Derivative
            - segment_type: Equity/Future/Option
        """
        pass

    async def save_catalog(self, df: pl.DataFrame) -> None:
        """Save catalog to Parquet file.

        Args:
            df: Polars DataFrame with catalog data
        """
        from app.services.broker_symbols.catalog_manager import CatalogManager

        catalog_manager = CatalogManager()
        path = catalog_manager.get_catalog_path(self.broker_title)

        # Write to parquet with compression
        df.write_parquet(path, compression="zstd")

    async def sync_catalog(self) -> dict:
        """Download and save catalog.

        This is the main entry point for syncing broker catalogs.

        Returns:
            Dictionary with sync results:
            - broker: Broker name
            - status: 'success' or 'error'
            - count: Number of instruments
            - message: Status message
        """

        try:
            # Download and process
            df = await self.download_catalog()

            # Get catalog info
            count = len(df)

            # Save to parquet
            await self.save_catalog(df)

            return {
                "broker": self.broker_title,
                "status": "success",
                "count": count,
                "message": f"Successfully synced {count} instruments for {self.broker_title}",
            }

        except Exception as e:
            return {
                "broker": self.broker_title,
                "status": "error",
                "count": 0,
                "message": f"Failed to sync catalog: {str(e)}",
            }

    def normalize_dataframe(self, df: pl.DataFrame) -> pl.DataFrame:
        """Normalize DataFrame to standard format.

        Override this method to handle broker-specific column names.

        Args:
            df: Raw DataFrame from broker

        Returns:
            Normalized DataFrame with standard columns
        """
        # This should be overridden by each broker adapter
        return df

    @staticmethod
    def determine_market_type(row: dict) -> str:
        """Determine market type from row data.

        Args:
            row: Dictionary with row data

        Returns:
            'Cash' or 'Derivative'
        """
        segment = str(row.get("segment_type", "")).upper()
        instrument = str(row.get("instrument_type", "")).upper()

        # Derivatives have FUT/OPT in instrument type
        if any(x in instrument for x in ["FUT", "OPT", "FUTURE", "OPTION"]):
            return "Derivative"

        if any(x in segment for x in ["FUTURE", "OPTION", "DERIVATIVE"]):
            return "Derivative"

        return "Cash"

    @staticmethod
    def determine_segment_type(row: dict) -> str:
        """Determine segment type from row data.

        Args:
            row: Dictionary with row data

        Returns:
            'Equity', 'Future', or 'Option'
        """
        instrument = str(row.get("instrument_type", "")).upper()

        if "FUT" in instrument:
            return "Future"

        if "OPT" in instrument or "CALL" in instrument or "PUT" in instrument:
            return "Option"

        if "CE" in instrument or "PE" in instrument:
            return "Option"

        return "Equity"

    @staticmethod
    def determine_option_type(row: dict) -> str:
        """Determine option type from row data.

        Args:
            row: Dictionary with row data

        Returns:
            'CE', 'PE', or ''
        """
        opt_type = str(row.get("opt_type", "")).upper()

        if opt_type in ["CE", "PE"]:
            return opt_type

        # Try to extract from symbol name
        symbol = str(row.get("symbol", "")).upper()
        if "CE" in symbol:
            return "CE"
        if "PE" in symbol:
            return "PE"

        return ""
