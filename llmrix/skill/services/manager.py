import os
import logging
from typing import Any, Optional, List
from llmrix.skill.git.repository import GitRepository
from llmrix.skill.storage.base import BaseStorage
from llmrix.skill.models.metadata import MetadataParser
from llmrix.skill.services.syncer import SkillSyncer
from llmrix.skill.services.publisher import SkillPublisher
from llmrix.skill.core.config import SkillConfig
from llmrix.skill.models.schema import Skill, SkillVersion
from llmrix.skill.core.exceptions import GitSkillError

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
        # 1. Decouple Configuration
        self.config = SkillConfig.create(repo_url, workspace, branch)
        self.storage = storage
        
        # 2. Initialize Internal Components
        self.repository = GitRepository(root=self.config.workspace, sub_dir=self.config.skills_path)
        self.parser = MetadataParser()
        
        # 3. Read Responsibility (Syncing)
        self.syncer = SkillSyncer(cache_dir=self.config.cache_root)
        
        # 4. Write Responsibility (Publishing - Lazy)
        self._publisher = None
        if storage:
            self._publisher = SkillPublisher(
                git=self.repository, 
                storage=storage, 
                parser=self.parser,
                default_branch=self.config.branch
            )

    @property
    def publisher(self) -> SkillPublisher:
        if not self._publisher:
            raise GitSkillError("Storage adapter is required for publishing operations.")
        return self._publisher

    def sync(self) -> str:
        """
        Worker Mode API: Synchronizes the local repository.
        Uses the pre-configured branch and workspace.
        """
        self.repository.ensure_initialized(
            remote_url=self.config.repo_url, 
            branch=self.config.branch
        )
        self.repository.fetch_latest(branch=self.config.branch)
        return self.repository.get_skill_path("")

    def publish(self, **kwargs) -> Skill:
        """
        Management Mode API: Deploys a new version.
        Arguments like 'branch' are optional as the manager uses defaults.
        """
        self.repository.ensure_initialized(
            remote_url=self.config.repo_url, 
            branch=self.config.branch
        )
        return self.publisher.publish(**kwargs)

    def rollback(self, **kwargs) -> Skill:
        """Management Mode API: Reverts to a previous version."""
        self.repository.ensure_initialized(
            remote_url=self.config.repo_url, 
            branch=self.config.branch
        )
        return self.publisher.rollback(**kwargs)

    def get_history(self, code: str) -> List[SkillVersion]:
        """Retrieves release history from the connected database."""
        if not self.storage:
            raise GitSkillError("Storage adapter is required for history queries.")
        return self.storage.get_history(code)

    @staticmethod
    def get_interim_path(uid: Any) -> str:
        """Static utility to resolve a standardized interim upload path for users."""
        base = os.path.expanduser(f"~/llmrix/skills/interim/{uid}")
        return os.path.abspath(base)
