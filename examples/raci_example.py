"""
RACI 매트릭스 사용 예제
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_factory.core import (
    MultiAgentOrchestrator, WorkflowConfig,
    AgentInstance, Work, WorkPriority,
    RACI, RACIRole
)


async def work_handler(inputs: dict, agent) -> dict:
    await asyncio.sleep(0.3)
    return {"status": "completed"}


async def main():
    print("=== RACI Matrix Example ===\n")
    
    orchestrator = MultiAgentOrchestrator(WorkflowConfig(enable_toc=False, auto_document=False))
    
    # 에이전트 등록
    agents = [
        AgentInstance(agent_id="alice", agent_type="design_development", capabilities=["design"]),
        AgentInstance(agent_id="bob", agent_type="training_optimization", capabilities=["training"]),
        AgentInstance(agent_id="charlie", agent_type="evaluation_validation", capabilities=["evaluation"]),
        AgentInstance(agent_id="diana", agent_type="deployment_monitoring", capabilities=["deployment"])
    ]
    
    for agent in agents:
        orchestrator.register_agent(agent)
        orchestrator.register_work_handler(agent.agent_type, work_handler)
    
    # Work 생성 및 RACI 할당
    work1 = orchestrator.create_work(
        name="Design Model",
        description="모델 설계",
        work_type="design_development",
        agent_type="design_development",
        inputs={}
    )
    
    # RACI 할당
    print("1. Assigning RACI roles...")
    orchestrator.assign_raci(
        work_id=work1.work_id,
        responsible=["alice"],
        accountable="bob",
        consulted=["charlie"],
        informed=["diana"]
    )
    
    work2 = orchestrator.create_work(
        name="Train Model",
        description="모델 학습",
        work_type="training_optimization",
        agent_type="training_optimization",
        inputs={}
    )
    
    orchestrator.assign_raci(
        work_id=work2.work_id,
        responsible=["bob"],
        accountable="bob",
        consulted=["alice"],
        informed=["charlie", "diana"]
    )
    
    work3 = orchestrator.create_work(
        name="Evaluate Model",
        description="모델 평가",
        work_type="evaluation_validation",
        agent_type="evaluation_validation",
        inputs={}
    )
    
    orchestrator.assign_raci(
        work_id=work3.work_id,
        responsible=["charlie"],
        accountable="alice",
        consulted=["bob"],
        informed=["diana"]
    )
    
    # RACI 검증
    print("2. Validating RACI assignments...")
    validation = orchestrator.raci.validate_all()
    if validation:
        print(f"   Validation errors: {validation}")
    else:
        print("   All RACI assignments are valid!")
    
    # 워크로드 분석
    print("3. Analyzing agent workload...")
    workload = orchestrator.raci.get_workload_summary()
    for agent_id, roles in workload.items():
        print(f"   {agent_id}:")
        print(f"     - Responsible: {roles[RACIRole.RESPONSIBLE]} works")
        print(f"     - Accountable: {roles[RACIRole.ACCOUNTABLE]} works")
        print(f"     - Consulted: {roles[RACIRole.CONSULTED]} works")
        print(f"     - Informed: {roles[RACIRole.INFORMED]} works")
    
    # 워크플로우 실행
    print("4. Executing workflow...")
    await orchestrator.execute_workflow(works=[work1, work2, work3])
    
    # 최종 상태
    print("5. Final status...")
    for work in [work1, work2, work3]:
        print(f"   {work.name}: {work.status.value}")


if __name__ == "__main__":
    asyncio.run(main())
