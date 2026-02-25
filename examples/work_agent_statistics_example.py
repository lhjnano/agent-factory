#!/usr/bin/env python3
"""
Work-Agent 통계 테스트
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from agent_factory.core import (
    TOCSupervisor, AgentPool, WorkQueue, RACI,
    Work, WorkStatus, WorkPriority, WorkResult,
    AgentInstance, AgentStatus
)
from datetime import datetime


def test_work_agent_statistics():
    print("=== Work-Agent 통계 테스트 ===\n")
    
    agent_pool = AgentPool()
    work_queue = WorkQueue()
    raci = RACI()
    
    toc = TOCSupervisor(agent_pool, work_queue, raci)
    
    print("1. 에이전트 등록...")
    agents = [
        AgentInstance(
            agent_id="dev_agent_1",
            agent_type="design_development",
            capabilities=["design", "code"],
            max_concurrent_works=2
        ),
        AgentInstance(
            agent_id="dev_agent_2",
            agent_type="design_development",
            capabilities=["design", "code"],
            max_concurrent_works=2
        ),
        AgentInstance(
            agent_id="data_agent_1",
            agent_type="data_collection",
            capabilities=["collect", "preprocess"],
            max_concurrent_works=1
        ),
        AgentInstance(
            agent_id="eval_agent_1",
            agent_type="evaluation_validation",
            capabilities=["eval", "validate"],
            max_concurrent_works=1
        )
    ]
    
    for agent in agents:
        agent_pool.register_agent(agent)
    
    print(f"  ✓ {len(agents)}개 에이전트 등록됨\n")
    
    print("2. Work 생성 및 시뮬레이션...")
    works = [
        Work(
            work_id="work_001",
            name="API 설계",
            description="REST API 설계",
            work_type="design_development",
            agent_type="design_development",
            priority=WorkPriority.HIGH,
            estimated_tokens=1500
        ),
        Work(
            work_id="work_002",
            name="데이터 수집",
            description="데이터 수집",
            work_type="data_collection",
            agent_type="data_collection",
            priority=WorkPriority.HIGH,
            estimated_tokens=2000
        ),
        Work(
            work_id="work_003",
            name="코드 구현",
            description="API 코드 구현",
            work_type="design_development",
            agent_type="design_development",
            priority=WorkPriority.MEDIUM,
            estimated_tokens=2500
        ),
        Work(
            work_id="work_004",
            name="평가",
            description="성능 평가",
            work_type="evaluation_validation",
            agent_type="evaluation_validation",
            priority=WorkPriority.MEDIUM,
            estimated_tokens=1000
        )
    ]
    
    assignments = [
        ("work_001", "dev_agent_1", 1200, 45),
        ("work_002", "data_agent_1", 1800, 60),
        ("work_003", "dev_agent_2", 2300, 80),
        ("work_004", "eval_agent_1", 900, 30)
    ]
    
    for work_id, agent_id, tokens, duration in assignments:
        work = next(w for w in works if w.work_id == work_id)
        work.start(agent_id)
        work.actual_tokens = tokens
        work.actual_duration_seconds = duration
        work.completed_at = datetime.now()
        work.status = WorkStatus.COMPLETED
        
        result = WorkResult(
            work_id=work_id,
            status=WorkStatus.COMPLETED,
            output={"success": True},
            completed_at=datetime.now()
        )
        
        toc.record_work_completion(work, result)
        print(f"  ✓ {work_id} 완료: {agent_id} ({tokens} tokens, {duration}s)")
    
    print(f"\n3. 개별 Work 통계 조회...")
    print("\n" + "="*80)
    print(toc.format_work_agent_report("work_001"))
    print("\n" + "="*80)
    print(toc.format_work_agent_report("work_003"))
    
    print("\n\n4. 전체 Work 통계 조회...")
    print("\n" + "="*80)
    print(toc.format_work_agent_report())
    print("="*80)
    
    print("\n5. JSON 형식 통계...")
    import json
    all_stats = toc.get_work_agent_statistics()
    print("\n전체 요약:")
    print(json.dumps(all_stats["summary"], indent=2, ensure_ascii=False))
    
    print("\n\nWork별 통계:")
    for work_id, stats in all_stats["by_work"].items():
        print(f"  {work_id}: {stats['total_activities']} 활동, {stats['total_tokens']} 토큰")
    
    print("\n\n에이전트 타입별 통계:")
    for agent_type, stats in all_stats["by_agent_type"].items():
        print(f"  {agent_type}: {stats['total_works']} 작업, {stats['total_tokens']} 토큰")
    
    print("\n\n=== 테스트 완료 ===")
    print("\n사용 방법:")
    print("  toc.format_work_agent_report()           # 전체 보고서")
    print("  toc.format_work_agent_report(work_id)      # 특정 Work 보고서")
    print("  toc.get_work_agent_statistics()            # JSON 데이터")
    print("  toc.get_work_agent_statistics(work_id)     # 특정 Work JSON")


if __name__ == "__main__":
    test_work_agent_statistics()
