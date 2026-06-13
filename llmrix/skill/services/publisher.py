import io
import os
import shutil
import logging
import zipfile
from typing import Any, Optional

from llmrix.skill.git.repository import GitRepository
from llmrix.skill.storage.base import BaseStorage
from llmrix.skill.models.metadata import MetadataParser
from llmrix.skill.models.schema import Skill, SkillVersion
from llmrix.skill.core.exceptions import PermissionDeniedError, VersionNotFoundError
from llmrix.skill.core.utils import build_authed_url

logger = logging.getLogger(__name__)


class SkillPublisher:
    """
    Handles the deployment lifecycle of Skills.
    Encapsulates permissions, filesystem updates, and persistence.
    """

    def __init__(
        self,
        git: GitRepository,
        storage: BaseStorage,
        parser: Optional[MetadataParser] = None,
        default_branch: str = "main"
    ):
        self.git = git
        self.storage = storage
        self.parser = parser or MetadataParser()
        self.default_branch = default_branch

    def publish_zip(
        self,
        code: str,
        zip_bytes: bytes,
        user_id: Any,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        message: Optional[str] = None,
        branch: Optional[str] = None,
    ) -> Skill:
        """Convenience wrapper: extracts zip_bytes to a temp dir then calls publish()."""
        interim = self.git.skill_dir(f"_interim_{code}")
        if os.path.exists(interim):
            shutil.rmtree(interim)
        os.makedirs(interim, exist_ok=True)
        try:
            _extract_zip_to(zip_bytes, interim)
            return self.publish(
                code=code, source_dir=interim, user_id=user_id,
                name=name, description=description, category=category,
                message=message, branch=branch,
            )
        finally:
            if os.path.exists(interim):
                shutil.rmtree(interim)

    def publish(
        self,
        code: str,
        source_dir: str,
        user_id: Any,
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        message: Optional[str] = None,
        branch: Optional[str] = None
    ) -> Skill:
        """Executes a full deployment workflow for a skill."""
        target_branch = branch or self.default_branch
        self.parser.validate_code(code)

        with self.git.lock(code):
            self.git.fetch_latest(branch=target_branch)

            # 1. Authorization
            existing = self.storage.get_skill(code)
            if existing and not self.storage.can_modify(code, user_id):
                raise PermissionDeniedError("User %s lacks permission for skill %s" % (user_id, code))

            # 2. Filesystem Update
            target_path = self.git.skill_dir(code)
            if os.path.exists(target_path):
                shutil.rmtree(target_path)
            shutil.copytree(source_dir, target_path)

            # 3. Metadata Extraction
            manifest_path = os.path.join(target_path, "SKILL.md")
            frontmatter = {}
            if os.path.exists(manifest_path):
                with open(manifest_path, "r", encoding="utf-8") as f:
                    frontmatter = self.parser.parse_frontmatter(f.read())

            final_name = name or frontmatter.get("name") or code
            final_description = description or frontmatter.get("description")
            final_category = (
                category
                or frontmatter.get("category")
                or self.parser.detect_category(code, final_name, final_description or "")
            )

            # 4. Git Orchestration
            commit_hash = self.git.commit_skill(code, user_id, message)
            self.git.push_changes(branch=target_branch)

            # 5. Database Persistence
            new_version_num = (existing.version + 1) if existing else 1
            skill = Skill(
                code=code,
                name=final_name,
                version=new_version_num,
                description=final_description,
                category=final_category,
                git_commit=commit_hash,
                git_path=self.git.skill_rel_path(code),
                status="inactive",
                user_id=int(user_id),
            )

            self.storage.save_skill(skill)
            self.storage.add_version(SkillVersion(
                code=code,
                version=new_version_num,
                git_commit=commit_hash,
                user_id=int(user_id),
                git_path=skill.git_path,
                message=message,
            ))

            return skill

    def rollback(
        self,
        code: str,
        target_version: int,
        user_id: Any,
        message: Optional[str] = None,
        branch: Optional[str] = None
    ) -> Skill:
        """Rolls back a skill to a specific historical version."""
        target_branch = branch or self.default_branch
        ver = self.storage.get_version(code, target_version)
        if not ver:
            raise VersionNotFoundError("Version %s not found for %s" % (target_version, code))

        with self.git.lock(code):
            self.git.fetch_latest(branch=target_branch)

            if not self.storage.can_modify(code, user_id):
                raise PermissionDeniedError("Access denied for skill %s" % code)

            new_commit = self.git.revert_to_commit(code, ver.git_commit, user_id, message)
            self.git.push_changes(branch=target_branch)

            existing = self.storage.get_skill(code)
            new_version_num = (existing.version + 1) if existing else 1

            skill = Skill(
                code=code,
                name=existing.name,
                version=new_version_num,
                description=existing.description,
                category=existing.category,
                git_commit=new_commit,
                git_path=existing.git_path,
                status=existing.status,
                user_id=int(user_id),
            )

            self.storage.save_skill(skill)
            self.storage.add_version(SkillVersion(
                code=code,
                version=new_version_num,
                git_commit=new_commit,
                user_id=int(user_id),
                git_path=skill.git_path,
                message=message or "Rollback to v%s" % target_version,
            ))

            return skill


def _extract_zip_to(zip_bytes: bytes, dest_dir: str) -> None:
    """Extract zip bytes to dest_dir, stripping a single top-level wrapper dir if present."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        top_dirs = {n.split("/")[0] for n in names if "/" in n}
        top_dir = list(top_dirs)[0] if len(top_dirs) == 1 else None
        strip = (top_dir + "/") if (
            top_dir
            and all(n.startswith(top_dir + "/") for n in names if "/" in n)
        ) else ""
        for member in zf.infolist():
            rel = member.filename[len(strip):] if strip and member.filename.startswith(strip) else member.filename
            if not rel:
                continue
            target = os.path.realpath(os.path.join(dest_dir, rel))
            if not target.startswith(os.path.realpath(dest_dir) + os.sep):
                continue
            if member.is_dir():
                os.makedirs(target, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with zf.open(member) as src, open(target, "wb") as dst:
                    dst.write(src.read())
