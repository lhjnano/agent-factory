# Agent-Factory - MCP Server

Work 기반 멀티 에이전트 자동화 플랫폼 - TOC (제약이론) 기반 최적화, RACI 매트릭스, 자동 문서화 지원

## 빠른 시작

### 설치

**방법 1: 전체 설치 (PostgreSQL 포함)**

```bash
cd <agent_factory_directory>
./setup-mcp.sh
```

PostgreSQL은 다음 세 가지 방법으로 실행됩니다:
1. **Docker Compose** (권장): `docker-compose.yml` 파일 사용
2. **Docker**: `docker run` 명령으로 실행
3. **System**: 시스템 PostgreSQL 서비스 (설치되어 있는 경우)

PostgreSQL이 설치되어 있지 않으면 경고가 표시되고, 데이터베이스 없이도 실행됩니다.

---

**방법 2: Docker Compose로 PostgreSQL 실행 (권장)**

```bash
cd <agent_factory_directory>

# Docker Compose로 PostgreSQL 시작
docker compose up -d

# 또는 docker-compose (구버전)
docker-compose up -d

# PostgreSQL 중지
docker compose down
```

---

**방법 3: Docker로 PostgreSQL 실행**

```bash
docker run -d \
  --name agent-postgres \
  -e POSTGRES_PASSWORD=whiteduck \
  -e POSTGRES_DB=postgres \
  -p 5432:5432 \
  postgres:15-alpine
```

---

**방법 4: 시스템 PostgreSQL 사용**

```bash
# PostgreSQL 설치 (Ubuntu/Debian)
sudo apt install postgresql postgresql-contrib

# PostgreSQL 시작
sudo systemctl start postgresql
```

---

**설치 후 설정**

```bash
# MCP 서버 테스트
source venv/bin/activate
python -m agent_factory.mcp_server

# 또는 OpenCode에서 자동 로드됨
```

### OpenCode에서 사용하기

MCP 서버는 자동으로 OpenCode에 연결됩니다:

1. OpenCode 설정: `~/.config/opencode/mcp.json`
2. 자동으로 모든 툴 로드됨

## 시스템 아키텍처

### 핵심 구성 요소

| 구성 요소 | 설명 |
|-----------|------|
| **Work Queue** | 작업(WORK) 단위 큐잉 및 관리 |
| **Agent Pool** | 다중 에이전트 배치 및 관리 |
| **RACI Matrix** | 책임 소재 명확화 (Responsible, Accountable, Consulted, Informed) |
| **Documentation Manager** | 작업 완료 후 자동 문서 생성 |
| **TOC Supervisor** | 제약이론 기반 병목 분석 및 최적화 |

### Work 기반 아키텍처

모든 작업이 **Work** 단위로 정의됩니다:

```python
from agent_factory.core import Work, WorkPriority

work = Work(
    work_id="unique_id",
    name="작업 이름",
    description="작업 설명",
    work_type="design_development",
    agent_type="design_development",
    priority=WorkPriority.HIGH,
    dependencies=["other_work_id"],
    estimated_tokens=1000
)
```

### 다중 에이전트 배치

여러 에이전트 인스턴스를 배치하여 병렬 처리:

```python
from agent_factory.core import AgentPool, AgentInstance

pool = AgentPool()
agent = AgentInstance(
    agent_id="dev_agent_1",
    agent_type="design_development",
    capabilities=["design", "code_generation"],
    max_concurrent_works=3
)
pool.register_agent(agent)
```

### RACI 매트릭스

명확한 책임 분담:

```python
from agent_factory.core import RACI, RACIRole

raci = RACI()
raci.assign("work_1", "agent_a", RACIRole.RESPONSIBLE)
raci.assign("work_1", "agent_b", RACIRole.ACCOUNTABLE)
raci.assign("work_1", "agent_c", RACIRole.CONSULTED)
raci.assign("work_1", "agent_d", RACIRole.INFORMED)
```

## 계획 승인 (Plan Approval)

개발 작업 실행 전에 RESPONSIBLE 에이전트가 계획과 예상 결과를 보고하고, ACCOUNTABLE 에이전트의 승인을 받는 프로세스입니다.

### 계획 승인 워크플로우

```
1. Work 생성 → RACI 할당 (RESPONSIBLE, ACCOUNTABLE)
2. require_plan_approval = True 설정
3. RESPONSIBLE agent가 계획 제출
4. ACCOUNTABLE agent가 계획 검토 후 승인/거절
5. 승인된 경우에만 작업 실행
```

### 계획 승인 API

```python
# 계획 승인 요구 설정
orchestrator.set_work_plan_approval_required(work_id, True)

# 계획 제출 (RESPONSIBLE agent)
plan_content = {
    "approach": "FastAPI 사용",
    "steps": ["1. FastAPI 앱 초기화", "2. Pydantic 모델 정의", ...],
    "estimated_files": ["main.py", "models.py"],
    "estimated_hours": 4,
    "risks": ["데이터베이스 연결 지연"],
    "expected_results": "GET /api/users 응답 반환"
}
submit_result = orchestrator.submit_work_plan(
    work_id=work.work_id,
    plan_content=plan_content,
    proposed_by="dev_agent_1"
)

# 계획 승인 (ACCOUNTABLE agent)
approve_result = orchestrator.approve_work_plan(
    work_id=work.work_id,
    approved_by="senior_agent_1"
)

# 계획 거절 (ACCOUNTABLE agent)
reject_result = orchestrator.reject_work_plan(
    work_id=work.work_id,
    rejected_by="senior_agent_1",
    reason="계획이 너무 부족합니다."
)

# 계획 상태 조회
plan_status = orchestrator.get_work_plan_status(work_id)
```

### TOC (제약이론) 최적화

병목 식별 및 처리량 최적화:

```python
from agent_factory.core import TOCSupervisor

supervisor = TOCSupervisor(pool, queue, raci)
analysis = await supervisor.analyze_system()
optimization = await supervisor.optimize()
```

## 에이전트 타입

| 에이전트 타입 | Work 타입 | 설명 |
|---------------|-----------|------|
| `problem_definition` | `problem_definition` | 문제 정의 및 계획 수립 |
| `data_collection` | `data_collection` | 데이터 수집 및 전처리 |
| `design_development` | `design_development` | 시스템 설계 및 코드 구현 |
| `training_optimization` | `training_optimization` | 모델 학습 및 최적화 |
| `evaluation_validation` | `evaluation_validation` | 모델 평가 및 검증 |
| `deployment_monitoring` | `deployment_monitoring` | 배포 및 운영 모니터링 |
| `toc_supervisor` | - | 시스템 최적화 및 총괄 |

## 워크플로우 템플릿

### ML Pipeline

```python
result = await orchestrator.execute_workflow(
    template="ml_pipeline",
    parameters={
        "requirements": "고객 이탈 예측 모델",
        "data_sources": ["/data/customers.csv"]
    }
)
```

### Web Development

```python
result = await orchestrator.execute_workflow(
    template="web_development",
    parameters={
        "requirements": "REST API + React 프론트엔드"
    }
)
```

### API Development

```python
result = await orchestrator.execute_workflow(
    template="api_development",
    parameters={
        "api_spec": "User management API"
    }
)
```

### Data Processing

```python
result = await orchestrator.execute_workflow(
    template="data_processing",
    parameters={
        "sources": ["/data/raw", "https://api.example.com/data"]
    }
)
```

## 문서화

### 자동 문서화

```python
config = WorkflowConfig(auto_document=True)
orchestrator = MultiAgentOrchestrator(config)
result = await orchestrator.execute_workflow(...)
print(result.documents)  # 생성된 문서 ID 목록
```

### 문서 타입

| 문서 타입 | 설명 |
|-----------|------|
| `PROBLEM_DEFINITION` | 문제 정의서 |
| `PROJECT_PLAN` | 프로젝트 계획서 |
| `DATA_SPECIFICATION` | 데이터 명세서 |
| `ARCHITECTURE_DESIGN` | 아키텍처 설계서 |
| `MODEL_EVALUATION` | 모델 평가 보고서 |
| `DEPLOYMENT_GUIDE` | 배포 가이드 |
| `WORK_SUMMARY` | 작업 요약 |

## TOC 최적화

### 병목 탐지

시스템은 다음 병목을 자동 탐지:

- **Agent Capacity**: 에이전트 용량 부족
- **Work Dependency**: 작업 의존성 대기
- **Token Limit**: 토큰 사용량 한계
- **Queue Overflow**: 큐 오버플로우
- **Imbalanced Load**: 부하 불균형

### 최종 분석 및 개선 제안

모든 Work가 완료되면 TOC Supervisor가 자동으로 최종 분석을 수행합니다.

#### 분석 내용

1. **작업 요약**: 전체/완료/실패/성공률
2. **Token 효율 분석**:
   - 예상 vs 실제 토큰 사용량 비교
   - 작업 타입별 효율 분석
   - 절감 가능 토큰 계산
   - 비효율적인 작업 타입 식별

3. **에이전트 효율 분석**:
   - 에이전트별 성과 분석
   - 에이전트 타입별 집계
   - 성공률, 평균 토큰 사용량, 평균 처리 시간

4. **병목 현상 분석**:
   - 에이전트 과부하/과소활용 식별
   - 에이전트 수 조정 권장

5. **개선 제안**:
   - Token 최적화 (프롬프트 간소화, context 재사용)
   - 에이전트 스케일링 권장
   - 처리 속도 향상 방안
   - 프로세스 개선 제안

#### 최종 분석 사용 예시

```python
# Workflow 실행 완료 후 자동으로 최종 분석 수행
result = await orchestrator.execute_workflow(
    works=works,
    template="ml_pipeline",
    parameters={"requirements": "이미지 분류 모델"}
)

# 콘솔에 TOC 최종 분석 보고서 자동 출력
# - 작업 요약
# - Token 효율 분석
# - 병목 현상 분석
# - 개선 제안
# - 기준 대비 비교
# - 데이터 저장 위치
```

#### 데이터 저장 위치

TOC Supervisor는 분석 데이터를 두 곳에 저장합니다:

**Memory Storage (MCP memory 서버)**:
- `toc_baselines` - 기준 메트릭
- `toc_bottleneck_history` - 병목 현상 기록
- `toc_optimization_log` - 최적화 로그
- `toc_work_history` - 작업 기록

**Filesystem Storage** (`~/.agents_toc/`):
- `toc_baselines.json`
- `toc_bottleneck_history.json`
- `toc_optimization_log.json`
- `toc_work_history.json`
- `toc_final_report_<timestamp>.json`

#### 기준 대비 비교 (Trend Analysis)

```python
comparison = await toc_supervisor.compare_with_baselines()

# 결과:
{
    "improvements": [...],   # 개선된 지표
    "degradations": [...],  # 저하된 지표
    "stable": [...]         # 안정적 지표
}
```

#### MCP 세션 설정

```python
orchestrator.set_mcp_sessions(
    memory_session=memory_client,
    filesystem_session=filesystem_client
)
```
# - 작업 요약
# - Token 효율 분석
# - 병목 현상 분석
# - 개선 제안
```

### 자동 최적화

```python
config = WorkflowConfig(
    enable_toc=True,
    optimization_interval=60.0,
    auto_scale=True
)
```

### 최적화 보고서

```python
report = supervisor.get_optimization_report()
# {
#   "summary": {
#     "works_completed": 50,
#     "works_per_hour": 12.5,
#     "tokens_per_work": 2500,
#     "success_rate": 0.95
#   },
#   "current_constraint": {...},
#   "recommendations": [...]
# }
```

## 사용 예시

### 기본 사용

```bash
cd <agents_directory>
python examples/basic_usage.py
```

### 계획 승인 (Plan Approval)

```bash
cd <agents_directory>
python examples/plan_approval_example2.py
```

### RACI 매트릭스

```bash
python examples/raci_example.py
```

### TOC 최종 분석

```bash
cd <agents_directory>
python examples/toc_analysis_example.py
```

### TOC 최적화

```bash
python examples/toc_optimization_example.py
```

### 문서화

```bash
python examples/documentation_example.py
```

### 워크플로우 템플릿

```bash
python examples/workflow_templates_example.py
```

## TOC 총괄 에이전트

```bash
# 시스템 분석
python -m agent_factory.toc_supervisor.agent analyze

# 최적화 실행
python -m agent_factory.toc_supervisor.agent optimize

# 병목 현상 확인
python -m agent_factory.toc_supervisor.agent bottlenecks

# TOC 보고서 생성
python -m agent_factory.toc_supervisor.agent report

# 자동 모니터링
python -m agent_factory.toc_supervisor.agent monitor
```

## 구조

```
<agents_directory>/
├── core/                      # 코어 시스템
│   ├── work.py                # Work, WorkQueue, WorkPlan, PlanStatus
│   ├── raci.py                # RACI 매트릭스
│   ├── documentation.py       # 문서화 시스템
│   ├── agent_pool.py          # 에이전트 풀
│   ├── toc_supervisor.py      # TOC 총괄 (최종 분석 포함)
│   └── orchestrator.py        # 메인 오케스트레이터
├── coordinator/               # 코디네이터 에이전트
├── problem_definition/        # 문제 정의 에이전트
├── data_collection/           # 데이터 수집 에이전트
├── design_development/        # 설계/개발 에이전트
├── training_optimization/     # 학습/최적화 에이전트
├── evaluation_validation/     # 평가/검증 에이전트
├── deployment_monitoring/     # 배포/모니터링 에이전트
├── toc_supervisor/           # TOC 총괄 에이전트
├── examples/                 # 사용 예제
│   ├── basic_usage.py
│   ├── raci_example.py
│   ├── plan_approval_example2.py  # 계획 승인 예제
│   ├── toc_analysis_example.py      # TOC 최종 분석 예제
│   ├── toc_optimization_example.py
│   ├── documentation_example.py
│   └── workflow_templates_example.py
├── ARCHITECTURE.md           # 아키텍처 문서 (계획 승인, 최종 분석 포함)
├── MCP_README.md             # MCP README
└── install-all.sh            # 설치 스크립트
```

## 성능 최적화 가이드

### 에이전트 스케일링

```python
if utilization > 0.85:
    pool.scale_up("design_development", 2, factory)
elif utilization < 0.3:
    pool.scale_down("design_development", 1)
```

### 토큰 비용 절감

```python
config = WorkflowConfig(
    token_budget=500000,
    enable_toc=True
)
```

### 처리량 증대

```python
config = WorkflowConfig(
    max_concurrent_works=20,
    optimization_interval=30.0
)
```

## 환경 변수

```bash
# <agents_directory>/.env
DB_PASSWORD=whiteduck
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
```

## 요구사항

- Python 3.12
- PostgreSQL 16.11
- MCP 1.0.0+
- PyTorch 2.0+ (선택사항, ML 프로젝트용)

## 기여

이 프로젝트는 OpenCode 생태계의 일부입니다.

## 최신 업데이트

- **계획 승인 (Plan Approval)**: RESPONSIBLE 에이전트가 계획을 제출하고 ACCOUNTABLE 에이전트가 승인하는 프로세스 추가
- **TOC 최종 분석**: 모든 Work 완료 후 자동으로 토큰 효율, 에이전트 효율, 병목 현상 분석
- **개선 제안 자동 생성**: Token 최적화, 에이전트 스케일링, 처리 속도 향상 방안 자동 제안

## 요구사항

- Python 3.12
- PostgreSQL 16.11
- MCP 1.0.0+
- PyTorch 2.0+ (선택사항, ML 프로젝트용)

## 설치된 Python 패키지

- mcp==1.26.0
- pandas==3.0.0
- numpy==2.4.2
- torch==2.10.0+cpu
- scikit-learn==1.8.0
- python-dotenv==1.2.1
