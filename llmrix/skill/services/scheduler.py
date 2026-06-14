"""
scheduler.py — Periodic background sync for remote skill sources.

Usage::

    from src.libs.skill import SkillScheduler, RemoteSource
    from src.harness.config.path import AppPaths

    scheduler = SkillScheduler(
        cache_dir=str(AppPaths.SKILLS_CACHE),
        sources=[
            RemoteSource(url="https://github.com/org/skills.git", branch="main", cache_ttl=300),
        ],
        interval=300,  # seconds between sync cycles
    )

    # In an async context:
    await scheduler.start()   # starts background task
    await scheduler.stop()    # graceful shutdown

    # Retrieve synced paths at any time:
    paths = scheduler.skill_paths   # list[str], ready to pass to SkillsMiddleware
"""
from __future__ import annotations

import asyncio
import logging
from typing import List, Optional

from llmrix.skill.services.syncer import RemoteSource, SkillSyncer, SyncResult

logger = logging.getLogger(__name__)


class SkillScheduler:
    """
    Runs ``SkillSyncer.sync_all`` on a fixed interval in the background.

    Parameters
    ----------
    cache_dir:
        Local directory for cached repositories.
        Recommended: ``~/.src.libs.skill.skills-remote/cache``
    sources:
        List of ``RemoteSource`` configs to sync.
    interval:
        Seconds between sync cycles (default 300).
        Individual sources can override TTL via ``RemoteSource.cache_ttl``.
    """

    def __init__(
        self,
        cache_dir: str,
        sources: List[RemoteSource],
        interval: int = 300,
    ) -> None:
        self.syncer = SkillSyncer(cache_dir=cache_dir)
        self.sources = sources
        self.interval = interval

        self._task: Optional[asyncio.Task] = None
        self._results: List[SyncResult] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def start(self) -> None:
        """Start the background sync loop. Safe to call multiple times."""
        if self._task and not self._task.done():
            return
        # Run an immediate sync before the first interval fires
        await self._run_sync()
        self._task = asyncio.create_task(self._loop(), name="skill-scheduler")
        logger.info("SkillScheduler started (interval=%ds, sources=%d)", self.interval, len(self.sources))

    async def stop(self) -> None:
        """Cancel the background task and wait for it to finish."""
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("SkillScheduler stopped")

    @property
    def skill_paths(self) -> List[str]:
        """
        Returns the list of local skill directory paths from the last
        successful sync. Safe to call at any time (returns [] before first sync).
        """
        return [
            str(r.local_path)
            for r in self._results
            if r.success
        ]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    async def _loop(self) -> None:
        while True:
            await asyncio.sleep(self.interval)
            await self._run_sync()

    async def _run_sync(self) -> None:
        try:
            self._results = await self.syncer.sync_all(self.sources)
            ok = sum(1 for r in self._results if r.success)
            fail = len(self._results) - ok
            if fail:
                logger.warning("SkillScheduler sync: %d ok, %d failed", ok, fail)
            else:
                logger.debug("SkillScheduler sync: %d sources ok", ok)
        except Exception as exc:
            logger.error("SkillScheduler sync error: %s", exc)
