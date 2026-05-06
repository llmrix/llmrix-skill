import os
import logging
from typing import Any, Dict, Optional, List
from .git import GitRepository
from .base import BaseStorage
from .metadata import MetadataParser
from .sync import SkillSyncer
from .publisher import SkillPublisher
from .schema import Skill, SkillVersion
from .exceptions import GitSkillError

logger = logging.getLogger(__name__)

class GitSkillManager:
    """
    Unified Facade for the llmrix.skill package.
    
    Provides a simple API for both:
    - Worker Mode: Syncing skills to local disk for execution.
    - Management Mode: Publishing/Rollbacking skills with version control.
    """

    def __init__(
        self, 
        repo_url: str, 
        workspace: Optional[str] = None, 
        branch: str = "main",
        storage: Optional[BaseStorage] = None
    ):
        # Default workspace for sync/remote caching
        if not workspace:
            workspace = os.path.expanduser("~/llmrix/skills/remote")
        
        self.repo_url = repo_url
        self.workspace = os.path.abspath(os.path.expanduser(workspace))
        self.branch = branch
        self.storage = storage
        
        # Internal components with clear responsibilities
        self.git = GitRepository(root=self.workspace)
        self.parser = MetadataParser()
        
        # Read responsibility: Use workspace parent as cache root
        self.syncer = SkillSyncer(cache_dir=os.path.dirname(self.workspace))
        
        # Write responsibility (lazy initialization if storage is provided)
        self._publisher = None
        if storage:
            self._publisher = SkillPublisher(git=self.git, storage=storage, parser=self.parser)

    @property
    def publisher(self) -> SkillPublisher:
        if not self._publisher:
            raise GitSkillError("Storage adapter is required for publishing operations.")
        return self._publisher

    def sync(self) -> str:
        """Worker Mode: Ensure local workspace is ready for use."""
        self.git.initialize(remote_url=self.repo_url, branch=self.branch)
        self.git.sync(branch=self.branch)
        return self.git.get_skill_path("")

    def publish(self, **kwargs) -> Skill:
        """Management Mode: Deploy a new version of a skill."""
        self.git.initialize(remote_url=self.repo_url, branch=self.branch)
        return self.publisher.publish(branch=self.branch, **kwargs)

    def rollback(self, **kwargs) -> Skill:
        """Management Mode: Revert a skill to a previous version."""
        self.git.initialize(remote_url=self.repo_url, branch=self.branch)
        return self.publisher.rollback(branch=self.branch, **kwargs)

    @staticmethod
    def get_interim_path(uid: Any) -> str:
        """Helper to resolve the interim upload directory for a specific user."""
        base = os.path.expanduser(f"~/llmrix/skills/interim/{uid}")
        return os.path.abspath(base)

    def get_history(self, code: str) -> List[SkillVersion]:
        """Retrieve version history from storage."""
        if not self.storage:
            raise GitSkillError("Storage adapter is required for history queries.")
        return self.storage.get_history(code)
