"""
Base Symbols routes for ProAlgoTrader FastAPI.
Handles syncing and listing base symbols from the global database.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select

from app.models.base_symbol import (
    BaseSymbol,
    BaseSymbolList,
    BaseSymbolRead,
)
from app.routers.auth import get_session_data
from db.database import get_global_session

router = APIRouter(prefix="/api/base-symbols", tags=["base-symbols"])
views_router = APIRouter(tags=["base-symbols-views"])


@views_router.get("/base-symbols", response_class=HTMLResponse)
async def base_symbols_page(request: Request):
    """Render base symbols page."""
    # Check authentication
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        from fastapi.responses import RedirectResponse

        return RedirectResponse(url="/login", status_code=302)

    session_data = get_session_data(session_cookie)
    if not session_data:
        from fastapi.responses import RedirectResponse

        return RedirectResponse(url="/login", status_code=302)

    # Read and return the HTML template
    from pathlib import Path

    template_path = (
        Path(__file__).parent.parent.parent / "templates" / "base_symbols.html"
    )
    with open(template_path) as f:
        return HTMLResponse(content=f.read())


@router.get("", response_model=BaseSymbolList)
async def list_base_symbols(
    request: Request,
    page: int = 1,
    per_page: int = 20,
    exchange: str | None = None,
    type: str | None = None,
    search: str | None = None,
    db: Session = Depends(get_global_session),
):
    """
    List all base symbols with pagination and filters.

    Query params:
    - page: Page number (default: 1)
    - per_page: Items per page (default: 20)
    - exchange: Filter by exchange (NSE, NFO, BSE)
    - type: Filter by type (Index, Stock)
    - search: Search by symbol name
    """
    # Verify user is authenticated
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_data = get_session_data(session_cookie)
    if not session_data:
        raise HTTPException(status_code=401, detail="Session expired")

    # Validate pagination parameters
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 20

    # Calculate offset
    offset = (page - 1) * per_page

    # Build query with filters
    query = select(BaseSymbol).where(BaseSymbol.deleted_at.is_(None))

    # Apply filters
    if exchange:
        query = query.where(BaseSymbol.exchange == exchange)

    if type:
        query = query.where(BaseSymbol.type == type)

    if search:
        query = query.where(BaseSymbol.value.contains(search))

    # Get total count
    total_count = len(
        db.exec(select(BaseSymbol).where(BaseSymbol.deleted_at.is_(None))).all()
    )

    # Get paginated symbols
    symbols = db.exec(
        query.order_by(BaseSymbol.value).offset(offset).limit(per_page)
    ).all()

    # Get last sync time
    last_synced = db.exec(
        select(BaseSymbol.last_synced_at)
        .where(BaseSymbol.last_synced_at.isnot(None))
        .order_by(BaseSymbol.last_synced_at.desc())
        .limit(1)
    ).first()

    total_pages = (total_count + per_page - 1) // per_page

    return BaseSymbolList(
        success=True,
        base_symbols=[BaseSymbolRead.model_validate(s) for s in symbols],
        count=total_count,
        last_synced=last_synced,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@router.post("/sync")
async def sync_base_symbols(
    request: Request,
    broker: str = "angel-one",
    db: Session = Depends(get_global_session),
):
    """
    Sync NSE F&O base symbols from broker catalog to database.

    Extracts ~217 NSE F&O symbols with accurate strike_size and lot_size.

    Args:
        broker: Broker catalog to use (default: angel-one)

    Returns:
        Sync results with statistics

    Example:
        POST /api/base-symbols/sync
        POST /api/base-symbols/sync?broker=fyers  # Future support
    """
    # Verify user is authenticated
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_data = get_session_data(session_cookie)
    if not session_data:
        raise HTTPException(status_code=401, detail="Session expired")

    # Sync from broker catalog
    try:
        from app.services.base_symbols_service import sync_base_symbols_from_catalog

        result = await sync_base_symbols_from_catalog(broker)

        if not result.get("success"):
            raise HTTPException(
                status_code=500, detail=f"Failed to sync: {result.get('error')}"
            )

        return {
            "success": True,
            "broker": broker,
            "catalog_summary": {
                "namespace": "NSE",
                "exchange": "NFO",
                "total": result.get("total", 0),
                "indices": 0,  # Stats not available from service
                "stocks": 0,  # Stats not available from service
            },
            "sync_results": {
                "added": result.get("added", 0),
                "updated": result.get("updated", 0),
                "unchanged": result.get("unchanged", 0),
            },
            "database_summary": {"total": result.get("total", 0)},
            "message": f"Successfully synced {result.get('total', 0)} NSE F&O symbols from {broker} catalog.",
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/stats")
async def get_base_symbols_stats(
    request: Request, db: Session = Depends(get_global_session)
):
    """Get base symbols statistics."""
    # Verify user is authenticated
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_data = get_session_data(session_cookie)
    if not session_data:
        raise HTTPException(status_code=401, detail="Session expired")

    # Get all non-deleted symbols
    all_symbols = db.exec(
        select(BaseSymbol).where(BaseSymbol.deleted_at.is_(None))
    ).all()

    # Calculate stats
    total_count = len(all_symbols)
    indices = sum(1 for s in all_symbols if s.type == "Index")
    stocks = sum(1 for s in all_symbols if s.type == "Stock")
    exchanges = list({s.exchange for s in all_symbols})

    return {
        "success": True,
        "total": total_count,
        "indices": indices,
        "stocks": stocks,
        "exchanges": exchanges,
    }


@router.get("/count")
async def get_base_symbols_count(
    request: Request, db: Session = Depends(get_global_session)
):
    """Get count of base symbols."""
    # Verify user is authenticated
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_data = get_session_data(session_cookie)
    if not session_data:
        raise HTTPException(status_code=401, detail="Session expired")

    count = db.exec(select(BaseSymbol).where(BaseSymbol.deleted_at.is_(None))).all()

    return {"success": True, "count": len(count)}
