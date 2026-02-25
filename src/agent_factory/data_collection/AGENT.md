# Data Collection Agent

데이터 수집 및 전처리를 담당하는 에이전트

## 역할

- 다양한 소스에서 데이터 수집
- 데이터 품질 검증
- 데이터 전처리 및 정제
- 통계 정보 생성

## RACI 역할

**DATA_COLLECTION 에이전트**는 다음 RACI 역할을 수행합니다:

| 역할 | 책임 |
|------|------|
| **RESPONSIBLE** | 데이터 소스 식별, 수집 계획 수립, 전처리 실행 |
| **ACCOUNTABLE** (Data Engineer) | 수집 계획 승인, 품질 검토 |

### RESPONSIBLE 역할

- 데이터 소스 조사 및 식별
- 데이터 수집 방법 결정
- ETL 파이프라인 설계
- 전처리 로직 구현

### ACCOUNTABLE 역할

- 데이터 소스 적절성 검토
- 수집 계획 승인
- 데이터 품질 기준 확인
- 최종 데이터 셋 승인

## 주요 기능

| 메서드 | 설명 |
|--------|------|
| `collect_data()` | 다양한 소스에서 데이터 수집 |
| `preprocess_data()` | 데이터 전처리 및 정제 |
| `validate_data_quality()` | 데이터 품질 검증 |

## 지원 데이터 소스

- HTTP/HTTPS URL (API, 웹 스크래핑)
- CSV 파일
- JSON 파일
- Parquet 파일

## 출력 데이터 구조

### Data Stats
```json
{
  "original_rows": 10000,
  "original_columns": 50,
  "missing_values": {"col1": 10, "col2": 5},
  "data_types": {"col1": "int64", "col2": "float64"},
  "cleaned_rows": 9500,
  "rows_removed": 500
}
```

### Quality Report
```json
{
  "completeness": 95.0,
  "uniqueness": 100,
  "consistency": {"col1": 50, "col2": 100}
}
```

## MCP 서버 의존성

- `fetch` - 외부 API/URL 데이터 수집
- `filesystem` - 로컬 파일 읽기/쓰기
- `memory` - 통계 정보 저장

## 표준 문서화

- 데이터 명세서 (Data Specification)
- 데이터 품질 보고서 (Data Quality Report)
- ETL 파이프라인 문서
