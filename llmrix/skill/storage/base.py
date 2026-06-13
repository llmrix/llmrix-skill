from abc import ABC, abstractmethod
from typing import Any, List, Literal, Optional

from llmrix.skill.models.schema import Skill, SkillVersion

# Ownership check result: "free" | "own" | "conflict"
OwnershipStatus = Literal["free", "own", "conflict"]


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

    @abstractmethod
    def delete_skill(self, code: str) -> None:
        """Soft-delete a skill and all its versions."""
        pass

    def check_ownership(self, code: str, user_id: Any) -> OwnershipStatus:
        """
        Three-way ownership check:
        - "free"     → skill does not exist, can be created
        - "own"      → skill exists and belongs to user_id, can be updated
        - "conflict" → skill exists and belongs to another user or system (user_id=0)
        Default implementation built on get_skill + can_modify.
        Override for more efficient single-query implementations.
        """
        skill = self.get_skill(code)
        if skill is None:
            return "free"
        if self.can_modify(code, user_id):
            return "own"
        return "conflict"
