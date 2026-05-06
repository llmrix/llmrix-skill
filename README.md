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

## Database Schema

You can find the MySQL schema in `database/schema.sql`.

## License

MIT
