"""Routers package initialization."""

from app.routers.algo_sessions import router as algo_sessions_router
from app.routers.auth import router as auth_router
from app.routers.base_symbols import router as base_symbols_router
from app.routers.broker import router as broker_router
from app.routers.broker_symbols import router as broker_symbols_router
from app.routers.project import router as project_router
from app.routers.strategy import router as strategy_router
from app.routers.trading_calendar import router as trading_calendar_router
from app.routers.websocket import router as websocket_router

__all__ = [
    "auth_router",
    "project_router",
    "algo_sessions_router",
    "strategy_router",
    "broker_router",
    "base_symbols_router",
    "trading_calendar_router",
    "broker_symbols_router",
    "websocket_router",
]
