"""
Strategy execution routes for ProAlgoTrader FastAPI.
"""

import json
import os
import subprocess
import sys
from uuid import UUID as validate_uuid_type

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlmodel import Session

from app.core.config import settings
from app.dependencies.auth import get_authenticated_user
from app.models.algo_session import AlgoSession
from app.routers.project import get_project_info
from app.services import (
    add_process,
    get_process,
    get_strategy_processes,
    remove_process,
)
from db.database import get_db_session

router = APIRouter(prefix="/api/algo-sessions", tags=["strategy"])


class StrategyStartPayload(BaseModel):
    """Optional payload for starting a strategy."""

    config: dict | None = None  # Additional config passed by user
    # Add more fields as needed


def validate_session_id(session_id: str):
    """Validate that session_id is a valid UUID string."""
    try:
        validate_uuid_type(session_id)
        return True
    except ValueError:
        return False


@router.post("/{session_id}/start")
async def start_strategy(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db_session),
    payload: StrategyStartPayload | None = Body(default=None),
    session_data: dict = Depends(get_authenticated_user),
):
    """Start a strategy for a session."""
    # Validate session_id format
    if not validate_session_id(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    # Verify session exists and belongs to user's project
    algo_session = db.get(AlgoSession, session_id)
    if not algo_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get project info to verify ownership
    try:
        project_info = get_project_info()
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to verify project")

    project_id = project_info.get("project", {}).get("id")
    if algo_session.project_id != project_id:
        raise HTTPException(
            status_code=403, detail="Session does not belong to your project"
        )

    # Check if already running for this session
    existing_process = get_process(session_id)
    if existing_process and existing_process.poll() is None:
        raise HTTPException(
            status_code=400, detail="Strategy is already running for this session"
        )

    # Check if any other session is running (only one session can run at a time)
    strategy_processes = get_strategy_processes()
    for sid, proc in strategy_processes.items():
        if proc and proc.poll() is None and sid != session_id:
            # Another session is running - get session info for better error message
            running_session = db.get(AlgoSession, sid)
            if running_session:
                raise HTTPException(
                    status_code=400,
                    detail=f"Another session is already running ({running_session.mode}). Stop it before starting a new session.",
                )
            else:
                raise HTTPException(
                    status_code=400,
                    detail="Another session is already running. Stop it before starting a new session.",
                )

    # Build session payload to pass to run.py
    session_payload = {
        "id": str(algo_session.id),
        "user_id": algo_session.user_id,
        "project_id": algo_session.project_id,
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
    }

    # Add payload config if provided
    if payload and payload.config:
        session_payload["config"] = payload.config

    # Get API token from authenticated session
    api_token = session_data.get("session", {}).get("access_token")
    if not api_token:
        raise HTTPException(status_code=401, detail="No access token found in session")

    # Get API URLs from settings
    local_api_url = settings.LOCAL_API_URL
    remote_api_url = settings.REMOTE_API_URL

    # Start strategy process
    try:
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        env["ALGO_SESSION_ID"] = session_id
        env["ALGO_SESSION_MODE"] = algo_session.mode
        env["ALGO_SESSION_TZ"] = algo_session.tz
        env["ALGO_SESSION_PAYLOAD"] = json.dumps(session_payload)

        print(f"[Strategy] Starting subprocess for session {session_id}")
        print("[Strategy] Command args:")
        print(f"[Strategy]   --local_api_url: {local_api_url}")
        print(f"[Strategy]   --remote_api_url: {remote_api_url}")
        print(f"[Strategy]   --algo_session_id: {session_id}")
        print(
            f"[Strategy]   --api_token: {api_token[:20]}..."
            if api_token
            else "[Strategy]   --api_token: None"
        )

        # Check if websockets is installed
        import importlib.util

        websockets_spec = importlib.util.find_spec("websockets")
        print(f"[Strategy] websockets package available: {websockets_spec is not None}")

        process = subprocess.Popen(
            [
                sys.executable,
                "-u",
                "run.py",
                "--local_api_url",
                local_api_url,
                "--remote_api_url",
                remote_api_url,
                "--api_token",
                api_token,
                "--algo_session_id",
                session_id,
            ],
            env=env,
        )

        add_process(session_id, process)
        print(f"[Strategy] Started session {session_id} with PID: {process.pid}")
        print(f"[Strategy] Session payload: {session_payload}")

        return {
            "status": "started",
            "session_id": session_id,
            "pid": process.pid,
            "mode": algo_session.mode,
            "session": session_payload,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to start strategy: {str(e)}"
        )


@router.post("/{session_id}/stop")
async def stop_strategy(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db_session),
    user_data: dict = Depends(get_authenticated_user),
):
    """Stop a running strategy."""
    # Validate session_id format
    if not validate_session_id(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID format")

    # Verify session exists and belongs to user's project
    algo_session = db.get(AlgoSession, session_id)
    if not algo_session:
        raise HTTPException(status_code=404, detail="Session not found")

    # Get project info to verify ownership
    try:
        project_info = get_project_info()
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to verify project")

    project_id = project_info.get("project", {}).get("id")
    if algo_session.project_id != project_id:
        raise HTTPException(
            status_code=403, detail="Session does not belong to your project"
        )

    # Check if running
    process = get_process(session_id)
    if not process:
        raise HTTPException(
            status_code=400, detail="No running strategy for this session"
        )

    # Terminate process
    try:
        print(f"[Strategy] Stopping session {session_id} PID: {process.pid}")
        process.terminate()
        process.wait(timeout=5)
        print(f"[Strategy] Session {session_id} stopped")
    except subprocess.TimeoutExpired:
        print(f"[Strategy] Force killing session {session_id} PID: {process.pid}")
        process.kill()
        process.wait()
    except Exception as e:
        print(f"[Strategy] Error stopping session {session_id}: {e}")

    # Remove from tracking
    remove_process(session_id)

    return {"status": "stopped", "session_id": session_id}


@router.get("/{session_id}/status")
async def get_strategy_status(
    session_id: str,
    request: Request,
    db: Session = Depends(get_db_session),
    user_data: dict = Depends(get_authenticated_user),
):
    """Get status of running strategy for a session."""
    # Validate session_id format
    if not validate_session_id(session_id):
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

    # Check if running
    process = get_process(session_id)
    if process:
        poll_result = process.poll()
        if poll_result is None:
            return {
                "status": "running",
                "session_id": session_id,
                "pid": process.pid,
                "mode": algo_session.mode,
            }
        else:
            # Process has exited
            remove_process(session_id)
            exit_code = poll_result
            message = "Process has exited"
            if exit_code != 0:
                message = f"Process crashed (exit code: {exit_code}). Check terminal for errors."
                if exit_code == 1:
                    message = "Process exited with error. Make sure your Strategy class implements initialize() and next() methods."
            return {
                "status": "stopped",
                "session_id": session_id,
                "mode": algo_session.mode,
                "message": message,
            }

    return {
        "status": "stopped",
        "session_id": session_id,
        "mode": algo_session.mode,
        "message": "No running process",
    }
