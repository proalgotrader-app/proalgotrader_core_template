"""
Algo session routes for ProAlgoTrader FastAPI.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select

from app.dependencies.auth import get_authenticated_user
from app.models import AlgoSession, AlgoSessionCreate
from app.routers.project import get_project_info
from app.services import get_strategy_processes
from db.database import get_db_session

router = APIRouter(prefix="/api/algo-sessions", tags=["algo-sessions"])


@router.get("/running")
async def get_running_session(
    request: Request,
    db: Session = Depends(get_db_session),
    user_data: dict = Depends(get_authenticated_user),
):
    """Get the currently running session (if any)."""
    # Get project info for ownership verification
    try:
        project_info = get_project_info()
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get project info")

    project_id = project_info.get("project", {}).get("id")
    strategy_processes = get_strategy_processes()

    # Find running session
    for sid, proc in strategy_processes.items():
        if proc and proc.poll() is None:
            # Get session info
            algo_session = db.get(AlgoSession, sid)
            if algo_session and algo_session.project_id == project_id:
                return {
                    "running": True,
                    "session": {
                        "id": str(algo_session.id),
                        "mode": algo_session.mode,
                        "tz": algo_session.tz,
                        "pid": proc.pid,
                    },
                }

    return {"running": False}


@router.post("")
async def create_algo_session(
    session_create: AlgoSessionCreate,
    request: Request,
    db: Session = Depends(get_db_session),
    user_data: dict = Depends(get_authenticated_user),
):
    """Create a new algo session."""

    # Get project info for user_id and project_id
    try:
        project_info = get_project_info()
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get project info")

    # Extract project data
    project_data = project_info.get("project", {})
    project_id = project_data.get("id")
    user_id = project_data.get("user_id")

    print(f"[Debug] Project ID: {project_id}")
    print(f"[Debug] User ID: {user_id}")

    if not user_id or not project_id:
        raise HTTPException(status_code=500, detail="Invalid project info")

    # Check for existing Live/Paper sessions (only one allowed per project)
    if session_create.mode in ["Live", "Paper"]:
        existing = db.exec(
            select(AlgoSession).where(
                AlgoSession.project_id == project_id,
                AlgoSession.mode == session_create.mode,
            )
        ).first()

        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"A {session_create.mode} session already exists for this project",
            )

    # Parse backtest dates if provided
    backtest_start = None
    backtest_end = None

    if session_create.backtest_start_date:
        try:
            # Parse date string (YYYY-MM-DD)
            backtest_start = datetime.strptime(
                session_create.backtest_start_date, "%Y-%m-%d"
            ).date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid backtest_start_date format. Use YYYY-MM-DD",
            )

    if session_create.backtest_end_date:
        try:
            # Parse date string (YYYY-MM-DD)
            backtest_end = datetime.strptime(
                session_create.backtest_end_date, "%Y-%m-%d"
            ).date()
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail="Invalid backtest_end_date format. Use YYYY-MM-DD",
            )

    # Validate backtest dates
    if session_create.mode == "Backtest":
        if not backtest_start or not backtest_end:
            raise HTTPException(
                status_code=400,
                detail="Backtest mode requires both start and end dates",
            )
        if backtest_end < backtest_start:
            raise HTTPException(
                status_code=400, detail="End date must be after start date"
            )

    # Create new session
    new_session = AlgoSession(
        user_id=user_id,
        project_id=project_id,
        mode=session_create.mode,
        tz=session_create.tz,
        backtest_start_date=backtest_start,
        backtest_end_date=backtest_end,
    )

    print(f"[Debug] Creating session: {new_session}")

    db.add(new_session)
    db.commit()
    db.refresh(new_session)

    print(f"[Debug] Session created successfully: ID={new_session.id}")

    return {"success": True, "session": new_session}


@router.get("")
async def list_algo_sessions(
    request: Request,
    db: Session = Depends(get_db_session),
    user_data: dict = Depends(get_authenticated_user),
):
    """List all algo sessions for current user's project with status."""

    # Get project info (sync function)
    try:
        project_info = get_project_info()
    except HTTPException as e:
        # If project not found (not synced yet), return empty sessions list
        if e.status_code == 404:
            return {"success": True, "sessions": []}
        # Re-raise other HTTPExceptions
        raise
    except Exception as e:
        # Log unexpected errors
        print(f"[Error] Failed to get project info: {e}")
        raise HTTPException(status_code=500, detail="Failed to get project info")

    project_id = project_info.get("project", {}).get("id")

    # Get all sessions for this project
    sessions = db.exec(
        select(AlgoSession).where(AlgoSession.project_id == project_id)
    ).all()

    # Get running processes
    strategy_processes = get_strategy_processes()

    # Add status to each session
    sessions_with_status = []
    for session in sessions:
        sid = str(session.id)
        process = strategy_processes.get(sid)

        if process and process.poll() is None:
            status = "running"
            pid = process.pid
        else:
            status = "stopped"
            pid = None

        sessions_with_status.append(
            {**session.model_dump(), "status": status, "pid": pid}
        )

    return {"success": True, "sessions": sessions_with_status}


@router.get("/{session_id}")
async def get_algo_session(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db_session),
    user_data: dict = Depends(get_authenticated_user),
):
    """Get details of a specific algo session."""
    # Validate session_id format (should be UUID string)
    try:
        # Check if it's a valid UUID string
        from uuid import UUID as validate_uuid

        validate_uuid(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    # Get project info for ownership verification
    try:
        project_info = get_project_info()
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get project info")

    project_id = project_info.get("project", {}).get("id")

    # Get session
    algo_session = db.get(AlgoSession, session_id)
    if not algo_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Verify ownership
    if algo_session.project_id != project_id:
        raise HTTPException(status_code=403, detail="Access denied")

    return {"success": True, "session": algo_session}


@router.get("/{session_id}/context")
async def get_algo_session_context(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db_session),
    user_data: dict = Depends(get_authenticated_user),
):
    """Get complete algo session context including project, broker, strategy for engine execution.

    Returns:
        Complete context needed by trading engine including:
        - Algo session details
        - Full project info (broker config, strategy)
        - GitHub repository and account details
    """
    # Validate session_id format (should be UUID string)
    try:
        from uuid import UUID as validate_uuid

        validate_uuid(session_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    # Get project info
    try:
        project_info = get_project_info()
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to get project info")

    project_id = project_info.get("project", {}).get("id")

    # Get algo session
    algo_session = db.get(AlgoSession, session_id)
    if not algo_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Verify ownership
    if algo_session.project_id != project_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Build response with complete context
    return {
        "success": True,
        "algo_session": {
            "id": str(algo_session.id),
            "mode": algo_session.mode,
            "tz": algo_session.tz,
            "backtest_start_date": (
                str(algo_session.backtest_start_date)
                if algo_session.backtest_start_date
                else None
            ),
            "backtest_end_date": (
                str(algo_session.backtest_end_date)
                if algo_session.backtest_end_date
                else None
            ),
            "created_at": (
                algo_session.created_at.isoformat() if algo_session.created_at else None
            ),
            "updated_at": (
                algo_session.updated_at.isoformat() if algo_session.updated_at else None
            ),
            "project": project_info.get("project", {}),
        },
    }
