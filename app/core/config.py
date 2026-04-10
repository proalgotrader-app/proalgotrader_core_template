"""Core configuration for ProAlgoTrader FastAPI."""

import os

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Settings:
    """Application settings from environment variables."""

    # API URLs
    LOCAL_API_URL: str = os.getenv("LOCAL_API_URL", "http://localhost:8000")
    REMOTE_API_URL: str = os.getenv("REMOTE_API_URL", "https://proalgotrader.com")

    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    SESSION_EXPIRE_HOURS: int = int(os.getenv("SESSION_EXPIRE_HOURS", "168"))  # 7 days

    # OAuth2 App credentials
    OAUTH_APP_ID: str | None = os.getenv("OAUTH_APP_ID")
    OAUTH_APP_SECRET: str | None = os.getenv("OAUTH_APP_SECRET")
    OAUTH_REDIRECT_URI: str = os.getenv(
        "OAUTH_REDIRECT_URI", "http://localhost:8000/oauth/callback"
    )

    # Project credentials
    PROJECT_KEY: str | None = os.getenv("PROJECT_KEY")
    PROJECT_SECRET: str | None = os.getenv("PROJECT_SECRET")

    # Database debug mode (optional)
    DEBUG_DB: bool = os.getenv("DEBUG_DB", "false").lower() == "true"

    # Note: Database paths are now dynamically configured in db/database.py
    # using pathlib for cross-platform compatibility

    @property
    def oauth_app_id(self) -> str:
        if not self.OAUTH_APP_ID:
            raise ValueError("OAUTH_APP_ID not set in environment")
        return self.OAUTH_APP_ID

    @property
    def oauth_app_secret(self) -> str:
        if not self.OAUTH_APP_SECRET:
            raise ValueError("OAUTH_APP_SECRET not set in environment")
        return self.OAUTH_APP_SECRET

    @property
    def project_key(self) -> str:
        if not self.PROJECT_KEY:
            raise ValueError("PROJECT_KEY not set in environment")
        return self.PROJECT_KEY

    @property
    def project_secret(self) -> str:
        if not self.PROJECT_SECRET:
            raise ValueError("PROJECT_SECRET not set in environment")
        return self.PROJECT_SECRET


# Global settings instance
settings = Settings()
