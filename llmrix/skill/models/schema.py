from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

DEFAULT_CATEGORY = "Other"

@dataclass
class Skill:
    """Represents the current state of a skill."""
    code: str
    name: str
    version: int = 1
    description: Optional[str] = None
    category: str = DEFAULT_CATEGORY
    git_commit: Optional[str] = None
    git_path: Optional[str] = None
    status: str = "inactive"
    user_id: int = 0

@dataclass
class SkillVersion:
    """Represents a specific point-in-time version of a skill."""
    code: str
    version: int
    git_commit: str
    user_id: int
    git_path: Optional[str] = None
    message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
