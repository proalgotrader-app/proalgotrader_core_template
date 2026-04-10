from typing import Any

from proalgotrader_core.protocols.github_repository_info import (
    GithubRepositoryInfoProtocol,
)


class GithubRepositoryInfo(GithubRepositoryInfoProtocol):
    def __init__(self, github_repository_info: dict[str, Any]) -> None:
        self.id: int = github_repository_info["id"]
        self.repository_owner: str = github_repository_info["repository_owner"]
        self.repository_name: str = github_repository_info["repository_name"]
        self.repository_full_name: str = github_repository_info["repository_full_name"]
        self.repository_id: int = github_repository_info["repository_id"]
