"""
Project routes for ProAlgoTrader FastAPI.
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from app.core.config import settings
from app.routers.auth import get_session_data
from app.services import get_strategy_processes
from app.services.project_service import (
    get_project_info,
    is_project_synced,
    sync_project_to_db,
)

router = APIRouter(prefix="/api/project", tags=["project"])


class SyncResponse(BaseModel):
    success: bool
    message: str
    project: dict | None = None
    user: dict | None = None


async def check_running_session(project_id: str) -> bool:
    """Check if there's a running algo session for the project."""
    strategy_processes = get_strategy_processes()

    # Check if any process is running for this project
    return any(proc and proc.poll() is None for proc in strategy_processes.values())


# Helper function for other modules (async wrapper for service function)
async def get_project_info_async() -> dict:
    """Get project info from database (async wrapper)."""
    return get_project_info()


@router.get("/info")
async def get_project(request: Request):
    """API endpoint to get project info from database."""
    # Verify user is authenticated
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_data = get_session_data(session_cookie)
    if not session_data:
        raise HTTPException(status_code=401, detail="Session expired")

    # Use the service function (it handles not found exception)
    return get_project_info()


@router.post("/sync", response_model=SyncResponse)
async def sync_project(request: Request):
    """Sync project info from ProAlgoTrader API to database."""
    # Verify user is authenticated
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_data = get_session_data(session_cookie)
    if not session_data:
        raise HTTPException(status_code=401, detail="Session expired")

    user_id = session_data.get("user", {}).get("id")
    access_token = session_data.get("session", {}).get("access_token")

    if not access_token:
        raise HTTPException(status_code=401, detail="No access token in session")

    try:
        # Check if project exists and if any algo session is running
        project_synced = is_project_synced(settings.PROJECT_KEY)

        if project_synced:
            # Check if any algo session is running
            project_info = get_project_info()
            project_id = project_info.get("project", {}).get("id")

            if await check_running_session(project_id):
                raise HTTPException(
                    status_code=400,
                    detail="Cannot sync project while an algo session is running. Please stop the running session first.",
                )

        # Sync project from API to database
        project_data = await sync_project_to_db(
            user_id=user_id,
            access_token=access_token,
            project_key=settings.project_key,
            project_secret=settings.project_secret,
        )

        # Get broker details for syncing with correct broker
        from sqlmodel import Session as SQLSession
        from sqlmodel import select

        from app.models.broker import Broker
        from app.models.project import Project
        from db.database import project_engine

        broker_title = "angel-one"  # Default fallback
        project_id = project_data.get("id")
        if project_id:
            db = SQLSession(project_engine)
            project = db.exec(select(Project).where(Project.id == project_id)).first()
            if project and project.broker_id:
                broker = db.exec(
                    select(Broker).where(Broker.id == project.broker_id)
                ).first()
                if broker:
                    broker_title = broker.broker_title
                    print(f"[Project Sync] Using broker: {broker_title}")
            db.close()

        # Sync base symbols and trading calendar on initial sync
        if not project_synced:
            # First sync - also sync base symbols and trading calendar
            from app.services.base_symbols_service import sync_base_symbols_from_catalog
            from app.services.trading_calendar_service import (
                sync_trading_calendar_from_nse,
            )

            # Sync base symbols
            try:
                base_symbols_result = await sync_base_symbols_from_catalog(broker_title)
                if base_symbols_result.get("success"):
                    print(
                        f"[Project Sync] Synced {base_symbols_result['total']} base symbols from {broker_title}"
                    )
                else:
                    print(
                        f"[Project Sync] Warning: Failed to sync base symbols: {base_symbols_result.get('error')}"
                    )
            except Exception as e:
                print(f"[Project Sync] Warning: Failed to sync base symbols: {e}")

            # Sync trading calendar
            try:
                calendar_result = await sync_trading_calendar_from_nse()
                if calendar_result.get("success"):
                    print(
                        f"[Project Sync] Synced {calendar_result['total_days']} trading calendar days"
                    )
                else:
                    print(
                        f"[Project Sync] Warning: Failed to sync trading calendar: {calendar_result.get('error')}"
                    )
            except Exception as e:
                print(f"[Project Sync] Warning: Failed to sync trading calendar: {e}")

        return SyncResponse(
            success=True,
            message="Project synced successfully",
            project=project_data,
            user=project_data.get("user"),
        )
    except HTTPException:
        raise
    except Exception as e:
        print(f"[Project Sync] Error: {e}")
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")
