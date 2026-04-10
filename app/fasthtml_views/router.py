"""FastHTML router - serves FastHTML views parallel to existing templates.

This router provides new routes that use FastHTML components while keeping
the existing Jinja2 template routes intact for comparison and testing.
"""

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from .algo_session_detail import algo_session_detail_page_html
from .algo_sessions import algo_sessions_page_html
from .base_symbols import base_symbols_page_html
from .broker_symbols import broker_symbols_page_html
from .dashboard import dashboard_page_html
from .initialize import initialize_page_html
from .login import login_page_html
from .trading_calendar import trading_calendar_page_html

router = APIRouter(tags=["fasthtml-views"])


def get_current_user(request: Request):
    """Get current user from session cookie or return None."""
    from app.routers.auth import get_session_data

    session_cookie = request.cookies.get("session")
    if not session_cookie:
        return None

    session_data = get_session_data(session_cookie)
    if not session_data:
        return None

    return session_data


@router.get("/login", response_class=HTMLResponse)
async def fh_login(request: Request, error: str = None):
    """Login page using FastHTML.

    This renders the same UI as templates/login_oauth.html but using FastHTML components.
    """
    # If already authenticated, redirect to dashboard
    user = get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=303)

    html = login_page_html(error=error)
    return HTMLResponse(content=html)


@router.get("/project/initialize", response_class=HTMLResponse)
async def fh_project_initialize(request: Request):
    """Project initialization page - syncs project from API on load.

    If project not synced, automatically syncs from NextJS API.
    If already synced, redirects to dashboard.
    """
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    from app.core.config import settings as proj_settings
    from app.services.project_service import is_project_synced, sync_project_to_db

    project_key = proj_settings.PROJECT_KEY
    project_synced = is_project_synced(project_key)

    # If already synced, redirect to dashboard
    if project_synced:
        return RedirectResponse(url="/dashboard", status_code=303)

    # Sync project from NextJS API
    try:
        user_id = user["user"]["id"]
        access_token = user["session"]["access_token"]

        # Sync project data
        project_data = await sync_project_to_db(
            user_id=user_id,
            access_token=access_token,
            project_key=proj_settings.PROJECT_KEY,
            project_secret=proj_settings.PROJECT_SECRET,
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
                    print(f"[Initialize] Using broker: {broker_title}")
            db.close()

        # Sync base symbols and trading calendar
        from app.services.base_symbols_service import sync_base_symbols_from_catalog
        from app.services.trading_calendar_service import sync_trading_calendar_from_nse

        # Base symbols sync
        try:
            base_result = await sync_base_symbols_from_catalog(broker_title)
            if base_result.get("success"):
                print(
                    f"[Initialize] Synced {base_result['total']} base symbols from {broker_title}"
                )
            else:
                print(
                    f"[Initialize] Warning: Base symbols sync failed: {base_result.get('error')}"
                )
        except Exception as e:
            print(f"[Initialize] Warning: Base symbols sync error: {e}")

        # Trading calendar sync
        try:
            calendar_result = await sync_trading_calendar_from_nse()
            if calendar_result.get("success"):
                print(
                    f"[Initialize] Synced {calendar_result['total_days']} trading calendar days"
                )
            else:
                print(
                    f"[Initialize] Warning: Trading calendar sync failed: {calendar_result.get('error')}"
                )
        except Exception as e:
            print(f"[Initialize] Warning: Trading calendar sync error: {e}")

        # Success - redirect to dashboard
        return RedirectResponse(url="/dashboard", status_code=303)

    except Exception as e:
        # Error - show initialize page with retry
        print(f"[Initialize] Error: {e}")
        import traceback

        traceback.print_exc()
        html = initialize_page_html(error=str(e))
        return HTMLResponse(content=html)


@router.get("/algo-sessions", response_class=HTMLResponse)
async def fh_algo_sessions(request: Request):
    """Algo Sessions page using FastHTML.

    This renders the same UI as templates/algo_sessions.html but using FastHTML components.
    """
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    html = algo_sessions_page_html(user_name=user["user"]["name"])
    return HTMLResponse(content=html)


@router.get("/algo-sessions/{session_id}", response_class=HTMLResponse)
async def fh_algo_session_detail(request: Request, session_id: str):
    """Algo Session Detail page using FastHTML.

    This renders the same UI as templates/algo_session_detail.html but using FastHTML components.
    """
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    html = algo_session_detail_page_html(
        user_name=user["user"]["name"], session_id=session_id
    )
    return HTMLResponse(content=html)


@router.get("/base-symbols", response_class=HTMLResponse)
async def fh_base_symbols(request: Request):
    """Base Symbols page using FastHTML.

    This renders the same UI as templates/base_symbols.html but using FastHTML components.
    """
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    html = base_symbols_page_html(user_name=user["user"]["name"])
    return HTMLResponse(content=html)


@router.get("/broker-symbols", response_class=HTMLResponse)
async def fh_broker_symbols(request: Request):
    """Broker Symbols page using FastHTML.

    This renders the same UI as templates/broker_symbols.html but using FastHTML components.
    """
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    html = broker_symbols_page_html(user_name=user["user"]["name"])
    return HTMLResponse(content=html)


@router.get("/trading-calendar", response_class=HTMLResponse)
async def fh_trading_calendar(request: Request):
    """Trading Calendar page using FastHTML.

    This renders the same UI as templates/trading_calendar.html but using FastHTML components.
    """
    user = get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    html = trading_calendar_page_html(user_name=user["user"]["name"])
    return HTMLResponse(content=html)


@router.get("/dashboard", response_class=HTMLResponse)
async def fh_dashboard(request: Request):
    """Dashboard page using FastHTML.

    This renders the same UI as templates/dashboard.html but using FastHTML components.
    """
    user = get_current_user(request)
    if not user:
        # Redirect to FastHTML login page
        return RedirectResponse(url="/login", status_code=303)

    html = dashboard_page_html(user_name=user["user"]["name"])
    return HTMLResponse(content=html)
