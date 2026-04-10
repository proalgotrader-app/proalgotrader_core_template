"""Core package for configuration and utilities."""

from app.core.config import settings
from app.core.env_validator import (
    EnvironmentValidationError,
    get_project_key,
    validate_environment,
    validate_on_startup,
)

__all__ = [
    "settings",
    "EnvironmentValidationError",
    "validate_environment",
    "validate_on_startup",
    "get_project_key",
]
