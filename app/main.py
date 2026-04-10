"""
Main entry point for ProAlgoTrader FastAPI application.
"""

import subprocess
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.core.env_validator import validate_on_startup
from app.fasthtml_views.router import router as fasthtml_router
from app.routers import (
    algo_sessions_router,
    auth_router,
    base_symbols_router,
    broker_router,
    broker_symbols_router,
    project_router,
    strategy_router,
    trading_calendar_router,
    websocket_router,
)
from app.services import clear_all, strategy_processes
from db.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup: Validate environment and initialize database
    print("[Startup] Initializing application...")
    validate_on_startup()  # Validate required environment variables
    create_db_and_tables()
    print("[Startup] Application initialized successfully!")

    yield

    # Shutdown: Terminate all running strategy processes
    print("[Shutdown] Terminating all strategy processes...")
    for session_id, process in strategy_processes.items():
        try:
            if process.poll() is None:
                print(f"[Shutdown] Terminating session {session_id} PID {process.pid}")
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    print(
                        f"[Shutdown] Force killing session {session_id} PID {process.pid}"
                    )
                    process.kill()
                    process.wait()
        except Exception as e:
            print(f"[Shutdown] Error stopping session {session_id}: {e}")

    clear_all()
    print("[Shutdown] All strategy processes terminated")
    print("[Shutdown] Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="ProAlgoTrader",
    description="Algorithmic trading platform with FastAPI",
    version="0.1.0",
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")


# Root route - redirect to dashboard
@app.get("/")
async def root():
    """Redirect root to dashboard."""
    from fastapi.responses import RedirectResponse

    return RedirectResponse(url="/dashboard", status_code=303)


# Include routers
app.include_router(fasthtml_router)  # FastHTML views
app.include_router(auth_router)  # OAuth authentication
app.include_router(project_router)  # Project API
app.include_router(algo_sessions_router)  # Algo sessions API
app.include_router(strategy_router)  # Strategy execution API
app.include_router(broker_router)  # Broker token API
app.include_router(base_symbols_router)  # Base symbols API
app.include_router(trading_calendar_router)  # Trading calendar API
app.include_router(broker_symbols_router)  # Broker symbols API
app.include_router(websocket_router)  # WebSocket for real-time logs


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
