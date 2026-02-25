"""
기본 사용 예제: Work 기반 멀티 에이전트 시스템
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_factory.core import (
    MultiAgentOrchestrator, WorkflowConfig,
    AgentInstance, Work, WorkPriority, WorkStatus,
    AgentStatus, DocumentType
)


async def work_handler(inputs: dict, agent) -> dict:
    """기본 작업 핸들러"""
    work_type = inputs.get("work_type", "unknown")
    data = inputs.get("data", {})
    
    # 작업 시뮬레이션
    await asyncio.sleep(0.5)
    
    return {
        "status": "completed",
        "work_type": work_type,
        "result": f"{work_type} completed successfully",
        "processed_data": data
    }


async def main():
    print("=== Multi-Agent Orchestrator Example ===\n")
    
    # 오케스트레이터 설정
    config = WorkflowConfig(
        max_concurrent_works=5,
        enable_toc=True,
        auto_document=True,
        optimization_interval=30.0
    )
    
    orchestrator = MultiAgentOrchestrator(config)
    
    # 에이전트 등록
    print("1. Registering agents...")
    agents = [
        AgentInstance(
            agent_id="dev_agent_1",
            agent_type="design_development",
            capabilities=["design", "code_generation", "testing"],
            max_concurrent_works=2
        ),
        AgentInstance(
            agent_id="data_agent_1",
            agent_type="data_collection",
            capabilities=["data_collection", "preprocessing"],
            max_concurrent_works=2
        ),
        AgentInstance(
            agent_id="train_agent_1",
            agent_type="training_optimization",
            capabilities=["training", "optimization"],
            max_concurrent_works=1
        ),
        AgentInstance(
            agent_id="eval_agent_1",
            agent_type="evaluation_validation",
            capabilities=["evaluation", "validation"],
            max_concurrent_works=1
        )
    ]
    
    for agent in agents:
        orchestrator.register_agent(agent)
    
    # 작업 핸들러 등록
    print("2. Registering work handlers...")
    work_types = [
        "problem_definition", "data_collection", "design_development",
        "training_optimization", "evaluation_validation", "deployment_monitoring"
    ]
    
    for wt in work_types:
        orchestrator.register_work_handler(wt, work_handler)
    
    # Work 생성 및 제출
    print("3. Creating and submitting works...")
    
    work1 = orchestrator.create_work(
        name="Define Problem",
        description="프로젝트 문제 정의",
        work_type="problem_definition",
        agent_type="problem_definition",
        inputs={"work_type": "problem_definition", "data": {"requirements": "이미지 분류 모델"}},
        priority=WorkPriority.HIGH
    )
    
    work2 = orchestrator.create_work(
        name="Collect Data",
        description="데이터 수집",
        work_type="data_collection",
        agent_type="data_collection",
        inputs={"work_type": "data_collection", "data": {"sources": ["/data/images"]}},
        dependencies=[work1.work_id],
        priority=WorkPriority.HIGH
    )
    
    work3 = orchestrator.create_work(
        name="Design Architecture",
        description="모델 설계",
        work_type="design_development",
        agent_type="design_development",
        inputs={"work_type": "design_development", "data": {"model_type": "CNN"}},
        dependencies=[work2.work_id]
    )
    
    work4 = orchestrator.create_work(
        name="Train Model",
        description="모델 학습",
        work_type="training_optimization",
        agent_type="training_optimization",
        inputs={"work_type": "training_optimization", "data": {"epochs": 100}},
        dependencies=[work3.work_id],
        estimated_tokens=3000
    )
    
    work5 = orchestrator.create_work(
        name="Evaluate Model",
        description="모델 평가",
        work_type="evaluation_validation",
        agent_type="evaluation_validation",
        inputs={"work_type": "evaluation_validation", "data": {"metrics": ["accuracy", "f1"]}},
        dependencies=[work4.work_id]
    )
    
    # 워크플로우 실행
    print("4. Executing workflow...")
    result = await orchestrator.execute_workflow(works=[work1, work2, work3, work4, work5])
    
    print(f"\n=== Workflow Result ===")
    print(f"Status: {result.status}")
    print(f"Works: {result.works_completed}/{result.works_total}")
    print(f"Failed: {result.works_failed}")
    print(f"Total Tokens: {result.total_tokens}")
    print(f"Total Duration: {result.total_duration_seconds:.2f}s")
    print(f"Documents Generated: {len(result.documents)}")
    
    # 상태 확인
    print(f"\n=== System Status ===")
    status = orchestrator.get_status()
    print(f"Pool Utilization: {status['pool_status']['utilization_rate']:.2%}")
    print(f"Active Agents: {status['pool_status']['busy_agents']}/{status['pool_status']['total_agents']}")
    
    # TOC 보고서
    if config.enable_toc:
        print(f"\n=== TOC Report ===")
        toc_report = status['toc_report']
        print(f"Completed Works: {toc_report['summary']['works_completed']}")
        print(f"Works/Hour: {toc_report['summary']['works_per_hour']:.2f}")
        print(f"Success Rate: {toc_report['summary']['success_rate']:.2%}")
        print(f"Bottlenecks Detected: {toc_report['bottlenecks_detected']}")
        print(f"Bottlenecks Resolved: {toc_report['bottlenecks_resolved']}")


if __name__ == "__main__":
    asyncio.run(main())
