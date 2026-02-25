"""
TOC (제약이론) 최적화 예제
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_factory.core import (
    MultiAgentOrchestrator, WorkflowConfig,
    AgentInstance, Work, WorkPriority,
    AgentStatus, WorkStatus
)


async def slow_handler(inputs: dict, agent) -> dict:
    """느린 작업 핸들러 (병목 시뮬레이션)"""
    await asyncio.sleep(2.0)
    return {"status": "completed"}


async def fast_handler(inputs: dict, agent) -> dict:
    """빠른 작업 핸들러"""
    await asyncio.sleep(0.3)
    return {"status": "completed"}


async def main():
    print("=== TOC Optimization Example ===\n")
    
    config = WorkflowConfig(
        max_concurrent_works=10,
        enable_toc=True,
        auto_document=False,
        optimization_interval=10.0
    )
    
    orchestrator = MultiAgentOrchestrator(config)
    
    # 에이전트 등록 (일부는 용량 제한)
    print("1. Registering agents with different capacities...")
    agents = [
        AgentInstance(
            agent_id="fast_agent_1",
            agent_type="fast_type",
            capabilities=["fast"],
            max_concurrent_works=5
        ),
        AgentInstance(
            agent_id="fast_agent_2",
            agent_type="fast_type",
            capabilities=["fast"],
            max_concurrent_works=5
        ),
        AgentInstance(
            agent_id="slow_agent_1",
            agent_type="slow_type",
            capabilities=["slow"],
            max_concurrent_works=1
        )
    ]
    
    for agent in agents:
        orchestrator.register_agent(agent)
    
    orchestrator.register_work_handler("fast_type", fast_handler)
    orchestrator.register_work_handler("slow_type", slow_handler)
    
    # 병목을 유발하는 Work 생성
    print("2. Creating works that will cause bottlenecks...")
    works = []
    
    for i in range(5):
        # 빠른 작업들
        work_fast = orchestrator.create_work(
            name=f"Fast Task {i+1}",
            description=f"빠른 작업 {i+1}",
            work_type="fast_type",
            agent_type="fast_type",
            inputs={},
            priority=WorkPriority.MEDIUM
        )
        works.append(work_fast)
        
        # 느린 작업 (병목 유발)
        if i < 3:
            work_slow = orchestrator.create_work(
                name=f"Slow Task {i+1}",
                description=f"느린 작업 {i+1}",
                work_type="slow_type",
                agent_type="slow_type",
                inputs={},
                priority=WorkPriority.HIGH,
                estimated_tokens=2000
            )
            works.append(work_slow)
    
    # 초기 상태 분석
    print("3. Initial system analysis...")
    initial_status = orchestrator.get_status()
    print(f"   Pool utilization: {initial_status['pool_status']['utilization_rate']:.2%}")
    
    # 워크플로우 실행 (TOC 활성화)
    print("4. Running workflow with TOC optimization...")
    
    # 별도 태스크에서 워크플로우 실행
    workflow_task = asyncio.create_task(
        orchestrator.execute_workflow(works=works)
    )
    
    # 최적화 모니터링
    print("5. Monitoring TOC optimizations...")
    for _ in range(10):
        await asyncio.sleep(2)
        
        status = orchestrator.get_status()
        toc_report = status['toc_report']
        
        print(f"   Progress: {status['works']['completed']}/{status['works']['total']}")
        print(f"   Throughput: {toc_report['summary']['works_per_hour']:.2f} works/hour")
        print(f"   Bottlenecks: {toc_report['bottlenecks_detected']}")
        print(f"   Optimizations: {toc_report['optimizations_applied']}")
        
        constraint = toc_report['current_constraint']
        if constraint:
            print(f"   Constraint: {constraint['type']}")
        
        print()
    
    # 최종 결과 대기
    result = await workflow_task
    
    print("=== Final Result ===")
    print(f"Status: {result.status}")
    print(f"Works: {result.works_completed}/{result.works_total}")
    print(f"Total Duration: {result.total_duration_seconds:.2f}s")
    print(f"Tokens: {result.total_tokens}")
    
    # 최종 TOC 보고서
    print("\n=== Final TOC Report ===")
    final_status = orchestrator.get_status()
    final_toc = final_status['toc_report']
    
    print(f"Total Works: {final_toc['summary']['works_completed']}")
    print(f"Works/Hour: {final_toc['summary']['works_per_hour']:.2f}")
    print(f"Tokens/Work: {final_toc['summary']['tokens_per_work']:.2f}")
    print(f"Success Rate: {final_toc['summary']['success_rate']:.2%}")
    print(f"Bottlenecks Found: {final_toc['bottlenecks_detected']}")
    print(f"Bottlenecks Resolved: {final_toc['bottlenecks_resolved']}")
    
    if final_toc['current_constraint']:
        print(f"Final Constraint: {final_toc['current_constraint']['type']}")
    
    # 권장 사항
    print("\n=== Recommendations ===")
    for rec in final_toc['recommendations'][:5]:
        print(f"- {rec.get('recommendation', 'N/A')}")


if __name__ == "__main__":
    asyncio.run(main())
