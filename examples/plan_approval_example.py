import asyncio
from agent_factory.core import (
    MultiAgentOrchestrator, WorkflowConfig, AgentInstance, AgentStatus,
    WorkPriority, RACIRole
)


async def main():
    config = WorkflowConfig(
        max_concurrent_works=5,
        enable_toc=False,
        auto_document=False
    )
    
    orchestrator = MultiAgentOrchestrator(config)
    
    dev_agent = AgentInstance(
        agent_id="dev_agent_1",
        agent_type="design_development",
        capabilities=["design", "code_generation"],
        max_concurrent_works=2
    )
    orchestrator.register_agent(dev_agent)
    
    senior_agent = AgentInstance(
        agent_id="senior_agent_1",
        agent_type="design_development",
        capabilities=["design", "review", "code_generation"],
        max_concurrent_works=1
    )
    orchestrator.register_agent(senior_agent)
    
    work = orchestrator.create_work(
        name="Build API Endpoint",
        description="REST API 엔드포인트 구현",
        work_type="design_development",
        agent_type="design_development",
        inputs={
            "endpoint": "/api/users",
            "method": "GET",
            "requirements": "사용자 목록 조회 기능"
        },
        estimated_tokens=3000,
        priority=WorkPriority.HIGH
    )
    
    orchestrator.assign_raci(
        work_id=work.work_id,
        responsible=["dev_agent_1"],
        accountable="senior_agent_1",
        consulted=[],
        informed=[]
    )
    
    orchestrator.set_work_plan_approval_required(work.work_id, True)
    
    print(f"[1] Created work: {work.work_id}")
    print(f"[2] RACI assignments:")
    print(f"    - RESPONSIBLE: dev_agent_1 (작업 실행)")
    print(f"    - ACCOUNTABLE: senior_agent_1 (계획 승인)")
    print(f"[3] Plan approval required: True")
    print()
    
    plan_status = orchestrator.get_work_plan_status(work.work_id)
    print(f"[4] Current plan status: {plan_status}")
    print()
    
    print("[5] RESPONSIBLE agent submitting plan...")
    plan_content = {
        "approach": "FastAPI 사용",
        "steps": [
            "1. FastAPI 앱 초기화",
            "2. Pydantic 모델 정의",
            "3. /api/users 엔드포인트 구현",
            "4. 데이터베이스 연결",
            "5. 단위 테스트 작성"
        ],
        "estimated_files": ["main.py", "models.py", "routers.py"],
        "estimated_hours": 4,
        "risks": ["데이터베이스 연결 지연 가능성"],
        "expected_results": "GET /api/users 요청 시 JSON 응답 반환"
    }
    
    submit_result = orchestrator.submit_work_plan(
        work_id=work.work_id,
        plan_content=plan_content,
        proposed_by="dev_agent_1"
    )
    print(f"    Result: {submit_result['message']}")
    print()
    
    plan_status = orchestrator.get_work_plan_status(work.work_id)
    print(f"[6] After plan submission:")
    print(f"    - Status: {plan_status['plan']['status']}")
    print(f"    - Proposed by: {plan_status['plan']['proposed_by']}")
    print(f"    - Content: {plan_status['plan']['content']}")
    print()
    
    print("[7] ACCOUNTABLE agent reviewing plan...")
    print(f"    - Plan includes {len(plan_content['steps'])} steps")
    print(f"    - Estimated: {plan_content['estimated_hours']} hours")
    print(f"    - Risks identified: {plan_content['risks']}")
    print()
    
    print("[8] ACCOUNTABLE agent approving plan...")
    approve_result = orchestrator.approve_work_plan(
        work_id=work.work_id,
        approved_by="senior_agent_1"
    )
    print(f"    Result: {approve_result['message']}")
    print()
    
    plan_status = orchestrator.get_work_plan_status(work.work_id)
    print(f"[9] After plan approval:")
    print(f"    - Status: {plan_status['plan']['status']}")
    print(f"    - Approved by: {plan_status['plan']['approved_by']}")
    print(f"    - Approved at: {plan_status['plan']['approved_at']}")
    print()
    
    print("[10] Now work can proceed with execution...")
    print(f"     (In real scenario, work would execute with the approved plan)")
    print()
    
    print("[11] Example: What if plan was rejected?")
    test_work = orchestrator.create_work(
        name="Rejected Plan Test",
        description="계획 거절 시나리오 테스트",
        work_type="design_development",
        agent_type="design_development",
        inputs={},
        priority=WorkPriority.LOW
    )
    
    orchestrator.assign_raci(
        work_id=test_work.work_id,
        responsible=["dev_agent_1"],
        accountable="senior_agent_1",
        consulted=[],
        informed=[]
    )
    
    orchestrator.set_work_plan_approval_required(test_work.work_id, True)
    
    orchestrator.submit_work_plan(
        work_id=test_work.work_id,
        plan_content={"incomplete": True},
        proposed_by="dev_agent_1"
    )
    
    reject_result = orchestrator.reject_work_plan(
        work_id=test_work.work_id,
        rejected_by="senior_agent_1",
        reason="계획이 너무 부족합니다. 더 상세한 단계와 예상 결과가 필요합니다."
    )
    print(f"     Rejection result: {reject_result['message']}")
    print(f"     Reason: {reject_result['rejection_reason']}")
    print()
    
    print("[12] Summary of Plan Approval Workflow:")
    print("     1. Work 생성 시 RACI 할당 (RESPONSIBLE, ACCOUNTABLE)")
    print("     2. require_plan_approval = True 설정")
    print("     3. RESPONSIBLE agent가 계획 제출 (submit_work_plan)")
    print("     4. ACCOUNTABLE agent가 계획 검토 및 승인/거절")
    print("     5. 승인된 경우에만 작업 실행")
    print("     6. 거절된 경우 RESPONSIBLE agent가 계획 수정 후 재제출")


if __name__ == "__main__":
    asyncio.run(main())
