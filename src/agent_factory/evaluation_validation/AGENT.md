# Evaluation Validation Agent

모델 성능 평가 및 검증을 담당하는 에이전트

## 역할

- 모델 성능 메트릭 계산
- 교차 검증 수행
- 평가 리포트 생성
- 성능 기록 관리

## RACI 역할

**EVALUATION_VALIDATION 에이전트**는 다음 RACI 역할을 수행합니다:

| 역할 | 책임 |
|------|------|
| **RESPONSIBLE** (ML Engineer) | 평가 계획 수립, 메트릭 계산, 리포트 작성 |
| **ACCOUNTABLE** (Data Scientist) | 평가 계획 승인, 메트릭 기준 검토, 최종 성능 승인 |
| **CONSULTED** (Domain Expert) | 평가 방법론 자문 |

### RESPONSIBLE 역할

- 평가 데이터셋 준비
- 평가 메트릭 정의
- 교차 검증 전략 수립
- 평가 결과 분석

### ACCOUNTABLE 역할

- 평가 계획 검토
- 메트릭 적절성 확인
- 성능 목표 달성 여부 판정
- 최종 평가 승인

## 주요 기능

| 메서드 | 설명 |
|--------|------|
| `evaluate_model()` | 모델 성능 평가 |
| `cross_validate()` | K-Fold 교차 검증 |
| `generate_report()` | 평가 리포트 생성 |

## 성능 메트릭

| 메트릭 | 설명 |
|--------|------|
| `accuracy` | 정확도 |
| `precision` | 정밀도 |
| `recall` | 재현율 |
| `f1_score` | F1 점수 |
| `auc_roc` | AUC-ROC |
| `confusion_matrix` | 혼동 행렬 |

## 출력 데이터 구조

```json
{
  "accuracy": 0.85,
  "precision": 0.82,
  "recall": 0.78,
  "f1_score": 0.80,
  "confusion_matrix": {
    "true_positive": 100,
    "false_positive": 20,
    "true_negative": 80,
    "false_negative": 10
  }
}
```

## MCP 서버 의존성

- `filesystem` - 리포트 파일 저장
- `postgres` - 평가 메트릭 저장

## 표준 문서화

- 모델 평가 보고서 (Model Evaluation Report)
- 교차 검증 결과 (Cross Validation Results)
- 성능 벤치마크 문서
- 모델 비교 분석서
