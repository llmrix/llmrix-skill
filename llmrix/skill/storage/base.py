from abc import ABC, abstractmethod
from typing import Any, List, Optional
from llmrix.skill.models.schema import Skill, SkillVersion

class BaseStorage(ABC):
    """
    Abstract base class for skill persistence.
    Implement this to support different databases.
    """

    @abstractmethod
    def get_skill(self, code: str) -> Optional[Skill]:
        """Retrieve skill by its unique code."""
        pass

    @abstractmethod
    def save_skill(self, skill: Skill) -> None:
        """Create or update skill metadata."""
        pass

    @abstractmethod
    def add_version(self, version: SkillVersion) -> None:
        """Record a new version in history."""
        pass

    @abstractmethod
    def get_history(self, code: str) -> List[SkillVersion]:
        """List all versions of a skill ordered by version descending."""
        pass

    @abstractmethod
    def get_version(self, code: str, version_number: int) -> Optional[SkillVersion]:
        """Retrieve a specific version record."""
        pass

    @abstractmethod
    def can_modify(self, code: str, user_id: Any) -> bool:
        """Check if the user has permission to modify the skill."""
        pass
