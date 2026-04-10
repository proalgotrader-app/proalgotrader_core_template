"""
Environment variable validator for ProAlgoTrader FastAPI.

Validates all required environment variables on startup.
"""

import os


class EnvironmentValidationError(Exception):
    """Raised when required environment variables are missing."""

    pass


def validate_environment() -> tuple[bool, list[str]]:
    """
    Validate all required environment variables.

    Returns:
        Tuple of (is_valid, missing_variables)
    """
    required_vars = [
        # OAuth2 credentials (required for authentication)
        ("OAUTH_APP_ID", "OAuth App ID for ProAlgoTrader API"),
        ("OAUTH_APP_SECRET", "OAuth App Secret for ProAlgoTrader API"),
        ("OAUTH_REDIRECT_URI", "OAuth redirect URI"),
        # Project credentials (required for database path)
        ("PROJECT_KEY", "Unique project key for database storage"),
        ("PROJECT_SECRET", "Project secret for API authentication"),
    ]

    missing_vars = []

    for var_name, description in required_vars:
        value = os.getenv(var_name)

        if not value:
            missing_vars.append(f"  ❌ {var_name:<20} - {description}")
        elif var_name == "PROJECT_KEY" and len(value) < 4:
            missing_vars.append(
                f"  ❌ {var_name:<20} - Must be at least 4 characters (got '{len(value)}')"
            )

    return len(missing_vars) == 0, missing_vars


def validate_on_startup():
    """
    Validate environment variables on application startup.

    Raises:
        EnvironmentValidationError: If required variables are missing
    """
    print("[Startup] Validating environment variables...")

    is_valid, missing_vars = validate_environment()

    if not is_valid:
        print("\n" + "=" * 80)
        print("❌ ENVIRONMENT VALIDATION FAILED")
        print("=" * 80)
        print("\nThe following environment variables are missing or invalid:\n")
        for var in missing_vars:
            print(var)
        print("\n" + "=" * 80)
        print("Please add the missing variables to your .env file:")
        print("=" * 80)
        print("\nExample .env file:")
        print("-" * 80)
        print(
            """
# OAuth2 Credentials (Required)
OAUTH_APP_ID=your-oauth-app-id
OAUTH_APP_SECRET=your-oauth-app-secret
OAUTH_REDIRECT_URI=http://localhost:8000/oauth/callback

# Project Configuration (Required)
PROJECT_KEY=your-project-key
PROJECT_SECRET=your-project-secret

# API Configuration (Optional - has defaults)
LOCAL_API_URL=http://localhost:8000
REMOTE_API_URL=https://proalgotrader.com

# Session Configuration (Optional - has defaults)
SECRET_KEY=your-secret-key-change-in-production
SESSION_EXPIRE_HOURS=168

# Database Debug Mode (Optional)
DEBUG_DB=false
"""
        )
        print("-" * 80)
        print(
            "\n⚠️  Get your OAuth credentials from: https://www.proalgotrader.com/oauth-applications"
        )
        print("=" * 80 + "\n")

        raise EnvironmentValidationError(
            f"Missing or invalid environment variables:\n{chr(10).join(missing_vars)}"
        )

    print("✅ All required environment variables are set")
    print(f"   PROJECT_KEY: {os.getenv('PROJECT_KEY')}")
    print(
        f"   Database will be stored at: ~/.proalgotrader/project_db/{os.getenv('PROJECT_KEY')}/"
    )
    return True


def get_project_key() -> str:
    """
    Get PROJECT_KEY from environment.

    Raises:
        EnvironmentValidationError: If PROJECT_KEY is not set

    Returns:
        PROJECT_KEY string
    """
    project_key = os.getenv("PROJECT_KEY")

    if not project_key:
        raise EnvironmentValidationError(
            "PROJECT_KEY not set in environment. "
            "Please add PROJECT_KEY=your-project-key to your .env file"
        )

    if len(project_key) < 4:
        raise EnvironmentValidationError(
            f"PROJECT_KEY must be at least 4 characters (got '{len(project_key)}')"
        )

    return project_key


if __name__ == "__main__":
    # Test validation
    try:
        validate_on_startup()
        print("\n✅ Environment is valid!")
    except EnvironmentValidationError as e:
        print(f"\n❌ {e}")
        exit(1)
