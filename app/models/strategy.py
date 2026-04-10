"""
Strategy model for ProAlgoTrader FastAPI.

Strategy - stores trading strategy information from API.
"""

from datetime import datetime

from sqlmodel import Field, SQLModel


class Strategy(SQLModel, table=True):
    """
    Strategy model - stores trading strategy information.

    Uses API UUID as primary key.
    Only stores fields returned by /api/v1/projects/info endpoint.
    """

    __tablename__ = "strategies"

    # API UUID as primary key
    id: str = Field(
        primary_key=True,
        max_length=36,
        description="Strategy ID from ProAlgoTrader API (UUID)",
    )

    # Strategy details
    identifier: str = Field(
        unique=True,
        max_length=255,
        description="Unique strategy identifier code",
    )
    title: str = Field(max_length=255, description="Strategy name")
    description: str | None = Field(default=None, description="Strategy description")

    # Foreign key to GitHub repository
    github_repo_id: str | None = Field(
        default=None,
        max_length=36,
        foreign_key="github_repositories.id",
        description="GitHub repository ID for this strategy",
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="When record was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
        description="When record was last updated",
    )

    class Config:
        from_attributes = True


# Pydantic models for API responses


class StrategyRead(SQLModel):
    """Model for reading strategy data."""

    id: str
    identifier: str
    title: str
    description: str | None
    github_repo_id: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StrategyCreate(SQLModel):
    """Model for creating strategy from API."""

    id: str  # API UUID
    identifier: str
    title: str
    description: str | None = None
    github_repo_id: str | None = None
