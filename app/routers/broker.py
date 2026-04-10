"""
Broker routes for ProAlgoTrader FastAPI.
Handles broker token generation and management.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Request
from logzero import logger
from pydantic import BaseModel
from sqlmodel import Session, select

from app.models.broker_token import BrokerToken
from app.routers.auth import get_session_data
from app.services.broker_token_manager import get_token_manager
from db.database import get_global_session

router = APIRouter(prefix="/api/brokers", tags=["broker"])


class BrokerConfigPayload(BaseModel):
    """Broker configuration payload for token generation."""

    broker_id: str  # Broker ID from project.json
    username: str | None = None
    totp_key: str | None = None
    pin: str | None = None
    api_key: str | None = None
    api_secret: str | None = None
    redirect_url: str | None = None
    client_id: str | None = None
    secret_key: str | None = None


async def _create_new_token(
    broker_title: str,
    broker_id: str,
    config_dict: dict,
    existing_token: BrokerToken | None,
    db: Session,
):
    """Create new token and save to database."""
    try:
        manager = get_token_manager(broker_title, config_dict)
        result = await manager.generate_token()

        if result["status"] != 200 or not result["data"]:
            error_msg = result.get("error", "Token generation failed")
            logger.error(f"[Broker] {error_msg}")
            raise HTTPException(status_code=500, detail=error_msg)

        jwt_token = result["data"].get("jwtToken")
        feed_token = result["data"].get("feedToken")

        if not jwt_token:
            raise HTTPException(status_code=500, detail="JWT token not generated")

        logger.info("[Broker] New token generated successfully")

        # Update or create broker token
        if existing_token:
            existing_token.token = jwt_token
            existing_token.feed_token = feed_token
            existing_token.updated_at = datetime.utcnow()
            db.add(existing_token)
            db.commit()
            db.refresh(existing_token)
        else:
            # Create new token
            new_token = BrokerToken(
                broker_id=broker_id, token=jwt_token, feed_token=feed_token
            )
            db.add(new_token)
            db.commit()
            db.refresh(new_token)

        return {
            "success": True,
            "token": jwt_token,
            "feed_token": feed_token,
            "broker_id": broker_id,
        }

    except ValueError as e:
        logger.error(f"[Broker] Unsupported broker: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"[Broker] Token generation failed: {e}")
        raise HTTPException(
            status_code=500, detail=f"Token generation failed: {str(e)}"
        )


@router.get("/{broker_title}/token")
async def get_broker_token(
    broker_title: str,
    broker_id: str,
    request: Request,
    db: Session = Depends(get_global_session),
):
    """
    Get existing broker token (no generation).

    Returns 404 if token doesn't exist.

    Args:
        broker_title: Broker title (e.g., 'angel-one', 'fyers')
        broker_id: Broker ID from project.json (query parameter)

    Returns:
        TokenResponse if token exists, 404 otherwise
    """
    # Verify user is authenticated
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_data = get_session_data(session_cookie)
    if not session_data:
        raise HTTPException(status_code=401, detail="Session expired")

    # Get existing token
    existing_token = db.exec(
        select(BrokerToken).where(BrokerToken.broker_id == broker_id)
    ).first()

    # If no token exists, return 404
    if not existing_token:
        raise HTTPException(
            status_code=404,
            detail="No token found for this broker. Please generate a token.",
        )

    logger.info(f"[Broker] Returning existing token for broker: {broker_title}")
    return {
        "success": True,
        "token": existing_token.token,
        "feed_token": existing_token.feed_token,
        "broker_id": broker_id,
    }


@router.post("/{broker_title}/generate")
async def generate_broker_token(
    broker_title: str,
    config: BrokerConfigPayload,
    request: Request,
    db: Session = Depends(get_global_session),
):
    """
    Get existing broker token or create if doesn't exist.

    Args:
        broker_title: Broker title (e.g., 'angel-one', 'fyers')
        config: Broker configuration containing broker_id, username, totp_key, pin, api_key, etc.

    Returns:
        TokenResponse with existing token (generated: false) or newly created token (generated: true)
    """
    # Verify user is authenticated
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_data = get_session_data(session_cookie)
    if not session_data:
        raise HTTPException(status_code=401, detail="Session expired")

    broker_id = config.broker_id

    # Convert config to dict
    config_dict = config.dict(exclude_none=True, exclude={"broker_id"})

    # Get existing token
    existing_token = db.exec(
        select(BrokerToken).where(BrokerToken.broker_id == broker_id)
    ).first()

    # If token exists, return it
    if existing_token:
        logger.info(f"[Broker] Returning existing token for broker: {broker_title}")
        return {
            "success": True,
            "token": existing_token.token,
            "feed_token": existing_token.feed_token,
            "broker_id": broker_id,
            "generated": False,
        }

    # No token exists - create new
    logger.info(
        f"[Broker] Creating new token for broker: {broker_title} (ID: {broker_id})"
    )

    # Generate new token
    result = await _create_new_token(
        broker_title, broker_id, config_dict, existing_token, db
    )
    result["generated"] = True
    return result


@router.post("/{broker_title}/regenerate")
async def regenerate_broker_token(
    broker_title: str,
    config: BrokerConfigPayload,
    request: Request,
    db: Session = Depends(get_global_session),
):
    """
    Force regenerate broker token - always creates new, replaces existing.

    Args:
        broker_title: Broker title (e.g., 'angel-one', 'fyers')
        config: Broker configuration containing broker_id, username, totp_key, pin, api_key, etc.

    Returns:
        TokenResponse with newly generated token details
    """
    # Verify user is authenticated
    session_cookie = request.cookies.get("session")
    if not session_cookie:
        raise HTTPException(status_code=401, detail="Not authenticated")

    session_data = get_session_data(session_cookie)
    if not session_data:
        raise HTTPException(status_code=401, detail="Session expired")

    broker_id = config.broker_id

    logger.info(
        f"[Broker] Force regenerate token for broker: {broker_title} (ID: {broker_id})"
    )

    # Convert config to dict (exclude broker_id as it's not needed for token generation)
    config_dict = config.dict(exclude_none=True, exclude={"broker_id"})

    # Get existing token (will be replaced)
    existing_token = db.exec(
        select(BrokerToken).where(BrokerToken.broker_id == broker_id)
    ).first()

    # Always create new token
    result = await _create_new_token(
        broker_title, broker_id, config_dict, existing_token, db
    )
    result["generated"] = True
    return result
