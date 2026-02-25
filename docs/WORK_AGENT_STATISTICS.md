# Work-Agent 통계 기능

## 개요

TOC 관리자(TOCSupervisor)를 통해 Work별로 어떤 Agent들이 얼마나 작업했는지에 대한 통계를 확인할 수 있습니다. 이 기능은 사용자가 원할 때만 조회할 수 있습니다.

## 주요 기능

### 1. 개별 Work 통계 조회

특정 Work에 할당된 Agent들의 작업 통계를 조회합니다.

```python
from agent_factory.core import TOCSupervisor

toc = TOCSupervisor(agent_pool, work_queue, raci)

# 특정 Work의 통계 조회
work_stats = toc.get_work_agent_statistics("work_001")

# 형식화된 보고서
report = toc.format_work_agent_report("work_001")
print(report)
```

**출력 예시:**
```
================================================================================
Work-Agent 통계 보고서: work_001
================================================================================

## 요약
  총 활동 수: 1
  총 토큰 사용: 1,200
  총 작업 시간: 45.00초

## 에이전트별 통계

### dev_agent_1 (design_development)
  작업 수: 1
  토큰 사용: 1,200
  작업 시간: 45.00초
  평균 토큰/작업: 1200
  평균 시간/작업: 45.00초
```

### 2. 전체 Work 통계 조회

모든 Work에 대한 Agent 작업 통계를 조회합니다.

```python
# 전체 통계 조회 (JSON)
all_stats = toc.get_work_agent_statistics()

# 전체 보고서
report = toc.format_work_agent_report()
print(report)
```

**출력 내용:**
- 전체 Work 수 및 활동 수
- Work별 통계 (토큰 사용, 시간, 에이전트 타입)
- 에이전트 타입별 통계 (총 Work 수, Work 타입별 분포)

### 3. JSON 형식 통계

프로그래밍 방식으로 통계 데이터에 접근할 수 있습니다.

```python
import json

# 전체 통계
stats = toc.get_work_agent_statistics()

print("전체 요약:")
print(json.dumps(stats["summary"], indent=2, ensure_ascii=False))

# Work별 통계
print("\nWork별 통계:")
for work_id, work_data in stats["by_work"].items():
    print(f"  {work_id}: {work_data['total_activities']} 활동, {work_data['total_tokens']} 토큰")

# 에이전트 타입별 통계
print("\n에이전트 타입별 통계:")
for agent_type, type_data in stats["by_agent_type"].items():
    print(f"  {agent_type}: {type_data['total_works']} 작업, {type_data['total_tokens']} 토큰")
```

## API

### `TOCSupervisor.get_work_agent_statistics(work_id: Optional[str] = None) -> Dict[str, Any]`

Work별 Agent 작업 통계를 반환합니다.

**매개변수:**
- `work_id` (Optional[str]): 특정 Work의 ID. `None`인 경우 전체 통계를 반환합니다.

**반환값:**
- `Dict[str, Any]`: 통계 데이터

**개별 Work 통계 구조:**
```json
{
  "work_id": "work_001",
  "total_activities": 2,
  "total_tokens": 3500,
  "total_duration_seconds": 125.0,
  "agents": {
    "agent_1": {
      "agent_type": "design_development",
      "work_count": 1,
      "total_tokens": 1200,
      "total_duration": 45.0,
      "activities": [...]
    },
    "agent_2": {
      "agent_type": "design_development",
      "work_count": 1,
      "total_tokens": 2300,
      "total_duration": 80.0,
      "activities": [...]
    }
  }
}
```

**전체 통계 구조:**
```json
{
  "summary": {
    "total_works": 4,
    "total_activities": 4,
    "total_tokens": 6200,
    "total_duration": 215.0
  },
  "by_work": {
    "work_001": {
      "work_type": "design_development",
      "total_activities": 1,
      "total_tokens": 1200,
      "total_duration_seconds": 45.0,
      "agent_types": {"design_development": 1}
    },
    ...
  },
  "by_agent_type": {
    "design_development": {
      "total_works": 2,
      "total_tokens": 3500,
      "total_duration": 125.0,
      "work_types": {"design_development": 2}
    },
    ...
  }
}
```

### `TOCSupervisor.format_work_agent_report(work_id: Optional[str] = None) -> str`

Work-Agent 통계 보고서를 형식화된 문자열로 반환합니다.

**매개변수:**
- `work_id` (Optional[str]): 특정 Work의 ID. `None`인 경우 전체 보고서를 반환합니다.

**반환값:**
- `str`: 형식화된 보고서

## 사용 예시

```python
import asyncio
from agent_factory.core import (
    TOCSupervisor, AgentPool, WorkQueue, RACI,
    Work, WorkStatus, WorkPriority, WorkResult,
    AgentInstance
)

async def main():
    # 초기화
    agent_pool = AgentPool()
    work_queue = WorkQueue()
    raci = RACI()
    toc = TOCSupervisor(agent_pool, work_queue, raci)
    
    # 에이전트 등록
    agent = AgentInstance(
        agent_id="dev_agent_1",
        agent_type="design_development",
        capabilities=["design", "code"],
        max_concurrent_works=2
    )
    agent_pool.register_agent(agent)
    
    # Work 생성 및 완료
    work = Work(
        work_id="work_001",
        name="API 설계",
        description="REST API 설계",
        work_type="design_development",
        agent_type="design_development",
        priority=WorkPriority.HIGH
    )
    
    work.start("dev_agent_1")
    work.actual_tokens = 1200
    work.actual_duration_seconds = 45
    
    result = WorkResult(
        work_id="work_001",
        status=WorkStatus.COMPLETED,
        output={"success": True}
    )
    
    # Work 완료 기록 (이때 통계도 기록됨)
    toc.record_work_completion(work, result)
    
    # 통계 조회
    print("=== 개별 Work 통계 ===")
    print(toc.format_work_agent_report("work_001"))
    
    print("\n=== 전체 통계 ===")
    print(toc.format_work_agent_report())

if __name__ == "__main__":
    asyncio.run(main())
```

## 주의사항

1. **자동 기록**: Work가 완료될 때 `record_work_completion()` 메서드가 호출되면 자동으로 통계가 기록됩니다.

2. **요청 시 조회**: 통계는 사용자가 `get_work_agent_statistics()` 또는 `format_work_agent_report()`를 호출할 때만 계산됩니다.

3. **메모리 저장**: 통계 데이터는 TOCSupervisor 인스턴스 내부에 저장됩니다. 영구 저장은 별도 구현이 필요합니다.

## 통계 포함 항목

### Work별 통계
- Work ID
- Work 타입
- 총 활동 수
- 총 토큰 사용량
- 총 작업 시간
- 참여한 에이전트 타입

### Agent별 통계
- Agent ID
- Agent 타입
- 작업 수
- 토큰 사용량
- 작업 시간
- 평균 토큰/작업
- 평균 시간/작업

### 에이전트 타입별 통계
- Agent 타입
- 총 Work 수
- 총 토큰 사용량
- 총 작업 시간
- Work 타입별 분포

## 예제 파일

`examples/work_agent_statistics_example.py` 파일에서 완전한 사용 예제를 확인할 수 있습니다.

```bash
cd $WORKDIR/agent-factory
source venv/bin/activate
python examples/work_agent_statistics_example.py
```
