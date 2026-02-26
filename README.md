# Agent Factory

Work 기반 멀티 에이전트 시스템 아키텍처

## 개요

이 시스템은 다음과 같은 핵심 기능을 제공합니다:

- **Work 기반 작업 분류**: 모든 작업을 Work 단위로 정의
- **다중 에이전트 배치**: 여러 에이전트 인스턴스를 배치하여 병렬 처리
- **RACI 매트릭스**: 책임 소재 명확화 및 협업 체계화
- **Skill 시스템**: Work 마다 동적으로 skill을 할당하고 효과를 모니터링
- **자동 문서화**: 작업 완료 후 표준화된 문서 자동 생성
- **TOC (제약이론) 기반 최적화**: 병목 현상 식별 및 처리량 최적화

## Skill 시스템

### 개요

Agent Factory v2에서는 **동적 Skill 시스템**을 도입하여 각 Work에 맞는 skill을 실시간으로 할당하고, Consulted 역할이 RACI 멤버들에게 skill을 배분할 수 있습니다.

### Skill 구조

```
.agent/skills/
├── problem-definition-skill/
│   └── SKILL.md
├── data-collection-skill/
│   └── SKILL.md
├── design-development-skill/
│   └── SKILL.md
├── training-optimization-skill/
│   └── SKILL.md
├── evaluation-validation-skill/
│   └── SKILL.md
├── deployment-monitoring-skill/
│   └── SKILL.md
└── toc-supervisor-skill/
    └── SKILL.md
```

### 사용 가능한 Skill

| Skill 이름 | 설명 | 사용 시나리오 |
|-----------|--------|---------------|
| `problem-definition-skill` | 문제 정의 및 요구사항 수집 | 프로젝트 시작, 범위 정의 |
| `data-collection-skill` | 데이터 수집 및 전처리 | ML/AI 데이터 파이프라인 |
| `design-development-skill` | 시스템 설계 및 코드 생성 | 아키텍처 설계, 개발 |
| `training-optimization-skill` | 모델 학습 및 최적화 | ML 모델 훈련, 하이퍼파라미터 튜닝 |
| `evaluation-validation-skill` | 모델 평가 및 검증 | 테스트, 성능 측정 |
| `deployment-monitoring-skill` | 배포 및 모니터링 | 프로덕션 배포, 운영 |
| `toc-supervisor-skill` | 워크플로우 오케스트레이션 및 최적화 | 병목 분석, 처리량 최적화 |

### 동적 Skill 할당

#### 자동 Skill 할당

Work 생성 시 자동으로 skill이 추천됩니다:

```python
work = orchestrator.create_work(
    name="Build REST API",
    description="Create a FastAPI backend for user management",
    work_type="design_development",
    agent_type="design_development",
    inputs={"tech_stack": "FastAPI, PostgreSQL"},
    tags=["web", "api", "backend"],
    auto_assign_skills=True  # 자동 skill 할당 활성화
)

# Work에 할당된 skill 확인
print(work.required_skills)
# ['design-development-skill', 'toc-supervisor-skill']

# RACI별 skill 할당 확인
print(work.skill_assignments)
# {
#   "responsible": {"agent_id": "dev_1", "skills": ["design-development-skill"], ...},
#   "accountable": {"agent_id": "senior_1", "skills": ["design-development-skill", "toc-supervisor-skill"], ...},
#   ...
# }
```

#### Consulted에 의한 Skill 할당

Consulted 역할의 에이전트가 skill을 검토하고 배분할 수 있습니다:

```python
# Consultant agent가 skill 할당 검토
assignment_result = await orchestrator.consult_and_assign_skills(
    work=work,
    consultant_agent_id="toc_supervisor_1"
)

# 결과 확인
print(assignment_result["recommended_skills"])
# ['design-development-skill', 'deployment-monitoring-skill']

print(assignment_result["skill_assignments"])
# 각 RACI 역할에 할당된 skill
```

### Skill Effectiveness 모니터링

TOC Supervisor는 각 skill의 효과를 모니터링합니다:

```python
# Workflow 완료 후 자동으로 skill effectiveness 분석
result = await orchestrator.execute_workflow(works=works)

# Skill effectiveness 보고서 확인
print(result.skill_effectiveness_analysis)
# {
#   "total_skills_loaded": 7,
#   "skills_with_metrics": 5,
#   "skill_recommendations": [
#     {"skill": "data-collection-skill", "action": "optimize", ...},
#     {"skill": "training-optimization-skill", "action": "maintain", ...}
#   ],
#   "top_performing_skill": {
#     "name": "design-development-skill",
#     "efficiency_score": 0.92,
#     "success_rate": 0.98,
#     "usage_count": 25
#   },
#   "detailed_effectiveness": {...}
# }
```

### Skill Effectiveness 메트릭

| 메트릭 | 설명 | 목표 |
|--------|------|------|
| Usage Count | Skill이 사용된 횟수 | 일관적 사용 |
| Success Rate | Skill 사용 시 성공률 | > 95% |
| Avg Tokens | Skill 사용당 평균 토큰 | 낮을수록 좋음 |
| Avg Duration | Skill 사용당 평균 시간 | 낮을수록 좋음 |
| Efficiency Score | 종합 효율 점수 (0-1) | > 0.8 |

### Skill 추천 알고리즘

SkillAnalyzer는 다음 요소를 고려하여 skill을 추천합니다:

1. **Work Type**: 기본적으로 work_type에 맞는 skill을 할당
2. **Description 분석**: 작업 설명의 키워드 매칭
3. **Tags**: 태그를 통한 skill 관련성 분석
4. **Inputs**: 입력 매개변수 분석

#### RACI 역할별 Skill 할당

| 역할 | Skill 카테고리 | 설명 |
|------|---------------|------|
| Responsible | CORE, SPECIALIZED | 주요 작업 수행 skill |
| Accountable | CORE, QUALITY | 승인 및 품질 보증 skill |
| Consulted | SUPPORT, SPECIALIZED, QUALITY | 자문 및 검토 skill |
| Informed | SUPPORT | 정보 수신을 위한 support skill |

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

## Skill 시스템 추가 기능

### Skill 검색 및 로드

```python
# 특정 skill 로드
skill_content = await orchestrator.skill_manager.get_skill_content("design-development-skill")

# 여러 skill 로드
skills = await orchestrator.skill_manager.load_all_skills([
    "design-development-skill",
    "deployment-monitoring-skill"
])
```

### Work의 Skill 정보 조회

```python
# Work에 할당된 skill 정보 조회
skill_info = await orchestrator.get_work_skills(work.work_id)

print(skill_info["required_skills"])
print(skill_info["skill_assignments"])
print(skill_info["skill_content"])
```

### Skill Effectiveness 조회

```python
# 전체 skill effectiveness
all_effectiveness = orchestrator.skill_manager.get_all_skill_effectiveness()

# 특정 skill effectiveness
skill_metrics = orchestrator.skill_manager.get_skill_effectiveness("design-development-skill")

# 결과
# {
#   "usage_count": 25,
#   "success_rate": 0.98,
#   "avg_tokens": 1800,
#   "avg_duration": 450.0,
#   "efficiency_score": 0.92
# }
```

### MCP 툴을 통한 Skill 할당

agent-factory MCP 서버는 다음 툴을 제공합니다:

| 툴 이름 | 설명 | 입력 |
|---------|------|------|
| `agent-factory_define_problem` | 문제 정의 | requirements |
| `agent-factory_collect_data` | 데이터 수집 | sources |
| `agent-factory_preprocess_data` | 데이터 전처리 | data_path |
| `agent-factory_design_architecture` | 아키텍처 설계 | problem_def |
| `agent-factory_generate_implementation` | 구현 코드 생성 | architecture |
| `agent-factory_optimize_process` | 프로세스 최적화 | config |
| `agent-factory_evaluate_results` | 결과 평가 | output_path, test_data_path |
| `agent-factory_deploy_system` | 시스템 배포 | artifact_path, config |
| `agent-factory_monitor_system` | 시스템 모니터링 | version |
| `analyze_work_for_skills` | Work 분석 및 Skill 추천 | work_name, work_description, work_type, tags |
| `assign_skills_to_work` | Work에 Skill 할당 | work_id, consultant_agent_id |
| `get_work_skills` | Work의 Skill 정보 조회 | work_id |
| `get_skill_effectiveness` | Skill 효과 메트릭 조회 | skill_name (optional) |

이 툴들은 각 skill의 allowed-tools 설정을 통해 제한됩니다.

### Skill 시스템 도입

**동적 Skill 할당**:
- Work 마다 자동으로 적절한 skill을 추천하고 할당
- Work 내용(description, tags, inputs)을 분석하여 skill 추천
- Consulted 역할이 skill 할당을 검토하고 조정 가능

**RACI 기반 Skill 배분**:
- 각 RACI 역할에 맞는 skill 카테고리 자동 할당
  - **Responsible**: CORE, SPECIALIZED skill (주요 작업 수행)
  - **Accountable**: CORE, QUALITY skill (승인 및 품질 보증)
  - **Consulted**: SUPPORT, SPECIALIZED, QUALITY skill (자문 및 검토)
  - **Informed**: SUPPORT skill (정보 수신)

**Skill Effectiveness 모니터링**:
- TOC Supervisor가 skill 효과를 실시간으로 모니터링
- 메트릭: 사용 횟수, 성공률, 평균 토큰, 평균 소요 시간, 효율 점수
- 자동으로 skill 개선/최적화/유지 권장사항 생성

**SkillAnalyzer**:
- Work를 분석하여 적절한 skill 추천
- 키워드 매칭, work type 매핑, tag 분석, inputs 분석
- 신뢰도(confidence) 점수로 정렬

**SkillManager**:
- SKILL.md 파일 로드 및 관리
- Skill effectiveness 기록 및 추적
- Skill content를 agent에 주입

### TOC 최종 분석 (Final Analysis) 기능 - Skill 확장

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

3. **Skill Effectiveness 분석** (신규)
   - 전체 skill 사용 현황
   - Skill별 성공률 및 효율 점수
   - 최고/최저 성능 skill 식별
   - Work 타입별 skill 사용 패턴 분석
   - Skill 개선/최적화 권장사항 생성

4. **병목 현상 분석**
   - 에이전트 수 조정 권장
   - 과부하: 에이전트 추가 필요
   - 과소활용: 에이전트 감축 필요

5. **개선 제안 자동 생성**
   - Token 최적화 방안 (프롬프트 간소화, context 재사용)
   - 에이전트 스케일링 권장
   - 처리 속도 향상 방안
   - **Skill 최적화 방안** (비효율적 skill 개선, underutilized skill 제거)

