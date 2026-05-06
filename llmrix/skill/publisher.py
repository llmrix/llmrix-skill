import os
import shutil
import logging
from typing import Any, Optional, List
from .git import GitRepository
from .base import BaseStorage
from .metadata import MetadataParser
from .schema import Skill, SkillVersion
from .exceptions import PermissionDeniedError, VersionNotFoundError, GitSkillError

logger = logging.getLogger(__name__)

class SkillPublisher:
    """
    Responsible for the 'Write' lifecycle of Skills:
    Publishing new versions, Rollbacking, and persistence.
    """

    def __init__(
        self, 
        git: GitRepository, 
        storage: BaseStorage,
        parser: Optional[MetadataParser] = None
    ):
        self.git = git
        self.storage = storage
        self.parser = parser or MetadataParser()

    def publish(
        self,
        code: str,
        source_dir: str,
        user_id: Any,
        branch: str = "main",
        name: Optional[str] = None,
        description: Optional[str] = None,
        category: Optional[str] = None,
        message: Optional[str] = None
    ) -> Skill:
        """Deploys a new version of a skill to the repository and database."""
        self.parser.validate_code(code)

        with self.git.lock(code):
            self.git.sync(branch=branch)

            # 1. Authorization check
            existing = self.storage.get_skill(code)
            if existing and not self.storage.can_modify(code, user_id):
                raise PermissionDeniedError(f"User {user_id} lacks permission for skill {code}")

            # 2. Update filesystem
            target_path = self.git.get_skill_path(code)
            if os.path.exists(target_path):
                shutil.rmtree(target_path)
            shutil.copytree(source_dir, target_path)

            # 3. Parse Metadata from SKILL.md
            manifest_path = os.path.join(target_path, "SKILL.md")
            manifest = {}
            if os.path.exists(manifest_path):
                with open(manifest_path, "r", encoding="utf-8") as f:
                    manifest = self.parser.parse_manifest(f.read())

            final_name = name or manifest.get("name") or code
            final_desc = description or manifest.get("description")
            final_cat = (
                category 
                or manifest.get("category") 
                or self.parser.detect_category(code, final_name, final_desc or "")
            )

            # 4. Commit to Git
            commit_hash = self.git.commit(code, user_id, message)
            self.git.publish(branch=branch)

            # 5. Database update
            new_version_num = (existing.version + 1) if existing else 1
            skill = Skill(
                code=code,
                name=final_name,
                version=new_version_num,
                description=final_desc,
                category=final_cat,
                commit_hash=commit_hash,
                file_path=self.git.get_relative_path(code),
                status=0
            )
            
            self.storage.save_skill(skill)
            self.storage.add_version(SkillVersion(
                code=code,
                version=new_version_num,
                commit_hash=commit_hash,
                author_id=user_id,
                file_path=skill.file_path,
                message=message
            ))

            return skill

    def rollback(
        self,
        code: str,
        target_version: int,
        user_id: Any,
        branch: str = "main",
        message: Optional[str] = None
    ) -> Skill:
        """Reverts a skill to a previous commit/version."""
        ver = self.storage.get_version(code, target_version)
        if not ver:
            raise VersionNotFoundError(f"Version {target_version} not found for {code}")

        with self.git.lock(code):
            self.git.sync(branch=branch)
            
            if not self.storage.can_modify(code, user_id):
                 raise PermissionDeniedError(f"Access denied for skill {code}")

            new_hash = self.git.revert(code, ver.commit_hash, user_id, message)
            self.git.publish(branch=branch)

            existing = self.storage.get_skill(code)
            new_version_num = (existing.version + 1) if existing else 1
            
            skill = Skill(
                code=code,
                name=existing.name,
                version=new_version_num,
                description=existing.description,
                category=existing.category,
                commit_hash=new_hash,
                file_path=existing.file_path,
                status=existing.status
            )
            
            self.storage.save_skill(skill)
            self.storage.add_version(SkillVersion(
                code=code,
                version=new_version_num,
                commit_hash=new_hash,
                author_id=user_id,
                file_path=skill.file_path,
                message=message or f"Rollback to v{target_version}"
            ))
            
            return skill
