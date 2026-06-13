"""
llmrix.skill — Git-backed Skill management library.

Package layout:
  core/      Cross-cutting concerns (config, exceptions, utils)
  models/    Domain models and data schemas
  git/       Low-level Git repository driver
  storage/   Abstract storage interface + concrete adapters
  services/  High-level orchestration (sync, publish, manage)
"""
# --- SDK ---
from llmrix.skill.sdk import init_sdk, init_storage, get_sdk, SkillSDK

# --- Core ---
from llmrix.skill.core.config import SkillConfig
from llmrix.skill.core.exceptions import (
    GitSkillError,
    SkillNotFoundError,
    VersionNotFoundError,
    PermissionDeniedError,
    ValidationError,
    GitOperationError,
)
from llmrix.skill.core.utils import build_file_tree, build_authed_url
from llmrix.skill.core.plugin import BaseSkill

# --- Models ---
from llmrix.skill.models.schema import Skill, SkillVersion
from llmrix.skill.models.metadata import MetadataParser

# --- Git ---
from llmrix.skill.git.repository import GitRepository

# --- Storage ---
from llmrix.skill.storage.base import BaseStorage, OwnershipStatus
from llmrix.skill.storage.sqlalchemy_store import SQLAlchemyStorage

# --- Services ---
from llmrix.skill.services.manager import GitSkillManager
from llmrix.skill.services.publisher import SkillPublisher
from llmrix.skill.services.syncer import SkillSyncer, RemoteSource, SyncResult
from llmrix.skill.services.scheduler import SkillScheduler

__version__ = "0.3.0"

__all__ = [
    # SDK
    "init_sdk",
    "init_storage",
    "get_sdk",
    "SkillSDK",
    # Core
    "SkillConfig",
    "GitSkillError",
    "SkillNotFoundError",
    "VersionNotFoundError",
    "PermissionDeniedError",
    "ValidationError",
    "GitOperationError",
    "build_file_tree",
    "build_authed_url",
    "BaseSkill",
    # Models
    "Skill",
    "SkillVersion",
    "MetadataParser",
    # Git
    "GitRepository",
    # Storage
    "BaseStorage",
    "OwnershipStatus",
    "SQLAlchemyStorage",
    # Services
    "GitSkillManager",
    "SkillPublisher",
    "SkillSyncer",
    "RemoteSource",
    "SyncResult",
    "SkillScheduler",
]
