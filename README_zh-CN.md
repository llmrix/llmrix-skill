# LLMRix Skill 插件库

`llmrix-skill` 是一个为 LLM Agent 设计的专业 Git-based 技能（Skill）和插件管理框架。它将复杂的代码、提示词和工具的发布、版本控制及多端同步逻辑封装成一个开箱即用的插件库，使得开发者可以专注于 Agent 核心逻辑的构建。

## 核心特性 (Features)

作为 Agent 框架的底层插件库，它提供了以下能力：

- **Git 驱动的插件市场**：以 Git 仓库作为唯一真实数据源（SSOT），实现技能的持久化、版本溯源和变更追踪。
- **开箱即用的双模式架构**：
  - **Worker 模式 (执行端)**：纯轻量级同步，负责将远程仓库的技能拉取到本地，供 Agent 实例高速加载。
  - **Management 模式 (管理端)**：集成数据库，支持多租户鉴权、技能发布、元数据解析和版本回滚。
- **动态元数据解析**：自动解析并校验技能包中的 `SKILL.md` (YAML Frontmatter) 获取插件名称、描述和分类。
- **并发与安全**：内置分布式文件锁机制，防止高并发发布和拉取时的文件状态竞争。

---

## 快速使用指南 (Usage Guide)

### 安装

你可以通过 pip 将本插件库集成到你的 Agent 项目中：

```bash
pip install llmrix-skill
```

### 场景一：Agent 执行端同步插件 (Worker Mode)

在你的 Agent 运行环境（如后台任务节点、容器启动时），通过配置指定分支来拉取最新的技能供模型调用。

```python
from llmrix.skill import GitSkillManager

def sync_skills_for_agent():
    # 初始化 Manager，配置远程仓库和目标分支
    manager = GitSkillManager(
        repo_url="https://github.com/your-org/skill-repo.git",
        branch="develop",                # 强烈建议：指定拉取的分支（如 main/develop/v1）
        workspace="/path/to/local/cache" # 本地缓存路径
    )

    # 执行同步，返回技能所在的文件系统绝对路径
    skills_path = manager.sync()
    print(f"✅ 技能插件已同步至: {skills_path}")
    
    # 接下来即可在 Agent 框架中动态加载 skills_path 下的模块
```

### 场景二：Web 服务端管理与发布 (Management Mode)

在你的 Web API 服务（如 FastAPI/Django 插件市场后台）中，使用 `GitSkillManager` 处理用户的上传、发布和版本回退。它封装了数据库持久化和并发文件锁。

```python
from llmrix.skill import GitSkillManager
from llmrix.skill import MySQLStorage

# 1. 配置数据库适配器
def get_db_connection():
    # 返回 pymysql/MySQLdb 连接对象
    pass

storage = MySQLStorage(connection_factory=get_db_connection)

# 2. 初始化 Manager，专用于管理端
manager = GitSkillManager(
    repo_url="git@github.com:your-org/skill-repo.git",
    storage=storage
)

# 3. 发布用户上传的技能
def publish_user_skill(user_id, uploaded_dir):
    skill = manager.publish(
        code="python_interpreter",      # 技能唯一编码
        source_dir=uploaded_dir,        # 用户上传的解压目录
        user_id=user_id,                # 当前操作用户 ID (鉴权)
        message="Initial release"       
    )
    print(f"🚀 发布成功: {skill.name} v{skill.version}")

# 4. 版本回滚
def rollback_skill(user_id):
    skill = manager.rollback(
        code="python_interpreter",
        target_version=1,
        user_id=user_id,
        message="Revert due to bugs"
    )
```

---

## 插件包规范 (Skill Package Specification)

一个标准的技能插件包是一个包含以下文件的目录：

```text
my_awesome_skill/
├── SKILL.md      # 技能描述与元数据 (必须)
├── main.py       # 核心逻辑 (推荐)
└── requirements.txt # 依赖 (可选)
```

`SKILL.md` 必须包含合法的 YAML Frontmatter 头：

```markdown
---
name: Web Scraper Pro
description: 强大的网页抓取工具，支持动态渲染。
category: Web & Search
---

这里是关于此技能的详细 Markdown 说明文档...
```

---

## 模块架构

你可以直接导入所需的子模块进行更底层的扩展：

- `llmrix.skill.services`: 包含 `GitSkillManager`，`SkillPublisher`，`SkillSyncer`。
- `llmrix.skill.storage`: 包含 `BaseStorage` 和 `MySQLStorage`。继承 `BaseStorage` 可实现你自己的 MongoDB 或 PostgreSQL 适配器。
- `llmrix.skill.git`: 底层 Git 驱动库 `GitRepository`。
- `llmrix.skill.models`: 数据模型 `Skill` 和 `SkillVersion`。
