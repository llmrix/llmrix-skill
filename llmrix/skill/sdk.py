import os
import threading
from typing import Optional

from llmrix.skill.storage.base import BaseStorage

#: 默认缓存子目录名，外部可通过 init_sdk(cache_dir_name=...) 或子类覆盖
DEFAULT_CACHE_DIR_NAME = "cached"


class DefaultPathProvider:
    """
    SDK 默认路径提供器。

    目录布局（base_dir 即 skills-remote 根目录）::

        {base_dir}/
        ├── cached/          ← Git repo 只读缓存（可通过 cache_dir_name 自定义）
        └── update/
            └── {user_id}/   ← 每用户工作目录

    Parameters
    ----------
    base_dir:
        远程 skill 根目录，通常为 ``~/.llmrix/skills-remote``。
    cache_dir_name:
        缓存子目录名，默认 ``"cached"``。
        外部应用可在调用 ``init_sdk()`` 时传入自定义值以适配遗留目录布局。
    """

    def __init__(self, base_dir: str, cache_dir_name: str = DEFAULT_CACHE_DIR_NAME):
        self.base_dir = os.path.abspath(os.path.expanduser(base_dir))
        self.cache_dir_name = cache_dir_name

    def get_update_dir(self, user_id) -> str:
        return os.path.join(self.base_dir, "update", str(user_id))

    def get_cache_dir(self) -> str:
        return os.path.join(self.base_dir, self.cache_dir_name)


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


def init_sdk(base_dir: str, cache_dir_name: str = DEFAULT_CACHE_DIR_NAME) -> SkillSDK:
    """
    Initialize the SDK path provider. Call once at application startup.

    Parameters
    ----------
    base_dir:
        Root directory for remote skill storage (e.g. ``~/.llmrix/skills-remote``).
    cache_dir_name:
        Name of the cache subdirectory under *base_dir*. Defaults to ``"cached"``.
        Pass a custom value to match legacy directory layouts (e.g. ``"cache"``).
    """
    sdk = SkillSDK.get_instance()
    sdk.register_path_provider(DefaultPathProvider(base_dir, cache_dir_name=cache_dir_name))
    return sdk


def init_storage(engine) -> SkillSDK:
    """Create SQLAlchemyStorage from a SQLAlchemy engine and register it on the SDK singleton."""
    from llmrix.skill.storage.sqlalchemy_store import SQLAlchemyStorage
    sdk = SkillSDK.get_instance()
    sdk.register_storage(SQLAlchemyStorage(engine))
    return sdk


def get_sdk() -> SkillSDK:
    return SkillSDK.get_instance()
