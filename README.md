# LLMRix SkillHub

A professional Git-based Skill management library for LLM agents. 

SkillHub allows you to manage, version, and synchronize "Skills" (sets of instructions, prompts, and tools) across multiple agents using Git as the source of truth.

## Features

- **Multi-User Publishing**: Deploy and version skills with built-in permission checks.
- **Async Synchronization**: Efficiently sync skills from remote repositories to local disk for agent execution.
- **Database Agnostic**: Use the included MySQL adapter or implement your own.
- **Metadata Parsing**: Automatic extraction of skill info from `SKILL.md` frontmatter.
- **Concurrency Safety**: Distributed file locking to prevent race conditions during updates.

## Installation

```bash
pip install llmrix-skill
```

## Quick Start

### 1. Worker Mode (Synchronization)

In your agent harness, simply sync the repo to a local directory:

```python
from llmrix.skill import GitSkillManager

manager = GitSkillManager(
    repo_url="https://github.com/llmrix/llmrix-skillhub.git",
    workspace="/path/to/local/cache"
)

# Initialize and sync to disk
skills_path = await manager.sync()
print(f"Skills ready at: {skills_path}")
```

### 2. Management Mode (Publishing)

In your API or dashboard, use a storage adapter to track versions:

```python
from llmrix.skill import GitSkillManager
from llmrix.skill.adapters.mysql import MySQLStorage

storage = MySQLStorage(connection_factory=get_db_conn)
manager = GitSkillManager(
    repo_url="https://github.com/llmrix/llmrix-skillhub.git",
    workspace="/path/to/mgmt/workspace",
    storage=storage
)

# Deploy a new version
skill = manager.publish(
    code="web_search",
    source_dir="/tmp/upload_123",
    user_id="user_789",
    message="Update search depth"
)
```

## API Reference

### `GitSkillManager`

The primary class for managing skills.

#### `__init__(repo_url: str, workspace: str = None, branch: str = "main", storage: BaseStorage = None)`
Initializes the manager.
- `repo_url`: Remote Git repository URL (SSH or HTTPS with credentials).
- `workspace`: Local directory for the Git repository. Defaults to `~/llmrix/skills/remote`.
- `branch`: Target Git branch. Defaults to `main`.
- `storage`: A database adapter instance (e.g., `MySQLStorage`). Required for publishing/rollback.

#### `sync() -> str`
Worker Mode: Clones or pulls the latest skills from the remote repository.
- **Returns**: Absolute path to the `skills/` directory on local disk.

#### `publish(code: str, source_dir: str, user_id: Any, name: str = None, description: str = None, category: str = None, message: str = None) -> Skill`
Management Mode: Deploys a new version of a skill.
- `code`: Unique identifier for the skill (e.g., "translator").
- `source_dir`: Local directory containing the skill files (must include `SKILL.md`).
- `user_id`: ID of the user performing the action (for permission checks and audit).
- `name/description/category`: Optional metadata. If provided, they override the values in `SKILL.md`.
- `message`: Commit message for the version history.

#### `rollback(code: str, target_version: int, user_id: Any, message: str = None) -> Skill`
Management Mode: Reverts a skill to a specific previous version.
- `target_version`: The version number to roll back to.

#### `get_history(code: str) -> List[SkillVersion]`
Retrieves the full release history for a skill.

#### `get_interim_path(uid: Any) -> str` (Static)
Returns the recommended temporary directory for user uploads: `~/llmrix/skills/interim/{uid}`.

## Database Schema

You can find the MySQL schema in `database/schema.sql`. The library currently supports the `MySQLStorage` adapter out of the box.

## License

MIT
