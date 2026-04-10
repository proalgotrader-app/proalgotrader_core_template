"""Services package initialization."""

from app.services.connection_manager import ConnectionManager
from app.services.project_service import (
    get_project_by_key,
    get_project_info,
    is_project_synced,
    sync_project_to_db,
)
from app.services.strategy_manager import (
    add_process,
    clear_all,
    get_process,
    get_strategy_processes,
    remove_process,
    strategy_processes,
)

# Global connection manager instance for WebSocket connections
connection_manager = ConnectionManager()

__all__ = [
    "strategy_processes",
    "get_strategy_processes",
    "add_process",
    "remove_process",
    "get_process",
    "clear_all",
    "connection_manager",
    "ConnectionManager",
    "is_project_synced",
    "get_project_by_key",
    "get_project_info",
    "sync_project_to_db",
]
