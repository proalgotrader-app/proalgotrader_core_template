"""
Broker Token model for ProAlgoTrader FastAPI.
"""

from datetime import datetime
from uuid import uuid4

from sqlmodel import Field, SQLModel


class BrokerToken(SQLModel, table=True):
    """
    Broker Token model - stores authentication tokens for brokers.

    Tokens are generated per broker and reused if valid (before 9 AM IST).
    """

    __tablename__ = "broker_tokens"

    id: str = Field(
        default_factory=lambda: str(uuid4()),  # Store as string with hyphens
        primary_key=True,
        max_length=36,
        description="Unique identifier (UUID with hyphens)",
    )

    # Reference to broker ID from project.json
    broker_id: str = Field(description="Broker ID from project.json")

    # Authentication tokens
    token: str = Field(description="JWT authentication token")
    feed_token: str | None = Field(
        default=None, description="Feed token for WebSocket (optional)"
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


class BrokerTokenGenerate(SQLModel):
    """Request model for generating broker token."""

    pass  # Uses broker config from project.json


class BrokerTokenRead(SQLModel):
    """Response model for broker token."""

    id: str
    broker_id: str
    token: str
    feed_token: str | None
    created_at: datetime
    updated_at: datetime
    reused: bool = False
