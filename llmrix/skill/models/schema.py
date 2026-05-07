from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

@dataclass
class Skill:
    """Represents the current state of a skill."""
    code: str
    name: str
    version: int = 1
    introduce: Optional[str] = None
    category: str = "Other"
    commit_hash: Optional[str] = None
    file_path: Optional[str] = None
    status: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SkillVersion:
    """Represents a specific point-in-time version of a skill."""
    code: str
    version: int
    commit_hash: str
    user_id: Any
    file_path: Optional[str] = None
    message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
