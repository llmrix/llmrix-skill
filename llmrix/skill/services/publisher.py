import io
import os
import shutil
import logging
import urllib.parse
import zipfile
from typing import Any, Optional
from llmrix.skill.git.repository import GitRepository
from llmrix.skill.storage.base import BaseStorage
from llmrix.skill.models.metadata import MetadataParser
from llmrix.skill.models.schema import Skill, SkillVersion
from llmrix.skill.core.exceptions import PermissionDeniedError, VersionNotFoundError

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
        introduce: Optional[str] = None,
        category: Optional[str] = None,
        message: Optional[str] = None,
        branch: Optional[str] = None,
    ) -> Skill:
        """Convenience wrapper: extracts zip_bytes to a temp dir then calls publish()."""
        interim = self.git.get_skill_path(f"_interim_{code}")
        if os.path.exists(interim):
            shutil.rmtree(interim)
        os.makedirs(interim, exist_ok=True)
        try:
            _extract_zip_to(zip_bytes, interim)
            return self.publish(
                code=code, source_dir=interim, user_id=user_id,
                name=name, introduce=introduce, category=category,
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
        introduce: Optional[str] = None,
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
                raise PermissionDeniedError(f"User {user_id} lacks permission for skill {code}")

            # 2. Filesystem Update
            target_path = self.git.get_skill_path(code)
            if os.path.exists(target_path):
                shutil.rmtree(target_path)
            shutil.copytree(source_dir, target_path)

            # 3. Metadata Extraction
            manifest_path = os.path.join(target_path, "SKILL.md")
            manifest = {}
            if os.path.exists(manifest_path):
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = self.parser.parse_manifest(f.read())

            final_name = name or manifest.get("name") or code
            final_introduce = introduce or manifest.get("description")
            final_cat = (
                category
                or manifest.get("category")
                or self.parser.detect_category(code, final_name, final_introduce or "")
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
                introduce=final_introduce,
                category=final_cat,
                commit_hash=commit_hash,
                file_path=self.git.get_relative_path(code),
                status=0
            )
            skill.user_id = user_id  # type: ignore[attr-defined]

            self.storage.save_skill(skill)
            self.storage.add_version(SkillVersion(
                code=code,
                version=new_version_num,
                commit_hash=commit_hash,
                user_id=user_id,
                file_path=skill.file_path,
                message=message
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
            raise VersionNotFoundError(f"Version {target_version} not found for {code}")

        with self.git.lock(code):
            self.git.fetch_latest(branch=target_branch)

            if not self.storage.can_modify(code, user_id):
                raise PermissionDeniedError(f"Access denied for skill {code}")

            new_hash = self.git.revert_to_commit(code, ver.commit_hash, user_id, message)
            self.git.push_changes(branch=target_branch)

            existing = self.storage.get_skill(code)
            new_version_num = (existing.version + 1) if existing else 1

            skill = Skill(
                code=code,
                name=existing.name,
                version=new_version_num,
                introduce=existing.introduce,
                category=existing.category,
                commit_hash=new_hash,
                file_path=existing.file_path,
                status=existing.status
            )
            skill.user_id = user_id  # type: ignore[attr-defined]

            self.storage.save_skill(skill)
            self.storage.add_version(SkillVersion(
                code=code,
                version=new_version_num,
                commit_hash=new_hash,
                user_id=user_id,
                file_path=skill.file_path,
                message=message or f"Rollback to v{target_version}"
            ))

            return skill


# ---------------------------------------------------------------------------
# Module-level helpers (also used by GitSkillManager / external callers)
# ---------------------------------------------------------------------------

def build_authed_url(url: str, token: Optional[str] = None,
                     username: Optional[str] = None, password: Optional[str] = None) -> str:
    """
    Embed authentication into an HTTPS Git URL.

    - token mode:    https://<token>@github.com/...
    - user/pass mode: https://<user>:<pass>@github.com/...
    """
    if not url.startswith("https://"):
        return url
    if token:
        return url.replace("https://", f"https://{token}@", 1)
    if username and password:
        u = urllib.parse.quote(username, safe="")
        p = urllib.parse.quote(password, safe="")
        return url.replace("https://", f"https://{u}:{p}@", 1)
    return url


def _extract_zip_to(zip_bytes: bytes, dest_dir: str) -> None:
    """Extract zip bytes to dest_dir, stripping a single top-level wrapper dir if present."""
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
        names = zf.namelist()
        top_dirs = {n.split("/")[0] for n in names if "/" in n}
        strip = (list(top_dirs)[0] + "/") if (
            len(top_dirs) == 1
            and all(n.startswith(list(top_dirs)[0] + "/") for n in names if "/" in n)
        ) else ""
        for member in zf.infolist():
            rel = member.filename[len(strip):] if strip and member.filename.startswith(strip) else member.filename
            if not rel:
                continue
            target = os.path.join(dest_dir, rel)
            if member.is_dir():
                os.makedirs(target, exist_ok=True)
            else:
                os.makedirs(os.path.dirname(target), exist_ok=True)
                with zf.open(member) as src, open(target, "wb") as dst:
                    dst.write(src.read())
