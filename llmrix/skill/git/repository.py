import logging
import os
import shutil
import subprocess
from contextlib import contextmanager
from typing import Any, Generator, List, Optional
from llmrix.skill.core.exceptions import GitOperationError

logger = logging.getLogger(__name__)

class GitRepository:
    """
    Handles low-level Git operations for skills.
    Focuses on repository maintenance, state transitions, and file management.
    """
    
    def __init__(self, root: str, sub_dir: str = "skills"):
        self.root = os.path.abspath(root)
        self.sub_dir = sub_dir
        self._lock_dir = os.path.join(self.root, ".locks")

    def get_skill_path(self, code: str) -> str:
        """Returns absolute path to a skill directory."""
        return os.path.join(self.root, self.sub_dir, code)

    def get_relative_path(self, code: str) -> str:
        """Returns relative path to a skill from repo root."""
        return f"{self.sub_dir}/{code}"

    @contextmanager
    def lock(self, code: str, timeout: int = 30) -> Generator[None, None, None]:
        """Provides a distributed file lock for a specific skill code."""
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
        """Executes a git command and returns the output."""
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

    def ensure_initialized(self, remote_url: Optional[str] = None, branch: str = "main"):
        """Ensures the repository is initialized and tracking the correct branch."""
        if not os.path.isdir(os.path.join(self.root, ".git")):
            if remote_url:
                logger.info(f"Cloning skill repository from {remote_url} (branch: {branch})")
                os.makedirs(os.path.dirname(self.root), exist_ok=True)
                subprocess.run(["git", "clone", "--branch", branch, remote_url, self.root], check=True)
            else:
                logger.info(f"Initializing local skill repository (branch: {branch})")
                os.makedirs(self.root, exist_ok=True)
                self._execute(["init", "-b", branch])
        
        # Ensure skills directory exists
        os.makedirs(os.path.join(self.root, self.sub_dir), exist_ok=True)

    def fetch_latest(self, remote: str = "origin", branch: str = "main"):
        """Pulls the latest changes from the remote repository."""
        try:
            self._execute(["pull", remote, branch])
        except GitOperationError as e:
            logger.warning(f"Git pull failed, falling back to local state: {e}")

    def push_changes(self, remote: str = "origin", branch: str = "main"):
        """Pushes local commits to the remote repository."""
        try:
            self._execute(["push", remote, branch])
        except GitOperationError as e:
            logger.warning(f"Git push failed: {e}")

    def commit_skill(self, code: str, author_id: Any, message: Optional[str] = None) -> str:
        """Adds and commits changes for a specific skill."""
        rel_path = self.get_relative_path(code)
        self._execute(["add", rel_path])
        
        # Check for staged changes
        diff = self._execute(["diff", "--cached", "--name-only"])
        if not diff:
            return self._execute(["rev-parse", "HEAD"])
            
        msg = message or f"Update skill: {code} by user: {author_id}"
        self._execute(["commit", "-m", msg])
        return self._execute(["rev-parse", "HEAD"])

    def revert_to_commit(self, code: str, commit_hash: str, author_id: Any, message: Optional[str] = None) -> str:
        """Checkouts a specific commit for a skill and commits the reversal."""
        rel_path = self.get_relative_path(code)
        self._execute(["checkout", commit_hash, "--", rel_path])
        self._execute(["add", rel_path])
        
        msg = message or f"Revert skill: {code} to {commit_hash} by user: {author_id}"
        self._execute(["commit", "-m", msg])
        return self._execute(["rev-parse", "HEAD"])

    def remove_skill(self, code: str, author_id: Any, message: Optional[str] = None) -> Optional[str]:
        """Removes a skill directory from the repo, commits and pushes the deletion."""
        skill_path = self.get_skill_path(code)
        rel_path = self.get_relative_path(code)

        if not os.path.exists(skill_path):
            logger.warning(f"Skill path not found, skipping git removal: {skill_path}")
            return None

        shutil.rmtree(skill_path)
        self._execute(["rm", "-r", "--cached", "--ignore-unmatch", rel_path])
        self._execute(["add", "-A", rel_path])

        diff = self._execute(["diff", "--cached", "--name-only"])
        if not diff:
            logger.info(f"No staged changes after removing skill {code}, skipping commit")
            return None

        msg = message or f"Delete skill: {code} by user: {author_id}"
        self._execute(["commit", "-m", msg])
        return self._execute(["rev-parse", "HEAD"])
