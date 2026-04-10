"""
User and Session models for ProAlgoTrader FastAPI.

User stores profile information from ProAlgoTrader API.
Session stores authentication tokens with expiry.
"""

from datetime import datetime
from uuid import uuid4

from sqlmodel import Field, SQLModel


class User(SQLModel, table=True):
    """
    User model - stores user profile from ProAlgoTrader API.

    Uses API UUID as primary key directly (no separate remote_user_id).
    Only stores fields returned by /api/v1/projects/info endpoint.
    """

    __tablename__ = "users"

    # API UUID as primary key (no separate id and remote_user_id)
    id: str = Field(
        primary_key=True,
        max_length=36,
        description="User ID from ProAlgoTrader API (UUID)",
    )

    # User profile from API
    name: str = Field(max_length=255, description="User's display name")
    email: str = Field(max_length=255, description="User's email address")

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="When user was first created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
        description="When user was last updated",
    )

    class Config:
        from_attributes = True


class Session(SQLModel, table=True):
    """
    Session model - stores authentication tokens for API access.

    Sessions are linked to users and have expiry times.
    A user can have multiple sessions (multiple devices/browsers).
    Uses local UUID for session ID (not from API).
    """

    __tablename__ = "sessions"

    id: str = Field(
        default_factory=lambda: str(uuid4()),
        primary_key=True,
        max_length=36,
        description="Local session ID (UUID)",
    )

    # Foreign key to user (in project.db)
    user_id: str = Field(
        max_length=36,
        foreign_key="users.id",
        description="User ID this session belongs to",
    )

    # Access token (JWT)
    access_token: str = Field(description="OAuth access token for ProAlgoTrader API")
    access_token_expires_at: datetime = Field(
        description="When the access token expires"
    )

    # Refresh token (for obtaining new access tokens)
    refresh_token: str | None = Field(default=None, description="OAuth refresh token")
    refresh_token_expires_at: datetime | None = Field(
        default=None, description="When the refresh token expires"
    )

    # Timestamps
    created_at: datetime = Field(
        default_factory=datetime.utcnow, description="When session was created"
    )
    updated_at: datetime = Field(
        default_factory=datetime.utcnow,
        sa_column_kwargs={"onupdate": datetime.utcnow},
        description="When session was last updated",
    )

    class Config:
        from_attributes = True


# Pydantic models for API responses (excluding sensitive data)


class UserRead(SQLModel):
    """Model for reading user data."""

    id: str
    name: str
    email: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SessionRead(SQLModel):
    """Model for reading session data (excludes actual tokens)."""

    id: str
    user_id: str
    access_token_expires_at: datetime
    refresh_token_expires_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserCreate(SQLModel):
    """Model for creating a user from API."""

    id: str  # API UUID
    name: str
    email: str


class SessionCreate(SQLModel):
    """Model for creating a session from OAuth."""

    user_id: str
    access_token: str
    access_token_expires_at: datetime
    refresh_token: str | None = None
    refresh_token_expires_at: datetime | None = None


class UserWithSession(SQLModel):
    """Model for user creation with session."""

    id: str  # API UUID
    name: str
    email: str
    access_token: str
    access_token_expires_at: datetime
    refresh_token: str | None = None
    refresh_token_expires_at: datetime | None = None
