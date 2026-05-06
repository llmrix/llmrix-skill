import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class SkillConfig:
    """Configuration for the Skill management system."""
    repo_url: str
    workspace: str
    branch: str = "main"
    skills_path: str = "skills"
    cache_ttl: int = 300

    @classmethod
    def create(
        cls, 
        repo_url: str, 
        workspace: Optional[str] = None, 
        branch: str = "main"
    ) -> "SkillConfig":
        if not workspace:
            workspace = os.path.expanduser("~/llmrix/skills/remote")
        
        return cls(
            repo_url=repo_url,
            workspace=os.path.abspath(os.path.expanduser(workspace)),
            branch=branch
        )

    @property
    def cache_root(self) -> str:
        return os.path.dirname(self.workspace)

    @property
    def skills_root(self) -> str:
        return os.path.join(self.workspace, self.skills_path)
