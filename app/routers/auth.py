"""
Authentication routes for ProAlgoTrader FastAPI.

Uses database-backed sessions instead of cookie-based sessions.
User and session data stored in project database with project-specific data.
"""

import secrets
from datetime import datetime, timedelta

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, RedirectResponse
from itsdangerous import SignatureExpired, URLSafeTimedSerializer
from sqlmodel import Session as DBSession
from sqlmodel import select

from app.core.config import settings
from app.models.user import Session as AuthSession
from app.models.user import User
from db.database import get_project_session

router = APIRouter(tags=["auth"])

# Session serializer for cookie
serializer = URLSafeTimedSerializer(settings.SECRET_KEY)


def create_session_cookie(session_id: str) -> str:
    """Create encrypted session ID cookie."""
    return serializer.dumps({"session_id": session_id})


def get_session_id_from_cookie(cookie: str) -> str | None:
    """Decrypt session ID from cookie."""
    try:
        data = serializer.loads(cookie, max_age=settings.SESSION_EXPIRE_HOURS * 3600)
        return data.get("session_id")
    except SignatureExpired:
        return None


def get_session_data(cookie: str) -> dict | None:
    """Get session data from cookie (backwards compatibility).

    This function looks up the session in the database and returns
    user data in the same format as the old cookie-based sessions.

    Args:
        cookie: The session cookie value

    Returns:
        Dict with user_id, user_name, user_email, access_token, refresh_token
        or None if session not found/expired
    """
    session_id = get_session_id_from_cookie(cookie)
    if not session_id:
        return None

    # Get session from database
    db_gen = get_project_session()
    db = next(db_gen)

    try:
        # Find session
        auth_session = db.exec(
            select(AuthSession).where(AuthSession.id == session_id)
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

        # Return in structured format
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


def get_current_user(request: Request, db: DBSession = None) -> dict | None:
    """Get current user from database session.

    Args:
        request: FastAPI request object
        db: Database session (optional, will create if not provided)

    Returns:
        User dict if authenticated, None otherwise
    """
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        return None

    session_id = get_session_id_from_cookie(session_cookie)
    if not session_id:
        return None

    # Get session from database
    db_gen = get_project_session() if db is None else iter([db])
    db_session = next(db_gen)

    try:
        # Find session
        auth_session = db_session.exec(
            select(AuthSession).where(AuthSession.id == session_id)
        ).first()

        if not auth_session:
            return None

        # Check if access token expired
        if auth_session.access_token_expires_at < datetime.utcnow():
            return None

        # Get user
        user = db_session.exec(
            select(User).where(User.id == auth_session.user_id)
        ).first()

        if not user:
            return None

        # Return in structured format
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
        if db is None:
            db_session.close()


@router.get("/api/oauth/config")
async def get_oauth_config(request: Request):
    """Get OAuth configuration for frontend."""
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)

    # Create response with state cookie
    response = JSONResponse(
        {
            "auth_url": f"{settings.REMOTE_API_URL}/oauth/authorize",
            "client_id": settings.oauth_app_id,
            "redirect_uri": settings.OAUTH_REDIRECT_URI,
            "state": state,
        }
    )

    # Set state in cookie so callback can verify it
    response.set_cookie(
        key="oauth_state", value=state, httponly=True, max_age=600  # 10 minutes
    )

    return response


@router.get("/oauth/login")
async def oauth_login(request: Request, redirect_to: str = None):
    """Initiate OAuth2 login flow.

    Args:
        redirect_to: Optional URL to redirect to after successful login.
                    Defaults to '/' if not specified.
    """
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)

    # Build OAuth2 authorization URL
    auth_url = (
        f"{settings.REMOTE_API_URL}/oauth/authorize?"
        f"client_id={settings.oauth_app_id}&"
        f"redirect_uri={settings.OAUTH_REDIRECT_URI}&"
        f"response_type=code&"
        f"state={state}"
    )

    # Store state in cookie
    response = RedirectResponse(url=auth_url)
    response.set_cookie(
        key="oauth_state", value=state, httponly=True, max_age=600  # 10 minutes
    )
    # Store redirect destination if provided
    if redirect_to:
        response.set_cookie(
            key="oauth_redirect_to", value=redirect_to, httponly=True, max_age=600
        )
    return response


@router.get("/oauth/callback")
async def oauth_callback(
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
    request: Request = None,
):
    """Handle OAuth2 callback from provider.

    Creates or updates user and session in database, then sets session cookie.
    """
    print(
        f"[OAuth] Callback received - code: {code[:10] if code else 'None'}, state: {state[:10] if state else 'None'}, error: {error}"
    )

    # Handle errors from OAuth provider
    if error:
        print(f"[OAuth] Error from provider: {error}")
        return RedirectResponse(url=f"/login?error={error}", status_code=303)

    if not code:
        print("[OAuth] No authorization code received")
        return RedirectResponse(url="/login?error=no_code", status_code=303)

    # Verify state parameter for CSRF protection
    stored_state = request.cookies.get("oauth_state")
    if state:
        print(f"[OAuth] State from callback: {state[:10]}...")
        print(
            f"[OAuth] State from cookie: {stored_state[:10] if stored_state else 'None'}..."
        )

        if stored_state and state != stored_state:
            print("[OAuth] State mismatch! Possible CSRF attack.")
            return RedirectResponse(url="/login?error=state_mismatch", status_code=303)
    else:
        print("[OAuth] Warning: No state parameter received")

    try:
        # Exchange authorization code for access token
        token_url = f"{settings.REMOTE_API_URL}/oauth/token"

        async with httpx.AsyncClient() as client:
            print(f"[OAuth] Exchanging code for token at {token_url}")
            print("[OAuth] Request payload:")
            print("  grant_type: authorization_code")
            print(f"  code: {code[:10]}...")
            print(f"  redirect_uri: {settings.OAUTH_REDIRECT_URI}")
            print(f"  client_id: {settings.oauth_app_id}")
            print(f"  client_secret: {'*' * 8}")

            response = await client.post(
                token_url,
                json={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": settings.OAUTH_REDIRECT_URI,
                    "client_id": settings.oauth_app_id,
                    "client_secret": settings.oauth_app_secret,
                },
                timeout=30.0,
                follow_redirects=True,
            )

            print(f"[OAuth] Token exchange response status: {response.status_code}")

            if response.status_code != 200:
                print("[OAuth] Token exchange failed!")
                print(f"[OAuth] Response body: {response.text}")
                error_data = (
                    response.json()
                    if response.headers.get("content-type", "").startswith(
                        "application/json"
                    )
                    else {}
                )
                error_msg = (
                    error_data.get("error")
                    or error_data.get("message")
                    or f"Token exchange failed with status {response.status_code}"
                )
                print(f"[OAuth] Error: {error_msg}")
                return RedirectResponse(
                    url=f"/login?error={error_msg}", status_code=303
                )

            data = response.json()
            print("[OAuth] Token exchange successful!")
            print(f"[OAuth] Response keys: {list(data.keys())}")

            # Extract user and token info from response
            access_token = data.get("accessToken") or data.get("access_token")
            refresh_token = data.get("refreshToken") or data.get("refresh_token")
            expires_in = data.get(
                "expires_in", 604800
            )  # Default 7 days if not provided
            user = data.get("user", {})

            print(f"[OAuth] User info from token response: {user}")
            print(f"[OAuth] expires_in: {expires_in} seconds")

            if not access_token:
                print("[OAuth] No access token in response")
                return RedirectResponse(url="/login?error=no_token", status_code=303)

            # Get user info
            user_id = str(user.get("id")) if user.get("id") else None
            user_name = user.get("name", "Unknown")
            user_email = user.get("email", "unknown@example.com")

            if not user_id:
                print("[OAuth] No user ID in response")
                return RedirectResponse(url="/login?error=no_user", status_code=303)

            # Calculate token expiry times
            access_token_expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
            refresh_token_expires_at = datetime.utcnow() + timedelta(
                days=30
            )  # 30 days for refresh token

            # Get database session
            db_gen = get_project_session()
            db = next(db_gen)

            try:
                # Check if user exists (use id as API UUID)
                existing_user = db.exec(select(User).where(User.id == user_id)).first()

                if existing_user:
                    # Update existing user
                    existing_user.name = user_name
                    existing_user.email = user_email
                    existing_user.updated_at = datetime.utcnow()
                    db.add(existing_user)
                    print(f"[OAuth] Updated existing user: {user_id}")

                    # Delete old sessions for this user
                    old_sessions = db.exec(
                        select(AuthSession).where(AuthSession.user_id == user_id)
                    ).all()
                    for old_session in old_sessions:
                        db.delete(old_session)
                else:
                    # Create new user (id is the API UUID)
                    new_user = User(
                        id=user_id,  # API UUID as primary key
                        name=user_name,
                        email=user_email,
                    )
                    db.add(new_user)
                    db.commit()
                    db.refresh(new_user)
                    print(f"[OAuth] Created new user: {user_id}")

                # Create new session
                auth_session = AuthSession(
                    user_id=user_id,
                    access_token=access_token,
                    access_token_expires_at=access_token_expires_at,
                    refresh_token=refresh_token,
                    refresh_token_expires_at=refresh_token_expires_at,
                )
                db.add(auth_session)
                db.commit()
                db.refresh(auth_session)
                session_id = auth_session.id
                print(f"[OAuth] Created session: {session_id}")

            finally:
                db.close()

            # Create session cookie with just the session ID
            session_cookie = create_session_cookie(session_id)
            print(f"[OAuth] Session cookie created (length: {len(session_cookie)})")

            # Check if project is synced
            from app.core.config import settings as proj_settings
            from app.services.project_service import is_project_synced

            project_key = proj_settings.PROJECT_KEY
            project_synced = is_project_synced(project_key)
            print(f"[OAuth] Project synced: {project_synced}")

            # Determine redirect destination
            if not project_synced:
                # Project not synced, redirect to initialize page
                redirect_to = "/project/initialize"
                print("[OAuth] Project not synced, redirecting to initialize page")
            else:
                # Project synced, use stored redirect or dashboard
                redirect_to = request.cookies.get("oauth_redirect_to", "/dashboard")
                print(f"[OAuth] Project synced, redirecting to: {redirect_to}")

            # Redirect to destination
            response = RedirectResponse(url=redirect_to, status_code=303)
            response.set_cookie(
                key="session",
                value=session_cookie,
                httponly=True,
                secure=False,  # Set to True in production with HTTPS
                samesite="lax",
                max_age=settings.SESSION_EXPIRE_HOURS * 3600,
            )
            # Clear the oauth_state cookie after successful authentication
            response.delete_cookie(key="oauth_state")
            # Clear the redirect_to cookie
            response.delete_cookie(key="oauth_redirect_to")

            print("[OAuth] Session created, redirecting to home")
            return response

    except httpx.HTTPError as e:
        print(f"[OAuth] HTTP error during token exchange: {str(e)}")
        return RedirectResponse(url="/login?error=connection_error", status_code=303)
    except Exception as e:
        print(f"[OAuth] Unexpected error: {str(e)}")
        import traceback

        traceback.print_exc()
        return RedirectResponse(url="/login?error=unknown_error", status_code=303)


@router.get("/oauth/logout")
async def logout(request: Request):
    """Logout user by deleting session from database and clearing cookie."""
    session_cookie = request.cookies.get("session")

    if session_cookie:
        session_id = get_session_id_from_cookie(session_cookie)
        if session_id:
            # Delete session from database
            db_gen = get_project_session()
            db = next(db_gen)
            try:
                auth_session = db.exec(
                    select(AuthSession).where(AuthSession.id == session_id)
                ).first()
                if auth_session:
                    db.delete(auth_session)
                    db.commit()
                    print(f"[OAuth] Deleted session: {session_id}")
            finally:
                db.close()

    # Clear cookie and redirect
    response = RedirectResponse(url="/")
    response.delete_cookie("session")
    return response


@router.get("/api/user/me")
async def get_current_user_api(request: Request):
    """Get current authenticated user info."""
    user = get_current_user(request)
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Return user info without tokens
    return {
        "id": user["user"]["id"],
        "name": user["user"]["name"],
        "email": user["user"]["email"],
    }


@router.get("/api/auth/user")
async def get_auth_user_api(request: Request):
    """Get current authenticated user info (for navbar).

    This endpoint is used by the navbar JavaScript to check authentication
    status and get user information. Returns authenticated flag and user data.
    """
    user = get_current_user(request)

    if not user:
        return {"authenticated": False}

    return {
        "authenticated": True,
        "user": {
            "id": user.get("user", {}).get("id"),
            "name": user.get("user", {}).get("name"),
            "email": user.get("user", {}).get("email"),
        },
    }
