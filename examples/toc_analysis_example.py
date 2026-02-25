import sys
import os
import asyncio
import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from agent_factory.core import (
    MultiAgentOrchestrator, WorkflowConfig, AgentInstance,
    WorkPriority, Work, WorkStatus
)
from agent_factory.core.work import WorkResult


async def main():
    config = WorkflowConfig(
        max_concurrent_works=5,
        enable_toc=True,
        auto_document=False
    )
    
    orchestrator = MultiAgentOrchestrator(config)
    
    dev_agent = AgentInstance(
        agent_id="dev_agent_1",
        agent_type="design_development",
        capabilities=["design", "code_generation"],
        max_concurrent_works=1
    )
    dev_agent.completed_works = 3
    dev_agent.failed_works = 1
    dev_agent.total_tokens_used = 15000
    dev_agent.total_work_time_seconds = 300
    orchestrator.register_agent(dev_agent)
    
    senior_agent = AgentInstance(
        agent_id="senior_agent_1",
        agent_type="design_development",
        capabilities=["design", "review", "code_generation"],
        max_concurrent_works=1
    )
    senior_agent.completed_works = 5
    senior_agent.failed_works = 0
    senior_agent.total_tokens_used = 20000
    senior_agent.total_work_time_seconds = 500
    orchestrator.register_agent(senior_agent)
    
    test_agent = AgentInstance(
        agent_id="test_agent_1",
        agent_type="evaluation_validation",
        capabilities=["testing", "validation"],
        max_concurrent_works=1
    )
    test_agent.completed_works = 1
    test_agent.failed_works = 2
    test_agent.total_tokens_used = 8000
    test_agent.total_work_time_seconds = 200
    orchestrator.register_agent(test_agent)
    
    works = []
    
    for i in range(5):
        work = orchestrator.create_work(
            name=f"Test Work {i+1}",
            description=f"테스트 작업 {i+1}",
            work_type="design_development",
            agent_type="design_development",
            inputs={},
            estimated_tokens=3000 + (i * 500),
            priority=WorkPriority.MEDIUM
        )
        
        orchestrator.assign_raci(
            work_id=work.work_id,
            responsible=["dev_agent_1"],
            accountable="senior_agent_1",
            consulted=[],
            informed=[]
        )
        
        orchestrator.set_work_plan_approval_required(work.work_id, True)
        
        orchestrator.submit_work_plan(
            work_id=work.work_id,
            plan_content={
                "approach": f"Test approach {i+1}",
                "steps": ["Step 1", "Step 2"],
                "estimated_hours": 2
            },
            proposed_by="dev_agent_1"
        )
        
        orchestrator.approve_work_plan(
            work_id=work.work_id,
            approved_by="senior_agent_1"
        )
        
        work.status = WorkStatus.COMPLETED
        work.actual_tokens = 3500 + (i * 600)
        work.actual_duration_seconds = 60 + (i * 10)
        work.completed_at = datetime.datetime.now()
        works.append(work)
    
    for work in works:
        result = WorkResult(
            work_id=work.work_id,
            status=WorkStatus.COMPLETED,
            output={},
            completed_at=work.completed_at
        )
        orchestrator.toc_supervisor.record_work_completion(work, result)
    
    print("[1] 테스트 Work 생성 완료")
    print(f"    총 Work: {len(works)}개")
    print(f"    에이전트: {len(orchestrator.agent_pool._agents)}개")
    print()
    
    print("[2] TOC 최종 분석 시작...")
    analysis = await orchestrator.toc_supervisor.generate_final_analysis(works)
    
    print(f"\n## 작업 요약")
    ws = analysis["work_summary"]
    print(f"  전체: {ws['total']}, 완료: {ws['completed']}, 성공률: {ws['success_rate']:.1%}")
    
    ta = analysis.get("token_analysis", {})
    if ta.get("status") != "no_data":
        print(f"\n## Token 효율")
        print(f"  전체 효율: {ta['overall_efficiency']:.1f}%")
        if ta.get("potential_savings", 0) > 0:
            print(f"  절감 가능: {ta['potential_savings']:,} 토큰")
        
        if ta.get("inefficiencies"):
            print(f"\n### 비효율적인 작업 타입:")
            for ineff in ta["inefficiencies"]:
                print(f"  - {ineff['work_type']}: {ineff['efficiency']:.1f}%")
    
    bn = analysis.get("bottleneck_analysis", [])
    if bn:
        print(f"\n## 병목 현상 ({len(bn)}개)")
        for b in bn:
            print(f"  [{b['severity'].upper()}] {b['agent_type']}")
            print(f"    {b['recommendation']}")
    
    recs = analysis.get("recommendations", [])
    if recs:
        print(f"\n## 개선 제안 ({len(recs)}개)")
        for i, r in enumerate(recs[:5], 1):
            print(f"  {i}. [{r['priority'].upper()}] {r['title']}")
            print(f"     예상 효과: {r['expected_benefit']}")
    
    print("\n" + "=" * 80)
    print(orchestrator.toc_supervisor.format_final_report(analysis))


if __name__ == "__main__":
    asyncio.run(main())
