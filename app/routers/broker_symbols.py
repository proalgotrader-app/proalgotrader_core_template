"""
Broker Symbols routes for ProAlgoTrader FastAPI.

Provides endpoints for:
- Resolving broker symbols
- Syncing broker catalogs
- Listing cached symbols
"""

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, field_validator, model_validator
from sqlmodel import Session, select

from app.models.base_symbol import BaseSymbol, BaseSymbolRead
from app.models.broker_symbol import BrokerSymbol
from app.routers.auth import get_session_data
from app.services.broker_symbols.catalog_manager import CatalogManager
from app.services.broker_symbols.symbol_resolver import SymbolResolver
from db.database import get_global_session

router = APIRouter(prefix="/api/broker-symbols", tags=["broker-symbols"])
views_router = APIRouter(tags=["broker-symbols-views"])


# =============================================================================
# Request/Response Models
# =============================================================================


class ResolveBrokerSymbolRequest(BaseModel):
    """Request for resolving a broker symbol.

    For Equity:
        - Only base_symbol_id and segment_type required

    For Future:
        - base_symbol_id, segment_type
        - expiry_input OR expiry_date

    For Option:
        - base_symbol_id, segment_type
        - expiry_input OR expiry_date
        - option_type
        - EITHER strike_price (direct) OR strike_price_input + equity_ltp (ATM-relative)

    Strike price can be provided in two ways:
    1. Direct: Pass strike_price (e.g., 22500)
    2. ATM-relative: Pass strike_price_input (-2, -1, 0, 1, 2) + equity_ltp
    """

    # Required for all
    base_symbol_id: str
    segment_type: Literal["Equity", "Future", "Option"]

    # Expiry (required for Future/Option)
    expiry_input: tuple[Literal["Weekly", "Monthly"], int] | None = None
    expiry_date: str | None = None  # ISO format: "2024-12-26"

    # Option-specific - strike can be provided two ways
    strike_price: int | None = None  # Direct strike price (e.g., 22500)
    strike_price_input: int | None = None  # ATM-relative offset: -2, -1, 0, 1, 2
    option_type: Literal["CE", "PE"] | None = None
    equity_ltp: float | None = None  # Required if using strike_price_input

    @model_validator(mode="after")
    def validate_derivatives(self):
        """Validate expiry is provided for Future/Option."""
        if (
            self.segment_type in ["Future", "Option"]
            and self.expiry_input is None
            and self.expiry_date is None
        ):
            raise ValueError(
                f"expiry_input or expiry_date is required for {self.segment_type}"
            )
        return self

    @model_validator(mode="after")
    def validate_options(self):
        """Validate strike and option_type for Option.

        Strike must be provided either:
        - Directly via strike_price, OR
        - Via ATM calculation using strike_price_input + equity_ltp
        """
        if self.segment_type == "Option":
            if self.option_type is None:
                raise ValueError("option_type is required for Option")

            # Must have either direct strike_price OR strike_price_input + equity_ltp
            if self.strike_price is None:
                if self.strike_price_input is None:
                    raise ValueError(
                        "strike_price or strike_price_input is required for Option"
                    )
                if self.equity_ltp is None:
                    raise ValueError(
                        "equity_ltp is required when using strike_price_input"
                    )
        return self

    @field_validator("expiry_input")
    @classmethod
    def validate_expiry_input(cls, v):
        """Validate expiry_input format."""
        if v is not None:
            period, index = v
            if period not in ["Weekly", "Monthly"]:
                raise ValueError("expiry period must be Weekly or Monthly")
            if index < 0:
                raise ValueError("expiry index must be >= 0")
        return v

    @field_validator("expiry_date")
    @classmethod
    def validate_expiry_date(cls, v):
        """Validate expiry_date format."""
        if v is not None:
            try:
                datetime.strptime(v, "%Y-%m-%d")
            except ValueError:
                raise ValueError("expiry_date must be in ISO format: YYYY-MM-DD")
        return v


class BrokerSymbolResponse(BaseModel):
    """Response for resolved broker symbol."""

    id: str
    base_symbol_id: str
    broker_title: str

    # Classification
    exchange: str
    market_type: str
    segment_type: str

    # Derivative details
    expiry_period: str | None = None
    expiry_date: str | None = None
    strike_price: int | None = None
    option_type: str | None = None
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


class CatalogSyncResponse(BaseModel):
    """Response for catalog sync."""

    broker: str
    status: str
    count: int
    message: str
    catalog_info: dict | None = None


# =============================================================================
# Views Routes
# =============================================================================


@views_router.get("/broker-symbols", response_class=HTMLResponse)
async def broker_symbols_page(request: Request):
    """Render broker symbols page."""
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        from fastapi.responses import RedirectResponse

        return RedirectResponse(url="/login", status_code=302)

    session_data = get_session_data(session_cookie)
    if not session_data:
        from fastapi.responses import RedirectResponse

        return RedirectResponse(url="/login", status_code=302)

    from pathlib import Path

    template_path = (
        Path(__file__).parent.parent.parent / "templates" / "broker_symbols.html"
    )
    with open(template_path) as f:
        return HTMLResponse(content=f.read())


# =============================================================================
# API Routes
# =============================================================================


@router.post("/{broker}/resolve", response_model=BrokerSymbolResponse)
async def resolve_broker_symbol(
    broker: str,
    payload: ResolveBrokerSymbolRequest,
    session: Session = Depends(get_global_session),
):
    """Resolve a broker symbol from base symbol.

    This endpoint:
    1. Checks if symbol already exists in broker_symbols table (cache)
    2. If not, resolves expiry from trading days (if Future/Option)
    3. Calculates strike price from ATM (if Option)
    4. Queries broker catalog (Parquet)
    5. Stores and returns the broker symbol

    Args:
        broker: Broker name (e.g., 'angel-one', 'fyers', 'paper-angel-one')
        payload: Resolution request

    Returns:
        Resolved BrokerSymbol

    Raises:
        HTTPException: If resolution fails
    """
    # Verify authentication (optional for local use)
    # For now, allow unauthenticated access for local development

    resolver = SymbolResolver(session)

    try:
        broker_symbol = await resolver.resolve(
            broker=broker,
            base_symbol_id=payload.base_symbol_id,
            segment_type=payload.segment_type,
            expiry_input=payload.expiry_input,
            expiry_date=payload.expiry_date,
            strike_price=payload.strike_price,
            strike_price_input=payload.strike_price_input,
            option_type=payload.option_type,
            equity_ltp=payload.equity_ltp,
        )

        if not broker_symbol:
            raise HTTPException(
                status_code=404,
                detail=f"Could not resolve symbol for {broker}. "
                f"Make sure the catalog is synced and the symbol exists.",
            )

        return BrokerSymbolResponse.model_validate(broker_symbol)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to resolve symbol: {str(e)}"
        )


@router.get("/list")
async def list_broker_symbols(
    request: Request,
    broker: str | None = None,
    segment_type: str | None = None,
    base_symbol_id: str | None = None,
    page: int = 1,
    per_page: int = 25,
    session: Session = Depends(get_global_session),
):
    """List cached broker symbols.

    Args:
        broker: Filter by broker (optional)
        segment_type: Filter by segment type (optional)
        base_symbol_id: Filter by base symbol (optional)
        page: Page number
        per_page: Items per page

    Returns:
        List of cached broker symbols
    """
    catalog_manager = CatalogManager()

    # Normalize broker if provided
    if broker:
        broker = catalog_manager.normalize_broker(broker)

    # Build query
    query = select(BrokerSymbol)

    if broker:
        query = query.where(BrokerSymbol.broker_title == broker)

    if base_symbol_id:
        query = query.where(BrokerSymbol.base_symbol_id == base_symbol_id)

    if segment_type:
        query = query.where(BrokerSymbol.segment_type == segment_type)

    # Get total count
    total_count = len(session.exec(query).all())

    # Paginate
    offset = (page - 1) * per_page
    query = (
        query.offset(offset).limit(per_page).order_by(BrokerSymbol.created_at.desc())
    )

    symbols = session.exec(query).all()

    # Get base symbol values for display
    base_symbol_ids = list({s.base_symbol_id for s in symbols})
    base_symbols_query = select(BaseSymbol).where(BaseSymbol.id.in_(base_symbol_ids))
    base_symbols_map = {s.id: s.value for s in session.exec(base_symbols_query).all()}

    # Add base_symbol_value to each symbol
    symbols_data = []
    for s in symbols:
        symbol_dict = s.model_dump()
        symbol_dict["base_symbol_value"] = base_symbols_map.get(
            s.base_symbol_id, s.base_symbol_id
        )
        symbols_data.append(symbol_dict)

    total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1

    return {
        "success": True,
        "broker_symbols": symbols_data,
        "count": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


@router.post("/{broker}/sync-catalog", response_model=CatalogSyncResponse)
async def sync_broker_catalog(
    broker: str,
    request: Request,
    force: bool = False,
    session: Session = Depends(get_global_session),
):
    """Sync broker instrument catalog.

    Downloads the latest instrument catalog from the broker
    and saves it as a Parquet file for fast local queries.

    Args:
        broker: Broker name
        force: If True, download even if catalog exists and is fresh

    Returns:
        Sync status and catalog info
    """
    # Normalize broker name
    catalog_manager = CatalogManager()
    broker = catalog_manager.normalize_broker(broker)

    # Check if catalog is fresh (skip if force=True)
    if not force and catalog_manager.is_catalog_fresh(broker):
        info = catalog_manager.get_catalog_info(broker)
        age = catalog_manager.get_catalog_age(broker)
        return CatalogSyncResponse(
            broker=broker,
            status="skipped",
            count=info.get("row_count", 0) if info else 0,
            message=f"Catalog is fresh (age: {age:.1f} hours). Use force=true to update.",
            catalog_info=info,
        )

    # Import the appropriate adapter
    try:
        if broker == "angel-one":
            from app.services.broker_symbols.adapters.angel_one_adapter import (
                AngelOneAdapter,
            )

            adapter = AngelOneAdapter()
        elif broker == "fyers":
            from app.services.broker_symbols.adapters.fyers_adapter import FyersAdapter

            adapter = FyersAdapter()
        elif broker == "shoonya":
            from app.services.broker_symbols.adapters.shoonya_adapter import (
                ShoonyaAdapter,
            )

            adapter = ShoonyaAdapter()
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported broker: {broker}")

        result = await adapter.sync_catalog()

        # Get catalog info if successful
        catalog_info = None
        if result["status"] == "success":
            catalog_info = catalog_manager.get_catalog_info(broker)

        return CatalogSyncResponse(
            broker=result["broker"],
            status=result["status"],
            count=result["count"],
            message=result["message"],
            catalog_info=catalog_info,
        )

    except ImportError:
        raise HTTPException(
            status_code=501, detail=f"Catalog sync not implemented for {broker}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to sync catalog: {str(e)}")


@router.get("/{broker}/catalog/info")
async def get_catalog_info(
    broker: str,
    request: Request,
):
    """Get information about a broker's cached catalog.

    Args:
        broker: Broker name

    Returns:
        Catalog information (size, row count, last modified) or status if not found
    """
    catalog_manager = CatalogManager()
    broker = catalog_manager.normalize_broker(broker)

    info = catalog_manager.get_catalog_info(broker)
    age = catalog_manager.get_catalog_age(broker)

    if not info:
        return {
            "success": True,
            "exists": False,
            "broker": broker,
            "age_hours": None,
            "catalog": None,
            "message": f"Catalog not found for {broker}. Sync the catalog first.",
        }

    return {
        "success": True,
        "exists": True,
        "broker": broker,
        "age_hours": round(age, 2) if age else None,
        "is_fresh": catalog_manager.is_catalog_fresh(broker),
        "catalog": info,
    }


@router.get("/stats")
async def get_broker_symbols_stats(
    request: Request, session: Session = Depends(get_global_session)
):
    """Get statistics about cached broker symbols.

    Returns counts by broker and segment type.
    """
    from sqlalchemy import func

    # Get count by broker
    query = select(
        BrokerSymbol.broker_title, func.count(BrokerSymbol.id).label("count")
    ).group_by(BrokerSymbol.broker_title)

    results = session.exec(query).all()

    by_broker = {row[0]: row[1] for row in results}
    total = sum(by_broker.values())

    # Get count by segment type
    segment_query = select(
        BrokerSymbol.segment_type, func.count(BrokerSymbol.id).label("count")
    ).group_by(BrokerSymbol.segment_type)

    segment_results = session.exec(segment_query).all()

    by_segment = {row[0]: row[1] for row in segment_results}

    return {
        "success": True,
        "total": total,
        "by_broker": by_broker,
        "equity": by_segment.get("Equity", 0),
        "futures": by_segment.get("Future", 0),
        "options": by_segment.get("Option", 0),
    }


@router.delete("/clear")
async def clear_broker_symbols_cache(
    request: Request,
    broker: str | None = None,
    session: Session = Depends(get_global_session),
):
    """Clear broker symbols cache.

    Args:
        broker: Optional broker name to clear only that broker's symbols

    Returns:
        Number of symbols cleared
    """
    catalog_manager = CatalogManager()

    # Build query
    if broker:
        broker = catalog_manager.normalize_broker(broker)
        query = select(BrokerSymbol).where(BrokerSymbol.broker_title == broker)
    else:
        query = select(BrokerSymbol)

    # Get count before deletion
    symbols = session.exec(query).all()
    count = len(symbols)

    # Delete all
    for symbol in symbols:
        session.delete(symbol)

    session.commit()

    return {
        "success": True,
        "count": count,
        "message": f"Cleared {count} symbols from cache",
    }


@router.get("/catalogs")
async def list_catalogs(request: Request):
    """List all available broker catalogs.

    Returns:
        List of catalog information for each broker
    """
    catalog_manager = CatalogManager()
    catalogs = catalog_manager.list_catalogs()

    return {
        "success": True,
        "catalogs": catalogs,
        "supported_brokers": catalog_manager.SUPPORTED_BROKERS,
    }


@router.get("/base-symbols")
async def list_base_symbols(
    request: Request,
    search: str | None = None,
    page: int = 1,
    per_page: int = 10,
    session: Session = Depends(get_global_session),
):
    """List base symbols for reference.

    Args:
        search: Search by key or value (optional)
        page: Page number
        per_page: Items per page

    Returns:
        List of base symbols
    """
    query = select(BaseSymbol).where(BaseSymbol.deleted_at.is_(None))

    if search:
        query = query.where(
            (BaseSymbol.key.contains(search)) | (BaseSymbol.value.contains(search))
        )

    query = query.order_by(BaseSymbol.value)

    # Get total count
    total_count = len(session.exec(query).all())

    # Paginate
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)

    symbols = session.exec(query).all()

    return {
        "success": True,
        "base_symbols": [BaseSymbolRead.model_validate(s) for s in symbols],
        "count": total_count,
        "page": page,
        "per_page": per_page,
    }
