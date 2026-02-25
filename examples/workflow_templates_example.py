
"""
워크플로우 템플릿 사용 예제
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_factory.core import MultiAgentOrchestrator, WorkflowConfig, AgentInstance


async def handler(inputs: dict, agent) -> dict:
    await asyncio.sleep(0.3)
    return {"status": "completed", "result": f"{inputs.get('work_type', 'unknown')} done"}


async def main():
    print("=== Workflow Templates Example ===\n")
    
    orchestrator = MultiAgentOrchestrator(
        WorkflowConfig(enable_toc=False, auto_document=False)
    )
    
    # 에이전트 등록
    agent_types = [
        "problem_definition", "data_collection", "design_development",
        "training_optimization", "evaluation_validation", "deployment_monitoring"
    ]
    
    for agent_type in agent_types:
        agent = AgentInstance(
            agent_id=f"{agent_type}_agent",
            agent_type=agent_type,
            capabilities=[agent_type]
        )
        orchestrator.register_agent(agent)
        orchestrator.register_work_handler(agent_type, handler)
    
    # 템플릿 1: ML Pipeline
    print("1. Using ML Pipeline Template...")
    result1 = await orchestrator.execute_workflow(
        template="ml_pipeline",
        parameters={
            "requirements": "고객 이탈 예측 모델",
            "data_sources": ["/data/customers.csv"]
        }
    )
    
    print(f"   ML Pipeline: {result1.works_completed}/{result1.works_total} works")
    print(f"   Duration: {result1.total_duration_seconds:.2f}s")
    
    # 템플릿 2: Web Development
    print("\n2. Using Web Development Template...")
    result2 = await orchestrator.execute_workflow(
        template="web_development",
        parameters={
            "requirements": "REST API + React 프론트엔드"
        }
    )
    
    print(f"   Web Dev: {result2.works_completed}/{result2.works_total} works")
    print(f"   Duration: {result2.total_duration_seconds:.2f}s")
    
    # 템플릿 3: API Development
    print("\n3. Using API Development Template...")
    result3 = await orchestrator.execute_workflow(
        template="api_development",
        parameters={
            "api_spec": "User management API with CRUD operations"
        }
    )
    
    print(f"   API Dev: {result3.works_completed}/{result3.works_total} works")
    print(f"   Duration: {result3.total_duration_seconds:.2f}s")
    
    # 템플릿 4: Data Pipeline
    print("\n4. Using Data Processing Template...")
    result4 = await orchestrator.execute_workflow(
        template="data_processing",
        parameters={
            "sources": ["/data/raw", "https://api.example.com/data"]
        }
    )
    
    print(f"   Data Pipeline: {result4.works_completed}/{result4.works_total} works")
    print(f"   Duration: {result4.total_duration_seconds:.2f}s")
    

if __name__ == "__main__":
    asyncio.run(main())
