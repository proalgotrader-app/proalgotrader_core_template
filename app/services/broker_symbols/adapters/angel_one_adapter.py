"""
Angel One Catalog Adapter - Downloads and processes Angel One instrument catalog.

Angel One Broker Specifics:
- Catalog URL: https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPISchemaToDownload.json
- Column names: name, symbol, token, expiry, strike, lotsize, etc.
- Weekly/Monthly expiry format: DDMMMYY (e.g., 26DEC24)
- Symbol names include full contract specification (NIFTY26DEC24FUT)
"""

import httpx
import polars as pl

from app.services.broker_symbols.adapters.base_adapter import BaseAdapter


class AngelOneAdapter(BaseAdapter):
    """Angel One broker catalog adapter.

    Downloads Angel One instrument catalog and converts to standard format.

    Example catalog entry:
        {
            "token": "26000",
            "symbol": "NIFTY",
            "name": "NIFTY",
            "expiry": "26DEC24",
            "strike": "24150",
            "lotsize": "25",
            "exchange": "NFO",
            "exch_seg": "NFO",
            "instrumenttype": "FUTSTK",
            ...
        }
    """

    CATALOG_URL = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"

    @property
    def broker_title(self) -> str:
        return "angel-one"

    @property
    def catalog_url(self) -> str:
        return self.CATALOG_URL

    async def download_catalog(self) -> pl.DataFrame:
        """Download and process Angel One catalog.

        Steps:
            1. Download JSON from Angel One
            2. Normalize column names
            3. Standardize market/segment types
            4. Return Polars DataFrame

        Returns:
            Polars DataFrame with standardized columns:
            - symbol: Full symbol name
            - name: Base symbol (NIFTY, BANKNIFTY, etc.)
            - token: Angel One token
            - expiry: Expiry string
            - strike: Strike price
            - opt_type: CE/PE
            - lotsize: Lot size
            - exchange: Exchange name
            - market_type: Cash/Derivative
            - segment_type: Equity/Future/Option
        """
        print(f"[Angel One] Downloading catalog from {self.CATALOG_URL}")

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(self.CATALOG_URL)
            response.raise_for_status()

        data = response.json()

        # Create Polars DataFrame
        df = pl.DataFrame(data)

        print(f"[Angel One] Raw catalog has {len(df)} instruments")

        # Normalize DataFrame
        df = self.normalize_dataframe(df)

        print(f"[Angel One] Processed {len(df)} instruments")

        return df

    def normalize_dataframe(self, df: pl.DataFrame) -> pl.DataFrame:
        """Normalize Angel One-specific format to standard.

        Angel One Specifics:
            - 'name' contains the base symbol
            - 'symbol' is the full contract name
            - 'token' is Angel One's instrument token
            - 'expiry' format depends on segment

        Args:
            df: Raw DataFrame from Angel One

        Returns:
            Normalized DataFrame with standard columns
        """
        # Select relevant columns and rename
        df = df.select(
            [
                pl.col("symbol").alias("symbol"),
                pl.col("name").alias("name"),
                pl.col("token").alias("token"),
                pl.col("expiry").alias("expiry"),
                pl.col("strike").alias("strike"),
                pl.col("lotsize").alias("lotsize"),
                pl.col("exch_seg").alias("exchange"),
                pl.col("instrumenttype").alias("instrument_type"),
            ]
        )

        # Derive segment_type from instrument_type
        instrument_upper = pl.col("instrument_type").str.to_uppercase()
        df = df.with_columns(
            [
                pl.when(
                    instrument_upper.str.contains("FUT")
                    | instrument_upper.str.contains("FUTURE")
                )
                .then(pl.lit("Future"))
                .when(
                    instrument_upper.str.contains("OPT")
                    | instrument_upper.str.contains("OPTION")
                )
                .then(pl.lit("Option"))
                .otherwise(pl.lit("Equity"))
                .alias("segment_type"),
                pl.when(pl.col("exchange").str.to_uppercase().is_in(["NSE", "BSE"]))
                .then(pl.lit("Cash"))
                .otherwise(pl.lit("Derivative"))
                .alias("market_type"),
            ]
        )

        # Derive option type from expiry or symbol
        # Angel One has opt_type in expiry sometimes: "26DEC24CE" or "26DEC24PE"
        symbol_upper = pl.col("symbol").str.to_uppercase()
        expiry_upper = pl.col("expiry").str.to_uppercase()

        df = df.with_columns(
            [
                pl.when(expiry_upper.str.ends_with("CE"))
                .then(pl.lit("CE"))
                .when(expiry_upper.str.ends_with("PE"))
                .then(pl.lit("PE"))
                .when(pl.col("segment_type") == pl.lit("Option"))
                .then(
                    pl.when(symbol_upper.str.contains("CE"))
                    .then(pl.lit("CE"))
                    .when(symbol_upper.str.contains("PE"))
                    .then(pl.lit("PE"))
                    .otherwise(pl.lit(""))
                )
                .otherwise(pl.lit(""))
                .alias("opt_type"),
            ]
        )

        # Normalize expiry format - remove CE/PE suffix if present
        df = df.with_columns(
            [pl.col("expiry").str.replace(r"(CE|PE)$", "").alias("expiry")]
        )

        # Filter out invalid entries
        df = df.filter(
            pl.col("token").is_not_null()
            & (pl.col("token") != "")
            & (pl.col("name").is_not_null())
            & (pl.col("name") != "")
        )

        # Convert strike to string (empty for non-options)
        df = df.with_columns(
            [
                pl.when(pl.col("segment_type").is_in(["Future", "Option"]))
                .then(pl.col("strike").fill_null("0"))
                .otherwise(pl.lit(""))
                .alias("strike"),
            ]
        )

        return df


class AngelOneSymbolAdapter:
    """Angel One symbol adapter for converting to broker-specific format.

    Handles conversion from base symbol to Angel One symbol names:
    - Equity: Name as-is (NIFTY, RELIANCE)
    - Future: NIFTY26DEC24FUT
    - Option: NIFTY26DEC2424150CE
    """

    @staticmethod
    def get_equity_symbol(base_symbol: str) -> str:
        """Get equity symbol name.

        Args:
            base_symbol: Base symbol (NIFTY, RELIANCE)

        Returns:
            Symbol name for Angel One
        """
        return base_symbol

    @staticmethod
    def get_future_symbol(base_symbol: str, expiry: str) -> str:
        """Get future symbol name.

        Args:
            base_symbol: Base symbol (NIFTY)
            expiry: Broker-formatted expiry (26DEC24)

        Returns:
            Future symbol name for Angel One (NIFTY26DEC24FUT)
        """
        return f"{base_symbol}{expiry}FUT"

    @staticmethod
    def get_option_symbol(
        base_symbol: str, expiry: str, strike: str, opt_type: str
    ) -> str:
        """Get option symbol name.

        Args:
            base_symbol: Base symbol (NIFTY)
            expiry: Broker-formatted expiry (26DEC24)
            strike: Strike price (24150)
            opt_type: CE or PE

        Returns:
            Option symbol name for Angel One (NIFTY26DEC2424150CE)
        """
        return f"{base_symbol}{expiry}{strike}{opt_type}"
