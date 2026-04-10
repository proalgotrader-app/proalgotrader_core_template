from __future__ import annotations

from typing import Any, Protocol

from proalgotrader_core.protocols.broker_info import BrokerInfoProtocol
from proalgotrader_core.protocols.github_repository_info import (
    GithubRepositoryInfoProtocol,
)


class ProjectInfoProtocol(Protocol):
    """Protocol for Project functionality."""

    # Properties from concrete implementation
    id: int
    name: str
    status: str

    broker_info: BrokerInfoProtocol
    github_repository_info: GithubRepositoryInfoProtocol

    # Methods from concrete implementation
    def __init__(self, project_info: dict[str, Any]) -> None: ...
