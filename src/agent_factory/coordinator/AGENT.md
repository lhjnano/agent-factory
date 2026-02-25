# Coordinator Agent

워크플로우 총괄 및 에이전트 간 조율을 담당하는 코디네이터 에이전트

## 역할

- 전체 워크플로우 실행 관리
- 에이전트 간 의존성 관리
- 세션 및 상태 관리
- 결과 취합 및 저장

## RACI 역할

**COORDINATOR**는 WORKFLOW 관리를 담당하며, 각 WORK에 다음 RACI 역할을 할당합니다:

| 에이전트 타입 | WORK에서의 RACI 역할 | 책임 |
|---------------|---------------------|------|
| `problem_definition` | RESPONSIBLE | 문제 정의, 계획 수립 |
| `design_development` (Junior) | RESPONSIBLE | 계획 제출, 작업 실행 |
| `design_development` (Senior) | ACCOUNTABLE | 계획 승인, 최종 책임 |
| `evaluation_validation` | CONSULTED | 품질 검토, 의견 제공 |
| `deployment_monitoring` | INFORMED | 배포 결과 통보 |

### 계획 승인 워크플로우

1. **RESPONSIBLE 에이전트** (Junior 개발자):
   - 작업에 대한 계획 수립
   - 계획 제출 (접근 방식, 단계, 예상 결과)
   - 승인 후 작업 실행

2. **ACCOUNTABLE 에이전트** (Senior 개발자/리뷰어):
   - 제출된 계획 검토
   - 계획 승인 또는 거절
   - 거절 시 수정 요청 및 사유 제공

3. **승인 시**: 작업 실행 가능
4. **거절 시**: RESPONSIBLE 에이전트가 계획 수정 후 재제출

## 주요 기능

| 메서드 | 설명 |
|--------|------|
| `connect_servers()` | MCP 서버 연결 |
| `initialize_agents()` | 하위 에이전트 초기화 |
| `execute_workflow()` | 전체 워크플로우 실행 |
| `_run_phase()` | 개별 페이즈 실행 |
| `monitor_workflow_status()` | 워크플로우 상태 모니터링 |

## 워크플로우 순서

```
1. problem_definition    → 문제 정의
2. data_collection       → 데이터 수집/전처리
3. design_development    → 아키텍처 설계/코드 생성
4. training_optimization → 모델 학습/최적화
5. evaluation_validation → 성능 평가/검증
6. deployment_monitoring → 배포/모니터링
```

## MCP 서버 의존성

- `memory` - 워크플로우 상태 저장
- `filesystem` - 결과 파일 저장

## 사용 예시

```python
coordinator = AgentCoordinator()
await coordinator.connect_servers()
await coordinator.initialize_agents()
result = await coordinator.execute_workflow("고객 이탈 예측 모델 개발")
```
