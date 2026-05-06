# LLMRix Skill 플러그인 라이브러리

`llmrix-skill`은 LLM Agent를 위해 설계된 전문적인 Git 기반 스킬(Skill) 및 플러그인 관리 프레임워크입니다. 코드, 프롬프트, 도구의 게시, 버전 제어 및 다중 동기화 로직을 즉시 사용 가능한 플러그인 라이브러리로 캡슐화하여 개발자가 Agent 핵심 로직 구축에 집중할 수 있도록 합니다.

## 핵심 기능 (Features)

Agent 프레임워크의 기본 플러그인 라이브러리로서 다음 기능을 제공합니다.

- **Git 기반 플러그인 마켓**: Git 리포지토리를 단일 진실 공급원(SSOT)으로 사용하여 스킬 지속성, 버전 추적 및 변경 사항 추적을 달성합니다.
- **즉시 사용 가능한 듀얼 모드 아키텍처**:
  - **Worker 모드 (실행단)**: 원격 저장소에서 로컬로 스킬을 가져와 Agent 인스턴스가 고속으로 로드할 수 있도록 하는 순수 경량 동기화입니다.
  - **Management 모드 (관리단)**: 데이터베이스와 통합되어 다중 테넌트 인증, 스킬 게시, 메타데이터 구문 분석 및 버전 롤백을 지원합니다.
- **동적 메타데이터 파싱**: 스킬 패키지의 `SKILL.md` (YAML Frontmatter)를 자동으로 파싱하고 검증하여 플러그인 이름, 설명 및 카테고리를 추출합니다.
- **동시성 및 안전성**: 분산 파일 잠금 메커니즘이 내장되어 있어 동시성이 높은 게시 및 동기화 중 파일 상태 경쟁 조건을 방지합니다.

---

## 빠른 사용 가이드 (Usage Guide)

### 설치

pip를 통해 이 플러그인 라이브러리를 Agent 프로젝트에 통합할 수 있습니다.

```bash
pip install llmrix-skill
```

### 시나리오 1: Agent 실행단 스킬 동기화 (Worker Mode)

Agent 실행 환경(예: 백그라운드 작업 노드 또는 컨테이너 시작 시)에서 특정 브랜치를 구성하여 모델 호출을 위한 최신 스킬을 가져옵니다.

```python
from llmrix.skill import GitSkillManager

def sync_skills_for_agent():
    # Manager 초기화, 원격 저장소 및 대상 브랜치 구성
    manager = GitSkillManager(
        repo_url="https://github.com/your-org/skill-repo.git",
        branch="develop",                # 강력 권장: 가져올 브랜치 지정 (예: main/develop/v1)
        workspace="/path/to/local/cache" # 로컬 캐시 경로
    )

    # 동기화 실행, 스킬이 위치한 파일 시스템 절대 경로 반환
    skills_path = manager.sync()
    print(f"✅ 스킬 플러그인 동기화 완료: {skills_path}")
    
    # 이후 Agent 프레임워크에서 skills_path 아래의 모듈을 동적으로 로드할 수 있습니다.
```

### 시나리오 2: Web 서버 관리 및 게시 (Management Mode)

Web API 서비스(예: FastAPI/Django 플러그인 마켓 백엔드)에서 `GitSkillManager`를 사용하여 사용자 업로드, 게시 및 버전 롤백을 처리합니다. 데이터베이스 지속성 및 동시 파일 잠금을 캡슐화합니다.

```python
from llmrix.skill import GitSkillManager
from llmrix.skill import MySQLStorage

# 1. 데이터베이스 어댑터 구성
def get_db_connection():
    # pymysql/MySQLdb 연결 객체 반환
    pass

storage = MySQLStorage(connection_factory=get_db_connection)

# 2. 관리단 전용 Manager 초기화
manager = GitSkillManager(
    repo_url="git@github.com:your-org/skill-repo.git",
    storage=storage
)

# 3. 사용자 업로드 스킬 게시
def publish_user_skill(user_id, uploaded_dir):
    skill = manager.publish(
        code="python_interpreter",      # 스킬 고유 코드
        source_dir=uploaded_dir,        # 사용자가 업로드한 압축 해제 디렉토리
        user_id=user_id,                # 현재 작업 사용자 ID (인증용)
        message="Initial release"       
    )
    print(f"🚀 게시 성공: {skill.name} v{skill.version}")

# 4. 버전 롤백
def rollback_skill(user_id):
    skill = manager.rollback(
        code="python_interpreter",
        target_version=1,
        user_id=user_id,
        message="Revert due to bugs"
    )
```

---

## 플러그인 패키지 사양 (Skill Package Specification)

표준 스킬 플러그인 패키지는 다음 파일을 포함하는 디렉토리입니다.

```text
my_awesome_skill/
├── SKILL.md      # 스킬 설명 및 메타데이터 (필수)
├── main.py       # 핵심 로직 (권장)
└── requirements.txt # 의존성 (선택 사항)
```

`SKILL.md`는 유효한 YAML Frontmatter 헤더를 포함해야 합니다.

```markdown
---
name: Web Scraper Pro
description: 동적 렌더링을 지원하는 강력한 웹 스크래핑 도구입니다.
category: Web & Search
---

이 스킬에 대한 자세한 Markdown 설명 문서가 여기에 들어갑니다...
```

---

## 모듈 아키텍처

필요한 하위 모듈을 직접 가져와서 더 낮은 수준으로 확장할 수 있습니다.

- `llmrix.skill.services`: `GitSkillManager`, `SkillPublisher`, `SkillSyncer`를 포함합니다.
- `llmrix.skill.storage`: `BaseStorage` 및 `MySQLStorage`를 포함합니다. 자신만의 MongoDB 또는 PostgreSQL 어댑터를 구현하려면 `BaseStorage`를 상속하세요.
- `llmrix.skill.git`: 저수준 Git 드라이버 라이브러리 `GitRepository`.
- `llmrix.skill.models`: 데이터 모델 `Skill` 및 `SkillVersion`.
