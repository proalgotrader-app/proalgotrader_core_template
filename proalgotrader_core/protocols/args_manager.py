from __future__ import annotations

from typing import Any, Protocol


class ArgsManagerProtocol(Protocol):
    """Protocol for ArgsManager functionality."""

    # Properties from concrete implementation
    arguments: Any  # argparse.Namespace
    algo_session_id: str
    local_api_url: str
    remote_api_url: str
    api_token: str

    # Public methods from concrete implementation
    def validate_arguments(self) -> None: ...
