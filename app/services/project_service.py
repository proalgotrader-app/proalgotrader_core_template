"""
Project service for ProAlgoTrader FastAPI.

Handles project-related business logic including checking if project is synced
and syncing project data from API to database.
"""

import json
from datetime import datetime

import httpx
from fastapi import HTTPException
from sqlmodel import Session, select

from app.core.config import settings
from app.models.broker import Broker
from app.models.github import GitHubAccount, GitHubRepository
from app.models.project import Project
from app.models.strategy import Strategy
from db.database import project_engine


def parse_iso_datetime(dt_string: str) -> datetime:
    """Parse ISO datetime string."""
    if not dt_string:
        return datetime.utcnow()
    return datetime.fromisoformat(dt_string.replace("Z", "+00:00"))


def is_project_synced(project_key: str) -> bool:
    """
    Check if project is already synced in database.

    Args:
        project_key: The unique project key from PROJECT_KEY env var

    Returns:
        True if project exists in database, False otherwise
    """
    with Session(project_engine) as session:
        project = session.exec(
            select(Project).where(Project.key == project_key)
        ).first()
        return project is not None


def get_project_by_key(project_key: str) -> Project | None:
    """
    Get project from database by project key.

    Args:
        project_key: The unique project key from PROJECT_KEY env var

    Returns:
        Project if found, None otherwise
    """
    with Session(project_engine) as session:
        return session.exec(select(Project).where(Project.key == project_key)).first()


def get_project_info(project_key: str = None) -> dict:
    """Get project info from database (reusable service function).

    Args:
        project_key: Project key to lookup (defaults to PROJECT_KEY env var)

    Returns:
        Dict with project info in API format

    Raises:
        HTTPException: If project not found
    """
    from app.models.github import GitHubAccount, GitHubRepository

    if project_key is None:
        project_key = settings.PROJECT_KEY

    with Session(project_engine) as db:
        project = db.exec(select(Project).where(Project.key == project_key)).first()

        if not project:
            raise HTTPException(
                status_code=404, detail="Project not found. Please sync."
            )

        # Get related entities
        broker = db.exec(select(Broker).where(Broker.id == project.broker_id)).first()

        strategy = db.exec(
            select(Strategy).where(Strategy.id == project.strategy_id)
        ).first()

        # Get GitHub repository and account for strategy
        github_repo = None
        github_account = None
        if strategy and strategy.github_repo_id:
            github_repo = db.exec(
                select(GitHubRepository).where(
                    GitHubRepository.id == strategy.github_repo_id
                )
            ).first()
            if github_repo and github_repo.github_account_id:
                github_account = db.exec(
                    select(GitHubAccount).where(
                        GitHubAccount.id == github_repo.github_account_id
                    )
                ).first()

        # Build response matching API format (snake_case)
        return {
            "success": True,
            "project": {
                "id": project.id,
                "user_id": project.user_id,
                "name": project.name,
                "status": project.status,
                "key": project.key,
                "created_at": project.created_at.isoformat(),
                "updated_at": project.updated_at.isoformat(),
                "broker": (
                    {
                        "id": broker.id,
                        "broker_title": broker.broker_title,
                        "broker_name": broker.broker_name,
                        "broker_config": (
                            json.loads(broker.broker_config)
                            if broker.broker_config
                            else None
                        ),
                    }
                    if broker
                    else None
                ),
                "strategy": (
                    {
                        "id": strategy.id,
                        "identifier": strategy.identifier,
                        "title": strategy.title,
                        "description": strategy.description,
                        "github_repository": (
                            {
                                "id": github_repo.id,
                                "user_id": (
                                    github_account.user_id if github_account else None
                                ),
                                "github_account_id": github_repo.github_account_id,
                                "repository_id": github_repo.repository_id,
                                "repository_owner": github_repo.repository_owner,
                                "repository_name": github_repo.repository_name,
                                "repository_full_name": github_repo.repository_full_name,
                                "created_at": github_repo.created_at.isoformat(),
                                "updated_at": github_repo.updated_at.isoformat(),
                                "github_account": (
                                    {
                                        "id": github_account.id,
                                        "user_id": github_account.user_id,
                                        "account_id": github_account.account_id,
                                        "type": github_account.account_type,
                                        "username": github_account.username,
                                        "name": github_account.name,
                                        "email": github_account.email,
                                        "created_at": github_account.created_at.isoformat(),
                                        "updated_at": github_account.updated_at.isoformat(),
                                    }
                                    if github_account
                                    else None
                                ),
                            }
                            if github_repo
                            else None
                        ),
                    }
                    if strategy
                    else None
                ),
            },
        }


async def sync_project_to_db(
    user_id: str, access_token: str, project_key: str, project_secret: str
) -> dict:
    """
    Sync project data from API to database.

    Args:
        user_id: User ID from session
        access_token: Access token for API authentication
        project_key: Project key from PROJECT_KEY
        project_secret: Project secret from PROJECT_SECRET

    Returns:
        Project data dict

    Raises:
        HTTPException: If sync fails
    """
    print("[Project Service] Fetching project info from API")

    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        response = await client.post(
            f"{settings.REMOTE_API_URL}/api/v1/projects/info",
            headers={"Authorization": f"Bearer {access_token}"},
            json={
                "key": project_key,
                "secret": project_secret,
            },
        )

        if response.status_code != 200:
            raise HTTPException(
                status_code=500, detail="Failed to fetch project info from API"
            )

        data = response.json()

        if not data.get("success"):
            raise HTTPException(status_code=500, detail="Invalid project data from API")

        project_data = data.get("project")
        if not project_data:
            raise HTTPException(
                status_code=500, detail="No project data in API response"
            )

        # Extract all entities from API response
        broker_data = project_data.get("broker", {})
        strategy_data = project_data.get("strategy", {})
        github_repo_data = strategy_data.get("githubRepository", {})
        github_account_data = github_repo_data.get("githubAccount", {})

        # Parse timestamps
        project_created_at = parse_iso_datetime(project_data.get("createdAt", ""))
        project_updated_at = parse_iso_datetime(project_data.get("updatedAt", ""))

        # Upsert all entities
        with Session(project_engine) as session:
            # Upsert GitHub Account
            github_account = GitHubAccount(
                id=github_account_data.get("id"),
                user_id=user_id,
                account_id=github_account_data.get("accountId"),
                account_type=github_account_data.get("type"),
                username=github_account_data.get("username"),
                name=github_account_data.get("name"),
                email=github_account_data.get("email"),
                created_at=parse_iso_datetime(github_account_data.get("createdAt", "")),
                updated_at=parse_iso_datetime(github_account_data.get("updatedAt", "")),
            )
            session.merge(github_account)
            print(
                f"[Project Service] Upserted GitHub Account: {github_account.username}"
            )

            # Upsert GitHub Repository
            github_repo = GitHubRepository(
                id=github_repo_data.get("id"),
                github_account_id=github_account_data.get("id"),
                repository_id=github_repo_data.get("repositoryId"),
                repository_owner=github_repo_data.get("repositoryOwner"),
                repository_name=github_repo_data.get("repositoryName"),
                repository_full_name=github_repo_data.get("repositoryFullName"),
                created_at=parse_iso_datetime(github_repo_data.get("createdAt", "")),
                updated_at=parse_iso_datetime(github_repo_data.get("updatedAt", "")),
            )
            session.merge(github_repo)
            print(
                f"[Project Service] Upserted GitHub Repository: {github_repo.repository_full_name}"
            )

            # Upsert Strategy
            strategy = Strategy(
                id=strategy_data.get("id"),
                identifier=strategy_data.get("identifier"),
                title=strategy_data.get("title"),
                description=strategy_data.get("description"),
                github_repo_id=github_repo_data.get("id"),
                created_at=project_created_at,
                updated_at=project_updated_at,
            )
            session.merge(strategy)
            print(f"[Project Service] Upserted Strategy: {strategy.title}")

            # Upsert Broker
            broker = Broker(
                id=broker_data.get("id"),
                broker_title=broker_data.get("brokerTitle"),
                broker_name=broker_data.get("brokerName"),
                available_broker_id=broker_data.get("availableBroker", {}).get("id"),
                broker_config=json.dumps(broker_data.get("brokerConfig", {})),
                created_at=project_created_at,
                updated_at=project_updated_at,
            )
            session.merge(broker)
            print(f"[Project Service] Upserted Broker: {broker.broker_name}")

            # Upsert Project
            project = Project(
                id=project_data.get("id"),
                user_id=user_id,
                name=project_data.get("name"),
                status=project_data.get("status", "active"),
                key=project_data.get("key"),
                broker_id=broker_data.get("id"),
                strategy_id=strategy_data.get("id"),
                created_at=project_created_at,
                updated_at=project_updated_at,
            )
            session.merge(project)
            print(f"[Project Service] Upserted Project: {project.name}")

            # Commit all changes
            session.commit()

        print("[Project Service] Successfully synced project to database")
        return project_data
