import logging
from typing import Any, List, Optional

from llmrix.skill.git.repository import GitRepository
from llmrix.skill.storage.base import BaseStorage
from llmrix.skill.models.metadata import MetadataParser
from llmrix.skill.services.syncer import SkillSyncer
from llmrix.skill.services.publisher import SkillPublisher
from llmrix.skill.core.config import SkillConfig
from llmrix.skill.models.schema import Skill, SkillVersion
from llmrix.skill.core.exceptions import GitSkillError
from llmrix.skill.sdk import get_sdk

logger = logging.getLogger(__name__)


class GitSkillManager:
    """
    High-level facade for Git-backed skill management.

    Supports two modes:
      - Worker mode  : sync() — pull latest changes from remote
      - Management mode : publish_zip() / rollback() — write and push
    """

    def __init__(
        self,
        repo_url: str,
        workspace: Optional[str] = None,
        branch: str = "main",
        storage: Optional[BaseStorage] = None,
    ):
        sdk = get_sdk()
        self.storage = storage or sdk.storage

        self.config = SkillConfig.create(repo_url, workspace, branch)
        self.repo = GitRepository(root=self.config.workspace, skills_subdir=self.config.skills_subdir)
        self.parser = MetadataParser()

        cache_dir = sdk.path_provider.get_cache_dir() if sdk.path_provider else self.config.cache_root
        self.syncer = SkillSyncer(cache_dir=cache_dir)

        self._publisher: Optional[SkillPublisher] = (
            SkillPublisher(
                git=self.repo,
                storage=self.storage,
                parser=self.parser,
                default_branch=self.config.branch,
            )
            if self.storage else None
        )

    @property
    def publisher(self) -> SkillPublisher:
        if not self._publisher:
            raise GitSkillError("Storage adapter is required for publishing operations.")
        return self._publisher

    def _ensure_repo(self) -> None:
        """Clone or verify the local repository before any write operation."""
        self.repo.ensure_initialized(
            remote_url=self.config.repo_url,
            branch=self.config.branch,
        )

    # ── Worker mode ───────────────────────────────────────────────────────────

    def sync(self) -> str:
        """Pull latest changes; returns path to the skills directory."""
        self._ensure_repo()
        self.repo.fetch_latest(branch=self.config.branch)
        return self.repo.skill_dir("")

    # ── Management mode ───────────────────────────────────────────────────────

    def publish(self, **kwargs) -> Skill:
        self._ensure_repo()
        return self.publisher.publish(**kwargs)

    def publish_zip(self, **kwargs) -> Skill:
        self._ensure_repo()
        return self.publisher.publish_zip(**kwargs)

    def rollback(self, **kwargs) -> Skill:
        self._ensure_repo()
        return self.publisher.rollback(**kwargs)

    # ── Queries ───────────────────────────────────────────────────────────────

    def get_history(self, code: str) -> List[SkillVersion]:
        if not self.storage:
            raise GitSkillError("Storage adapter is required for history queries.")
        return self.storage.get_history(code)

    def get_interim_path(self, uid: Any) -> str:
        """Return the per-user interim upload directory."""
        sdk = get_sdk()
        if sdk.path_provider:
            return sdk.path_provider.get_update_dir(uid)
        raise GitSkillError("SDK path_provider not initialised — call init_sdk() first.")
