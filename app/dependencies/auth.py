"""
Authentication dependencies for FastAPI.
"""

from datetime import datetime

from fastapi import HTTPException, Request
from sqlmodel import select

from app.models.user import Session as AuthSession
from app.models.user import User
from db.database import get_project_session


def get_user_from_bearer_token(request: Request) -> dict | None:
    """Extract user info from Bearer token in Authorization header.

    Returns dict with user info if valid, None otherwise.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        return None

    token = auth_header.split(" ")[1]

    # Get session from database
    db_gen = get_project_session()
    db = next(db_gen)

    try:
        # Find session by access token
        auth_session = db.exec(
            select(AuthSession).where(AuthSession.access_token == token)
        ).first()

        if not auth_session:
            return None

        # Check if access token expired
        if auth_session.access_token_expires_at < datetime.utcnow():
            return None

        # Get user
        user = db.exec(select(User).where(User.id == auth_session.user_id)).first()

        if not user:
            return None

        return {
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
            },
            "session": {
                "access_token": auth_session.access_token,
                "refresh_token": auth_session.refresh_token,
            },
        }
    finally:
        db.close()


def get_user_from_cookie_session(request: Request) -> dict | None:
    """Extract user info from cookie session.

    Returns dict with user info if valid, None otherwise.
    """
    from app.routers.auth import get_session_data

    session_cookie = request.cookies.get("session")
    if not session_cookie:
        return None

    session_data = get_session_data(session_cookie)
    return session_data


async def get_authenticated_user(request: Request) -> dict:
    """Dependency to get authenticated user from either Bearer token or cookie session.

    Supports both:
    - Bearer token in Authorization header (for API/subprocess access)
    - Cookie session (for web UI access)

    Returns dict with user info if authenticated.
    Raises HTTPException if not authenticated.
    """
    # Try Bearer token first (for API/subprocess access)
    user_data = get_user_from_bearer_token(request)
    if user_data:
        return user_data

    # Fall back to cookie session (for web UI access)
    user_data = get_user_from_cookie_session(request)
    if user_data:
        return user_data

    # No valid authentication found
    raise HTTPException(status_code=401, detail="Not authenticated")


async def get_authenticated_user_optional(request: Request) -> dict | None:
    """Dependency to get authenticated user (optional - returns None if not authenticated).

    Returns dict with user info if authenticated, None otherwise.
    """
    # Try Bearer token first
    user_data = get_user_from_bearer_token(request)
    if user_data:
        return user_data

    # Fall back to cookie session
    return get_user_from_cookie_session(request)
