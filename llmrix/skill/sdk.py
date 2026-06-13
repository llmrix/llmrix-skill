import os
import threading
from typing import Optional

from llmrix.skill.storage.base import BaseStorage


class DefaultPathProvider:
    def __init__(self, base_dir: str):
        self.base_dir = os.path.abspath(os.path.expanduser(base_dir))

    def get_update_dir(self, user_id) -> str:
        return os.path.join(self.base_dir, "update", str(user_id))

    def get_cache_dir(self) -> str:
        return os.path.join(self.base_dir, "cache")


class SkillSDK:
    _instance: Optional["SkillSDK"] = None
    _lock: threading.Lock = threading.Lock()

    def __init__(self):
        self.storage: Optional[BaseStorage] = None
        self.path_provider: Optional[DefaultPathProvider] = None

    @classmethod
    def get_instance(cls) -> "SkillSDK":
        if not cls._instance:
            with cls._lock:
                if not cls._instance:
                    cls._instance = cls()
        return cls._instance

    def register_storage(self, storage: BaseStorage) -> None:
        self.storage = storage

    def register_path_provider(self, provider: DefaultPathProvider) -> None:
        self.path_provider = provider


def init_sdk(base_dir: str) -> SkillSDK:
    """Initialize path provider from base_dir. Call once at application startup."""
    sdk = SkillSDK.get_instance()
    sdk.register_path_provider(DefaultPathProvider(base_dir))
    return sdk


def init_storage(engine) -> SkillSDK:
    """Create SQLAlchemyStorage from a SQLAlchemy engine and register it on the SDK singleton."""
    from llmrix.skill.storage.sqlalchemy_store import SQLAlchemyStorage
    sdk = SkillSDK.get_instance()
    sdk.register_storage(SQLAlchemyStorage(engine))
    return sdk


def get_sdk() -> SkillSDK:
    return SkillSDK.get_instance()
