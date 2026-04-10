from __future__ import annotations

from typing import Protocol


class GithubRepositoryInfoProtocol(Protocol):
    """Protocol for GithubRepositoryInfo functionality."""

    # Properties from concrete implementation
    id: int
    repository_owner: str
    repository_name: str
    repository_full_name: str
    repository_id: int
