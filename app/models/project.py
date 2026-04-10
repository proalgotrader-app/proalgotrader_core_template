"""
Project model for ProAlgoTrader FastAPI.

Project - stores project information from API.
"""

from datetime import datetime

from sqlmodel import Field, SQLModel


class Project(SQLModel, table=True):
    """
    Project model - stores project information.

    Uses API UUID as primary key.
    Only stores fields returned by /api/v1/projects/info endpoint.
    Direct foreign keys to broker and strategy.
    """

    __tablename__ = "projects"

    # API UUID as primary key
    id: str = Field(
        primary_key=True,
        max_length=36,
        description="Project ID from ProAlgoTrader API (UUID)",
    )

    # Foreign key to user
    user_id: str = Field(
        max_length=36,
        foreign_key="users.id",
        description="User ID this project belongs to",
    )

    # Project details
    name: str = Field(max_length=255, description="Project name")
    status: str = Field(
        default="active", max_length=50, description="Project status (active/inactive)"
    )
    key: str = Field(unique=True, max_length=255, description="Unique project key")

    # Direct foreign keys (one-to-one relationships)
    broker_id: str | None = Field(
        default=None,
        max_length=36,
        foreign_key="brokers.id",
        description="Broker ID for this project",
    )
    strategy_id: str | None = Field(
        default=None,
        max_length=36,
        foreign_key="strategies.id",
        description="Strategy ID for this project",
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


class ProjectRead(SQLModel):
    """Model for reading project data."""

    id: str
    user_id: str
    name: str
    status: str
    key: str
    broker_id: str | None
    strategy_id: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectCreate(SQLModel):
    """Model for creating project from API."""

    id: str  # API UUID
    user_id: str
    name: str
    status: str = "active"
    key: str
    broker_id: str | None = None
    strategy_id: str | None = None
