# Problem Definition Agent

프로젝트 문제 정의 및 계획 수립을 담당하는 에이전트

## 역할

- 사용자 요구사항 분석
- 문제 범위 정의
- 성공 기준 설정
- 프로젝트 계획 수립

## RACI 역할

**PROBLEM_DEFINITION 에이전트**는 다음 RACI 역할을 수행합니다:

| 역할 | 책임 |
|------|------|
| **RESPONSIBLE** | 문제 정의, 요구사항 분석, 계획 수립 |
| **ACCOUNTABLE** (Senior/Coordinator) | 문제 정의 승인, 최종 계획 승인 |

### RESPONSIBLE 역할

- 사용자 요구사항 파악
- 문제 범위 명확화
- 프로젝트 계획 초안 작성
- SUCCESS_CRITERIA 정의

### ACCOUNTABLE 역할

- 문제 정의 검토
- 요구사항 충분 여부 확인
- 계획 현실성 검토
- 최종 승인

## 주요 기능

| 메서드 | 설명 |
|--------|------|
| `define_problem()` | 문제 정의 및 범위 설정 |
| `create_project_plan()` | 단계별 프로젝트 계획 생성 |

## 출력 데이터 구조

### Problem Definition
```json
{
  "problem_statement": "문제 설명",
  "objectives": ["목표1", "목표2"],
  "constraints": ["제약사항"],
  "success_criteria": ["성공 기준"],
  "stakeholders": ["이해관계자"]
}
```

### Project Plan
```json
{
  "phases": [
    {"name": "phase_name", "estimated_days": 3, "dependencies": []}
  ],
  "timeline": 28
}
```

## MCP 서버 의존성

- `memory` - 문제 정의 데이터 저장

## 표준 문서화

- 문제 정의서 (Problem Statement)
- 프로젝트 계획서 (Project Plan)
- 요구사항 명세서 (Requirements Specification)
