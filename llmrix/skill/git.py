import logging
import os
import subprocess
from contextlib import contextmanager
from typing import Any, Generator, List, Optional
from .exceptions import GitOperationError

logger = logging.getLogger(__name__)

class GitRepository:
    """Handles low-level Git operations for skills."""
    
    def __init__(self, root: str, sub_dir: str = "skills"):
        self.root = os.path.abspath(root)
        self.sub_dir = sub_dir
        self._lock_dir = os.path.join(self.root, ".locks")

    def get_skill_path(self, code: str) -> str:
        return os.path.join(self.root, self.sub_dir, code)

    def get_relative_path(self, code: str) -> str:
        return f"{self.sub_dir}/{code}"

    @contextmanager
    def lock(self, code: str, timeout: int = 30) -> Generator[None, None, None]:
        try:
            from filelock import FileLock
            os.makedirs(self._lock_dir, exist_ok=True)
            lock = FileLock(os.path.join(self._lock_dir, f"{code}.lock"), timeout=timeout)
            with lock:
                yield
        except ImportError:
            logger.warning("filelock not installed, running without concurrency protection")
            yield

    def _execute(self, command: List[str]) -> str:
        try:
            result = subprocess.run(
                ["git"] + command,
                cwd=self.root,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            error_msg = (e.stdout + "\\n" + e.stderr).strip()
            raise GitOperationError(f"Git command {' '.join(command)} failed: {error_msg}") from e

    def initialize(self, remote_url: Optional[str] = None, branch: str = "main"):
        if not os.path.isdir(os.path.join(self.root, ".git")):
            if remote_url:
                os.makedirs(os.path.dirname(self.root), exist_ok=True)
                subprocess.run(["git", "clone", "--branch", branch, remote_url, self.root], check=True)
            else:
                os.makedirs(self.root, exist_ok=True)
                self._execute(["init", "-b", branch])
        os.makedirs(os.path.join(self.root, self.sub_dir), exist_ok=True)

    def sync(self, remote: str = "origin", branch: str = "main"):
        try:
            self._execute(["pull", remote, branch])
        except GitOperationError as e:
            logger.warning(f"Sync failed, continuing locally: {e}")

    def publish(self, remote: str = "origin", branch: str = "main"):
        try:
            self._execute(["push", remote, branch])
        except GitOperationError as e:
            logger.warning(f"Push failed: {e}")

    def commit(self, code: str, author_id: Any, message: Optional[str] = None) -> str:
        rel_path = self.get_relative_path(code)
        self._execute(["add", rel_path])
        
        # Check for staged changes
        diff = self._execute(["diff", "--cached", "--name-only"])
        if not diff:
            return self._execute(["rev-parse", "HEAD"])
            
        msg = message or f"Update skill: {code} by user: {author_id}"
        self._execute(["commit", "-m", msg])
        return self._execute(["rev-parse", "HEAD"])

    def revert(self, code: str, commit_hash: str, author_id: Any, message: Optional[str] = None) -> str:
        rel_path = self.get_relative_path(code)
        self._execute(["checkout", commit_hash, "--", rel_path])
        self._execute(["add", rel_path])
        
        msg = message or f"Revert skill: {code} to {commit_hash} by user: {author_id}"
        self._execute(["commit", "-m", msg])
        return self._execute(["rev-parse", "HEAD"])
