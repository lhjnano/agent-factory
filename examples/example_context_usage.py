"""
Context Management System 예제

이 예제는 WorkContext와 WorkflowContext를 사용하여
work 별 context가 누적되는 것을 보여줍니다.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src" / "agent_factory" / "core"))

from context import WorkContext, WorkflowContext
from context_manager import ContextManager


async def example_1_work_context():
    """WorkContext 기본 사용 예제"""
    print("=" * 80)
    print("예제 1: WorkContext 기본 사용")
    print("=" * 80)
    
    work_ctx = WorkContext(
        work_id="work_001",
        work_type="data_collection",
        inputs={"source": "data.csv"}
    )
    
    work_ctx.update_outputs({"rows": 100, "columns": 5})
    work_ctx.add_to_context("summary", {"total_rows": 100})
    
    print(f"Work ID: {work_ctx.work_id}")
    print(f"Inputs: {work_ctx.inputs}")
    print(f"Outputs: {work_ctx.outputs}")
    print(f"Accumulated Context: {work_ctx.accumulated_context}")
    print()


async def example_2_workflow_context():
    """WorkflowContext 기본 사용 예제"""
    print("=" * 80)
    print("예제 2: WorkflowContext 기본 사용")
    print("=" * 80)
    
    workflow_ctx = WorkflowContext(
        workflow_id="workflow_001",
        name="ML Pipeline",
        description="머신러닝 파이프라인"
    )
    
    work1_ctx = WorkContext(
        work_id="data_collection",
        work_type="data_collection",
        inputs={"source": "data.csv"}
    )
    work1_ctx.update_outputs({"data": [[1, 2], [3, 4]]})
    
    work2_ctx = WorkContext(
        work_id="preprocessing",
        work_type="preprocessing",
        inputs={"data": "data_collection"}
    )
    work2_ctx.metadata["dependencies"] = ["data_collection"]
    work2_ctx.update_outputs({"preprocessed": [[1.0, 2.0], [3.0, 4.0]]})
    
    workflow_ctx.add_work_context(work1_ctx)
    workflow_ctx.add_work_context(work2_ctx)
    
    resolved = workflow_ctx.resolve_dependencies("preprocessing", ["data_collection"])
    print(f"Resolved dependencies for preprocessing: {resolved}")
    print()


async def example_3_context_manager():
    """ContextManager 사용 예제"""
    print("=" * 80)
    print("예제 3: ContextManager를 통한 context 관리")
    print("=" * 80)
    
    ctx_manager = ContextManager()
    
    workflow_ctx = ctx_manager.create_workflow_context(
        workflow_id="workflow_002",
        name="Image Classification",
        description="이미지 분류 모델 개발"
    )
    
    work1 = ctx_manager.create_work_context(
        workflow_id="workflow_002",
        work_id="data_prep",
        work_type="data_preparation",
        inputs={"images": "/data/images", "labels": "/data/labels"}
    )
    
    work2 = ctx_manager.create_work_context(
        workflow_id="workflow_002",
        work_id="train_model",
        work_type="training",
        inputs={"model_config": "resnet50"},
        dependencies=["data_prep"]
    )
    
    ctx_manager.update_work_outputs(
        "workflow_002",
        "data_prep",
        {"train_images": 1000, "val_images": 200}
    )
    
    full_ctx = ctx_manager.get_full_context_for_work("workflow_002", "train_model")
    print(f"Full context for train_model:")
    print(f"  Work inputs: {full_ctx.get('work_inputs')}")
    print(f"  Resolved dependencies: {full_ctx.get('resolved_dependencies')}")
    
    print(f"\nGlobal context: {ctx_manager.get_global_context('workflow_002')}")
    print()


async def example_4_work_accumulation():
    """Work가 진행될수록 context가 누적되는 예제"""
    print("=" * 80)
    print("예제 4: Context 누적 및 전파")
    print("=" * 80)
    
    ctx_manager = ContextManager()
    
    workflow_ctx = ctx_manager.create_workflow_context(
        workflow_id="workflow_003",
        name="Context Accumulation Demo"
    )
    
    works = [
        {"id": "collect", "type": "collection", "inputs": {"source": "api"}},
        {"id": "process", "type": "processing", "inputs": {"data": None}, "deps": ["collect"]},
        {"id": "analyze", "type": "analysis", "inputs": {"data": None}, "deps": ["process"]},
        {"id": "report", "type": "reporting", "inputs": {"data": None}, "deps": ["analyze"]}
    ]
    
    for work in works:
        work_ctx = ctx_manager.create_work_context(
            workflow_id="workflow_003",
            work_id=work["id"],
            work_type=work["type"],
            inputs=work["inputs"],
            dependencies=work.get("deps", [])
        )
        
        outputs = {
            "collect": {"raw_data": [1, 2, 3, 4, 5]},
            "process": {"processed": [1.0, 2.0, 3.0, 4.0, 5.0]},
            "analyze": {"stats": {"mean": 3.0, "std": 1.58}},
            "report": {"summary": "Analysis complete"}
        }
        
        ctx_manager.update_work_outputs("workflow_003", work["id"], outputs[work["id"]])
        
        print(f"Work '{work['id']}' completed:")
        print(f"  Outputs: {outputs[work['id']]}")
        print(f"  Global context keys: {list(ctx_manager.get_global_context('workflow_003').keys())}")
        print()


async def main():
    await example_1_work_context()
    await example_2_workflow_context()
    await example_3_context_manager()
    await example_4_work_accumulation()
    
    print("=" * 80)
    print("모든 예제 완료!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
