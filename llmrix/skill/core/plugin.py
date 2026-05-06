from abc import ABC, abstractmethod
from typing import Any, Dict

class BaseSkill(ABC):
    """
    Standard interface contract for LLMRix skills.
    
    Plugin developers should inherit from this class in their `main.py` 
    to ensure seamless integration with the host Agent framework.
    """
    
    @property
    def name(self) -> str:
        """The identifier name of the skill."""
        return self.__class__.__name__

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Any:
        """
        The main execution entry point for the skill.
        All core business logic and external API calls should be implemented here.
        """
        pass
        
    def setup(self, context: Dict[str, Any]) -> None:
        """
        Optional initialization hook.
        The Agent framework can pass configuration, credentials, or runtime context 
        here before the skill is executed.
        """
        pass
