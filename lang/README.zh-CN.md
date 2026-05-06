# LLMRix SkillHub

面向 LLM Agent 的专业级 Git 技能管理库。

SkillHub 允许您使用 Git 作为单一事实来源，在多个 Agent 之间管理、版本化和同步“技能”（技能集包含指令、提示词和工具）。

## 特性

- **多用户发布**：支持多用户部署和版本化，内置权限校验。
- **异步同步**：高效地从远程仓库同步技能到本地磁盘，供 Agent 执行。
- **数据库无关**：内置 MySQL 适配器，也支持自定义存储实现。
- **元数据解析**：自动从 `SKILL.md` 的 YAML frontmatter 中提取技能信息。
- **并发安全**：使用分布式文件锁防止更新时的竞态条件。

## 安装

```bash
pip install llmrix-skill
```

## 快速上手

### 1. 工作模式 (同步)

在 Agent 运行端，只需将仓库同步到本地目录：

```python
from llmrix.skill import GitSkillManager

manager = GitSkillManager(
    repo_url="https://github.com/llmrix/llmrix-skillhub.git",
    workspace="/path/to/local/cache"
)

# 初始化并同步到磁盘
skills_path = await manager.sync()
print(f"技能已就绪: {skills_path}")
```

### 2. 管理模式 (发布)

在 API 或后台管理端，使用存储适配器来记录版本：

```python
from llmrix.skill import GitSkillManager
from llmrix.skill.adapters.mysql import MySQLStorage

storage = MySQLStorage(connection_factory=get_db_conn)
manager = GitSkillManager(
    repo_url="https://github.com/llmrix/llmrix-skillhub.git",
    workspace="/path/to/mgmt/workspace",
    storage=storage
)

# 发布新版本
skill = manager.publish(
    code="web_search",
    source_dir="/tmp/upload_123",
    user_id="user_789",
    message="更新搜索深度"
)
```

## API 参考

### `GitSkillManager`

用于管理技能的核心类。

#### `__init__(repo_url: str, workspace: str = None, branch: str = "main", storage: BaseStorage = None)`
初始化管理器。
- `repo_url`: 远程 Git 仓库 URL (SSH 或带凭据的 HTTPS)。
- `workspace`: 本地 Git 仓库的工作目录。默认为 `~/llmrix/skills/remote`。
- `branch`: 目标 Git 分支。默认为 `main`。
- `storage`: 数据库适配器实例 (如 `MySQLStorage`)。执行发布/回退操作时必填。

#### `sync() -> str`
工作模式 (Worker Mode)：从远程仓库克隆或拉取最新的技能。
- **返回**: 本地磁盘上 `skills/` 目录的绝对路径。

#### `publish(code: str, source_dir: str, user_id: Any, name: str = None, description: str = None, category: str = None, message: str = None) -> Skill`
管理模式 (Management Mode)：部署技能的新版本。
- `code`: 技能的唯一标识符 (如 "translator")。
- `source_dir`: 包含技能文件的本地目录 (必须包含 `SKILL.md`)。
- `user_id`: 执行操作的用户 ID (用于权限校验和审计)。
- `name/description/category`: 可选元数据。如果提供，将覆盖 `SKILL.md` 中的对应值。
- `message`: 版本历史的提交信息。

#### `rollback(code: str, target_version: int, user_id: Any, message: str = None) -> Skill`
管理模式 (Management Mode)：将技能回退到指定的历史版本。
- `target_version`: 要回退到的版本号。

#### `get_history(code: str) -> List[SkillVersion]`
获取技能的完整发布历史。

#### `get_interim_path(uid: Any) -> str` (静态方法)
返回推荐的用户上传临时目录: `~/llmrix/skills/interim/{uid}`。

## 数据库结构

您可以在 `database/schema.sql` 中找到 MySQL 建表语句。本库目前开箱即用支持 `MySQLStorage` 适配器。

## 许可证

MIT
