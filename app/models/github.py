"""
GitHub account and repository models for ProAlgoTrader FastAPI.

GitHubAccount - stores user's GitHub account info from API.
GitHubRepository - stores user's GitHub repository info from API.
"""

from datetime import datetime

from sqlmodel import Field, SQLModel


class GitHubAccount(SQLModel, table=True):
    """
    GitHub Account model - stores GitHub account information.

    Uses API UUID as primary key.
    Only stores fields returned by /api/v1/projects/info endpoint.
    """

    __tablename__ = "github_accounts"

    # API UUID as primary key
    id: str = Field(
        primary_key=True,
        max_length=36,
        description="GitHub account ID from ProAlgoTrader API (UUID)",
    )

    # Foreign key to user
    user_id: str = Field(
        max_length=36,
        foreign_key="users.id",
        description="User ID this GitHub account belongs to",
    )

    # GitHub account details
    account_id: str = Field(max_length=255, description="GitHub numeric account ID")
    account_type: str = Field(
        max_length=50, description="Account type: 'User' or 'Organization'"
    )
    username: str = Field(max_length=255, description="GitHub username")
    name: str | None = Field(default=None, max_length=255, description="Display name")
    email: str | None = Field(default=None, max_length=255, description="Email address")

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


class GitHubRepository(SQLModel, table=True):
    """
    GitHub Repository model - stores GitHub repository information.

    Uses API UUID as primary key.
    Only stores fields returned by /api/v1/projects/info endpoint.
    """

    __tablename__ = "github_repositories"

    # API UUID as primary key
    id: str = Field(
        primary_key=True,
        max_length=36,
        description="Repository ID from ProAlgoTrader API (UUID)",
    )

    # Foreign key to GitHub account
    github_account_id: str = Field(
        max_length=36,
        foreign_key="github_accounts.id",
        description="GitHub account ID this repository belongs to",
    )

    # Repository details
    repository_id: str = Field(
        max_length=255, description="GitHub numeric repository ID"
    )
    repository_owner: str = Field(
        max_length=255, description="Repository owner username"
    )
    repository_name: str = Field(max_length=255, description="Repository name")
    repository_full_name: str = Field(
        max_length=500, description="Full repository name (owner/repo)"
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


class GitHubAccountRead(SQLModel):
    """Model for reading GitHub account data."""

    id: str
    user_id: str
    account_id: str
    account_type: str
    username: str
    name: str | None
    email: str | None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GitHubRepositoryRead(SQLModel):
    """Model for reading GitHub repository data."""

    id: str
    github_account_id: str
    repository_id: str
    repository_owner: str
    repository_name: str
    repository_full_name: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class GitHubAccountCreate(SQLModel):
    """Model for creating GitHub account from API."""

    id: str  # API UUID
    user_id: str
    account_id: str
    account_type: str
    username: str
    name: str | None = None
    email: str | None = None


class GitHubRepositoryCreate(SQLModel):
    """Model for creating GitHub repository from API."""

    id: str  # API UUID
    github_account_id: str
    repository_id: str
    repository_owner: str
    repository_name: str
    repository_full_name: str
