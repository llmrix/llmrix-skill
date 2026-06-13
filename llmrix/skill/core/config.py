import os
from dataclasses import dataclass
from typing import Optional

_DEFAULT_SKILLS_SUBDIR = "skills"

@dataclass
class SkillConfig:
    """Configuration for the Skill management system."""
    repo_url: str
    workspace: str
    branch: str = "main"
    skills_subdir: str = _DEFAULT_SKILLS_SUBDIR

    @classmethod
    def create(
        cls,
        repo_url: str,
        workspace: Optional[str] = None,
        branch: str = "main"
    ) -> "SkillConfig":
        if not workspace:
            from src.harness.config.path import AppPaths
            workspace = str(AppPaths.SKILLS_UPDATE)

        return cls(
            repo_url=repo_url,
            workspace=os.path.abspath(os.path.expanduser(workspace)),
            branch=branch
        )

    @property
    def cache_root(self) -> str:
        """Returns the cache directory (sibling of update/ under SKILLS_REMOTE)."""
        remote_root = os.path.dirname(self.workspace)
        return os.path.join(remote_root, "cache")

    @property
    def skills_dir(self) -> str:
        """Absolute path to the skills subdirectory inside the workspace."""
        return os.path.join(self.workspace, self.skills_subdir)
