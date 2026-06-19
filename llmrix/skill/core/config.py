import os
from dataclasses import dataclass, field
from typing import Optional

_DEFAULT_SKILLS_SUBDIR = "skills"


@dataclass
class SkillConfig:
    """Configuration for the Skill management system."""
    repo_url:      str
    workspace:     str
    branch:        str = "main"
    skills_subdir: str = _DEFAULT_SKILLS_SUBDIR
    # 缓存子目录名，与 DefaultPathProvider.cache_dir_name 保持一致
    cache_dir_name: str = field(default="cached")

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

        # 从已注册的 path_provider 读取 cache_dir_name，保持一致
        cache_dir_name = "cached"
        try:
            from llmrix.skill.sdk import get_sdk as _get_sdk
            pp = _get_sdk().path_provider
            if pp and hasattr(pp, "cache_dir_name"):
                cache_dir_name = pp.cache_dir_name
        except Exception:
            pass

        return cls(
            repo_url=repo_url,
            workspace=os.path.abspath(os.path.expanduser(workspace)),
            branch=branch,
            cache_dir_name=cache_dir_name,
        )

    @property
    def cache_root(self) -> str:
        """Cache directory — sibling of update/ under the remote root."""
        return os.path.join(os.path.dirname(self.workspace), self.cache_dir_name)

    @property
    def skills_dir(self) -> str:
        """Absolute path to the skills subdirectory inside the workspace."""
        return os.path.join(self.workspace, self.skills_subdir)
