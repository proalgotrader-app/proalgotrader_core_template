"""
Trading Calendar routes for ProAlgoTrader FastAPI.
Handles syncing and listing trading calendar from NSE India API.
"""

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse
from sqlmodel import Session, select

from app.dependencies.auth import get_authenticated_user
from app.models.trading_calendar import (
    SyncResponse,
    TradingCalendar,
    TradingCalendarList,
    TradingCalendarRead,
)
from app.routers.auth import get_session_data
from db.database import get_global_session

router = APIRouter(prefix="/api/trading-calendar", tags=["trading-calendar"])
views_router = APIRouter(tags=["trading-calendar-views"])


@views_router.get("/trading-calendar", response_class=HTMLResponse)
async def trading_calendar_page(request: Request):
    """Render trading calendar page."""
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
        Path(__file__).parent.parent.parent / "templates" / "trading_calendar.html"
    )
    with open(template_path) as f:
        return HTMLResponse(content=f.read())


@router.get("", response_model=TradingCalendarList)
async def list_trading_calendar(
    request: Request,
    page: int = 1,
    per_page: int = 10,
    year: int | None = None,
    month: int | None = None,
    db: Session = Depends(get_global_session),
    user_data: dict = Depends(get_authenticated_user),
):
    """List trading calendar entries with pagination and optional filtering."""
    # Validate pagination parameters
    if page < 1:
        page = 1
    if per_page < 1 or per_page > 100:
        per_page = 10

    # Calculate offset
    offset = (page - 1) * per_page

    # Build query with filters
    query = select(TradingCalendar)

    # Filter by year
    if year:
        query = query.where(TradingCalendar.date >= date(year, 1, 1))
        query = query.where(TradingCalendar.date < date(year + 1, 1, 1))

    # Filter by month
    if month and year:
        if month < 1 or month > 12:
            month = 1
        start_date = date(year, month, 1)
        end_date = date(year + 1, 1, 1) if month == 12 else date(year, month + 1, 1)
        query = query.where(TradingCalendar.date >= start_date)
        query = query.where(TradingCalendar.date < end_date)

    # Get total count
    all_entries = db.exec(query).all()
    total_count = len(all_entries)

    # Get paginated entries ordered by date
    query = query.order_by(TradingCalendar.date).offset(offset).limit(per_page)
    entries = db.exec(query).all()

    # Get last sync time
    last_synced = db.exec(
        select(TradingCalendar.updated_at)
        .order_by(TradingCalendar.updated_at.desc())
        .limit(1)
    ).first()

    total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1

    return TradingCalendarList(
        success=True,
        calendar=[TradingCalendarRead.model_validate(e) for e in entries],
        count=total_count,
        last_synced=last_synced,
        page=page,
        per_page=per_page,
        total_pages=total_pages,
    )


@router.get("/all", response_model=TradingCalendarList)
async def get_all_trading_calendar(
    request: Request,
    years: str | None = None,  # Comma-separated years, e.g., "2025,2026"
    db: Session = Depends(get_global_session),
    user_data: dict = Depends(get_authenticated_user),
):
    """Get all trading calendar entries for specified years without pagination.

    Use this endpoint when you need all records at once.
    Accepts a list of years (comma-separated).
    If records for a requested year are not found, it will be synced from NSE API.

    Args:
        years: Comma-separated list of years (e.g., "2025,2026").
               Defaults to current year and previous year if not provided.

    Returns:
        TradingCalendarList with all entries for the specified years.
    """
    from datetime import datetime as dt

    # Default to current year and previous year
    current_year = dt.now().year
    if years:
        try:
            year_list = [int(y.strip()) for y in years.split(",") if y.strip()]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid years format. Use comma-separated years like '2025,2026'",
            )
    else:
        year_list = [current_year - 1, current_year]

    # Check which years need syncing and sync them
    from app.services.trading_calendar_service import sync_trading_calendar_from_nse

    for year in year_list:
        # Check if entries exist for this year
        start_date = date(year, 1, 1)
        end_date = date(year + 1, 1, 1)

        existing_count = len(
            db.exec(
                select(TradingCalendar)
                .where(TradingCalendar.date >= start_date)
                .where(TradingCalendar.date < end_date)
            ).all()
        )

        # If no entries for this year, sync from NSE
        if existing_count == 0:
            try:
                await sync_trading_calendar_from_nse([year])
            except Exception as e:
                # Log error but continue - don't fail the request
                print(f"Failed to sync year {year}: {str(e)}")

    # Build query for requested years
    query = select(TradingCalendar)

    # Filter by years
    if year_list:
        year_conditions = []
        for year in year_list:
            year_conditions.append(
                (TradingCalendar.date >= date(year, 1, 1))
                & (TradingCalendar.date < date(year + 1, 1, 1))
            )
        from sqlalchemy import or_

        query = query.where(or_(*year_conditions))

    # Get all entries ordered by date
    query = query.order_by(TradingCalendar.date)
    entries = db.exec(query).all()
    total_count = len(entries)

    # Get last sync time
    last_synced = db.exec(
        select(TradingCalendar.updated_at)
        .order_by(TradingCalendar.updated_at.desc())
        .limit(1)
    ).first()

    return TradingCalendarList(
        success=True,
        calendar=[TradingCalendarRead.model_validate(e) for e in entries],
        count=total_count,
        last_synced=last_synced,
        page=1,
        per_page=total_count,
        total_pages=1,
    )


@router.get("/holidays")
async def get_holidays(
    request: Request,
    year: int | None = None,
    db: Session = Depends(get_global_session),
    user_data: dict = Depends(get_authenticated_user),
):
    """Get all holidays (non-trading days) for a year."""
    # Default to current year
    if not year:
        year = datetime.now().year

    # Get all entries where closed_exchanges is not empty
    start_date = date(year, 1, 1)
    end_date = date(year + 1, 1, 1)

    entries = db.exec(
        select(TradingCalendar)
        .where(TradingCalendar.date >= start_date)
        .where(TradingCalendar.date < end_date)
        .where(TradingCalendar.closed_exchanges != "")
        .order_by(TradingCalendar.date)
    ).all()

    return {
        "success": True,
        "holidays": [TradingCalendarRead.model_validate(e) for e in entries],
        "count": len(entries),
    }


@router.post("/sync", response_model=SyncResponse)
async def sync_trading_calendar(
    request: Request,
    years: str | None = None,  # Comma-separated years, e.g., "2025,2026"
    db: Session = Depends(get_global_session),
    user_data: dict = Depends(get_authenticated_user),
):
    """Sync trading calendar from NSE India API.

    Fetches market holidays from NSE and generates complete trading calendar
    for current year and previous year by default.

    Args:
        years: Optional comma-separated list of years to sync.
               Defaults to current year and previous year.
    """
    # Parse years if provided
    sync_years: list[int] | None = None
    if years:
        try:
            sync_years = [int(y.strip()) for y in years.split(",") if y.strip()]
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid years format. Use comma-separated years like '2025,2026'",
            )

    # Sync trading calendar
    try:
        from app.services.trading_calendar_service import sync_trading_calendar_from_nse

        result = await sync_trading_calendar_from_nse(sync_years)

        if not result.get("success"):
            raise HTTPException(
                status_code=500, detail="Failed to sync trading calendar from NSE"
            )

        return SyncResponse(
            success=True,
            message=f"Successfully synced calendar from NSE India API for years {result.get('years')}",
            count=result.get("total_days", 0),
            inserted=result.get("inserted", 0),
            updated=result.get("updated", 0),
        )

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")


@router.get("/stats")
async def get_trading_calendar_stats(
    request: Request,
    db: Session = Depends(get_global_session),
    user_data: dict = Depends(get_authenticated_user),
):
    """Get trading calendar statistics."""
    # Get all entries
    all_entries = db.exec(select(TradingCalendar)).all()

    # Calculate stats
    total_days = len(all_entries)
    trading_days = 0
    holidays = 0
    weekends = 0

    for entry in all_entries:
        if not entry.closed_exchanges or entry.closed_exchanges == "":
            trading_days += 1
        elif entry.description == "Weekend":
            weekends += 1
        else:
            holidays += 1

    return {
        "success": True,
        "total_days": total_days,
        "trading_days": trading_days,
        "holidays": holidays,
        "weekends": weekends,
    }


@router.get("/count")
async def get_trading_calendar_count(
    request: Request,
    year: int | None = None,
    db: Session = Depends(get_global_session),
    user_data: dict = Depends(get_authenticated_user),
):
    """Get count of trading calendar entries."""
    # Default to current year
    if not year:
        year = datetime.now().year

    start_date = date(year, 1, 1)
    end_date = date(year + 1, 1, 1)

    count = len(
        db.exec(
            select(TradingCalendar)
            .where(TradingCalendar.date >= start_date)
            .where(TradingCalendar.date < end_date)
        ).all()
    )

    return {"success": True, "count": count, "year": year}
