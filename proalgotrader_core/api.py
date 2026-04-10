from typing import Any

import httpx

from proalgotrader_core.protocols.args_manager import ArgsManagerProtocol


class Api:
    def __init__(self, args_manager: ArgsManagerProtocol) -> None:
        self.algo_session_id = args_manager.algo_session_id
        self.local_api_url = args_manager.local_api_url
        self.remote_api_url = args_manager.remote_api_url
        self.api_token = args_manager.api_token

        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_token}",
        }

        # HTTP client for all API requests
        self.client = httpx.AsyncClient(
            base_url=self.local_api_url,
            headers=self.headers,
            timeout=httpx.Timeout(30.0, connect=60.0),
        )

    async def _request(
        self,
        method: str,
        endpoint: str,
        *,
        data: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        print(f"[Api] Making request: {method.upper()} {self.local_api_url}{endpoint}")
        print(f"[Api] Headers: {self.headers}")

        try:
            response = await self.client.request(
                method,
                endpoint,
                json=json,
                data=data,
                params=params,
            )

            print(f"[Api] Response status: {response.status_code}")
            print(f"[Api] Response headers: {dict(response.headers)}")

            # Try to parse JSON response
            result: dict[str, Any]
            try:
                result = response.json()
                print(f"[Api] Response JSON: {result}")
            except Exception as json_err:
                print(f"[Api] Failed to parse JSON: {json_err}")
                print(f"[Api] Response text: {response.text}")
                result = {}

            # Check if response is successful
            if not response.is_success:
                # Extract error details from FastAPI response
                error_detail = "Unknown error"
                if result:
                    # FastAPI typically returns errors in 'detail' field
                    if "detail" in result:
                        error_detail = result["detail"]
                    else:
                        error_detail = str(result)
                else:
                    # No JSON response, use status code
                    error_detail = (
                        f"HTTP {response.status_code}: {response.reason_phrase}"
                    )

                print("[Api] ❌ Request failed!")
                print(f"[Api]   Status: {response.status_code}")
                print(f"[Api]   Reason: {response.reason_phrase}")
                print(f"[Api]   Detail: {error_detail}")
                print(f"[Api]   Full response: {result}")

                raise Exception(
                    f"API request failed (HTTP {response.status_code}): {error_detail}"
                )

            print("[Api] ✅ Request successful")
            return result

        except httpx.HTTPError as http_err:
            print(f"[Api] ❌ HTTP error: {http_err}")
            print(f"[Api]   Error type: {type(http_err).__name__}")
            raise Exception(f"HTTP error: {http_err}")
        except Exception as e:
            print(f"[Api] ❌ Unexpected error: {e}")
            print(f"[Api]   Error type: {type(e).__name__}")
            raise

    async def get_algo_session_info(self) -> dict[str, Any]:
        print(f"[Api] Fetching algo session info for: {self.algo_session_id}")

        endpoint = f"/api/algo-sessions/{self.algo_session_id}/context"

        result = await self._request("get", endpoint)

        print("[Api] ✅ Successfully retrieved algo session info")

        return result

    async def get_trading_days(
        self,
        years: str | None = None,
    ) -> dict[str, Any]:
        """Fetch ALL trading calendar days from the API.

        Uses the /all endpoint to get records for specified years.

        Args:
            years: Optional comma-separated years (e.g., "2024,2025").
                   Defaults to current year and previous year.

        Returns:
            Dict containing trading calendar data with all records
        """
        # /all endpoint returns all records for specified years (defaults to previous + current year)
        endpoint = "/api/trading-calendar/all"
        params = {"years": years} if years else None

        result = await self._request("get", endpoint, params=params)

        print("[Api] ✅ Successfully retrieved trading days")

        return result

    async def close(self) -> None:
        print("[Api] Closing HTTP client")
        await self.client.aclose()
