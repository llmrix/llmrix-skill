import os
import urllib.parse
from typing import Any, Dict, List, Optional


def build_file_tree(base_dir: str, rel_prefix: str = "") -> List[Dict[str, Any]]:
    """
    Recursively builds a nested file tree (directories first, sorted by name).
    Returns structure:
      [
        {"name": "scripts", "path": "scripts", "type": "dir", "children": [...]},
        {"name": "SKILL.md", "path": "SKILL.md", "type": "file", "size": 1024},
      ]
    """
    items: List[Dict[str, Any]] = []
    try:
        entries = sorted(os.scandir(base_dir), key=lambda e: (e.is_file(), e.name))
    except (FileNotFoundError, PermissionError):
        return items

    for entry in entries:
        if entry.name.startswith("."):
            continue
        rel_path = f"{rel_prefix}{entry.name}" if rel_prefix else entry.name
        if entry.is_dir(follow_symlinks=False):
            children = build_file_tree(entry.path, rel_path + "/")
            items.append({
                "name":     entry.name,
                "path":     rel_path,
                "type":     "dir",
                "children": children,
            })
        else:
            items.append({
                "name": entry.name,
                "path": rel_path,
                "type": "file",
                "size": entry.stat().st_size,
            })
    return items


def build_authed_url(url: str, token: Optional[str] = None,
                     username: Optional[str] = None, password: Optional[str] = None) -> str:
    """
    Embed authentication into an HTTPS Git URL.

    - token mode:     https://<token>@github.com/...
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
