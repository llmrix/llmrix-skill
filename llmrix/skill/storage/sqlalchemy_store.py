from typing import Any, List, Optional

from sqlalchemy.orm import sessionmaker

from llmrix.skill.storage.base import BaseStorage, OwnershipStatus
from llmrix.skill.models.schema import Skill, SkillVersion
from llmrix.skill.models.orm import SkillInfoModel, SkillVersionModel


class SQLAlchemyStorage(BaseStorage):
    """
    Database agnostic storage using SQLAlchemy ORM.
    Supports MySQL, PostgreSQL, etc.
    """

    def __init__(self, engine):
        self.engine = engine
        self._session_factory = sessionmaker(bind=self.engine)

    def _row_to_skill(self, row: SkillInfoModel) -> Skill:
        return Skill(
            code=row.skill_code,
            name=row.skill_name,
            version=row.version,
            description=row.introduce,
            category=row.category,
            git_commit=row.git_commit,
            git_path=row.git_path,
            status=row.status,
            user_id=row.user_id,
        )

    def get_skill(self, code: str) -> Optional[Skill]:
        with self._session_factory() as db:
            row = db.query(SkillInfoModel).filter_by(skill_code=code, deleted=False).first()
            return self._row_to_skill(row) if row else None

    def save_skill(self, skill: Skill) -> None:
        with self._session_factory() as db:
            row = db.query(SkillInfoModel).filter_by(skill_code=skill.code, deleted=False).first()
            if row:
                row.skill_name = skill.name
                row.introduce = skill.description
                row.version = skill.version
                row.git_commit = skill.git_commit
                row.git_path = skill.git_path
                row.status = skill.status
                row.category = skill.category
            else:
                row = SkillInfoModel(
                    skill_code=skill.code,
                    skill_name=skill.name,
                    introduce=skill.description,
                    version=skill.version,
                    git_commit=skill.git_commit,
                    git_path=skill.git_path,
                    status=skill.status,
                    category=skill.category,
                    user_id=skill.user_id,
                )
                db.add(row)
            db.commit()

    def add_version(self, version: SkillVersion) -> None:
        with self._session_factory() as db:
            row = SkillVersionModel(
                skill_code=version.code,
                version=version.version,
                git_commit=version.git_commit,
                git_path=version.git_path,
                user_id=version.user_id,
                message=version.message,
            )
            db.add(row)
            db.commit()

    def get_history(self, code: str) -> List[SkillVersion]:
        with self._session_factory() as db:
            rows = (
                db.query(SkillVersionModel)
                .filter_by(skill_code=code, deleted=False)
                .order_by(SkillVersionModel.version.desc())
                .all()
            )
            return [
                SkillVersion(
                    code=r.skill_code,
                    version=r.version,
                    git_commit=r.git_commit,
                    user_id=r.user_id,
                    git_path=r.git_path,
                    message=r.message,
                    created_at=r.created_at,
                )
                for r in rows
            ]

    def get_version(self, code: str, version_number: int) -> Optional[SkillVersion]:
        with self._session_factory() as db:
            r = db.query(SkillVersionModel).filter_by(
                skill_code=code, version=version_number, deleted=False
            ).first()
            if not r:
                return None
            return SkillVersion(
                code=r.skill_code,
                version=r.version,
                git_commit=r.git_commit,
                user_id=r.user_id,
                git_path=r.git_path,
                message=r.message,
                created_at=r.created_at,
            )

    def can_modify(self, code: str, user_id: Any) -> bool:
        with self._session_factory() as db:
            row = db.query(SkillInfoModel).filter_by(
                skill_code=code, user_id=int(user_id), deleted=False
            ).first()
            return row is not None

    def check_ownership(self, code: str, user_id: Any) -> OwnershipStatus:
        with self._session_factory() as db:
            row = db.query(SkillInfoModel).filter_by(skill_code=code, deleted=False).first()
            if not row:
                return "free"
            return "own" if int(row.user_id) == int(user_id) else "conflict"

    def delete_skill(self, code: str) -> None:
        with self._session_factory() as db:
            db.query(SkillInfoModel).filter_by(skill_code=code).update({"deleted": True})
            db.query(SkillVersionModel).filter_by(skill_code=code).update({"deleted": True})
            db.commit()
