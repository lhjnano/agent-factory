"""
Context Management System 예제

이 예제는 WorkContext와 WorkflowContext를 사용하여
work 별 context가 누적되는 것을 보여줍니다.
"""

import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass
class WorkContext:
    work_id: str
    work_type: str
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    accumulated_context: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def update_outputs(self, outputs: Dict[str, Any]):
        self.outputs.update(outputs)
        self.updated_at = datetime.now()
    
    def add_to_context(self, key: str, value: Any):
        self.accumulated_context[key] = value
        self.updated_at = datetime.now()


@dataclass
class WorkflowContext:
    workflow_id: str
    name: str
    description: str = ""
    work_contexts: Dict[str, WorkContext] = field(default_factory=dict)
    global_context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def add_work_context(self, work_context: WorkContext):
        self.work_contexts[work_context.work_id] = work_context
        self.updated_at = datetime.now()
    
    def get_work_context(self, work_id: str) -> Optional[WorkContext]:
        return self.work_contexts.get(work_id)
    
    def resolve_dependencies(self, work_id: str, dependency_ids: List[str]) -> Dict[str, Any]:
        resolved_context = {}
        for dep_id in dependency_ids:
            dep_context = self.work_contexts.get(dep_id)
            if dep_context:
                resolved_context[dep_id] = {
                    "outputs": dep_context.outputs,
                    "accumulated": dep_context.accumulated_context
                }
        return resolved_context
    
    def merge_work_outputs_to_global(self, work_id: str):
        work_context = self.work_contexts.get(work_id)
        if not work_context:
            return
        self.global_context[work_id] = work_context.outputs
        self.updated_at = datetime.now()


class ContextManager:
    def __init__(self):
        self._workflow_contexts: Dict[str, WorkflowContext] = {}
    
    def create_workflow_context(self, workflow_id: str, name: str, description: str = "") -> WorkflowContext:
        workflow_ctx = WorkflowContext(
            workflow_id=workflow_id,
            name=name,
            description=description
        )
        self._workflow_contexts[workflow_id] = workflow_ctx
        return workflow_ctx
    
    def create_work_context(
        self,
        workflow_id: str,
        work_id: str,
        work_type: str,
        inputs: Dict[str, Any],
        dependencies: Optional[list] = None
    ) -> WorkContext:
        workflow_ctx = self._workflow_contexts.get(workflow_id)
        if not workflow_ctx:
            raise ValueError(f"Workflow context not found: {workflow_id}")
        
        work_ctx = WorkContext(
            work_id=work_id,
            work_type=work_type,
            inputs=inputs
        )
        
        if dependencies:
            work_ctx.metadata["dependencies"] = dependencies
            resolved = workflow_ctx.resolve_dependencies(work_id, dependencies)
            work_ctx.accumulated_context.update(resolved)
        
        workflow_ctx.add_work_context(work_ctx)
        return work_ctx
    
    def update_work_outputs(
        self,
        workflow_id: str,
        work_id: str,
        outputs: Dict[str, Any],
        propagate_to_global: bool = True
    ):
        workflow_ctx = self._workflow_contexts.get(workflow_id)
        if not workflow_ctx:
            raise ValueError(f"Workflow context not found: {workflow_id}")
        
        work_ctx = workflow_ctx.get_work_context(work_id)
        if not work_ctx:
            raise ValueError(f"Work context not found: {work_id}")
        
        work_ctx.update_outputs(outputs)
        
        if propagate_to_global:
            workflow_ctx.merge_work_outputs_to_global(work_id)
    
    def get_global_context(self, workflow_id: str) -> Dict[str, Any]:
        workflow_ctx = self._workflow_contexts.get(workflow_id)
        if not workflow_ctx:
            return {}
        return workflow_ctx.global_context
    
    def get_full_context_for_work(self, workflow_id: str, work_id: str) -> Dict[str, Any]:
        workflow_ctx = self._workflow_contexts.get(workflow_id)
        if not workflow_ctx:
            return {}
        work_ctx = workflow_ctx.get_work_context(work_id)
        if not work_ctx:
            return {}
        return {
            "work_inputs": work_ctx.inputs,
            "global_context": workflow_ctx.global_context,
            "resolved_dependencies": workflow_ctx.resolve_dependencies(
                work_id,
                work_ctx.metadata.get("dependencies", [])
            )
        }


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
