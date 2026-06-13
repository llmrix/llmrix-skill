from sqlalchemy import Boolean, Column, Integer, String, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class SkillInfoModel(Base):
    __tablename__ = 'skill_info'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, nullable=False, index=True)
    skill_code = Column(String(64), nullable=False, unique=True, index=True)
    skill_name = Column(String(128), nullable=False)
    introduce = Column(Text, nullable=True)
    version = Column(Integer, nullable=False, default=1)
    git_commit = Column(String(64), nullable=True)
    git_path = Column(String(256), nullable=True)
    status = Column(String(16), nullable=False, default='inactive')
    category = Column(String(32), nullable=True)
    deleted = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now)

class SkillVersionModel(Base):
    __tablename__ = 'skill_version'

    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_code = Column(String(64), ForeignKey('skill_info.skill_code'), nullable=False, index=True)
    version = Column(Integer, nullable=False, index=True)
    git_commit = Column(String(64), nullable=False)
    git_path = Column(String(256), nullable=True)
    user_id = Column(Integer, nullable=False)
    message = Column(Text, nullable=True)
    deleted = Column(Boolean, nullable=False, default=False)

    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now)
