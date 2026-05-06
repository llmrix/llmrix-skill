"""
core: Cross-cutting concerns — configuration, exceptions, and utilities.
"""
from .config import SkillConfig
from .exceptions import (
    GitSkillError,
    SkillNotFoundError,
    VersionNotFoundError,
    PermissionDeniedError,
    ValidationError,
    GitOperationError,
)
from .utils import build_file_tree
from .plugin import BaseSkill

__all__ = [
    "SkillConfig",
    "GitSkillError",
    "SkillNotFoundError",
    "VersionNotFoundError",
    "PermissionDeniedError",
    "ValidationError",
    "GitOperationError",
    "build_file_tree",
    "BaseSkill",
]
