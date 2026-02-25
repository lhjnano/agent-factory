# TOC Supervisor Agent

제약이론(TOC) 기반 시스템 최적화 및 병목 관리를 담당하는 총괄 에이전트

## 역할

- 시스템 병목 현상 식별 및 분석
- 처리량(Throughput) 최적화
- 에이전트 스케일링 권장
- 토큰 비용 절감
- 전체 워크플로우 총괄

## TOC (제약이론) 원칙

### 5단계 포커싱 프로세스

1. **제약 식별 (Identify Constraint)**: 시스템의 병목 찾기
2. **제약 활용 (Exploit Constraint)**: 제약 요소 최대한 활용
3. **다른 것 조율 (Subordinate Others)**: 제약에 맞춰 다른 요소 조정
4. **제약 상향 (Elevate Constraint)**: 제약 완화/제거
5. **반복 (Repeat)**: 새로운 제약 발생 시 반복

## 주요 기능

| 메서드 | 설명 |
|--------|------|
| `analyze_system()` | 전체 시스템 분석 및 병목 식별 |
| `optimize_system()` | 시스템 최적화 실행 |
| `identify_bottlenecks()` | 병목 현상 식별 |
| `calculate_throughput()` | 처리량 계산 |
| `identify_constraint()` | 현재 제약 요소 식별 |
| `recommend_scaling()` | 스케일링 권장 사항 생성 |
| `monitor_and_optimize()` | 자동 모니터링 및 최적화 |
| `generate_toc_report()` | TOC 최적화 보고서 생성 |

## 병목 현상 유형

| 유형 | 설명 | 심각도 계산 |
|------|------|-----------|
| `agent_capacity` | 에이전트 용량 부족 | `0.8 ~ 1.0` |
| `work_dependency` | 작업 의존성으로 인한 대기 | `blocked_count / 10` |
| `token_limit` | 토큰 사용량 한계 도달 | `0.8` |
| `queue_overflow` | 큐 오버플로우 | `pending / 100` |
| `imbalanced_load` | 부하 불균형 | `0.5` |

## 최적화 전략

### 에이전트 스케일링

```python
# 과부하 시 스케일 업
if utilization > 0.85:
    pool.scale_up(agent_type, 2, factory)

# 저활용 시 스케일 다운
if utilization < 0.3:
    pool.scale_down(agent_type, 1)
```

### 토큰 최적화

- 프롬프트 최적화로 토큰 사용량 감소
- 토큰 캐싱 구현
- 간단한 작업에 저비용 모델 사용

### 의존성 최적화

- 병렬화 가능한 작업 식별
- 의존성 체인 최소화
- 중요 작업 우선 처리

## 주요 기능

| 메서드 | 설명 |
|--------|------|
| `analyze_system()` | 전체 시스템 분석 및 병목 식별 |
| `optimize_system()` | 시스템 최적화 실행 |
| `identify_bottlenecks()` | 병목 현상 식별 |
| `calculate_throughput()` | 처리량 계산 |
| `identify_constraint()` | 현재 제약 요소 식별 |
| `recommend_scaling()` | 스케일링 권장 사항 생성 |
| `monitor_and_optimize()` | 자동 모니터링 및 최적화 |
| `generate_toc_report()` | TOC 최적화 보고서 생성 |
| `generate_final_analysis()` | 최종 분석 생성 |
| `compare_with_baselines()` | 기준 대비 비교 |
| `save_final_analysis()` | 분석 데이터 저장 |

## 데이터 저장

### Memory Storage (MCP memory 서버)

저장되는 데이터:
- `toc_baselines` - 기준 메트릭 (처리량, 토큰 효율 등)
- `toc_bottleneck_history` - 병목 현상 기록
- `toc_optimization_log` - 최적화 실행 로그
- `toc_work_history` - 완료된 작업 기록

장점:
- 빠른 접근
- 세션 간 유지
- 기준 비교 지원

### Filesystem Storage (MCP filesystem 서버)

저장 위치: `~/.agents_toc/`

저장되는 파일:
- `toc_baselines.json` - 기준 메트릭
- `toc_bottleneck_history.json` - 병목 현상 기록
- `toc_optimization_log.json` - 최적화 로그
- `toc_work_history.json` - 작업 기록
- `toc_final_report_<timestamp>.json` - 최종 분석 보고서

장점:
- 영구 보관
- 히스토리 추적 가능
- 외부 분석 도구 활용

## 기준 대비 비교 (Trend Analysis)

저장된 기준 데이터와 현재 데이터 비교:

```python
comparison = await toc_supervisor.compare_with_baselines()

# 결과 예시:
{
    "improvements": [
        {
            "metric": "Works per Hour",
            "baseline": 10.0,
            "current": 12.5,
            "change_pct": 25.0  # 25% 개선
        }
    ],
    "degradations": [
        {
            "metric": "Tokens per Work",
            "baseline": 2500,
            "current": 3000,
            "change_pct": 20.0  # 20% 저하
        }
    ],
    "stable": [
        {
            "metric": "Success Rate",
            "baseline": 0.95,
            "current": 0.94,
            "change_pct": -1.1  # 안정적
        }
    ]
}
```

### 기준 데이터 기반 개선 제안

1. **개선 추세 유지**
   - 개선된 지표 확인
   - 유사 작업에 적용
   - 개선 요인 추가 분석

2. **저하 원인 분석**
   - 저하된 지표 식별
   - 원인 분석
   - 이전 설정으로 롤백 검토

3. **안정적 지표 모니터링**
   - 변동 폭 5% 미만인 지표 유지
   - 안정성 유지 전략

## 데이터 저장 설정

```python
# Orchestrator에서 MCP 세션 전달
orchestrator.set_mcp_sessions(
    memory_session=memory_client,
    filesystem_session=filesystem_client
)

# 자동으로 최종 분석 시 데이터 저장
await toc_supervisor.save_final_analysis(analysis)
```

## 사용 예시

```bash
# 시스템 분석
python -m agents.toc_supervisor.agent analyze

# 최적화 실행
python -m agents.toc_supervisor.agent optimize

# 병목 현상 확인
python -m agents.toc_supervisor.agent bottlenecks

# 스케일링 권장 사항
python -m agents.toc_supervisor.agent scaling

# TOC 보고서 생성
python -m agents.toc_supervisor.agent report

# 자동 모니터링 및 최적화
python -m agents.toc_supervisor.agent monitor
```

## 처리량 메트릭

| 메트릭 | 설명 | 목표치 |
|--------|------|--------|
| `works_per_hour` | 시간당 완료 작업 수 | 최대화 |
| `tokens_per_work` | 작업당 토큰 사용량 | 최소화 |
| `success_rate` | 작업 성공률 | > 95% |
| `average_duration` | 평균 작업 시간 | 최소화 |

## 표준 문서화

- TOC 최적화 보고서 (TOC Optimization Report)
- 병목 분석서 (Bottleneck Analysis)
- 처리량 벤치마크 (Throughput Benchmark)
- 스케일링 계획서 (Scaling Plan)
