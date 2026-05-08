from typing import Any, List, Optional
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

from llmrix.skill.storage.base import BaseStorage
from llmrix.skill.models.schema import Skill, SkillVersion

Base = declarative_base()

class SkillModel(Base):
    __tablename__ = "skill_info"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_code = Column(String(100), unique=True, nullable=False, index=True)
    skill_name = Column(String(200), nullable=False)
    introduce = Column(Text, nullable=True) # Description
    category = Column(String(100), nullable=True)
    version = Column(Integer, default=1)
    git_commit = Column(String(40), nullable=False)
    git_path = Column(String(500), nullable=False)
    status = Column(Integer, default=0)
    user_id = Column(String(100), nullable=True) # Author/Owner
    deleted = Column(Integer, default=0)
    create_time = Column(DateTime, default=datetime.utcnow)
    update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class SkillVersionModel(Base):
    __tablename__ = "skill_version"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_code = Column(String(100), nullable=False, index=True)
    version = Column(Integer, nullable=False)
    git_commit = Column(String(40), nullable=False)
    git_path = Column(String(500), nullable=False)
    user_id = Column(String(100), nullable=False)
    introduce = Column(Text, nullable=True)
    deleted = Column(Integer, default=0)
    create_time = Column(DateTime, default=datetime.utcnow)

class SQLAlchemyStorage(BaseStorage):
    """
    Database agnostic storage using SQLAlchemy ORM.
    Supports MySQL, PostgreSQL, SQLite, etc.
    """
    def __init__(self, engine_or_url: Any, auto_create_tables: bool = True):
        if isinstance(engine_or_url, str):
            self.engine = create_engine(engine_or_url)
        else:
            self.engine = engine_or_url
            
        self.SessionLocal = sessionmaker(bind=self.engine)
        
        if auto_create_tables:
            Base.metadata.create_all(self.engine)

    def _to_skill(self, model: SkillModel) -> Skill:
        return Skill(
            code=model.skill_code,
            name=model.skill_name,
            version=model.version,
            description=model.introduce,
            category=model.category,
            commit_hash=model.git_commit,
            file_path=model.git_path,
            status=model.status
        )

    def get_skill(self, code: str) -> Optional[Skill]:
        with self.SessionLocal() as db:
            model = db.query(SkillModel).filter_by(skill_code=code, deleted=0).first()
            return self._to_skill(model) if model else None

    def save_skill(self, skill: Skill) -> None:
        with self.SessionLocal() as db:
            model = db.query(SkillModel).filter_by(skill_code=skill.code, deleted=0).first()
            if model:
                model.skill_name = skill.name
                model.introduce = skill.description
                model.version = skill.version
                model.git_commit = skill.commit_hash
                model.git_path = skill.file_path
                model.status = skill.status
                model.category = skill.category
            else:
                model = SkillModel(
                    skill_code=skill.code,
                    skill_name=skill.name,
                    introduce=skill.description,
                    version=skill.version,
                    git_commit=skill.commit_hash,
                    git_path=skill.file_path,
                    status=skill.status,
                    category=skill.category
                )
                db.add(model)
            db.commit()

    def add_version(self, version: SkillVersion) -> None:
        with self.SessionLocal() as db:
            model = SkillVersionModel(
                skill_code=version.code,
                version=version.version,
                git_commit=version.commit_hash,
                git_path=version.file_path,
                user_id=str(version.author_id),
                introduce=version.message
            )
            db.add(model)
            db.commit()

    def get_history(self, code: str) -> List[SkillVersion]:
        with self.SessionLocal() as db:
            models = db.query(SkillVersionModel).filter_by(skill_code=code, deleted=0).order_by(SkillVersionModel.version.desc()).all()
            return [
                SkillVersion(
                    code=m.skill_code,
                    version=m.version,
                    commit_hash=m.git_commit,
                    author_id=m.user_id,
                    file_path=m.git_path,
                    message=m.introduce,
                    created_at=m.create_time
                ) for m in models
            ]

    def get_version(self, code: str, version_number: int) -> Optional[SkillVersion]:
        with self.SessionLocal() as db:
            m = db.query(SkillVersionModel).filter_by(skill_code=code, version=version_number, deleted=0).first()
            if not m: return None
            return SkillVersion(
                code=m.skill_code,
                version=m.version,
                commit_hash=m.git_commit,
                author_id=m.user_id,
                file_path=m.git_path,
                message=m.introduce,
                created_at=m.create_time
            )

    def can_modify(self, code: str, user_id: Any) -> bool:
        with self.SessionLocal() as db:
            model = db.query(SkillModel).filter_by(skill_code=code, user_id=str(user_id), deleted=0).first()
            return model is not None
