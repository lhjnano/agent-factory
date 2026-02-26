"""
Context Management System 단위 테스트
"""
import pytest
import json
from datetime import datetime

from agent_factory.core.context import WorkContext, WorkflowContext


class TestWorkContext:
    """WorkContext 단위 테스트"""
    
    def test_work_context_initialization(self):
        """WorkContext 초기화 테스트"""
        work_ctx = WorkContext(
            work_id="work_001",
            work_type="data_collection",
            inputs={"source": "data.csv"}
        )
        
        assert work_ctx.work_id == "work_001"
        assert work_ctx.work_type == "data_collection"
        assert work_ctx.inputs == {"source": "data.csv"}
        assert work_ctx.outputs == {}
        assert work_ctx.accumulated_context == {}
        assert isinstance(work_ctx.created_at, datetime)
        assert isinstance(work_ctx.updated_at, datetime)
    
    def test_update_outputs(self):
        """outputs 업데이트 테스트"""
        work_ctx = WorkContext(
            work_id="work_001",
            work_type="data_collection"
        )
        
        work_ctx.update_outputs({"rows": 100, "columns": 5})
        
        assert work_ctx.outputs == {"rows": 100, "columns": 5}
        assert isinstance(work_ctx.updated_at, datetime)
        
        # outputs 덮어쓰기 테스트
        work_ctx.update_outputs({"rows": 200})
        
        assert work_ctx.outputs == {"rows": 200, "columns": 5}
    
    def test_add_to_context(self):
        """accumulated_context 추가 테스트"""
        work_ctx = WorkContext(
            work_id="work_001",
            work_type="data_collection"
        )
        
        work_ctx.add_to_context("summary", {"total_rows": 100})
        work_ctx.add_to_context("metrics", {"accuracy": 0.95})
        
        assert work_ctx.accumulated_context == {
            "summary": {"total_rows": 100},
            "metrics": {"accuracy": 0.95}
        }
        assert isinstance(work_ctx.updated_at, datetime)
    
    def test_extend_context(self):
        """accumulated_context 병합 테스트"""
        work_ctx = WorkContext(
            work_id="work_001",
            work_type="data_collection"
        )
        
        work_ctx.extend_context({
            "summary": {"total_rows": 100},
            "metrics": {"accuracy": 0.95}
        })
        
        assert work_ctx.accumulated_context == {
            "summary": {"total_rows": 100},
            "metrics": {"accuracy": 0.95}
        }
    
    def test_get_full_context(self):
        """전체 context 조회 테스트"""
        work_ctx = WorkContext(
            work_id="work_001",
            work_type="data_collection",
            inputs={"source": "data.csv"},
            metadata={"priority": "high"}
        )
        
        work_ctx.update_outputs({"rows": 100})
        work_ctx.add_to_context("summary", {"total_rows": 100})
        
        full_ctx = work_ctx.get_full_context()
        
        assert full_ctx["inputs"] == {"source": "data.csv"}
        assert full_ctx["outputs"] == {"rows": 100}
        assert full_ctx["accumulated"] == {"summary": {"total_rows": 100}}
        assert full_ctx["metadata"] == {"priority": "high"}
    
    def test_to_dict(self):
        """WorkContext to_dict 테스트"""
        work_ctx = WorkContext(
            work_id="work_001",
            work_type="data_collection",
            inputs={"source": "data.csv"}
        )
        
        work_ctx.update_outputs({"rows": 100})
        work_ctx.add_to_context("summary", {"total_rows": 100})
        
        data = work_ctx.to_dict()
        
        assert data["work_id"] == "work_001"
        assert data["work_type"] == "data_collection"
        assert data["inputs"] == {"source": "data.csv"}
        assert data["outputs"] == {"rows": 100}
        assert data["accumulated_context"] == {"summary": {"total_rows": 100}}
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_from_dict(self):
        """WorkContext from_dict 테스트"""
        data = {
            "work_id": "work_001",
            "work_type": "data_collection",
            "inputs": {"source": "data.csv"},
            "outputs": {"rows": 100},
            "accumulated_context": {"summary": {"total_rows": 100}},
            "metadata": {},
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        work_ctx = WorkContext.from_dict(data)
        
        assert work_ctx.work_id == "work_001"
        assert work_ctx.work_type == "data_collection"
        assert work_ctx.inputs == {"source": "data.csv"}
        assert work_ctx.outputs == {"rows": 100}
        assert work_ctx.accumulated_context == {"summary": {"total_rows": 100}}


class TestWorkflowContext:
    """WorkflowContext 단위 테스트"""
    
    def test_workflow_context_initialization(self):
        """WorkflowContext 초기화 테스트"""
        workflow_ctx = WorkflowContext(
            workflow_id="workflow_001",
            name="ML Pipeline",
            description="머신러닝 파이프라인"
        )
        
        assert workflow_ctx.workflow_id == "workflow_001"
        assert workflow_ctx.name == "ML Pipeline"
        assert workflow_ctx.description == "머신러닝 파이프라인"
        assert workflow_ctx.work_contexts == {}
        assert workflow_ctx.global_context == {}
        assert isinstance(workflow_ctx.created_at, datetime)
        assert isinstance(workflow_ctx.updated_at, datetime)
    
    def test_add_work_context(self):
        """work context 추가 테스트"""
        workflow_ctx = WorkflowContext(
            workflow_id="workflow_001",
            name="ML Pipeline"
        )
        
        work_ctx = WorkContext(
            work_id="work_001",
            work_type="data_collection"
        )
        
        workflow_ctx.add_work_context(work_ctx)
        
        assert "work_001" in workflow_ctx.work_contexts
        assert workflow_ctx.work_contexts["work_001"] == work_ctx
    
    def test_get_work_context(self):
        """work context 조회 테스트"""
        workflow_ctx = WorkflowContext(
            workflow_id="workflow_001",
            name="ML Pipeline"
        )
        
        work_ctx = WorkContext(
            work_id="work_001",
            work_type="data_collection"
        )
        workflow_ctx.add_work_context(work_ctx)
        
        retrieved = workflow_ctx.get_work_context("work_001")
        
        assert retrieved is not None
        assert retrieved.work_id == "work_001"
        
        # 존재하지 않는 work_id 조회
        not_found = workflow_ctx.get_work_context("work_999")
        assert not_found is None
    
    def test_get_work_outputs(self):
        """work outputs 조회 테스트"""
        workflow_ctx = WorkflowContext(
            workflow_id="workflow_001",
            name="ML Pipeline"
        )
        
        work_ctx = WorkContext(
            work_id="work_001",
            work_type="data_collection"
        )
        work_ctx.update_outputs({"rows": 100})
        workflow_ctx.add_work_context(work_ctx)
        
        outputs = workflow_ctx.get_work_outputs("work_001")
        
        assert outputs == {"rows": 100}
        
        # 존재하지 않는 work_id
        not_found_outputs = workflow_ctx.get_work_outputs("work_999")
        assert not_found_outputs == {}
    
    def test_resolve_dependencies(self):
        """dependencies 해결 테스트"""
        workflow_ctx = WorkflowContext(
            workflow_id="workflow_001",
            name="ML Pipeline"
        )
        
        # 이전 work 추가
        work1 = WorkContext(
            work_id="data_collection",
            work_type="data_collection"
        )
        work1.update_outputs({"data": [[1, 2], [3, 4]]})
        work1.add_to_context("summary", {"total": 4})
        workflow_ctx.add_work_context(work1)
        
        # dependency 해결
        resolved = workflow_ctx.resolve_dependencies(
            "preprocessing",
            ["data_collection"]
        )
        
        assert "data_collection" in resolved
        assert resolved["data_collection"]["outputs"] == {"data": [[1, 2], [3, 4]]}
        assert resolved["data_collection"]["accumulated"] == {"summary": {"total": 4}}
    
    def test_resolve_dependencies_multiple(self):
        """여러 dependencies 해결 테스트"""
        workflow_ctx = WorkflowContext(
            workflow_id="workflow_001",
            name="ML Pipeline"
        )
        
        work1 = WorkContext(work_id="work1", work_type="type1")
        work1.update_outputs({"result": 1})
        workflow_ctx.add_work_context(work1)
        
        work2 = WorkContext(work_id="work2", work_type="type2")
        work2.update_outputs({"result": 2})
        workflow_ctx.add_work_context(work2)
        
        resolved = workflow_ctx.resolve_dependencies("work3", ["work1", "work2"])
        
        assert len(resolved) == 2
        assert resolved["work1"]["outputs"] == {"result": 1}
        assert resolved["work2"]["outputs"] == {"result": 2}
    
    def test_resolve_dependencies_not_found(self):
        """존재하지 않는 dependency 해결 테스트"""
        workflow_ctx = WorkflowContext(
            workflow_id="workflow_001",
            name="ML Pipeline"
        )
        
        resolved = workflow_ctx.resolve_dependencies(
            "preprocessing",
            ["nonexistent_work"]
        )
        
        assert resolved == {}
    
    def test_add_global_context(self):
        """global context 추가 테스트"""
        workflow_ctx = WorkflowContext(
            workflow_id="workflow_001",
            name="ML Pipeline"
        )
        
        workflow_ctx.add_global_context("project_id", "proj_123")
        workflow_ctx.add_global_context("config", {"batch_size": 32})
        
        assert workflow_ctx.global_context == {
            "project_id": "proj_123",
            "config": {"batch_size": 32}
        }
    
    def test_get_full_context_for_work(self):
        """work 전체 context 조회 테스트"""
        workflow_ctx = WorkflowContext(
            workflow_id="workflow_001",
            name="ML Pipeline"
        )
        
        workflow_ctx.add_global_context("project_id", "proj_123")
        
        # 이전 work 추가
        work1 = WorkContext(
            work_id="data_collection",
            work_type="data_collection"
        )
        work1.update_outputs({"data": [[1, 2], [3, 4]]})
        workflow_ctx.add_work_context(work1)
        
        # 현재 work 추가
        work2 = WorkContext(
            work_id="preprocessing",
            work_type="preprocessing",
            inputs={"data": "data_collection"}
        )
        work2.metadata["dependencies"] = ["data_collection"]
        workflow_ctx.add_work_context(work2)
        
        full_ctx = workflow_ctx.get_full_context_for_work("preprocessing")
        
        assert full_ctx["work_inputs"] == {"data": "data_collection"}
        assert full_ctx["global_context"] == {"project_id": "proj_123"}
        assert "data_collection" in full_ctx["resolved_dependencies"]
        assert full_ctx["resolved_dependencies"]["data_collection"]["outputs"] == {
            "data": [[1, 2], [3, 4]]
        }
    
    def test_get_full_context_for_work_not_found(self):
        """존재하지 않는 work의 context 조회 테스트"""
        workflow_ctx = WorkflowContext(
            workflow_id="workflow_001",
            name="ML Pipeline"
        )
        
        full_ctx = workflow_ctx.get_full_context_for_work("nonexistent_work")
        
        assert full_ctx == {}
    
    def test_merge_work_outputs_to_global(self):
        """work outputs를 global context로 병합 테스트"""
        workflow_ctx = WorkflowContext(
            workflow_id="workflow_001",
            name="ML Pipeline"
        )
        
        work_ctx = WorkContext(
            work_id="data_collection",
            work_type="data_collection"
        )
        work_ctx.update_outputs({"data": [[1, 2], [3, 4]]})
        workflow_ctx.add_work_context(work_ctx)
        
        workflow_ctx.merge_work_outputs_to_global("data_collection")
        
        assert "data_collection" in workflow_ctx.global_context
        assert workflow_ctx.global_context["data_collection"] == {"data": [[1, 2], [3, 4]]}
    
    def test_merge_work_outputs_to_global_with_keys(self):
        """특정 keys만 global context로 병합 테스트"""
        workflow_ctx = WorkflowContext(
            workflow_id="workflow_001",
            name="ML Pipeline"
        )
        
        work_ctx = WorkContext(
            work_id="data_collection",
            work_type="data_collection"
        )
        work_ctx.update_outputs({"data": [[1, 2], [3, 4]], "rows": 4})
        workflow_ctx.add_work_context(work_ctx)
        
        # "data" key만 병합
        workflow_ctx.merge_work_outputs_to_global("data_collection", keys=["data"])
        
        # 전체 work 결과가 아닌 특정 key만 병합되어야 함
        assert "data_collection" not in workflow_ctx.global_context
        assert "data_collection.data" in workflow_ctx.global_context
        assert workflow_ctx.global_context["data_collection.data"] == [[1, 2], [3, 4]]
    
    def test_to_dict(self):
        """WorkflowContext to_dict 테스트"""
        workflow_ctx = WorkflowContext(
            workflow_id="workflow_001",
            name="ML Pipeline",
            description="머신러닝 파이프라인"
        )
        
        workflow_ctx.add_global_context("project_id", "proj_123")
        
        work_ctx = WorkContext(
            work_id="work_001",
            work_type="data_collection"
        )
        workflow_ctx.add_work_context(work_ctx)
        
        data = workflow_ctx.to_dict()
        
        assert data["workflow_id"] == "workflow_001"
        assert data["name"] == "ML Pipeline"
        assert data["description"] == "머신러닝 파이프라인"
        assert "work_contexts" in data
        assert "global_context" in data
        assert data["global_context"] == {"project_id": "proj_123"}
        assert "created_at" in data
        assert "updated_at" in data
    
    def test_from_dict(self):
        """WorkflowContext from_dict 테스트"""
        data = {
            "workflow_id": "workflow_001",
            "name": "ML Pipeline",
            "description": "머신러닝 파이프라인",
            "work_contexts": {},
            "global_context": {"project_id": "proj_123"},
            "dependency_chain": [],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        workflow_ctx = WorkflowContext.from_dict(data)
        
        assert workflow_ctx.workflow_id == "workflow_001"
        assert workflow_ctx.name == "ML Pipeline"
        assert workflow_ctx.description == "머신러닝 파이프라인"
        assert workflow_ctx.global_context == {"project_id": "proj_123"}
