"""
SQLModel models for ProAlgoTrader FastAPI.
"""

from datetime import date, datetime
from uuid import uuid4

from sqlmodel import Field, SQLModel


class AlgoSession(SQLModel, table=True):
    """
    Algo Session model - stores trading bot sessions.

    Modes:
    - Live: Real-time trading with real money
    - Paper: Simulated trading without real money
    - Backtest: Historical data testing

    Foreign keys to users and projects tables in project.db.
    Uses local UUID for session ID (not from API).
    """

    __tablename__ = "algo_sessions"

    id: str = Field(
        default_factory=lambda: str(uuid4()),  # Store as string with hyphens
        primary_key=True,
        max_length=36,
        description="Unique identifier (UUID with hyphens)",
    )

    # Foreign key to user (in project.db)
    user_id: str = Field(
        max_length=36,
        foreign_key="users.id",
        description="User ID from users table",
    )

    # Foreign key to project (in project.db)
    project_id: str = Field(
        max_length=36,
        foreign_key="projects.id",
        description="Project ID from projects table",
    )

    # Session details
    mode: str = Field(description="Trading mode: 'Live', 'Paper', or 'Backtest'")
    tz: str = Field(default="Asia/Kolkata", description="Timezone for the session")

    # Backtest specific fields (optional) - date only
    backtest_start_date: date | None = Field(
        default=None, description="Start date for backtest mode"
    )
    backtest_end_date: date | None = Field(
        default=None, description="End date for backtest mode"
    )

    # Timestamps
    created_at: datetime | None = Field(
        default_factory=datetime.utcnow, description="Creation timestamp"
    )
    updated_at: datetime | None = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
        description="Last update timestamp",
    )


# Pydantic models for API (without table=True)
class AlgoSessionCreate(SQLModel):
    """Model for creating an algo session."""

    mode: str  # 'Live', 'Paper', or 'Backtest'
    tz: str = "Asia/Kolkata"
    backtest_start_date: str | None = None  # ISO date string (YYYY-MM-DD)
    backtest_end_date: str | None = None  # ISO date string (YYYY-MM-DD)


class AlgoSessionRead(SQLModel):
    """Model for reading an algo session."""

    id: str
    user_id: str
    project_id: str
    mode: str
    tz: str
    backtest_start_date: date | None
    backtest_end_date: date | None
    created_at: datetime
    updated_at: datetime
