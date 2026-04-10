"""
Strategy process manager for ProAlgoTrader FastAPI.
Tracks all running strategy subprocess instances.
"""

# Global dictionary to track running strategy processes by session_id
strategy_processes = {}


def get_strategy_processes():
    """Get the strategy processes dictionary."""
    return strategy_processes


def add_process(session_id: str, process):
    """Add a process to tracking."""
    strategy_processes[session_id] = process


def remove_process(session_id: str):
    """Remove a process from tracking."""
    if session_id in strategy_processes:
        del strategy_processes[session_id]


def get_process(session_id: str):
    """Get a process by session_id."""
    return strategy_processes.get(session_id)


def clear_all():
    """Clear all tracked processes."""
    strategy_processes.clear()
