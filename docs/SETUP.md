# Agent-Factory Setup Complete

## Environment
- Python: 3.12
- Virtual Environment: <agent_factory_directory>/venv
- PostgreSQL: 15-alpine (Optional - for database features)
- Database Password: whiteduck (default, can be changed in .env)

**참고**: PostgreSQL은 선택적입니다. Docker Compose, Docker, 또는 시스템 설치 중 하나를 선택할 수 있습니다.

## PostgreSQL (Optional)

PostgreSQL은 **선택적** 구성 요소입니다. 설치되지 않아도 MCP 서버와 에이전트 기능은 정상 작동합니다.

### PostgreSQL이 필요한 기능
- **데이터베이스 저장**: 배포 정보, 성능 메트릭, 학습 로그 저장
- **데이터 지속성**: 작업 결과, 평가 결과 영구 저장

### PostgreSQL이 없어도 되는 기능
- ✅ MCP 서버 동작
- ✅ 에이전트 간 통신
- ✅ 워크플로우 실행
- ✅ 파일 시스템 액세스
- ✅ 기억 저장

### PostgreSQL 설치 방법

#### 방법 1: Docker Compose (권장)

```bash
cd <agent_factory_directory>

# PostgreSQL 시작
docker compose up -d

# PostgreSQL 중지
docker compose down
```

**장점**:
- 간단하고 빠른 설치
- 데이터 볼륨으로 영속성 보장
- `docker-compose.yml` 포함됨

#### 방법 2: Docker (대안)

```bash
docker run -d \
  --name agent-postgres \
  -e POSTGRES_PASSWORD=whiteduck \
  -e POSTGRES_DB=postgres \
  -p 5432:5432 \
  postgres:15-alpine
```

#### 방법 3: 시스템 설치

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql

# macOS
brew install postgresql
brew services start postgresql

# 설정
sudo -u postgres psql -c "CREATE DATABASE monitoring;"
sudo -u postgres psql -c "CREATE DATABASE training;"
sudo -u postgres psql -c "CREATE DATABASE evaluation;"
```

### PostgreSQL 없이 실행

PostgreSQL이 설치되어 있지 않아도 시스템은 작동합니다:

```bash
# 설치 (DB 없이)
cd <agent_factory_directory>
./setup-mcp.sh

# 출력될 메시지:
# ⚠ PostgreSQL not found (neither systemctl nor docker)
#   Running without database support
# ✓ Dependencies installed
# ✓ OpenCode MCP configuration created
```

### 데이터베이스 구성

**PostgreSQL 데이터베이스** (선택적):
- `data` - Raw and processed data storage
- `training` - Processing checkpoints and logs
- `evaluation` - Evaluation metrics and results
- `monitoring` - Deployment and monitoring data

## Directory Structure
```
<home_directory>/
├── agent_factory/               # Agent source code
│   ├── mcp_server.py           # MCP Server entry point
│   ├── setup-mcp.sh            # MCP server setup
│   ├── opencode-integrate.sh    # OpenCode integration
│   └── docker-compose.yml       # PostgreSQL Docker Compose config
├── data/                       # Data files (CSV, JSON, etc.)
├── models/                      # Generated models/artifacts
├── checkpoints/                  # Processing checkpoints
├── results/                      # Experiment results
├── reports/                      # Evaluation reports
├── deployments/                  # Deployment configurations
└── logs/                         # Application logs
```

## Agents
1. **problem_definition** - Problem analysis and project planning
2. **data_collection** - Data gathering and preprocessing
3. **design_development** - System architecture design and code generation
4. **training_optimization** - Process optimization and tuning
5. **evaluation_validation** - Performance evaluation and validation
6. **deployment_monitoring** - Deployment and runtime monitoring
7. **coordinator** - Workflow orchestration

## Examples

모든 예제는 `examples/` 디렉토리에 있습니다:

- `work_agent_statistics_example.py` - Work-Agent 통계 예제 (신규)
- `basic_usage.py` - 기본 사용 예제
- `plan_approval_example.py` - 계획 승인 워크플로우 예제 1
- `plan_approval_example2.py` - 계획 승인 워크플로우 예제 2
- `toc_analysis_example.py` - TOC 최종 분석 예제
- `toc_optimization_example.py` - TOC 최적화 예제
- `raci_example.py` - RACI 매트릭스 예제
- `documentation_example.py` - 문서화 예제
- `workflow_templates_example.py` - 워크플로우 템플릿 예제

### 예제 실행

```bash
cd <agent_factory_directory>
source venv/bin/activate

# 예제 실행
python examples/work_agent_statistics_example.py
python examples/basic_usage.py
# ... 기타 예제들
```

## Usage

### Option 1: Direct Agent Execution
```bash
cd <agent_factory_directory>
source venv/bin/activate

# Run a specific agent
./run.sh coordinator "고객 관리 웹 앱 개발"

# Or run individual agents
./run.sh problem_definition
./run.sh data_collection
```

### Option 2: Plan Approval Workflow
```bash
cd <agent_factory_directory>
source venv/bin/activate

# 계획 승인 예제 실행
python examples/plan_approval_example2.py
```

### Option 3: MCP Server (Recommended for OpenCode)

#### PostgreSQL 없이 실행 (빠른 시작)

```bash
cd <agent_factory_directory>
source venv/bin/activate

# MCP 서버 시작 (DB 없이)
python -m agent_factory.mcp_server
```

#### PostgreSQL 포함하여 실행 (권장)

```bash
# 방법 1: Docker Compose (가장 쉬운 방법)
cd <agent_factory_directory>
docker compose up -d
source venv/bin/activate
python -m agent_factory.mcp_server

# 방법 2: 자동 설치 스크립트
cd <agent_factory_directory>
./setup-mcp.sh
source venv/bin/activate
python -m agent_factory.mcp_server

# 방법 3: OpenCode 통합
cd <agent_factory_directory>
./opencode-integrate.sh
# OpenCode 재시작하여 MCP 서버 자동 로드
```

### PostgreSQL 설정 (선택적)

PostgreSQL을 사용하려면 `.env` 파일에 비밀번호를 설정하세요:

```bash
# .env 파일 생성 또는 수정
echo "DB_PASSWORD=your_password" >> .env

# Docker Compose 사용 시
docker compose up -d
```

**기본 비밀번호**: `whiteduck`

## MCP Server Features

The MCP server exposes all agent functionality as tools:

- **execute_workflow** - Run complete development pipeline
- **define_problem** - Define problem scope and project plan
- **collect_data** - Collect from sources
- **preprocess_data** - Clean and validate
- **design_architecture** - Design system architecture
- **generate_implementation** - Generate implementation code
- **optimize_process** - Run process with optimization
- **evaluate_results** - Evaluate performance
- **deploy_system** - Deploy to production
- **monitor_system** - Monitor deployed system
- **submit_work_plan** - Submit work plan for approval
- **approve_work_plan** - Approve work plan
- **reject_work_plan** - Reject work plan
- **get_work_plan_status** - Get work plan status

See `MCP_README.md` for detailed documentation.

## Supported Project Types

This system supports various development workflows:

- **Web Applications** - REST APIs, Frontend, Backend
- **Data Pipelines** - ETL, Analytics, Reporting
- **Machine Learning** - Model training, optimization, deployment
- **Automation Scripts** - CI/CD, Task automation
- **Microservices** - Distributed systems, API integration

## Environment Variables

- `DB_PASSWORD=whiteduck` (set in <agent_factory_directory>/.env, Optional)
  - PostgreSQL 비밀번호
  - PostgreSQL 사용 시에만 필요
  - `.env` 파일에 설정 또는 환경 변수로 전달

## MCP Servers Used by Agents
- **filesystem** - File system access (Always available)
- **fetch** - HTTP/Fetch API for web requests (Always available)
- **postgres** - PostgreSQL database access (Optional, requires PostgreSQL)
- **memory** - Persistent memory storage (Always available)
- **sequential-thinking** - Enhanced reasoning (processing) (Optional)
- **git** - Git version control (Optional, requires Git)

### 필수 vs 선택적 서버

| MCP 서버 | 필수 | 설명 |
|------------|-------|------|
| filesystem | ✅ 필수 | 파일 읽기/쓰기 |
| fetch | ✅ 필수 | 웹 요청, 데이터 다운로드 |
| memory | ✅ 필수 | 기억 저장, 캐시 |
| postgres | ⚠ 선택적 | 데이터베이스 저장, 메트릭 저장 |
| sequential-thinking | ⚠ 선택적 | 향상된 추론 |
| git | ⚠ 선택적 | 버전 컨트롤 |

## 최신 업데이트

### 추가 기능

1. **Work-Agent 통계 (Work-Agent Statistics)**
    - Work별로 어떤 Agent들이 얼마나 작업했는지 통계 제공
    - 토큰 사용, 작업 시간, 에이전트 타입별 분석
    - API:
        - `toc.get_work_agent_statistics(work_id)` - 특정 Work 통계
        - `toc.get_work_agent_statistics()` - 전체 통계
        - `toc.format_work_agent_report(work_id)` - 형식화된 보고서
    - 예제: `examples/work_agent_statistics_example.py`

2. **계획 승인 (Plan Approval)**
    - RESPONSIBLE 에이전트가 계획을 제출하는 기능
    - ACCOUNTABLE 에이전트가 계획을 승인/거절하는 기능
    - 계획 내용: 접근 방식, 단계, 예상 시간, 리스크, 예상 결과
    - 예제: `examples/plan_approval_example.py`, `examples/plan_approval_example2.py`

3. **TOC 최종 분석 (Final Analysis)**
    - 모든 Work 완료 후 자동 분석
    - Token 효율 분석 (예상 vs 실제)
    - 에이전트 효율 분석
    - 병목 현상 분석
    - 개선 제안 자동 생성
    - 예제: `examples/toc_analysis_example.py`, `examples/toc_optimization_example.py`

4. **선택적 PostgreSQL 지원**
    - PostgreSQL은 선택적 구성 요소
    - 설치되지 않아도 MCP 서버와 에이전트 기능 정상 작동
    - PostgreSQL이 필요한 기능:
        - 데이터베이스 저장 (배포 정보, 성능 메트릭)
        - 데이터 지속성
    - 설치 방법:
        - Docker Compose (권장): `docker compose up -d`
        - Docker: `docker run -d -p 5432:5432 postgres:15-alpine`
        - 시스템: `sudo apt install postgresql`

### 추가 예제

- `examples/work_agent_statistics_example.py` - Work-Agent 통계 예제
- `examples/plan_approval_example2.py` - 계획 승인 워크플로우 예제
- `examples/toc_analysis_example.py` - TOC 최종 분석 예제
- `examples/toc_optimization_example.py` - TOC 최적화 예제
