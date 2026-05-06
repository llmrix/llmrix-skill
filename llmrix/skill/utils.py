import os
from typing import Any, Dict, List

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
    except PermissionError:
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
