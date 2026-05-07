from typing import Any, List, Optional
from llmrix.skill.storage.base import BaseStorage, OwnershipStatus
from llmrix.skill.models.schema import Skill, SkillVersion

class MySQLStorage(BaseStorage):
    def __init__(self, connection_factory):
        self.get_conn = connection_factory

    def _to_skill(self, row: dict) -> Skill:
        return Skill(
            code=row["skill_code"],
            name=row["skill_name"],
            version=row["version"],
            introduce=row["introduce"],
            category=row["category"],
            commit_hash=row["git_commit"],
            file_path=row["git_path"],
            status=row["status"]
        )

    def get_skill(self, code: str) -> Optional[Skill]:
        with self.get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM skill_info WHERE skill_code=%s AND deleted=0", (code,))
            row = cur.fetchone()
            return self._to_skill(row) if row else None

    def save_skill(self, skill: Skill) -> None:
        sql = """
            INSERT INTO skill_info (user_id, skill_code, skill_name, introduce, version, git_commit, git_path, status, category)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                skill_name  = VALUES(skill_name),
                introduce   = VALUES(introduce),
                version     = VALUES(version),
                git_commit  = VALUES(git_commit),
                git_path    = VALUES(git_path),
                category    = VALUES(category),
                update_time = NOW()
        """
        with self.get_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, (
                getattr(skill, "user_id", None),
                skill.code, skill.name, skill.introduce,
                skill.version, skill.commit_hash, skill.file_path,
                skill.status, skill.category
            ))
            conn.commit()

    def add_version(self, version: SkillVersion) -> None:
        sql = """
            INSERT INTO skill_version (skill_code, version, git_commit, git_path, user_id, introduce)
            VALUES (%s, %s, %s, %s, %s, %s)
        """
        with self.get_conn() as conn:
            cur = conn.cursor()
            cur.execute(sql, (
                version.code, version.version, version.commit_hash,
                version.file_path, version.user_id, version.message
            ))
            conn.commit()

    def get_history(self, code: str) -> List[SkillVersion]:
        with self.get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM skill_version WHERE skill_code=%s AND deleted=0 ORDER BY version DESC", (code,))
            rows = cur.fetchall()
            return [SkillVersion(
                code=r["skill_code"],
                version=r["version"],
                commit_hash=r["git_commit"],
                user_id=r["user_id"],
                file_path=r["git_path"],
                message=r["introduce"],
                created_at=r["create_time"]
            ) for r in rows]

    def get_version(self, code: str, version_number: int) -> Optional[SkillVersion]:
        with self.get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM skill_version WHERE skill_code=%s AND version=%s AND deleted=0",
                        (code, version_number))
            r = cur.fetchone()
            if not r:
                return None
            return SkillVersion(
                code=r["skill_code"],
                version=r["version"],
                commit_hash=r["git_commit"],
                user_id=r["user_id"],
                file_path=r["git_path"],
                message=r["introduce"],
                created_at=r["create_time"]
            )

    def can_modify(self, code: str, user_id: Any) -> bool:
        with self.get_conn() as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM skill_info WHERE skill_code=%s AND user_id=%s AND deleted=0",
                        (code, user_id))
            return cur.fetchone() is not None

    def check_ownership(self, code: str, user_id: Any) -> OwnershipStatus:
        """Single-query three-way ownership check."""
        with self.get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT user_id FROM skill_info WHERE skill_code=%s AND deleted=0",
                (code,)
            )
            row = cur.fetchone()
        if row is None:
            return "free"
        owner_id = row.get("user_id") or 0
        return "own" if int(owner_id) == int(user_id) else "conflict"

    def delete_skill(self, code: str) -> None:
        """Hard-delete (soft-flag) skill_info and all skill_version records."""
        with self.get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                "UPDATE skill_info SET deleted=1, update_time=NOW() WHERE skill_code=%s",
                (code,)
            )
            cur.execute(
                "UPDATE skill_version SET deleted=1 WHERE skill_code=%s",
                (code,)
            )
            conn.commit()
