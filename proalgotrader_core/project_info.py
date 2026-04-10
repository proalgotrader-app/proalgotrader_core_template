from typing import Any

from proalgotrader_core.broker_info import BrokerInfo
from proalgotrader_core.github_repository_info import GithubRepositoryInfo
from proalgotrader_core.protocols.broker_info import BrokerInfoProtocol
from proalgotrader_core.protocols.github_repository_info import (
    GithubRepositoryInfoProtocol,
)
from proalgotrader_core.protocols.project_info import ProjectInfoProtocol


class ProjectInfo(ProjectInfoProtocol):
    def __init__(self, project_info: dict[str, Any]):
        self.id: int = project_info["id"]

        self.name: str = project_info["name"]

        self.status: str = project_info["status"]

        self.broker_info: BrokerInfoProtocol = BrokerInfo(project_info["broker"])

        self.github_repository_info: GithubRepositoryInfoProtocol = (
            GithubRepositoryInfo(project_info["strategy"]["github_repository"])
        )
