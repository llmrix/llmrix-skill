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
        branch: str = "main",
    ) -> "SkillConfig":
        """
        Build a SkillConfig.  When workspace is omitted the SDK path_provider
        is used (requires init_sdk() to have been called first).
        """
        if not workspace:
            from llmrix.skill.sdk import get_sdk
            sdk = get_sdk()
            if sdk.path_provider:
                workspace = os.path.join(sdk.path_provider.base_dir, "update")
            else:
                raise RuntimeError(
                    "SkillConfig.create() requires either an explicit workspace "
                    "or an initialised SDK (call init_sdk() first)."
                )

        return cls(
            repo_url=repo_url,
            workspace=os.path.abspath(os.path.expanduser(workspace)),
            branch=branch,
        )

    @property
    def cache_root(self) -> str:
        """Cache directory — sibling of update/ under the remote root."""
        return os.path.join(os.path.dirname(self.workspace), "cache")

    @property
    def skills_dir(self) -> str:
        """Absolute path to the skills subdirectory inside the workspace."""
        return os.path.join(self.workspace, self.skills_subdir)
