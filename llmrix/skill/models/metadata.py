import yaml
import re
from typing import Any, Dict, Optional
from llmrix.skill.core.exceptions import ValidationError

class MetadataParser:
    """Parses skill files and validates codes."""

    @staticmethod
    def parse_manifest(content: str) -> Dict[str, Any]:
        """Extracts frontmatter from SKILL.md."""
        if not content.startswith("---"):
            return {}
        try:
            match = re.match(r"^---\s*\\n(.*?)\\n---\s*\\n", content, re.DOTALL)
            if match:
                return yaml.safe_load(match.group(1)) or {}
        except Exception as e:
            raise ValidationError(f"Failed to parse metadata frontmatter: {e}") from e
        return {}

    @staticmethod
    def validate_code(code: str) -> None:
        """Ensures skill code follows naming conventions."""
        if not (code and re.match(r"^[a-z0-9_\\-]+$", code)):
            raise ValidationError(
                f"Invalid skill code '{code}'. Only lowercase, numbers, - and _ are allowed."
            )

    @staticmethod
    def detect_category(code: str, name: str, description: str) -> str:
        """Heuristically detects skill category based on keywords."""
        text = " ".join([code, name or "", description or ""]).lower()
        
        KEYWORDS = [
            ("Developer Tools", ["git", "code", "python", "javascript", "typescript", "compiler", "debug", "ide", "sdk", "api"]),
            ("Data Analytics", ["data", "sql", "database", "excel", "csv", "chart", "analytics", "bi", "统计", "数据", "分析"]),
            ("Content Creation", ["image", "photo", "video", "audio", "canvas", "design", "content", "图片", "图像", "设计"]),
            ("Web & Search", ["search", "web", "browser", "crawl", "scrape", "http", "url", "搜索", "网页"]),
            ("System Integration", ["shell", "bash", "deploy", "docker", "k8s", "ci", "cd", "monitor", "email", "notify", "自动化", "集成"]),
        ]

        for category, keywords in KEYWORDS:
            if any(kw in text for kw in keywords):
                return category
        return "Other"
