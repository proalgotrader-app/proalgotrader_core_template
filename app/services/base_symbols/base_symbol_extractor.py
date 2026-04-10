"""
Base Symbol Extractor - Main orchestrator for extracting base symbols from catalogs.

Orchestrates the complete flow:
1. Load broker catalog (Parquet)
2. Filter to NSE F&O symbols only
3. Infer strike_size from option strikes
4. Extract lot_size from any contract
5. Create/update base_symbols in database
"""

from datetime import datetime
from uuid import uuid4

import polars as pl
from sqlmodel import Session, select

from app.models.base_symbol import BaseSymbol
from app.services.base_symbols.adapters.angel_one_adapter import (
    AngelOneBaseSymbolAdapter,
)
from app.services.base_symbols.adapters.base_adapter import (
    ExtractedBaseSymbol,
    SymbolType,
)
from app.services.base_symbols.strike_inference import (
    infer_strike_size_from_strikes,
)
from app.services.broker_symbols.catalog_manager import CatalogManager

# Known NSE F&O indices
KNOWN_NSE_FNO_INDICES = {"NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "NIFTYNXT50"}


class BaseSymbolExtractor:
    """
    Extract NSE F&O base symbols from broker catalog.

    Extracts:
    - NSE F&O Indices (NIFTY, BANKNIFTY, etc.)
    - NSE F&O Stocks (RELIANCE, INFY, etc.)

    Excludes:
    - BSE symbols (SENSEX, BANKEX)
    - Non-F&O stocks
    - Test symbols

    Result: ~217 NSE F&O symbols
    """

    ADAPTERS = {
        "angel-one": AngelOneBaseSymbolAdapter,
        # 'fyers': FyersBaseSymbolAdapter,  # Future implementation
        # 'shoonya': ShoonyaBaseSymbolAdapter,  # Future implementation
    }

    def __init__(self, session: Session, broker: str = "angel-one"):
        """
        Initialize extractor.

        Args:
            session: Database session
            broker: Broker name (default: angel-one)
        """
        self.session = session
        self.broker = broker.lower()
        self.catalog_manager = CatalogManager()

        if self.broker not in self.ADAPTERS:
            raise ValueError(f"Unsupported broker: {broker}")

        self.adapter = self.ADAPTERS[self.broker]()

    def extract_nse_fno_symbols(self) -> list[ExtractedBaseSymbol]:
        """
        Extract NSE F&O activated symbols from catalog.

        Steps:
        1. Load catalog
        2. Filter to NSE F&O (NFO segment)
        3. Find symbols with derivatives AND cash market
        4. Filter out test/GS symbols
        5. Infer strike_size from options
        6. Extract lot_size from contracts

        Returns:
            List of ExtractedBaseSymbol (~217 symbols)
        """
        # Load catalog
        df = self.catalog_manager.load_catalog(self.broker).collect()

        # Get column mappings
        mappings = self.adapter.get_column_mappings()
        symbol_col = mappings["symbol"]

        # Step 1: Get NSE derivatives (NFO segment)
        exchange_filter = self.adapter.get_exchange_filter()
        nse_deriv = df.filter(
            pl.col(exchange_filter.keys().__iter__().__next__())
            == list(exchange_filter.values())[0]
        )

        # Step 2: Get NSE cash market
        nse_cash = df.filter(pl.col("exchange") == "NSE")

        # Step 3: F&O activated (derivatives + cash)
        nse_deriv_symbols = set(nse_deriv[symbol_col].unique().to_list())
        nse_cash_symbols = set(nse_cash[symbol_col].unique().to_list())
        nse_fno_activated = nse_deriv_symbols & nse_cash_symbols

        # Step 4: Filter clean
        nse_fno_clean = [
            s
            for s in nse_fno_activated
            if "TEST" not in s.upper() and "GS" not in s and not s[:3].isdigit()
        ]

        # Step 5: Get symbols with options
        nse_with_options = set(
            nse_deriv.filter(pl.col("segment_type") == "Option")[symbol_col]
            .unique()
            .to_list()
        )

        # Step 6: Final NSE F&O list
        nse_fno_with_options = [s for s in nse_fno_clean if s in nse_with_options]

        # Step 7: Separate indices and stocks
        nse_indices = [s for s in nse_deriv_symbols if s in KNOWN_NSE_FNO_INDICES]
        nse_stocks = [s for s in nse_fno_with_options if s not in KNOWN_NSE_FNO_INDICES]

        print("NSE F&O Symbols:")
        print(f"  Indices: {len(nse_indices)}")
        print(f"  Stocks: {len(nse_stocks)}")
        print(f"  Total: {len(nse_indices) + len(nse_stocks)}")

        # Step 8: Extract details for each
        symbols = []

        for symbol_name in set(nse_indices) | set(nse_stocks):
            extracted = self._extract_symbol_details(df, symbol_name)
            if extracted:
                symbols.append(extracted)

        return symbols

    def _extract_symbol_details(
        self, df: pl.DataFrame, symbol: str
    ) -> ExtractedBaseSymbol | None:
        """
        Extract details for a symbol from catalog.

        Args:
            df: Full catalog DataFrame
            symbol: Symbol name

        Returns:
            ExtractedBaseSymbol or None
        """
        mappings = self.adapter.get_column_mappings()
        symbol_col = mappings["symbol"]
        multiplier = self.adapter.get_strike_multiplier()

        # Classify type
        symbol_type = (
            SymbolType.INDEX if symbol in KNOWN_NSE_FNO_INDICES else SymbolType.STOCK
        )

        # Filter to this symbol
        symbol_data = df.filter(pl.col(symbol_col) == symbol)

        if len(symbol_data) == 0:
            return None

        # Infer strike_size from options
        strike_size = self._infer_strike_size(symbol_data, multiplier)

        # Extract lot_size from any derivative contract
        lot_size = self._extract_lot_size(symbol_data)

        # All base symbols are NSE exchange (NFO is a segment, not an exchange)
        exchange = "NSE"

        return ExtractedBaseSymbol(
            exchange=exchange,
            key=f"{symbol}_NSE",
            value=symbol,
            type=symbol_type,
            strike_size=strike_size,
            lot_size=lot_size,
            has_derivatives=True,
            broker=self.broker,
            confidence="High",
        )

    def _infer_strike_size(self, symbol_data: pl.DataFrame, multiplier: int) -> int:
        """
        Infer strike_size from option strikes.

        Args:
            symbol_data: DataFrame filtered to this symbol
            multiplier: Strike multiplier (100 for Angel One, 1 for Fyers)

        Returns:
            Inferred strike_size
        """
        # Get option strikes
        options = symbol_data.filter(pl.col("segment_type") == "Option")

        if len(options) == 0:
            return 0

        # Extract strikes
        strike_col = "strike"
        raw_strikes = options.select(strike_col).unique().to_series().to_list()

        # Normalize to rupees
        normalized_strikes = []
        for s in raw_strikes:
            if s is None:
                continue
            try:
                strike_val = float(str(s).replace(".000000", "").replace(".0", ""))
                strike_rupees = strike_val / multiplier
                normalized_strikes.append(int(strike_rupees))
            except (ValueError, TypeError):
                continue

        if not normalized_strikes:
            return 0

        # Infer strike_size
        strike_size, confidence = infer_strike_size_from_strikes(normalized_strikes)

        return strike_size

    def _extract_lot_size(self, symbol_data: pl.DataFrame) -> int:
        """
        Extract lot_size from derivative contracts.

        Lot size is same for futures and options of the same symbol.
        Prioritize derivatives over cash market.

        Args:
            symbol_data: DataFrame filtered to this symbol

        Returns:
            Lot size (default: 1)
        """
        # Get derivatives first (prioritize over cash)
        derivatives = symbol_data.filter(
            pl.col("segment_type").is_in(["Option", "Future"])
        )

        if len(derivatives) > 0:
            lot_sizes = derivatives.select("lotsize").unique().to_series().to_list()

            if lot_sizes and lot_sizes[0]:
                try:
                    # Return first lot size (should be same for all derivatives)
                    return int(float(lot_sizes[0]))
                except (ValueError, TypeError):
                    pass

        # Fallback to cash market
        cash = symbol_data.filter(pl.col("segment_type") == "Equity")
        if len(cash) > 0:
            lot_sizes = cash.select("lotsize").unique().to_series().to_list()

            if lot_sizes and lot_sizes[0]:
                try:
                    return int(float(lot_sizes[0]))
                except (ValueError, TypeError):
                    pass

        return 1

    def store_symbols(
        self, symbols: list[ExtractedBaseSymbol], dry_run: bool = False
    ) -> dict:
        """
        Store extracted symbols in database.

        Args:
            symbols: List of extracted symbols
            dry_run: If True, don't save (preview only)

        Returns:
            Statistics dict
        """
        stats = {
            "added": 0,
            "updated": 0,
            "unchanged": 0,
            "added_symbols": [],
            "updated_symbols": [],
        }

        if dry_run:
            return stats

        for extracted in symbols:
            existing = self.session.exec(
                select(BaseSymbol).where(BaseSymbol.value == extracted.value)
            ).first()

            if existing:
                # Update if strike_size or lot_size differs
                if (
                    existing.strike_size != extracted.strike_size
                    or existing.lot_size != extracted.lot_size
                ):

                    existing.strike_size = extracted.strike_size
                    existing.lot_size = extracted.lot_size
                    existing.updated_at = datetime.utcnow()
                    self.session.add(existing)
                    stats["updated"] += 1
                    stats["updated_symbols"].append(
                        {
                            "value": extracted.value,
                            "old_strike_size": existing.strike_size,
                            "new_strike_size": extracted.strike_size,
                            "old_lot_size": existing.lot_size,
                            "new_lot_size": extracted.lot_size,
                        }
                    )
                else:
                    stats["unchanged"] += 1
            else:
                # Create new
                new_symbol = BaseSymbol(
                    id=str(uuid4()),
                    exchange=extracted.exchange,
                    key=extracted.key,
                    value=extracted.value,
                    type=extracted.type.value,
                    strike_size=extracted.strike_size,
                    lot_size=extracted.lot_size,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                self.session.add(new_symbol)
                stats["added"] += 1
                stats["added_symbols"].append(
                    {
                        "value": extracted.value,
                        "strike_size": extracted.strike_size,
                        "lot_size": extracted.lot_size,
                    }
                )

        self.session.commit()
        return stats
