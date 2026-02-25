# Multi-Agent Development System Architecture

Work 기반 멀티 에이전트 시스템 아키텍처

## 개요

이 시스템은 다음과 같은 핵심 기능을 제공합니다:

- **Work 기반 작업 분류**: 모든 작업을 Work 단위로 정의
- **다중 에이전트 배치**: 여러 에이전트 인스턴스를 배치하여 병렬 처리
- **RACI 매트릭스**: 책임 소재 명확화 및 협업 체계화
- **자동 문서화**: 작업 완료 후 표준화된 문서 자동 생성
- **TOC (제약이론) 기반 최적화**: 병목 현상 식별 및 처리량 최적화

## 아키텍처 다이어그램

```
┌─────────────────────────────────────────────────────────────────┐
│                    MultiAgentOrchestrator                        │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  WorkQueue  │  │  AgentPool  │  │   DocumentationManager  │ │
│  └──────┬──────┘  └──────┬──────┘  └─────────────┬───────────┘ │
│         │                │                       │              │
│         └────────────────┼───────────────────────┘              │
│                          │                                       │
│  ┌───────────────────────┴───────────────────────────────────┐ │
│  │                    TOCSupervisor                            │ │
│  │  - 병목 분석  - 처리량 계산  - 최적화 실행  - 제약 식별   │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                          │                                       │
│  ┌───────────────────────┴───────────────────────────────────┐ │
│  │                       RACI Matrix                           │ │
│  │  R(Responsible) - A(Accountable) - C(Consulted) - I(Informed)│
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                           │
       ┌───────────────────┼───────────────────┐
       ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────┐
│   Agent 1    │   │   Agent 2    │   │   Agent N    │
│  (Instance)  │   │  (Instance)  │   │  (Instance)  │
└──────────────┘   └──────────────┘   └──────────────┘
```

## 핵심 구성 요소

### 1. Work (작업 단위)

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
    inputs={"key": "value"},
    estimated_tokens=1000,
    require_plan_approval=True  # 계획 승인 요구
)
```

### 2. AgentPool (에이전트 풀)

```python
from agent_factory.core import AgentPool, AgentInstance, AgentStatus

pool = AgentPool()

agent = AgentInstance(
    agent_id="agent_1",
    agent_type="design_development",
    capabilities=["design", "code_generation"],
    max_concurrent_works=3
)

pool.register_agent(agent)
```

### 3. RACI 매트릭스

```python
from agent_factory.core import RACI, RACIRole

raci = RACI()
raci.assign("work_1", "agent_a", RACIRole.RESPONSIBLE)
raci.assign("work_1", "agent_b", RACIRole.ACCOUNTABLE)
raci.assign("work_1", "agent_c", RACIRole.CONSULTED)
raci.assign("work_1", "agent_d", RACIRole.INFORMED)
```

### 4. TOC Supervisor (총괄 에이전트)

```python
from agent_factory.core import TOCSupervisor

supervisor = TOCSupervisor(
    agent_pool=pool,
    work_queue=queue,
    raci=raci
)

analysis = await supervisor.analyze_system()
optimization = await supervisor.optimize()
report = supervisor.get_optimization_report()
```

### 5. 계획 승인 (Plan Approval)

```python
# Work 생성 및 RACI 할당
work = orchestrator.create_work(
    name="Build API",
    description="REST API 구현",
    work_type="design_development",
    agent_type="design_development",
    inputs={"endpoint": "/api/users"},
    priority=WorkPriority.HIGH
)

orchestrator.assign_raci(
    work_id=work.work_id,
    responsible=["dev_agent"],      # 계획 제출 및 작업 실행
    accountable="senior_agent",      # 계획 승인
    consulted=[],
    informed=[]
)

# 계획 승인 요구 설정
orchestrator.set_work_plan_approval_required(work.work_id, True)

# RESPONSIBLE agent가 계획 제출
plan = {
    "approach": "FastAPI 사용",
    "steps": [
        "1. FastAPI 앱 초기화",
        "2. Pydantic 모델 정의",
        "3. /api/users 엔드포인트 구현"
    ],
    "estimated_files": ["main.py", "models.py"],
    "estimated_hours": 4,
    "risks": ["DB 연결 지연 가능성"],
    "expected_results": "JSON 응답 반환"
}

submit_result = orchestrator.submit_work_plan(
    work_id=work.work_id,
    plan_content=plan,
    proposed_by="dev_agent"
)

# ACCOUNTABLE agent가 계획 검토 후 승인
approve_result = orchestrator.approve_work_plan(
    work_id=work.work_id,
    approved_by="senior_agent"
)

# 이제 작업 실행 가능
```

### 6. 문서화 시스템

```python
from agent_factory.core import DocumentationManager, DocumentType

doc_manager = DocumentationManager()

doc = doc_manager.create_document(
    document_type=DocumentType.ARCHITECTURE_DESIGN,
    work_id="work_1",
    agent_id="agent_1",
    sections={
        "overview": "시스템 개요",
        "components": "구성 요소",
        "data_flow": "데이터 흐름"
    }
)
```

## Work 타입 및 에이전트 매핑

| Work 타입 | 에이전트 타입 | 설명 |
|-----------|---------------|------|
| `problem_definition` | ProblemDefinitionAgent | 문제 정의 |
| `data_collection` | DataCollectionAgent | 데이터 수집/전처리 |
| `design_development` | DesignDevelopmentAgent | 설계/개발 |
| `training_optimization` | TrainingOptimizationAgent | 학습/최적화 |
| `evaluation_validation` | EvaluationValidationAgent | 평가/검증 |
| `deployment_monitoring` | DeploymentMonitoringAgent | 배포/모니터링 |

## 워크플로우 템플릿

### ML Pipeline

```python
orchestrator = MultiAgentOrchestrator()

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

## TOC (제약이론) 기반 최적화

### 병목 탐지

시스템은 다음과 같은 병목을 자동으로 탐지합니다:

- **Agent Capacity**: 에이전트 용량 부족
- **Work Dependency**: 작업 의존성으로 인한 대기
- **Token Limit**: 토큰 사용량 한계
- **Queue Overflow**: 큐 오버플로우
- **Imbalanced Load**: 부하 불균형

### 최종 분석 및 개선 제안

모든 Work가 완료되면 TOC Supervisor는 자동으로 다음 분석을 수행합니다:

1. **Token 효율 분석**
   - 예상 vs 실제 토큰 사용량 비교
   - 작업 타입별 효율 분석
   - 절감 가능 토큰 계산
   - 비효율적인 작업 타입 식별

2. **에이전트 효율 분석**
   - 에이전트별 성과 분석
   - 에이전트 타입별 집계
   - 성공률, 평균 토큰 사용량, 평균 처리 시간

3. **병목 현상 분석**
   - 에이전트 과부하/과소활용 식별
   - 에이전트 수 조정 권장

4. **개선 제안 생성**
   - Token 최적화 방안
   - 에이전트 스케일링 권장
   - 처리 속도 향상 방안
   - 프로세스 개선 제안

### 최종 분석 사용 예시

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
```

### 최종 분석 API

```python
# Work 완료 시 기록
toc_supervisor.record_work_completion(work, result)

# 최종 분석 생성
analysis = await toc_supervisor.generate_final_analysis(completed_works)

# 포맷된 보고서 생성
report = toc_supervisor.format_final_report(analysis)
```

### 자동 최적화

```python
# 자동 최적화 활성화
config = WorkflowConfig(
    enable_toc=True,
    optimization_interval=60.0,  # 60초마다 최적화
    auto_scale=True
)

orchestrator = MultiAgentOrchestrator(config)
```

### 최적화 리포트

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

## RACI 역할 정의

| 역할 | 설명 | 책임 |
|------|------|------|
| **R**esponsible | 실행 담당 | 작업 수행, 계획 제출 |
| **A**ccountable | 최종 책임 | 승인/거부, 계획 검토 |
| **C**onsulted | 자문 | 의견 제공 |
| **I**nformed | 정보 수신 | 결과 통보 |

## 계획 승인 (Plan Approval) 워크플로우

개발 작업 실행 전에 RESPONSIBLE 에이전트가 계획과 예상 결과를 보고하고, ACCOUNTABLE 에이전트의 승인을 받는 프로세스입니다.

### 계획 승인 단계

1. **Work 생성 및 RACI 할당**
   - Work 생성 시 RESPONSIBLE, ACCOUNTABLE 에이전트 지정
   - `require_plan_approval = True` 설정으로 계획 승인 요구

2. **계획 제출 (RESPONSIBLE)**
   - RESPONSIBLE 에이전트가 계획 제출
   - 계획 내용: 접근 방식, 단계, 예상 파일, 예상 시간, 리스크, 예상 결과

3. **계획 검토 및 승인 (ACCOUNTABLE)**
   - ACCOUNTABLE 에이전트가 계획 검토
   - 승인 또는 거절 결정
   - 거절 시 재작성 요청 및 사유 전달

4. **작업 실행**
   - 승인된 계획에 따라 작업 실행
   - 실행 중 문제 발생 시 계획과의 차이점 보고

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
    reason="계획이 너무 부족합니다. 더 상세한 단계 필요."
)

# 계획 상태 조회
plan_status = orchestrator.get_work_plan_status(work_id)
```

### WorkStatus 추가

- `PLAN_SUBMITTED`: 계획이 제출됨 (ACCOUNTABLE 승인 대기)
- `PLAN_APPROVED`: 계획이 승인됨 (작업 실행 가능)

### PlanStatus 열거형

- `NOT_REQUIRED`: 계획 승인 불필요
- `PENDING`: 승인 대기 중
- `APPROVED`: 승인됨
- `REJECTED`: 거절됨

## 문서화 표준

### 문서 유형

- `PROBLEM_DEFINITION`: 문제 정의서
- `PROJECT_PLAN`: 프로젝트 계획서
- `DATA_SPECIFICATION`: 데이터 명세서
- `ARCHITECTURE_DESIGN`: 아키텍처 설계서
- `MODEL_EVALUATION`: 모델 평가 보고서
- `DEPLOYMENT_GUIDE`: 배포 가이드
- `WORK_SUMMARY`: 작업 요약

### 자동 문서화

```python
config = WorkflowConfig(auto_document=True)
orchestrator = MultiAgentOrchestrator(config)

# 작업 완료 시 자동으로 문서 생성
result = await orchestrator.execute_workflow(...)
print(result.documents)  # 생성된 문서 ID 목록
```

## 디렉토리 구조

```
agents/
├── core/
│   ├── __init__.py
│   ├── work.py           # Work, WorkQueue 정의
│   ├── raci.py           # RACI 매트릭스
│   ├── documentation.py  # 문서화 시스템
│   ├── agent_pool.py     # 에이전트 풀 관리
│   ├── toc_supervisor.py # TOC 총괄 에이전트
│   └── orchestrator.py   # 메인 오케스트레이터
├── coordinator/
│   ├── agent.py
│   └── AGENT.md
├── problem_definition/
│   ├── agent.py
│   └── AGENT.md
├── data_collection/
│   ├── agent.py
│   └── AGENT.md
├── design_development/
│   ├── agent.py
│   └── AGENT.md
├── training_optimization/
│   ├── agent.py
│   └── AGENT.md
├── evaluation_validation/
│   ├── agent.py
│   └── AGENT.md
├── deployment_monitoring/
│   ├── agent.py
│   └── AGENT.md
└── MCP_README.md
```

## 시작하기

```python
import asyncio
from agent_factory.core import (
    MultiAgentOrchestrator, WorkflowConfig,
    AgentInstance, Work, WorkPriority
)

async def main():
    config = WorkflowConfig(
        max_concurrent_works=10,
        enable_toc=True,
        auto_document=True
    )
    
    orchestrator = MultiAgentOrchestrator(config)
    
    agent = AgentInstance(
        agent_id="dev_agent_1",
        agent_type="design_development",
        capabilities=["design", "code_generation", "testing"],
        max_concurrent_works=3
    )
    orchestrator.register_agent(agent)
    
    result = await orchestrator.execute_workflow(
        template="ml_pipeline",
        parameters={"requirements": "이미지 분류 모델"}
    )
    
    print(f"Completed: {result.works_completed}/{result.works_total}")
    print(f"Tokens used: {result.total_tokens}")
    print(f"Documents: {result.documents}")

asyncio.run(main())
```

## 성능 최적화 가이드

### 1. 에이전트 스케일링

```python
# 부하에 따른 자동 스케일링
if utilization > 0.85:
    pool.scale_up("design_development", 2, agent_factory)
elif utilization < 0.3:
    pool.scale_down("design_development", 1)
```

### 2. 토큰 비용 절감

```python
config = WorkflowConfig(
    token_budget=500000,
    enable_toc=True  # 토큰 사용량 모니터링
)
```

### 3. 처리량 증대

```python
# 병렬 처리 최적화
config = WorkflowConfig(
    max_concurrent_works=20,
    optimization_interval=30.0
)
```

## 최신 업데이트 (v1.1)

### 계획 승인 (Plan Approval) 기능

- **RESPONSIBLE 에이전트**: 작업 실행 전 계획 제출
  - 접근 방식
  - 실행 단계
  - 예상 파일
  - 예상 소요 시간
  - 리스크 식별
  - 예상 결과

- **ACCOUNTABLE 에이전트**: 계획 검토 및 승인/거절
  - 계획의 명확성 검토
  - 현실성 확인
  - 승인: 작업 진행 허가
  - 거절: 수정 요청 및 사유 제공

### TOC 최종 분석 (Final Analysis) 기능

모든 Work 완료 후 자동으로 다음 분석 수행:

1. **Token 효율 분석**
   - 예상 vs 실제 토큰 비교
   - 작업 타입별 효율 분석
   - 절감 가능 토큰 계산
   - 비효율적인 작업 타입 식별

2. **에이전트 효율 분석**
   - 에이전트별 성과 분석
   - 성공률, 평균 토큰 사용량, 평균 처리 시간
   - 과부하/과소활용 식별

3. **병목 현상 분석**
   - 에이전트 수 조정 권장
   - 과부하: 에이전트 추가 필요
   - 과소활용: 에이전트 감축 필요

4. **개선 제안 자동 생성**
   - Token 최적화 방안 (프롬프트 간소화, context 재사용)
   - 에이전트 스케일링 권장
   - 처리 속도 향상 방안
   - 성능 개선 제안

### 주요 추가 API

```python
# 계획 승인
orchestrator.set_work_plan_approval_required(work_id, True)
orchestrator.submit_work_plan(work_id, plan_content, responsible_agent)
orchestrator.approve_work_plan(work_id, accountable_agent)
orchestrator.reject_work_plan(work_id, accountable_agent, reason)
plan_status = orchestrator.get_work_plan_status(work_id)

# TOC 최종 분석
analysis = await toc_supervisor.generate_final_analysis(completed_works)
report = toc_supervisor.format_final_report(analysis)

# 데이터 저장
await toc_supervisor.save_final_analysis(analysis)
comparison = await toc_supervisor.compare_with_baselines()

# MCP 세션 설정
orchestrator.set_mcp_sessions(
    memory_session=memory_client,
    filesystem_session=filesystem_client
)
```

## 데이터 저장 및 기준 비교

### 저장 위치

TOC Supervisor는 분석 데이터를 영구적으로 저장합니다:

**Memory Storage (MCP memory 서버)**:
- 빠른 접근, 세션 간 유지
- 저장 키: `toc_baselines`, `toc_bottleneck_history`, `toc_optimization_log`, `toc_work_history`

**Filesystem Storage** (`~/.agents_toc/`):
- 영구 보관, 히스토리 추적
- 파일: `toc_baselines.json`, `toc_bottleneck_history.json`, `toc_optimization_log.json`, `toc_work_history.json`

### 기준 대비 비교

저장된 기준 데이터와 현재 데이터 비교하여 트렌드 분석:

```python
comparison = await toc_supervisor.compare_with_baselines()

# 결과:
{
    "improvements": [...],   # 개선된 지표 (+5% 이상)
    "degradations": [...],  # 저하된 지표 (-5% 이상)
    "stable": [...]         # 안정적 지표 (±5% 미만)
}
```

### 데이터 기반 개선

- 개선 추세 유지 전략
- 저하 원인 분석
- 안정적 지표 모니터링
