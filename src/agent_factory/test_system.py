"""
시스템 통합 테스트
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from agent_factory.core import (
    MultiAgentOrchestrator, WorkflowConfig,
    AgentInstance, Work, WorkPriority,
    DocumentType, RACIRole
)


async def mock_handler(inputs: dict, agent) -> dict:
    """모의 작업 핸들러"""
    work_type = inputs.get("work_type", "unknown")
    await asyncio.sleep(0.5)
    
    if work_type == "training_optimization":
        await asyncio.sleep(1.0)
    
    return {
        "status": "completed",
        "work_type": work_type,
        "agent_id": agent.agent_id,
        "metrics": {"tokens_used": 100 + len(work_type) * 10}
    }


async def test_basic_workflow():
    """기본 워크플로우 테스트"""
    print("\n=== Test 1: Basic Workflow ===")
    
    orchestrator = MultiAgentOrchestrator(WorkflowConfig(enable_toc=False, auto_document=False))
    
    agent = AgentInstance(
        agent_id="test_agent",
        agent_type="design_development",
        capabilities=["design"]
    )
    orchestrator.register_agent(agent)
    orchestrator.register_work_handler("design_development", mock_handler)
    
    work = orchestrator.create_work(
        name="Test Work",
        description="테스트 작업",
        work_type="design_development",
        agent_type="design_development",
        inputs={"work_type": "test"}
    )
    
    result = await orchestrator.execute_workflow(works=[work])
    
    assert result.status == "completed", f"Expected completed, got {result.status}"
    assert result.works_completed == 1, f"Expected 1 completed, got {result.works_completed}"
    
    print("✓ Basic workflow test passed")


async def test_raci_assignment():
    """RACI 할당 테스트"""
    print("\n=== Test 2: RACI Assignment ===")
    
    orchestrator = MultiAgentOrchestrator(WorkflowConfig(enable_toc=False, auto_document=False))
    
    agents = [
        AgentInstance(agent_id="agent_a", agent_type="type_a", capabilities=["a"]),
        AgentInstance(agent_id="agent_b", agent_type="type_b", capabilities=["b"]),
        AgentInstance(agent_id="agent_c", agent_type="type_c", capabilities=["c"])
    ]
    
    for agent in agents:
        orchestrator.register_agent(agent)
        orchestrator.register_work_handler(agent.agent_type, mock_handler)
    
    work = orchestrator.create_work(
        name="RACI Test",
        description="RACI 테스트",
        work_type="type_a",
        agent_type="type_a",
        inputs={"work_type": "test"}
    )
    
    orchestrator.assign_raci(
        work_id=work.work_id,
        responsible=["agent_a"],
        accountable="agent_b",
        consulted=["agent_c"],
        informed=["agent_c"]
    )
    
    validation = orchestrator.raci.validate_all()
    assert len(validation) == 0, f"RACI validation failed: {validation}"
    
    workload = orchestrator.raci.get_workload_summary()
    assert "agent_a" in workload, "agent_a not in workload"
    assert workload["agent_a"][RACIRole.RESPONSIBLE] == 1
    
    print("✓ RACI assignment test passed")


async def test_multi_agent_parallel():
    """다중 에이전트 병렬 처리 테스트"""
    print("\n=== Test 3: Multi-Agent Parallel Processing ===")
    
    config = WorkflowConfig(max_concurrent_works=5, enable_toc=False, auto_document=False)
    orchestrator = MultiAgentOrchestrator(config)
    
    for i in range(3):
        agent = AgentInstance(
            agent_id=f"parallel_agent_{i}",
            agent_type="parallel",
            capabilities=["parallel"],
            max_concurrent_works=2
        )
        orchestrator.register_agent(agent)
    
    orchestrator.register_work_handler("parallel", mock_handler)
    
    works = []
    for i in range(5):
        work = orchestrator.create_work(
            name=f"Parallel Work {i}",
            description=f"병렬 작업 {i}",
            work_type="parallel",
            agent_type="parallel",
            inputs={"work_type": "parallel"}
        )
        works.append(work)
    
    result = await orchestrator.execute_workflow(works=works)
    
    assert result.works_completed == 5, f"Expected 5 completed, got {result.works_completed}"
    assert result.total_duration_seconds < 3.0, f"Expected < 3s, got {result.total_duration_seconds:.2f}s"
    
    print("✓ Multi-agent parallel test passed")


async def test_workflow_dependencies():
    """워크플로우 의존성 테스트"""
    print("\n=== Test 4: Workflow Dependencies ===")
    
    orchestrator = MultiAgentOrchestrator(WorkflowConfig(enable_toc=False, auto_document=False))
    
    agent = AgentInstance(
        agent_id="dep_agent",
        agent_type="dep",
        capabilities=["dep"]
    )
    orchestrator.register_agent(agent)
    orchestrator.register_work_handler("dep", mock_handler)
    
    work1 = orchestrator.create_work(
        name="Work 1",
        description="첫 번째 작업",
        work_type="dep",
        agent_type="dep",
        inputs={"work_type": "dep"},
        priority=WorkPriority.HIGH
    )
    
    work2 = orchestrator.create_work(
        name="Work 2",
        description="두 번째 작업",
        work_type="dep",
        agent_type="dep",
        inputs={"work_type": "dep"},
        dependencies=[work1.work_id]
    )
    
    work3 = orchestrator.create_work(
        name="Work 3",
        description="세 번째 작업",
        work_type="dep",
        agent_type="dep",
        inputs={"work_type": "dep"},
        dependencies=[work2.work_id]
    )
    
    result = await orchestrator.execute_workflow(works=[work1, work2, work3])
    
    assert result.works_completed == 3, f"Expected 3 completed, got {result.works_completed}"
    assert work3.completed_at is not None and work1.completed_at is not None and work3.completed_at > work1.completed_at, "Work 3 should complete after Work 1"
    
    print("✓ Workflow dependencies test passed")


async def test_documentation():
    """문서화 테스트"""
    print("\n=== Test 5: Documentation ===")
    
    orchestrator = MultiAgentOrchestrator(WorkflowConfig(enable_toc=False, auto_document=False))
    
    agent = AgentInstance(
        agent_id="doc_agent",
        agent_type="doc",
        capabilities=["doc"]
    )
    orchestrator.register_agent(agent)
    orchestrator.register_work_handler("doc", mock_handler)
    
    work = orchestrator.create_work(
        name="Doc Test",
        description="문서화 테스트",
        work_type="doc",
        agent_type="doc",
        inputs={"work_type": "doc"}
    )
    
    # 수동 문서 생성
    doc = orchestrator.generate_documentation(
        work_id=work.work_id,
        document_type=DocumentType.ARCHITECTURE_DESIGN,
        sections={
            "overview": "테스트 아키텍처",
            "components": "Component A, Component B",
            "data_flow": "데이터 흐름 설명",
            "interfaces": "인터페이스 정의"
        },
        metadata={"version": "1.0"}
    )
    
    assert doc.document_id is not None, "Document ID should not be None"
    assert doc.document_type == DocumentType.ARCHITECTURE_DESIGN
    
    # 워크 문서 생성
    await orchestrator.execute_workflow(works=[work])
    
    work_docs = orchestrator.doc_manager.get_work_documents(work.work_id)
    assert len(work_docs) > 0, "Should have work documents"
    
    print("✓ Documentation test passed")


async def test_toc_optimization():
    """TOC 최적화 테스트"""
    print("\n=== Test 6: TOC Optimization ===")
    
    config = WorkflowConfig(
        max_concurrent_works=10,
        enable_toc=True,
        auto_document=False,
        optimization_interval=5.0
    )
    
    orchestrator = MultiAgentOrchestrator(config)
    
    # 용량 제약 에이전트
    bottleneck_agent = AgentInstance(
        agent_id="bottleneck",
        agent_type="bottleneck",
        capabilities=["bottleneck"],
        max_concurrent_works=1
    )
    orchestrator.register_agent(bottleneck_agent)
    
    # 빠른 에이전트
    fast_agent = AgentInstance(
        agent_id="fast",
        agent_type="fast",
        capabilities=["fast"],
        max_concurrent_works=10
    )
    orchestrator.register_agent(fast_agent)
    
    async def slow_handler(inputs: dict, agent) -> dict:
        await asyncio.sleep(1.0)
        return {"status": "completed"}
    
    async def fast_handler(inputs: dict, agent) -> dict:
        await asyncio.sleep(0.1)
        return {"status": "completed"}
    
    orchestrator.register_work_handler("bottleneck", slow_handler)
    orchestrator.register_work_handler("fast", fast_handler)
    
    works = []
    # 병목 유발 작업
    for i in range(3):
        work = orchestrator.create_work(
            name=f"Bottleneck Work {i}",
            description="병목 작업",
            work_type="bottleneck",
            agent_type="bottleneck",
            inputs={},
            priority=WorkPriority.HIGH,
            estimated_tokens=2000
        )
        works.append(work)
    
    # 빠른 작업
    for i in range(5):
        work = orchestrator.create_work(
            name=f"Fast Work {i}",
            description="빠른 작업",
            work_type="fast",
            agent_type="fast",
            inputs={}
        )
        works.append(work)
    
    result = await orchestrator.execute_workflow(works=works)
    
    assert result.works_completed == 8, f"Expected 8 completed, got {result.works_completed}"
    
    # 병목 탐지 확인
    toc_report = orchestrator.toc_supervisor.get_optimization_report()
    assert toc_report['summary']['works_completed'] > 0
    
    print("✓ TOC optimization test passed")


async def test_workflow_template():
    """워크플로우 템플릿 테스트"""
    print("\n=== Test 7: Workflow Template ===")
    
    orchestrator = MultiAgentOrchestrator(WorkflowConfig(enable_toc=False, auto_document=False))
    
    # 모든 에이전트 타입 등록
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
        orchestrator.register_work_handler(agent_type, mock_handler)
    
    # ML 파이프라인 템플릿 실행
    result = await orchestrator.execute_workflow(
        template="ml_pipeline",
        parameters={"requirements": "테스트 모델", "data_sources": []}
    )
    
    assert result.works_completed == 6, f"Expected 6 works, got {result.works_completed}"
    
    # 웹 개발 템플릿 실행
    result2 = await orchestrator.execute_workflow(
        template="web_development",
        parameters={"requirements": "테스트 웹 앱"}
    )
    
    assert result2.works_completed == 5, f"Expected 5 works, got {result2.works_completed}"
    
    print("✓ Workflow template test passed")


async def run_all_tests():
    """모든 테스트 실행"""
    print("=" * 60)
    print("Running System Integration Tests")
    print("=" * 60)
    
    tests = [
        test_basic_workflow,
        test_raci_assignment,
        test_multi_agent_parallel,
        test_workflow_dependencies,
        test_documentation,
        test_toc_optimization,
        test_workflow_template
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            await test()
            passed += 1
        except AssertionError as e:
            print(f"✗ Test failed: {e}")
            failed += 1
        except Exception as e:
            print(f"✗ Test error: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("=" * 60)
    
    if failed == 0:
        print("\n✓ All tests passed!")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(run_all_tests())
    sys.exit(exit_code)
