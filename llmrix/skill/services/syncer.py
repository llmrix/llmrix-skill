import asyncio
import hashlib
import logging
import os
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from llmrix.skill.git.repository import GitRepository
from llmrix.skill.core.utils import build_authed_url

logger = logging.getLogger(__name__)


@dataclass
class RemoteSource:
    """Configuration for a remote skill repository source."""
    url: str
    branch: str = "main"
    ssh_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    token: Optional[str] = None
    cache_ttl: int = 300  # seconds
    skills_subdir: str = "skills"

    @property
    def identity(self) -> str:
        """Unique identifier based on URL and branch."""
        return f"{self.url}:{self.branch}"


@dataclass
class SyncResult:
    """Result of a repository sync operation."""
    source: RemoteSource
    local_path: Path
    success: bool
    last_sync: datetime
    cached: bool = False
    error: Optional[str] = None


class SkillSyncer:
    """
    Manages synchronization of multiple remote skill repositories.
    Supports local caching with TTL and authentication.
    """

    def __init__(self, cache_dir: str):
        self.cache_dir = Path(cache_dir).absolute()
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._locks: Dict[str, asyncio.Lock] = {}
        self._sync_history: Dict[str, datetime] = {}

    def _get_lock(self, identity: str) -> asyncio.Lock:
        if identity not in self._locks:
            self._locks[identity] = asyncio.Lock()
        return self._locks[identity]

    def _cache_path(self, source: RemoteSource) -> Path:
        """Generates a unique directory name for the repository hash."""
        url_hash = hashlib.md5(source.identity.encode()).hexdigest()[:12]
        return self.cache_dir / f"repo_{url_hash}"

    async def sync_source(self, source: RemoteSource) -> SyncResult:
        """
        Synchronizes a single remote source.
        Returns the path to the skills directory within the repo.
        """
        identity = source.identity
        lock = self._get_lock(identity)

        async with lock:
            repo_path = self._cache_path(source)
            repo = GitRepository(root=str(repo_path), skills_subdir=source.skills_subdir)

            # Check TTL
            last_sync = self._sync_history.get(identity)
            if last_sync and (datetime.now() - last_sync).total_seconds() < source.cache_ttl:
                if repo_path.exists():
                    return SyncResult(source, Path(repo.skill_dir("")), True, last_sync)

            try:
                authed_url = build_authed_url(
                    source.url,
                    token=source.token,
                    username=source.username,
                    password=source.password,
                )

                if not repo_path.exists():
                    logger.info("Cloning remote skill source: %s", source.url)
                    await asyncio.to_thread(repo.ensure_initialized, authed_url, source.branch)
                else:
                    logger.debug("Syncing remote skill source: %s", source.url)
                    await asyncio.to_thread(repo.fetch_latest, "origin", source.branch)

                self._sync_history[identity] = datetime.now()
                return SyncResult(
                    source, Path(repo.skill_dir("")), True, self._sync_history[identity]
                )

            except Exception as e:
                logger.error("Failed to sync %s: %s", source.url, e)
                if repo_path.exists():
                    logger.warning("Falling back to stale cache for %s", source.url)
                    return SyncResult(
                        source, Path(repo.skill_dir("")),
                        success=False, cached=True,
                        last_sync=last_sync or datetime.min,
                        error=str(e),
                    )
                return SyncResult(source, repo_path, success=False, last_sync=datetime.min, error=str(e))

    async def sync_all(self, sources: List[RemoteSource]) -> List[SyncResult]:
        """Synchronizes multiple sources in parallel."""
        tasks = [self.sync_source(s) for s in sources]
        return await asyncio.gather(*tasks)

    def clear_cache(self):
        """Deletes all cached repositories."""
        if self.cache_dir.exists():
            shutil.rmtree(self.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._sync_history.clear()
