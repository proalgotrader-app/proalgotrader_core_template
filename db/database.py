"""
Database configuration for ProAlgoTrader FastAPI.

Provides two databases:

1. **Global Database** (~/.proalgotrader/shared_db/global.db)
   Stores data shared across all projects:
   - Base symbols (stocks, indices, etc.)
   - Broker symbols (broker-specific instrument data)
   - Broker tokens (authentication credentials)
   - Trading calendar (market holidays/working days)

2. **Project Database** (~/.proalgotrader/project_db/{PROJECT_KEY}/proalgotrader.db)
   Stores project-specific data:
   - Users (user accounts)
   - Sessions (user authentication)
   - Projects (project configurations)
   - Strategies (trading strategy definitions)
   - Brokers (broker configurations)
   - GitHub accounts & repositories (strategy sources)
   - Algo sessions (strategy execution instances)

Database Structure:

GLOBAL DATABASE (global.db):
┌─────────────────────┬──────────────────────────────────────┐
│ Table               │ Purpose                              │
├─────────────────────┼──────────────────────────────────────┤
│ base_symbols        │ Master symbol list (shared)          │
│ broker_symbols      │ Broker-specific instrument data      │
│ broker_tokens       │ Broker authentication tokens         │
│ trading_calendar   │ Market calendar (holidays, etc.)     │
└─────────────────────┴──────────────────────────────────────┘

PROJECT DATABASE (proalgotrader.db):
┌─────────────────────┬──────────────────────────────────────┐
│ Table               │ Purpose                              │
├─────────────────────┼──────────────────────────────────────┤
│ users               │ User accounts (API UUID as PK)       │
│ sessions            │ User sessions (local UUID)           │
│ github_accounts     │ GitHub account details               │
│ github_repositories │ GitHub repos (FK: github_accounts)   │
│ strategies          │ Trading strategies (FK: github_repos)│
│ brokers             │ Broker configurations (FK: projects) │
│ projects            │ Project configurations               │
│ algo_sessions       │ Strategy execution instances         │
└─────────────────────┴──────────────────────────────────────┘

Key Features:
- Foreign keys enabled (referential integrity)
- WAL mode (better concurrency)
- Indexes on FK columns (performance)
- Timestamps on all tables (audit trail)

Directory structure:
    ~/.proalgotrader/
    ├── shared_db/
    │   └── global.db           # Global database
    └── project_db/
        └── {PROJECT_KEY}/
            └── proalgotrader.db  # Project database
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlmodel import Session, create_engine, text

# Load environment variables
load_dotenv()

# =============================================================================
# Utility Functions for Dynamic Paths
# =============================================================================


def get_global_db_url() -> str:
    """Get the global database URL (shared across all projects).

    Creates the directory if it doesn't exist.
    Uses as_posix() for cross-platform compatibility.
    """
    db_path = Path.home() / ".proalgotrader" / "shared_db" / "global.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_path.as_posix()}"


def get_project_db_url() -> str:
    """Get the project database URL.

    Uses PROJECT_KEY from environment to create project-specific database.
    Path: ~/.proalgotrader/project_db/{PROJECT_KEY}/proalgotrader.db

    Raises:
        ValueError: If PROJECT_KEY is not set

    Returns:
        SQLite URL for the project database
    """
    # Import here to avoid circular dependency
    from app.core.env_validator import get_project_key

    project_key = get_project_key()

    # Create project-specific database path
    db_path = (
        Path.home() / ".proalgotrader" / "project_db" / project_key / "proalgotrader.db"
    )
    db_path.parent.mkdir(parents=True, exist_ok=True)

    return f"sqlite:///{db_path.as_posix()}"


# =============================================================================
# Path Configuration
# =============================================================================

# Debug mode for SQL echo
DEBUG_DB = os.getenv("DEBUG_DB", "false").lower() == "true"

# Database URLs (using utility functions)
PROJECT_DB_URL = get_project_db_url()
GLOBAL_DB_URL = get_global_db_url()

# =============================================================================
# Database Engines with WAL Mode
# =============================================================================


def create_sqlite_engine(db_url: str, echo: bool = False) -> create_engine:
    """Create a SQLite engine with WAL mode for better concurrency.

    WAL (Write-Ahead Logging) allows:
    - Multiple readers while one writer is active
    - Better concurrency than default journal mode
    """
    engine = create_engine(
        db_url,
        echo=echo,
        connect_args={"check_same_thread": False},  # Needed for SQLite
    )

    # Enable WAL mode for better write concurrency
    with engine.connect() as conn:
        conn.execute(text("PRAGMA journal_mode=WAL;"))
        conn.commit()

    return engine


# Project database engine (for project-specific data)
project_engine = create_sqlite_engine(PROJECT_DB_URL, echo=DEBUG_DB)

# Global database engine (for shared data across projects)
global_engine = create_sqlite_engine(GLOBAL_DB_URL, echo=DEBUG_DB)

print(f"[Database] Project database: {PROJECT_DB_URL}")
print(f"[Database] Global database: {GLOBAL_DB_URL}")

# =============================================================================
# Model Registry for Dual Database
# =============================================================================

# Models that belong to the project database
PROJECT_MODELS = [
    # Core project data (from API)
    "User",
    "Session",
    "Project",
    "Broker",
    "Strategy",
    "GitHubAccount",
    "GitHubRepository",
    # Local project data
    "AlgoSession",
]

# Models that belong to the global database
GLOBAL_MODELS = [
    # BrokerToken is shared across projects
    "BrokerToken",
    # BaseSymbol is shared across projects
    "BaseSymbol",
    # TradingCalendar is shared across projects
    "TradingCalendar",
    # BrokerSymbol is shared across projects
    "BrokerSymbol",
]


def get_model_table(model_class):
    """Get the table for a model class."""
    return model_class.__table__


def create_db_and_tables():
    """Create database and all tables on startup."""
    from app.models import (
        AlgoSession,
        BaseSymbol,
        Broker,
        BrokerSymbol,
        BrokerToken,
        GitHubAccount,
        GitHubRepository,
        Project,
        Strategy,
        TradingCalendar,
    )
    from app.models.user import Session, User

    print("[Database] Creating tables...")

    # Create project database tables (in correct order for FK constraints)
    print("[Database] Creating project tables...")

    # First: tables with no FKs or self-referencing FKs
    for model in [User, GitHubAccount]:
        model.__table__.create(project_engine, checkfirst=True)
        print(f"[Database] Created table: {model.__tablename__}")

    # Second: tables with FKs to previous tables
    for model in [GitHubRepository, Strategy, Broker]:
        model.__table__.create(project_engine, checkfirst=True)
        print(f"[Database] Created table: {model.__tablename__}")

    # Third: tables with FKs to all previous tables
    for model in [Project, AlgoSession]:
        model.__table__.create(project_engine, checkfirst=True)
        print(f"[Database] Created table: {model.__tablename__}")

    # Create Session table (depends on User)
    Session.__table__.create(project_engine, checkfirst=True)
    print(f"[Database] Created table: {Session.__tablename__}")

    # Create global database tables
    print("[Database] Creating global tables...")
    for model in [
        BrokerToken,
        BaseSymbol,
        TradingCalendar,
        BrokerSymbol,
    ]:
        model.__table__.create(global_engine, checkfirst=True)
        print(f"[Database] Created table: {model.__tablename__}")

    print("[Database] Tables created successfully!")


def get_project_session():
    """Get project database session for dependency injection."""
    with Session(project_engine) as session:
        yield session


def get_global_session():
    """Get global database session for dependency injection."""
    with Session(global_engine) as session:
        yield session


# Backward compatibility: default session points to project database
def get_db_session():
    """Get database session for dependency injection (backwards compatible)."""
    yield from get_project_session()


def init_db():
    """Initialize database (can be run manually)."""
    print("[Database] Initializing database...")
    create_db_and_tables()
    print("[Database] Database initialized successfully!")
