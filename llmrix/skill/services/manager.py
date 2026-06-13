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
    Converged Orchestrator for SkillHub.

    Acts as a high-level facade that decouples configuration from method calls,
    providing a clean interface for both Agent Workers and Management APIs.
    """

    def __init__(
        self,
        repo_url: str,
        workspace: Optional[str] = None,
        branch: str = "main",
        storage: Optional[BaseStorage] = None
    ):
        sdk = get_sdk()
        # 1. Fallback to provided storage or SDK storage
        self.storage = storage or sdk.storage

        # 2. Initialize Internal Components
        self.config = SkillConfig.create(repo_url, workspace, branch)
        self.repo = GitRepository(root=self.config.workspace, skills_subdir=self.config.skills_subdir)
        self.parser = MetadataParser()

        # 3. Read Responsibility (Syncing)
        cache_dir = sdk.path_provider.get_cache_dir() if sdk.path_provider else self.config.cache_root
        self.syncer = SkillSyncer(cache_dir=cache_dir)

        # 4. Write Responsibility (Publishing — lazy)
        self._publisher: Optional[SkillPublisher] = None
        if self.storage:
            self._publisher = SkillPublisher(
                git=self.repo,
                storage=self.storage,
                parser=self.parser,
                default_branch=self.config.branch
            )

    @property
    def publisher(self) -> SkillPublisher:
        if not self._publisher:
            raise GitSkillError("Storage adapter is required for publishing operations.")
        return self._publisher

    def _ensure_repo(self):
        """Ensures the repository is initialized before write operations."""
        self.repo.ensure_initialized(
            remote_url=self.config.repo_url,
            branch=self.config.branch,
        )

    def sync(self) -> str:
        """
        Worker Mode API: Synchronizes the local repository.
        Uses the pre-configured branch and workspace.
        """
        self._ensure_repo()
        self.repo.fetch_latest(branch=self.config.branch)
        return self.repo.skill_dir("")

    def publish(self, **kwargs) -> Skill:
        """
        Management Mode API: Deploys a new version.
        Arguments like 'branch' are optional as the manager uses defaults.
        """
        self._ensure_repo()
        return self.publisher.publish(**kwargs)

    def publish_zip(self, **kwargs) -> Skill:
        """
        Management Mode API: Deploys a new version from a zip file.
        Ensures the repository is initialized before publishing.
        """
        self._ensure_repo()
        return self.publisher.publish_zip(**kwargs)

    def rollback(self, **kwargs) -> Skill:
        """Management Mode API: Reverts to a previous version."""
        self._ensure_repo()
        return self.publisher.rollback(**kwargs)

    def get_history(self, code: str) -> List[SkillVersion]:
        """Retrieves release history from the connected database."""
        if not self.storage:
            raise GitSkillError("Storage adapter is required for history queries.")
        return self.storage.get_history(code)

    def get_interim_path(self, uid: Any) -> str:
        """Resolves the standardized interim upload path for a user via SDK path_provider."""
        sdk = get_sdk()
        if sdk.path_provider:
            return sdk.path_provider.get_update_dir(uid)
        from src.harness.config.path import AppPaths
        return str(AppPaths.SKILLS_UPDATE / str(uid))
