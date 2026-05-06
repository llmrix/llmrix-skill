# LLMRix Skill Plugin Library

`llmrix-skill` is a professional Git-based Skill and plugin management framework designed for LLM Agents. It encapsulates the complex logic of publishing, versioning, and syncing code, prompts, and tools into an out-of-the-box plugin library, allowing developers to focus on building core Agent logic.

## Core Features

As the foundational plugin library for an Agent framework, it provides the following capabilities:

- **Git-Driven Plugin Market**: Uses Git repositories as the Single Source of Truth (SSOT) to achieve skill persistence, version tracing, and change tracking.
- **Out-of-the-box Dual Mode Architecture**:
  - **Worker Mode (Execution)**: Pure lightweight synchronization, responsible for pulling skills from remote repositories to local storage for high-speed loading by Agent instances.
  - **Management Mode (Admin)**: Integrates with databases to support multi-tenant authentication, skill publishing, metadata parsing, and version rollbacks.
- **Dynamic Metadata Parsing**: Automatically parses and validates `SKILL.md` (YAML Frontmatter) in the skill package to extract the plugin name, description, and category.
- **Concurrency & Safety**: Built-in distributed file lock mechanism to prevent file state race conditions during high-concurrency publishing and pulling.

---

## Quick Usage Guide

### Installation

You can integrate this plugin library into your Agent project via pip:

```bash
pip install llmrix-skill
```

### Scene 1: Syncing Plugins on Agent Execution Node (Worker Mode)

In your Agent execution environment (such as background task nodes, or upon container startup), configure a specific branch to pull the latest skills for model invocation.

```python
from llmrix.skill import GitSkillManager

def sync_skills_for_agent():
    # Initialize the Manager, configuring the remote repository and target branch
    manager = GitSkillManager(
        repo_url="https://github.com/your-org/skill-repo.git",
        branch="develop",                # Highly recommended: specify the branch to pull (e.g., main/develop/v1)
        workspace="/path/to/local/cache" # Local cache path
    )

    # Execute sync, returning the absolute filesystem path where the skills are located
    skills_path = manager.sync()
    print(f"✅ Skill plugins synced to: {skills_path}")
    
    # You can now dynamically load modules under skills_path in your Agent framework
```

### Scene 2: Web Server Management & Publishing (Management Mode)

In your Web API service (such as FastAPI/Django plugin market backend), use `GitSkillManager` to handle user uploads, publishing, and version rollbacks. It encapsulates database persistence and concurrent file locking.

```python
from llmrix.skill import GitSkillManager
from llmrix.skill import MySQLStorage

# 1. Configure the database adapter
def get_db_connection():
    # Return a pymysql/MySQLdb connection object
    pass

storage = MySQLStorage(connection_factory=get_db_connection)

# 2. Initialize the Manager, dedicated for the management end
manager = GitSkillManager(
    repo_url="git@github.com:your-org/skill-repo.git",
    storage=storage
)

# 3. Publish user-uploaded skills
def publish_user_skill(user_id, uploaded_dir):
    skill = manager.publish(
        code="python_interpreter",      # Unique skill code
        source_dir=uploaded_dir,        # Unzipped directory uploaded by the user
        user_id=user_id,                # Current operating user ID (for auth)
        message="Initial release"       
    )
    print(f"🚀 Publish successful: {skill.name} v{skill.version}")

# 4. Version Rollback
def rollback_skill(user_id):
    skill = manager.rollback(
        code="python_interpreter",
        target_version=1,
        user_id=user_id,
        message="Revert due to bugs"
    )
```

---

## Skill Package Specification

A standard skill plugin package is a directory containing the following files:

```text
my_awesome_skill/
├── SKILL.md      # Skill description and metadata (Required)
├── main.py       # Core logic (Recommended)
└── requirements.txt # Dependencies (Optional)
```

`SKILL.md` must contain a valid YAML Frontmatter header:

```markdown
---
name: Web Scraper Pro
description: Powerful web scraping tool, supports dynamic rendering.
category: Web & Search
---

Detailed Markdown documentation about this skill goes here...
```

---

## Module Architecture

You can directly import the required submodules for lower-level extensions:

- `llmrix.skill.services`: Contains `GitSkillManager`, `SkillPublisher`, and `SkillSyncer`.
- `llmrix.skill.storage`: Contains `BaseStorage` and `MySQLStorage`. Inherit `BaseStorage` to implement your own MongoDB or PostgreSQL adapters.
- `llmrix.skill.git`: Low-level Git driver library `GitRepository`.
- `llmrix.skill.models`: Data models `Skill` and `SkillVersion`.
