"""
Entry point for ProAlgoTrader FastAPI.
Run with: uv run fastapi dev (development) or uv run fastapi run (production)
"""

from app.main import app

__all__ = ["app"]
