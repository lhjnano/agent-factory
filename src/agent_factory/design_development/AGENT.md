# Design Development Agent

시스템 아키텍처 설계 및 코드 구현을 담당하는 에이전트

## 역할

- 시스템 아키텍처 설계
- 모델 구조 정의
- 코드 템플릿 생성
- 학습 스크립트 작성
- Git 커밋 관리

## RACI 역할

**DESIGN_DEVELOPMENT 에이전트**는 다음 RACI 역할을 수행합니다:

| 역할 | 에이전트 유형 | 책임 |
|------|---------------|------|
| **RESPONSIBLE** | Junior Developer | 작업 실행, 계획 제출 |
| **ACCOUNTABLE** | Senior Developer | 계획 승인, 최종 책임 |

### RESPONSIBLE 역할 (Junior Developer)

작업 실행 전에 계획을 제출해야 합니다:

```python
# 계획 제출
plan_content = {
    "approach": "FastAPI 사용",
    "steps": [
        "1. FastAPI 앱 초기화",
        "2. Pydantic 모델 정의",
        "3. /api/users 엔드포인트 구현",
        "4. 데이터베이스 연결",
        "5. 단위 테스트 작성"
    ],
    "estimated_files": ["main.py", "models.py", "routers.py"],
    "estimated_hours": 4,
    "risks": ["데이터베이스 연결 지연 가능성"],
    "expected_results": "GET /api/users 요청 시 JSON 응답 반환"
}

orchestrator.submit_work_plan(
    work_id=work.work_id,
    plan_content=plan_content,
    proposed_by="junior_dev_1"
)
```

### ACCOUNTABLE 역할 (Senior Developer)

제출된 계획을 검토하고 승인/거절:

```python
# 계획 검토 후 승인
orchestrator.approve_work_plan(
    work_id=work.work_id,
    approved_by="senior_dev_1"
)

# 또는 계획 거절
orchestrator.reject_work_plan(
    work_id=work.work_id,
    rejected_by="senior_dev_1",
    reason="계획이 너무 부족합니다. 더 상세한 단계와 예상 결과가 필요합니다."
)
```

## 주요 기능

| 메서드 | 설명 |
|--------|------|
| `design_architecture()` | 시스템 아키텍처 설계 |
| `generate_code()` | 모델 코드 생성 |
| `create_training_script()` | 학습 스크립트 생성 |
| `commit_changes()` | Git 커밋 실행 |

## 아키텍처 구조

```json
{
  "model_type": "neural_network",
  "input_features": [],
  "output_size": 1,
  "hidden_layers": [
    {"size": 128, "activation": "relu", "dropout": 0.2},
    {"size": 64, "activation": "relu", "dropout": 0.3},
    {"size": 32, "activation": "relu", "dropout": 0.4}
  ],
  "optimizer": "adam",
  "learning_rate": 0.001
}
```

## 생성 파일

- `src/model.py` - 모델 정의
- `src/train.py` - 학습 스크립트

## MCP 서버 의존성

- `filesystem` - 코드 파일 저장
- `git` - 버전 관리

## 표준 문서화

- 아키텍처 설계서 (Architecture Design Document)
- API 명세서 (API Specification)
- 기술 스택 문서 (Tech Stack Document)
- 코드 스타일 가이드
