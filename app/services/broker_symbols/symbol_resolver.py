"""
Symbol Resolver - Main orchestrator for resolving broker symbols.

Orchestrates the complete flow:
1. Check cache (broker_symbols table)
2. Resolve expiry (if needed) - from broker catalog (data-driven)
3. Resolve strike (if Option)
4. Query broker catalog
5. Store result

Universal values (from base_symbols):
- strike_size: Used for ATM strike calculation
- lot_size: Contract lot size

Broker-specific values (from catalog):
- symbol_name: Broker's symbol identifier
- symbol_token: Broker's token
- exchange_token: Exchange token
- expiry dates: Derived from catalog data
"""

import uuid
from datetime import date

from sqlmodel import Session, select

from app.models.base_symbol import BaseSymbol
from app.models.broker_symbol import BrokerSymbol
from app.services.broker_symbols.catalog_manager import CatalogManager
from app.services.broker_symbols.expiry_resolver import ExpiryResolver
from app.services.broker_symbols.strike_resolver import resolve_strike_price


class SymbolResolver:
    """Main orchestrator for resolving broker symbols.

    Handles the complete resolution flow:
    1. Check if symbol already exists in broker_symbols table
    2. Resolve expiry date from user input
    3. Resolve strike price (for options)
    4. Query broker catalog (Parquet)
    5. Store result in broker_symbols table

    Auto-downloads catalog if:
    - Catalog doesn't exist
    - Catalog is older than 24 hours

    Example Usage:
        resolver = SymbolResolver(session)
        symbol = await resolver.resolve(
            broker="angel-one",
            base_symbol_id="uuid-nifty-50",
            segment_type="Option",
            expiry_input=("Weekly", 0),
            strike_price_input=0,
            option_type="CE",
            equity_ltp=24167.50,
        )
    """

    # Catalog freshness threshold in hours
    CATALOG_MAX_AGE_HOURS = 24

    def __init__(self, session: Session):
        """Initialize SymbolResolver with database session.

        Args:
            session: SQLModel session for database access
        """
        self.session = session
        self.catalog_manager = CatalogManager()
        self._adapters = {}  # Lazy-load adapters

    def _get_adapter(self, broker: str):
        """Get the catalog adapter for a broker (lazy-load).

        Args:
            broker: Broker name

        Returns:
            Adapter instance for the broker
        """
        broker = self.catalog_manager.normalize_broker(broker)

        if broker not in self._adapters:
            if broker == "angel-one":
                from app.services.broker_symbols.adapters.angel_one_adapter import (
                    AngelOneAdapter,
                )

                self._adapters[broker] = AngelOneAdapter()
            elif broker == "fyers":
                from app.services.broker_symbols.adapters.fyers_adapter import (
                    FyersAdapter,
                )

                self._adapters[broker] = FyersAdapter()
            elif broker == "shoonya":
                from app.services.broker_symbols.adapters.shoonya_adapter import (
                    ShoonyaAdapter,
                )

                self._adapters[broker] = ShoonyaAdapter()
            else:
                raise ValueError(f"No adapter for broker: {broker}")

        return self._adapters[broker]

    async def ensure_catalog_fresh(self, broker: str) -> None:
        """Ensure catalog exists and is fresh.

        Downloads catalog if:
        - Catalog doesn't exist
        - Catalog is older than CATALOG_MAX_AGE_HOURS

        Args:
            broker: Broker name

        Raises:
            Exception: If download fails
        """
        broker = self.catalog_manager.normalize_broker(broker)

        # Check if catalog is fresh
        if self.catalog_manager.is_catalog_fresh(broker, self.CATALOG_MAX_AGE_HOURS):
            return  # Catalog is fresh, no action needed

        # Catalog needs to be downloaded
        print(
            f"[SymbolResolver] Catalog for {broker} is missing or stale. Downloading..."
        )

        adapter = self._get_adapter(broker)
        await adapter.sync_catalog()

        print(f"[SymbolResolver] Catalog for {broker} downloaded successfully.")

    def normalize_broker(self, broker: str) -> str:
        """Normalize broker name (handle paper trading).

        Args:
            broker: Broker name (e.g., 'angel-one', 'paper-angel-one')

        Returns:
            Normalized broker name
        """
        return self.catalog_manager.normalize_broker(broker)

    async def resolve(
        self,
        broker: str,
        base_symbol_id: str,
        segment_type: str,
        expiry_input: tuple[str, int] | None = None,
        expiry_date: str | None = None,
        strike_price: int | None = None,
        strike_price_input: int | None = None,
        option_type: str | None = None,
        equity_ltp: float | None = None,
    ) -> BrokerSymbol | None:
        """Resolve a broker symbol.

        Args:
            broker: Broker name (e.g., 'angel-one', 'fyers', 'paper-angel-one')
            base_symbol_id: UUID of the base symbol
            segment_type: 'Equity', 'Future', or 'Option'
            expiry_input: ('Weekly', index) or ('Monthly', index) for Future/Option
                         e.g., ('Weekly', 0) for current weekly
                         e.g., ('Monthly', 1) for next monthly
            expiry_date: ISO date string '2024-12-26' (alternative to expiry_input)
            strike_price: Direct strike price (e.g., 22500) for Option
            strike_price_input: ATM-relative strike (-2, -1, 0, 1, 2) for Option
                                Requires equity_ltp to be provided
            option_type: 'CE' or 'PE' for Option
            equity_ltp: LTP of equity symbol (required if using strike_price_input)

        Returns:
            BrokerSymbol instance or None if resolution fails

        Raises:
            ValueError: If required parameters are missing or invalid

        Example:
            >>> # Resolve equity
            >>> symbol = await resolver.resolve(
            ...     broker="angel-one",
            ...     base_symbol_id="uuid-nifty-50",
            ...     segment_type="Equity",
            ... )

            >>> # Resolve future
            >>> symbol = await resolver.resolve(
            ...     broker="angel-one",
            ...     base_symbol_id="uuid-nifty-50",
            ...     segment_type="Future",
            ...     expiry_input=("Monthly", 0),
            ... )

            >>> # Resolve option with ATM-relative strike
            >>> symbol = await resolver.resolve(
            ...     broker="angel-one",
            ...     base_symbol_id="uuid-nifty-50",
            ...     segment_type="Option",
            ...     expiry_input=("Weekly", 0),
            ...     strike_price_input=0,  # ATM
            ...     option_type="CE",
            ...     equity_ltp=24167.50,
            ... )

            >>> # Resolve option with direct strike
            >>> symbol = await resolver.resolve(
            ...     broker="angel-one",
            ...     base_symbol_id="uuid-nifty-50",
            ...     segment_type="Option",
            ...     expiry_input=("Weekly", 0),
            ...     strike_price=24150,  # Direct strike
            ...     option_type="CE",
            ... )
        """
        # Normalize broker name
        broker = self.normalize_broker(broker)

        # Validate broker
        if broker not in self.catalog_manager.SUPPORTED_BROKERS:
            raise ValueError(f"Unsupported broker: {broker}")

        # Get base symbol
        base_symbol = self.session.get(BaseSymbol, base_symbol_id)
        if not base_symbol:
            raise ValueError(f"Base symbol not found: {base_symbol_id}")

        # Infer market_type from segment_type
        market_type = "Cash" if segment_type == "Equity" else "Derivative"

        # === EQUITY RESOLUTION ===
        if segment_type == "Equity":
            # Check cache first
            existing = self._check_cache(
                broker=broker,
                base_symbol=base_symbol,
                market_type=market_type,
                segment_type=segment_type,
            )

            if existing:
                return existing

            # Ensure catalog is fresh before querying
            await self.ensure_catalog_fresh(broker)

            return await self._resolve_equity(
                broker=broker,
                base_symbol=base_symbol,
                market_type=market_type,
                segment_type=segment_type,
            )

        # === FUTURE/OPTION RESOLUTION ===
        # Parse expiry first (needed for cache check)
        if expiry_date:
            # Use provided date directly
            # Determine period - default to Weekly if not specified
            expiry_period = "Weekly"  # Will be determined from catalog later
        elif expiry_input:
            # Need catalog to resolve expiry_input
            # Check cache first with just the input
            pass  # Will handle below
        else:
            raise ValueError(
                "expiry_input or expiry_date is required for Future/Option"
            )

        # Parse strike for Option (needed for cache check)
        if segment_type == "Option":
            if option_type is None:
                raise ValueError("option_type is required for Option")
            if option_type.upper() not in ["CE", "PE"]:
                raise ValueError("option_type must be 'CE' or 'PE'")

            # Calculate strike price for cache lookup
            if strike_price is not None:
                cache_strike_price = strike_price
            elif strike_price_input is not None:
                if equity_ltp is None:
                    raise ValueError(
                        "equity_ltp is required when using strike_price_input for ATM calculation"
                    )
                cache_strike_price = resolve_strike_price(
                    ltp=equity_ltp,
                    strike_size=base_symbol.strike_size,
                    strike_price_input=strike_price_input,
                )
            else:
                raise ValueError(
                    "Either strike_price or strike_price_input+equity_ltp is required for Option"
                )
        else:
            cache_strike_price = None

        # If expiry_date provided directly, check cache first
        if expiry_date:
            # Determine period from catalog or default
            expiry_period = "Weekly"  # Default

            # Check cache
            existing = self._check_cache(
                broker=broker,
                base_symbol=base_symbol,
                market_type=market_type,
                segment_type=segment_type,
                expiry_date=expiry_date,
                strike_price=cache_strike_price,
                option_type=option_type.upper() if option_type else None,
            )

            if existing:
                return existing

            # Not in cache - need catalog
            await self.ensure_catalog_fresh(broker)

            # Determine period from catalog
            expiry_resolver = ExpiryResolver()
            weekly_dates, monthly_dates = expiry_resolver.get_expiry_dates(
                broker=broker,
                base_symbol=base_symbol.value,
                segment_type="Option" if segment_type == "Option" else "Future",
            )

            expiry_period = "Monthly" if expiry_date in monthly_dates else "Weekly"

            broker_expiry = self.catalog_manager.format_expiry(broker, expiry_date)
            final_expiry_date = expiry_date
            final_strike_price = cache_strike_price

        else:
            # expiry_input provided - need catalog to resolve
            # Ensure catalog is fresh
            await self.ensure_catalog_fresh(broker)

            # Resolve expiry from catalog
            resolved_expiry = await self._resolve_expiry(
                broker=broker,
                base_symbol=base_symbol,
                expiry_input=expiry_input,
                expiry_date=None,
                segment_type=segment_type,
            )

            if not resolved_expiry:
                raise ValueError(
                    "Could not resolve expiry. Provide either expiry_input or expiry_date."
                )

            expiry_period, final_expiry_date = resolved_expiry
            broker_expiry = self.catalog_manager.format_expiry(
                broker, final_expiry_date
            )
            final_strike_price = cache_strike_price

        # === FUTURE RESOLUTION ===
        if segment_type == "Future":
            return await self._resolve_future(
                broker=broker,
                base_symbol=base_symbol,
                market_type=market_type,
                segment_type=segment_type,
                expiry_period=expiry_period,
                expiry_date=final_expiry_date,
                broker_expiry=broker_expiry,
            )

        # === OPTION RESOLUTION ===
        return await self._resolve_option(
            broker=broker,
            base_symbol=base_symbol,
            market_type=market_type,
            segment_type=segment_type,
            expiry_period=expiry_period,
            expiry_date=final_expiry_date,
            broker_expiry=broker_expiry,
            strike_price=final_strike_price,
            option_type=option_type.upper(),
        )

    async def _resolve_expiry(
        self,
        broker: str,
        base_symbol: BaseSymbol,
        expiry_input: tuple[str, int] | None,
        expiry_date: str | None,
        segment_type: str = "Option",
    ) -> tuple[str, str] | None:
        """Resolve expiry from input or provided date.

        Uses data-driven approach from broker catalog:
        - Queries catalog for actual expiry dates
        - Monthly = last expiry in month
        - Weekly = all other expiries

        Priority:
            1. If expiry_input provided → convert to date using catalog
            2. If expiry_date provided → use directly

        Args:
            broker: Broker name
            base_symbol: BaseSymbol instance
            expiry_input: ('Weekly', index) or ('Monthly', index)
            expiry_date: ISO date string '2024-12-26'
            segment_type: 'Future' or 'Option'

        Returns:
            Tuple of (expiry_period, expiry_date) or None
        """
        expiry_resolver = ExpiryResolver()

        if expiry_input:
            # Convert expiry_input to date using broker catalog
            period, idx = expiry_input

            # Get expiry dates from catalog
            # Futures always use Monthly
            actual_segment = "Future" if segment_type == "Future" else "Option"

            dates = expiry_resolver.get_filtered_expiry_dates(
                broker=broker,
                base_symbol=base_symbol.value,
                expiry_period=period,
                segment_type=actual_segment,
            )

            # Filter to today or later
            today = date.today().isoformat()
            future_dates = [d for d in dates if d >= today]

            if idx < len(future_dates):
                return (period, future_dates[idx])

            return None

        if expiry_date:
            # Use provided date directly
            # Determine period from catalog classification
            weekly_dates, monthly_dates = expiry_resolver.get_expiry_dates(
                broker=broker,
                base_symbol=base_symbol.value,
                segment_type="Option" if segment_type == "Option" else "Future",
            )

            if expiry_date in monthly_dates:
                return ("Monthly", expiry_date)
            elif expiry_date in weekly_dates:
                return ("Weekly", expiry_date)
            else:
                # Default to Weekly if not found in either
                return ("Weekly", expiry_date)

        return None

    async def _resolve_equity(
        self,
        broker: str,
        base_symbol: BaseSymbol,
        market_type: str,
        segment_type: str,
    ) -> BrokerSymbol | None:
        """Resolve equity symbol from catalog.

        Args:
            broker: Broker name
            base_symbol: BaseSymbol instance
            market_type: 'Cash'
            segment_type: 'Equity'

        Returns:
            BrokerSymbol instance or None
        """
        # Check cache first
        existing = self._check_cache(
            broker=broker,
            base_symbol=base_symbol,
            market_type=market_type,
            segment_type=segment_type,
        )

        if existing:
            return existing

        # Query catalog
        result = self.catalog_manager.query_equity(
            broker=broker,
            base_symbol_value=base_symbol.value,
        )

        if not result:
            return None

        # Create and store
        return self._create_broker_symbol(
            broker=broker,
            base_symbol=base_symbol,
            market_type=market_type,
            segment_type=segment_type,
            catalog_result=result,
        )

    async def _resolve_future(
        self,
        broker: str,
        base_symbol: BaseSymbol,
        market_type: str,
        segment_type: str,
        expiry_period: str,
        expiry_date: str,
        broker_expiry: str,
    ) -> BrokerSymbol | None:
        """Resolve future symbol from catalog.

        Args:
            broker: Broker name
            base_symbol: BaseSymbol instance
            market_type: 'Derivative'
            segment_type: 'Future'
            expiry_period: 'Weekly' or 'Monthly'
            expiry_date: ISO date string
            broker_expiry: Broker-formatted expiry string

        Returns:
            BrokerSymbol instance or None
        """
        # Check cache first
        existing = self._check_cache(
            broker=broker,
            base_symbol=base_symbol,
            market_type=market_type,
            segment_type=segment_type,
            expiry_date=expiry_date,
        )

        if existing:
            return existing

        # Query catalog
        result = self.catalog_manager.query_future(
            broker=broker,
            base_symbol_value=base_symbol.value,
            expiry=broker_expiry,
        )

        if not result:
            return None

        # Create and store
        return self._create_broker_symbol(
            broker=broker,
            base_symbol=base_symbol,
            market_type=market_type,
            segment_type=segment_type,
            expiry_period=expiry_period,
            expiry_date=expiry_date,
            catalog_result=result,
        )

    async def _resolve_option(
        self,
        broker: str,
        base_symbol: BaseSymbol,
        market_type: str,
        segment_type: str,
        expiry_period: str,
        expiry_date: str,
        broker_expiry: str,
        strike_price: int,
        option_type: str,
    ) -> BrokerSymbol | None:
        """Resolve option symbol from catalog.

        Args:
            broker: Broker name
            base_symbol: BaseSymbol instance
            market_type: 'Derivative'
            segment_type: 'Option'
            expiry_period: 'Weekly' or 'Monthly'
            expiry_date: ISO date string
            broker_expiry: Broker-formatted expiry string
            strike_price: Strike price (e.g., 24150)
            option_type: 'CE' or 'PE'

        Returns:
            BrokerSymbol instance or None
        """
        # Check cache first
        existing = self._check_cache(
            broker=broker,
            base_symbol=base_symbol,
            market_type=market_type,
            segment_type=segment_type,
            expiry_date=expiry_date,
            strike_price=strike_price,
            option_type=option_type,
        )

        if existing:
            return existing

        # Query catalog (strike is now an integer, catalog_manager handles formatting)
        result = self.catalog_manager.query_option(
            broker=broker,
            base_symbol_value=base_symbol.value,
            expiry=broker_expiry,
            strike=strike_price,  # Pass int, catalog_manager formats for broker
            option_type=option_type,
        )

        if not result:
            return None

        # Create and store
        return self._create_broker_symbol(
            broker=broker,
            base_symbol=base_symbol,
            market_type=market_type,
            segment_type=segment_type,
            expiry_period=expiry_period,
            expiry_date=expiry_date,
            strike_price=strike_price,
            option_type=option_type,
            catalog_result=result,
        )

    def _check_cache(
        self,
        broker: str,
        base_symbol: BaseSymbol,
        market_type: str,
        segment_type: str,
        expiry_date: str | None = None,
        strike_price: int | None = None,
        option_type: str | None = None,
    ) -> BrokerSymbol | None:
        """Check if symbol already exists in cache.

        Args:
            broker: Broker name
            base_symbol: BaseSymbol instance
            market_type: 'Cash' or 'Derivative'
            segment_type: 'Equity', 'Future', or 'Option'
            expiry_date: ISO date string (for Future/Option)
            strike_price: Strike price (for Option)
            option_type: 'CE' or 'PE' (for Option)

        Returns:
            BrokerSymbol if found, None otherwise
        """
        query = select(BrokerSymbol).where(
            BrokerSymbol.broker_title == broker,
            BrokerSymbol.base_symbol_id == base_symbol.id,
            BrokerSymbol.market_type == market_type,
            BrokerSymbol.segment_type == segment_type,
        )

        if expiry_date:
            query = query.where(BrokerSymbol.expiry_date == expiry_date)

        if strike_price is not None:
            query = query.where(BrokerSymbol.strike_price == strike_price)

        if option_type:
            query = query.where(BrokerSymbol.option_type == option_type)

        return self.session.exec(query).first()

    def _create_broker_symbol(
        self,
        broker: str,
        base_symbol: BaseSymbol,
        market_type: str,
        segment_type: str,
        catalog_result: dict,
        expiry_period: str | None = None,
        expiry_date: str | None = None,
        strike_price: int | None = None,
        option_type: str | None = None,
    ) -> BrokerSymbol:
        """Create and store a new broker symbol.

        Args:
            broker: Broker name
            base_symbol: BaseSymbol instance
            market_type: 'Cash' or 'Derivative'
            segment_type: 'Equity', 'Future', or 'Option'
            catalog_result: Result from catalog query
            expiry_period: 'Weekly' or 'Monthly'
            expiry_date: ISO date string
            strike_price: Strike price
            option_type: 'CE' or 'PE'

        Returns:
            Created BrokerSymbol instance
        """
        broker_symbol = BrokerSymbol(
            id=str(uuid.uuid4()),
            base_symbol_id=base_symbol.id,
            broker_title=broker,
            exchange=catalog_result.get(
                "exchange", "NSE" if segment_type == "Equity" else "NFO"
            ),
            market_type=market_type,
            segment_type=segment_type,
            expiry_period=expiry_period,
            expiry_date=expiry_date,
            strike_price=strike_price,
            option_type=option_type,
            lot_size=str(base_symbol.lot_size),  # Lot size from base_symbol (universal)
            symbol_name=catalog_result.get("symbol_name", ""),
            symbol_token=catalog_result.get("symbol_token", ""),
            exchange_token=catalog_result.get("exchange_token", ""),
        )

        self.session.add(broker_symbol)
        self.session.commit()
        self.session.refresh(broker_symbol)

        return broker_symbol
