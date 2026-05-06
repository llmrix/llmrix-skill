"""
llmrix.skill — Git-backed Skill management library.

Package layout:
  core/      Cross-cutting concerns (config, exceptions, utils)
  models/    Domain models and data schemas
  git/       Low-level Git repository driver
  storage/   Abstract storage interface + concrete adapters
  services/  High-level orchestration (sync, publish, manage)
"""
# --- Core ---
from .core.config import SkillConfig
from .core.exceptions import (
    GitSkillError,
    SkillNotFoundError,
    VersionNotFoundError,
    PermissionDeniedError,
    ValidationError,
    GitOperationError,
)
from .core.utils import build_file_tree
from .core.plugin import BaseSkill

# --- Models ---
from .models.schema import Skill, SkillVersion
from .models.metadata import MetadataParser

# --- Git ---
from .git.repository import GitRepository

# --- Storage ---
from .storage.base import BaseStorage
from .storage.mysql import MySQLStorage
from .storage.sqlalchemy_store import SQLAlchemyStorage

# --- Services ---
from .services.manager import GitSkillManager
from .services.publisher import SkillPublisher
from .services.syncer import SkillSyncer, RemoteSource, SyncResult

__version__ = "0.2.0"

__all__ = [
    # Core
    "SkillConfig",
    "GitSkillError",
    "SkillNotFoundError",
    "VersionNotFoundError",
    "PermissionDeniedError",
    "ValidationError",
    "GitOperationError",
    "build_file_tree",
    "BaseSkill",
    # Models
    "Skill",
    "SkillVersion",
    "MetadataParser",
    # Git
    "GitRepository",
    # Storage
    "BaseStorage",
    "MySQLStorage",
    "SQLAlchemyStorage",
    # Services
    "GitSkillManager",
    "SkillPublisher",
    "SkillSyncer",
    "RemoteSource",
    "SyncResult",
]
