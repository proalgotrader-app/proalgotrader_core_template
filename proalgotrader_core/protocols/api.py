from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from proalgotrader_core.protocols.args_manager import ArgsManagerProtocol


class ApiProtocol(Protocol):
    """Protocol for Api functionality."""

    # Properties from concrete implementation
    algo_session_id: str
    local_api_url: str
    remote_api_url: str
    api_token: str
    headers: dict[str, str]
    client: Any  # httpx.AsyncClient

    # Constructor
    def __init__(self, args_manager: ArgsManagerProtocol) -> None: ...

    # Public methods
    async def get_algo_session_info(self) -> dict[str, Any]: ...

    async def get_trading_days(
        self,
        years: str | None = None,
    ) -> dict[str, Any]: ...

    async def close(self) -> None: ...
