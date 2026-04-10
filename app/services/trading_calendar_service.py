"""
Trading calendar service for ProAlgoTrader FastAPI.

Handles syncing trading calendar from NSE API to database.
"""

from datetime import datetime

from sqlmodel import Session, select

from app.models.trading_calendar import TradingCalendar
from app.services.trading_calendar.nse_calendar_service import NSECalendarService
from db.database import global_engine


async def sync_trading_calendar_from_nse(years: list[int] | None = None) -> dict:
    """
    Sync trading calendar from NSE India API to database.

    Args:
        years: List of years to sync. Defaults to [current_year - 1, current_year]

    Returns:
        Dict with sync results:
        {
            "success": bool,
            "years": list[int],
            "total_days": int,
            "inserted": int,
            "updated": int
        }
    """
    try:
        # Fetch holidays and generate calendar from NSE
        calendar_service = NSECalendarService()
        result = await calendar_service.sync_trading_calendar(years)

        if not result.get("success"):
            return result

        calendar_days = result.get("calendar", [])
        if not calendar_days:
            return {
                "success": True,
                "years": years,
                "total_days": 0,
                "inserted": 0,
                "updated": 0,
            }

        # Store calendar days to database
        db = Session(global_engine)
        sync_time = datetime.utcnow()
        inserted = 0
        updated = 0

        for day in calendar_days:
            # Check if entry exists
            existing = db.exec(
                select(TradingCalendar).where(TradingCalendar.date == day.date)
            ).first()

            # Convert closed_exchanges list to comma-separated string
            closed_exchanges_str = (
                ",".join(day.closed_exchanges) if day.closed_exchanges else ""
            )

            if existing:
                existing.description = day.description
                existing.closed_exchanges = closed_exchanges_str
                existing.updated_at = sync_time
                db.add(existing)
                updated += 1
            else:
                new_entry = TradingCalendar(
                    date=day.date,
                    description=day.description,
                    closed_exchanges=closed_exchanges_str,
                    created_at=sync_time,
                    updated_at=sync_time,
                )
                db.add(new_entry)
                inserted += 1

        db.commit()
        db.close()

        return {
            "success": True,
            "years": years,
            "total_days": len(calendar_days),
            "inserted": inserted,
            "updated": updated,
        }
    except Exception as e:
        print(f"[Trading Calendar Service] Error syncing: {e}")
        return {"success": False, "error": str(e)}
