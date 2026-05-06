import asyncio
import hashlib
import logging
import os
import shutil
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from llmrix.skill.git.repository import GitRepository

logger = logging.getLogger(__name__)

@dataclass
class RemoteSource:
    """Configuration for a remote skill repository source."""
    url: str
    branch: str = "main"
    ssh_key: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    cache_ttl: int = 300  # seconds
    skills_path: str = "skills"

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

    def _get_cache_path(self, source: RemoteSource) -> Path:
        """Generates a unique directory name for the repository hash."""
        url_hash = hashlib.md5(source.identity.encode()).hexdigest()[:12]
        return self.cache_dir / f"repo_{url_hash}"

    def _build_authed_url(self, source: RemoteSource) -> str:
        url = source.url
        if source.username and source.password and url.startswith("https://"):
            encoded_user = urllib.parse.quote(source.username, safe="")
            encoded_pass = urllib.parse.quote(source.password, safe="")
            url = url.replace("https://", f"https://{encoded_user}:{encoded_pass}@")
        return url

    async def sync_source(self, source: RemoteSource) -> SyncResult:
        """
        Synchronizes a single remote source. 
        Returns the path to the skills directory within the repo.
        """
        identity = source.identity
        lock = self._get_lock(identity)
        
        async with lock:
            repo_path = self._get_cache_path(source)
            repo = GitRepository(root=str(repo_path), sub_dir=source.skills_path)
            
            # Check TTL
            last_sync = self._sync_history.get(identity)
            if last_sync and (datetime.now() - last_sync).total_seconds() < source.cache_ttl:
                if repo_path.exists():
                    return SyncResult(source, Path(repo.get_skill_path("")), True, last_sync)

            try:
                authed_url = self._build_authed_url(source)
                
                # We use a thread pool for blocking git operations since they are subprocess calls
                loop = asyncio.get_event_loop()
                
                if not repo_path.exists():
                    logger.info(f"Cloning remote skill source: {source.url}")
                    await loop.run_in_executor(None, repo.initialize, authed_url, source.branch)
                else:
                    logger.debug(f"Syncing remote skill source: {source.url}")
                    await loop.run_in_executor(None, repo.sync, "origin", source.branch)

                self._sync_history[identity] = datetime.now()
                return SyncResult(source, Path(repo.get_skill_path("")), True, self._sync_history[identity])

            except Exception as e:
                logger.error(f"Failed to sync {source.url}: {e}")
                if repo_path.exists():
                    logger.warning(f"Falling back to stale cache for {source.url}")
                    return SyncResult(source, Path(repo.get_skill_path("")), True, last_sync or datetime.min, str(e))
                return SyncResult(source, repo_path, False, datetime.min, str(e))

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
