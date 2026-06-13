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

    def __init__(self, root: str, skills_subdir: str = "skills"):
        self.root = os.path.abspath(root)
        self.skills_subdir = skills_subdir
        self._lock_dir = os.path.join(self.root, ".locks")

    def skill_dir(self, code: str) -> str:
        """Returns absolute path to a skill directory."""
        return os.path.join(self.root, self.skills_subdir, code)

    def skill_rel_path(self, code: str) -> str:
        """Returns relative path to a skill from repo root."""
        return f"{self.skills_subdir}/{code}"

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
            error_msg = (e.stdout + "\n" + e.stderr).strip()
            raise GitOperationError("Git command %s failed: %s" % (" ".join(command), error_msg)) from e

    def ensure_initialized(self, remote_url: Optional[str] = None, branch: str = "main"):
        """Ensures the repository is initialized and tracking the correct branch."""
        if not os.path.isdir(os.path.join(self.root, ".git")):
            if remote_url:
                logger.info("Cloning skill repository from %s (branch: %s)", remote_url, branch)
                os.makedirs(os.path.dirname(self.root), exist_ok=True)
                self._execute(["clone", "--branch", branch, remote_url, self.root])
            else:
                logger.info("Initializing local skill repository (branch: %s)", branch)
                os.makedirs(self.root, exist_ok=True)
                self._execute(["init", "-b", branch])

        # Ensure skills directory exists
        os.makedirs(os.path.join(self.root, self.skills_subdir), exist_ok=True)

    def fetch_latest(self, remote: str = "origin", branch: str = "main"):
        """Pulls the latest changes from the remote repository."""
        self._execute(["pull", remote, branch])

    def push_changes(self, remote: str = "origin", branch: str = "main"):
        """Pushes local commits to the remote repository."""
        self._execute(["push", remote, branch])

    def commit_skill(self, code: str, author_id: Any, message: Optional[str] = None) -> str:
        """Adds and commits changes for a specific skill."""
        rel_path = self.skill_rel_path(code)
        self._execute(["add", rel_path])

        diff = self._execute(["diff", "--cached", "--name-only"])
        if not diff:
            return self._execute(["rev-parse", "HEAD"])

        msg = message or "Update skill: %s by user: %s" % (code, author_id)
        self._execute(["commit", "-m", msg])
        return self._execute(["rev-parse", "HEAD"])

    def revert_to_commit(self, code: str, commit_hash: str, author_id: Any, message: Optional[str] = None) -> str:
        """Checkouts a specific commit for a skill and commits the reversal."""
        rel_path = self.skill_rel_path(code)
        self._execute(["checkout", commit_hash, "--", rel_path])
        self._execute(["add", rel_path])

        msg = message or "Revert skill: %s to %s by user: %s" % (code, commit_hash, author_id)
        self._execute(["commit", "-m", msg])
        return self._execute(["rev-parse", "HEAD"])

    def remove_skill(self, code: str, author_id: Any, message: Optional[str] = None) -> Optional[str]:
        """Removes a skill directory from the repo, commits and pushes the deletion."""
        path = self.skill_dir(code)
        rel_path = self.skill_rel_path(code)

        if not os.path.exists(path):
            logger.warning("Skill path not found, skipping git removal: %s", path)
            return None

        shutil.rmtree(path)
        self._execute(["rm", "-r", "--cached", "--ignore-unmatch", rel_path])
        self._execute(["add", "-A", rel_path])

        diff = self._execute(["diff", "--cached", "--name-only"])
        if not diff:
            logger.info("No staged changes after removing skill %s, skipping commit", code)
            return None

        msg = message or "Delete skill: %s by user: %s" % (code, author_id)
        self._execute(["commit", "-m", msg])
        return self._execute(["rev-parse", "HEAD"])
