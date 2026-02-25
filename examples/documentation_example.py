"""
문서화 시스템 사용 예제
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent_factory.core import (
    MultiAgentOrchestrator, WorkflowConfig,
    AgentInstance, Work, WorkPriority,
    DocumentType
)


async def work_handler(inputs: dict, agent) -> dict:
    await asyncio.sleep(0.3)
    return {
        "status": "completed",
        "metrics": {"accuracy": 0.95, "f1_score": 0.93}
    }


async def main():
    print("=== Documentation System Example ===\n")
    
    config = WorkflowConfig(
        enable_toc=False,
        auto_document=True
    )
    
    orchestrator = MultiAgentOrchestrator(config)
    
    # 에이전트 등록
    agent = AgentInstance(
        agent_id="agent_1",
        agent_type="design_development",
        capabilities=["design", "code_generation"]
    )
    orchestrator.register_agent(agent)
    orchestrator.register_work_handler("design_development", work_handler)
    
    # Work 생성
    work = orchestrator.create_work(
        name="Design Model",
        description="CNN 모델 설계",
        work_type="design_development",
        agent_type="design_development",
        inputs={"model_type": "CNN"}
    )
    
    # 수동 문서 생성
    print("1. Creating architecture design document...")
    doc1 = orchestrator.generate_documentation(
        work_id=work.work_id,
        document_type=DocumentType.ARCHITECTURE_DESIGN,
        sections={
            "overview": "이미지 분류를 위한 CNN 아키텍처",
            "components": "Conv2D layers, MaxPooling, Dense layers",
            "data_flow": "Input -> Conv Layers -> FC Layers -> Output",
            "interfaces": "API endpoint for inference"
        },
        metadata={"version": "1.0", "author": "agent_1"}
    )
    
    print(f"   Document ID: {doc1.document_id}")
    print(f"   Type: {doc1.document_type.value}")
    
    # API 스펙 문서 생성
    print("2. Creating API specification document...")
    doc2 = orchestrator.generate_documentation(
        work_id=work.work_id,
        document_type=DocumentType.API_SPECIFICATION,
        sections={
            "endpoint": "/api/predict",
            "method": "POST",
            "request_body": '{"image_url": "string"}',
            "response": '{"prediction": "label", "confidence": 0.95}'
        },
        metadata={"version": "1.0"}
    )
    
    print(f"   Document ID: {doc2.document_id}")
    
    # 워크플로우 실행 (자동 문서화)
    print("3. Executing workflow with auto-documentation...")
    result = await orchestrator.execute_workflow(works=[work])
    
    print(f"   Auto-generated documents: {len(result.documents)}")
    
    # 문서 요약
    print("\n4. Documentation summary...")
    summary = orchestrator.doc_manager.get_documentation_summary()
    print(f"   Total documents: {summary['total_documents']}")
    print(f"   Works with docs: {summary['work_with_docs']}")
    print(f"   By type:")
    for doc_type, count in summary['by_type'].items():
        print(f"     - {doc_type}: {count}")
    
    # 특정 문서 가져오기
    print("\n5. Retrieving work documents...")
    work_docs = orchestrator.doc_manager.get_work_documents(work.work_id)
    print(f"   Documents for work {work.work_id}: {len(work_docs)}")
    for doc in work_docs:
        print(f"     - {doc.title} ({doc.document_type.value})")
        print(f"       Sections: {list(doc.sections.keys())}")


if __name__ == "__main__":
    asyncio.run(main())
