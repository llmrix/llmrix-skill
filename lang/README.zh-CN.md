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

## 数据库结构

您可以在 `database/schema.sql` 中找到 MySQL 建表语句。

## 许可证

MIT
