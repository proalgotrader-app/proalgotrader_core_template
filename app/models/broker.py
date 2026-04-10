"""
Broker model for ProAlgoTrader FastAPI.

Broker - stores broker configuration from API.
"""

from datetime import datetime

from sqlmodel import Field, SQLModel


class Broker(SQLModel, table=True):
    """
    Broker model - stores broker configuration.

    Uses API UUID as primary key.
    Only stores fields returned by /api/v1/projects/info endpoint.
    broker_config is stored as JSON string.
    """

    __tablename__ = "brokers"

    # API UUID as primary key
    id: str = Field(
        primary_key=True,
        max_length=36,
        description="Broker ID from ProAlgoTrader API (UUID)",
    )

    # Broker details
    broker_title: str = Field(
        max_length=255, description="Broker title (e.g., 'angel-one')"
    )
    broker_name: str = Field(
        max_length=255, description="Broker name (e.g., 'Angel One')"
    )
    available_broker_id: str | None = Field(
        default=None,
        max_length=36,
        description="Available broker ID (string, not FK)",
    )

    # Broker config as JSON string
    broker_config: str | None = Field(
        default=None,
        description="Broker configuration as JSON string",
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


class BrokerRead(SQLModel):
    """Model for reading broker data."""

    id: str
    broker_title: str
    broker_name: str
    available_broker_id: str | None
    broker_config: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class BrokerCreate(SQLModel):
    """Model for creating broker from API."""

    id: str  # API UUID
    broker_title: str
    broker_name: str
    available_broker_id: str | None = None
    broker_config: str | None = None
