"""
Broker Token Managers for ProAlgoTrader FastAPI.
Handles token generation for different brokers.
"""

import httpx
import pyotp
from logzero import logger


class AngelOneTokenManager:
    """
    Token manager for Angel One broker.
    Generates JWT tokens using TOTP authentication.
    """

    # Angel One API endpoints
    LOGIN_URL = "https://apiconnect.angelbroking.com/rest/auth/angelbroking/user/v1/loginByPassword"

    # Angel One headers
    HEADERS = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-ClientLocalIP": "clientLocalIp",
        "X-ClientPublicIP": "clientPublicIp",
        "X-MACAddress": "clientMacAddress",
        "X-UserType": "USER",
        "X-SourceID": "WEB",
    }

    def __init__(self, config: dict):
        """
        Initialize Angel One token manager.

        Args:
            config: Broker configuration containing:
                - username: Angel One client code
                - totp_key: TOTP secret key
                - pin: MPIN
                - api_key: API key
                - api_secret: API secret
        """
        self.username = config.get("username", "")
        self.totp_key = config.get("totp_key", "")
        self.mpin = config.get("pin", "")
        self.api_key = config.get("api_key", "")
        self.api_secret = config.get("api_secret", "")
        self.redirect_url = config.get("redirect_url", "")

    async def generate_token(self) -> dict:
        """
        Generate token using Angel One API.

        Returns:
            dict with status, data (jwtToken, feedToken), and error if failed
        """
        try:
            # Generate TOTP code
            totp = pyotp.TOTP(self.totp_key)
            totp_code = totp.now()

            # Prepare headers with API key
            headers = {**self.HEADERS, "X-PrivateKey": self.api_key}

            # Prepare request body
            payload = {
                "clientcode": self.username,
                "password": self.mpin,
                "totp": totp_code,
            }

            logger.info(f"[AngelOne] Generating token for user: {self.username}")

            # Make API request
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    self.LOGIN_URL, headers=headers, json=payload
                )

            if response.status_code != 200:
                error_msg = f"Login failed: {response.text}"
                logger.error(f"[AngelOne] {error_msg}")
                return {
                    "data": None,
                    "status": response.status_code,
                    "error": error_msg,
                }

            data = response.json()

            # Extract tokens
            session_data = data.get("data", {})
            jwt_token = session_data.get("jwtToken")
            feed_token = session_data.get("feedToken")

            if not jwt_token:
                error_msg = "JWT Token not found in response"
                logger.error(f"[AngelOne] {error_msg}")
                return {"data": None, "status": 500, "error": error_msg}

            logger.info("[AngelOne] Token generated successfully")

            return {
                "data": {
                    "jwtToken": jwt_token,
                    "feedToken": feed_token,
                },
                "status": 200,
            }

        except Exception as e:
            error_msg = f"Token generation failed: {str(e)}"
            logger.error(f"[AngelOne] {error_msg}")
            return {"data": None, "status": 500, "error": error_msg}


class FyersTokenManager:
    """
    Token manager for Fyers broker.
    Generates tokens using OAuth flow.
    """

    def __init__(self, config: dict):
        """
        Initialize Fyers token manager.

        Args:
            config: Broker configuration containing:
                - client_id: Fyers client ID
                - secret_key: Fyers secret key
                - redirect_uri: Redirect URI for OAuth
        """
        self.client_id = config.get("client_id", "")
        self.secret_key = config.get("secret_key", "")
        self.redirect_uri = config.get("redirect_uri", "")

    async def generate_token(self) -> dict:
        """
        Generate token for Fyers broker.

        Returns:
            dict with status, data (jwtToken, feedToken), and error if failed
        """
        # TODO: Implement Fyers token generation
        return {
            "data": None,
            "status": 501,
            "error": "Fyers token generation not implemented yet",
        }


class ShoonyaTokenManager:
    """
    Token manager for Shoonya broker.
    """

    def __init__(self, config: dict):
        """
        Initialize Shoonya token manager.

        Args:
            config: Broker configuration
        """
        self.config = config

    async def generate_token(self) -> dict:
        """
        Generate token for Shoonya broker.

        Returns:
            dict with status, data (jwtToken, feedToken), and error if failed
        """
        # TODO: Implement Shoonya token generation
        return {
            "data": None,
            "status": 501,
            "error": "Shoonya token generation not implemented yet",
        }


def get_token_manager(broker_title: str, config: dict):
    """
    Get appropriate token manager for broker.

    Args:
        broker_title: Broker title (e.g., 'angel-one', 'fyers')
        config: Broker configuration

    Returns:
        Token manager instance
    """
    broker_title = broker_title.lower().replace(" ", "-").replace("_", "-")

    if broker_title == "angel-one":
        return AngelOneTokenManager(config)
    elif broker_title == "fyers":
        return FyersTokenManager(config)
    elif broker_title == "shoonya":
        return ShoonyaTokenManager(config)
    else:
        raise ValueError(f"Unsupported broker: {broker_title}")
