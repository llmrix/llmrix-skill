# LLMRix SkillHub

LLM 에이전트를 위한 전문적인 Git 기반 스킬 관리 라이브러리입니다.

SkillHub를 사용하면 Git을 단일 소스로 사용하여 여러 에이전트 간에 "스킬"(지침, 프롬프트 및 도구 세트)을 관리, 버전 관리 및 동기화할 수 있습니다.

## 주요 기능

- **다중 사용자 게시**: 기본 제공 권한 확인을 통해 스킬을 배포하고 버전 관리를 수행합니다.
- **비동기 동기화**: 에이전트 실행을 위해 원격 저장소의 스킬을 로컬 디스크로 효율적으로 동기화합니다.
- **데이터베이스 독립성**: 기본 제공되는 MySQL 어댑터를 사용하거나 자체 스토리지를 구현할 수 있습니다.
- **메타데이터 파싱**: `SKILL.md`의 YAML frontmatter에서 스킬 정보를 자동으로 추출합니다.
- **동시성 안전**: 업데이트 중 레이스 컨디션을 방지하기 위해 분산 파일 잠금을 사용합니다.

## 설치

```bash
pip install llmrix-skill
```

## 빠른 시작

### 1. 워커 모드 (동기화)

에이전트 하네스에서 저장소를 로컬 디렉토리로 동기화하기만 하면 됩니다:

```python
from llmrix.skill import GitSkillManager

manager = GitSkillManager(
    repo_url="https://github.com/llmrix/llmrix-skillhub.git",
    workspace="/path/to/local/cache"
)

# 초기화 및 디스크 동기화
skills_path = await manager.sync()
print(f"스킬 준비 완료: {skills_path}")
```

### 2. 관리 모드 (게시)

API 또는 대시보드에서 스토리지 어댑터를 사용하여 버전을 추적합니다:

```python
from llmrix.skill import GitSkillManager
from llmrix.skill.adapters.mysql import MySQLStorage

storage = MySQLStorage(connection_factory=get_db_conn)
manager = GitSkillManager(
    repo_url="https://github.com/llmrix/llmrix-skillhub.git",
    workspace="/path/to/mgmt/workspace",
    storage=storage
)

# 새 버전 배포
skill = manager.publish(
    code="web_search",
    source_dir="/tmp/upload_123",
    user_id="user_789",
    message="검색 깊이 업데이트"
)
```

## API 레퍼런스

### `GitSkillManager`

스킬 관리를 위한 핵심 클래스입니다.

#### `__init__(repo_url: str, workspace: str = None, branch: str = "main", storage: BaseStorage = None)`
관리자를 초기화합니다.
- `repo_url`: 원격 Git 저장소 URL (SSH 또는 자격 증명이 포함된 HTTPS).
- `workspace`: 로컬 Git 저장소 작업 디렉토리. 기본값은 `~/llmrix/skills/remote`입니다.
- `branch`: 대상 Git 브랜치. 기본값은 `main`입니다.
- `storage`: 데이터베이스 어댑터 인스턴스(예: `MySQLStorage`). 게시/롤백 작업 시 필수입니다.

#### `sync() -> str`
워커 모드 (Worker Mode): 원격 저장소에서 최신 스킬을 복제하거나 가져옵니다.
- **반환**: 로컬 디스크의 `skills/` 디렉토리에 대한 절대 경로입니다.

#### `publish(code: str, source_dir: str, user_id: Any, name: str = None, description: str = None, category: str = None, message: str = None) -> Skill`
관리 모드 (Management Mode): 스킬의 새 버전을 배포합니다.
- `code`: 스킬의 고유 식별자(예: "translator").
- `source_dir`: 스킬 파일이 포함된 로컬 디렉토리(`SKILL.md` 포함 필수).
- `user_id`: 작업을 수행하는 사용자 ID(권한 확인 및 감사용).
- `name/description/category`: 선택적 메타데이터. 제공된 경우 `SKILL.md`의 값을 덮어씁니다.
- `message`: 버전 기록을 위한 커밋 메시지입니다.

#### `rollback(code: str, target_version: int, user_id: Any, message: str = None) -> Skill`
관리 모드 (Management Mode): 스킬을 특정 이전 버전으로 되돌립니다.
- `target_version`: 되돌릴 버전 번호입니다.

#### `get_history(code: str) -> List[SkillVersion]`
스킬의 전체 릴리스 기록을 가져옵니다.

#### `get_interim_path(uid: Any) -> str` (정적 메서드)
사용자 업로드를 위한 권장 임시 디렉토리인 `~/llmrix/skills/interim/{uid}`를 반환합니다.

## 데이터베이스 스키마

MySQL 스키마는 `database/schema.sql`에서 확인할 수 있습니다. 이 라이브러리는 현재 `MySQLStorage` 어댑터를 기본적으로 지원합니다.

## 라이선스

MIT
