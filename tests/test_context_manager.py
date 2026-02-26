"""
ContextManager 단위 테스트
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from agent_factory.core.context_manager import ContextManager
from agent_factory.core.context import WorkContext, WorkflowContext


class TestContextManager:
    """ContextManager 단위 테스트"""
    
    def test_context_manager_initialization(self):
        """ContextManager 초기화 테스트"""
        ctx_manager = ContextManager()
        
        assert ctx_manager._workflow_contexts == {}
        assert ctx_manager._memory_storage is None
        assert ctx_manager._filesystem_storage is None
    
    def test_set_mcp_sessions(self):
        """MCP sessions 설정 테스트"""
        ctx_manager = ContextManager()
        
        memory_session = MagicMock()
        filesystem_session = MagicMock()
        
        ctx_manager.set_mcp_sessions(memory_session, filesystem_session)
        
        assert ctx_manager._memory_storage == memory_session
        assert ctx_manager._filesystem_storage == filesystem_session
    
    def test_create_workflow_context(self):
        """workflow context 생성 테스트"""
        ctx_manager = ContextManager()
        
        workflow_ctx = ctx_manager.create_workflow_context(
            workflow_id="workflow_001",
            name="ML Pipeline",
            description="머신러닝 파이프라인"
        )
        
        assert isinstance(workflow_ctx, WorkflowContext)
        assert workflow_ctx.workflow_id == "workflow_001"
        assert workflow_ctx.name == "ML Pipeline"
        assert workflow_ctx.description == "머신러닝 파이프라인"
        assert "workflow_001" in ctx_manager._workflow_contexts
    
    def test_get_workflow_context(self):
        """workflow context 조회 테스트"""
        ctx_manager = ContextManager()
        
        workflow_ctx = ctx_manager.create_workflow_context(
            workflow_id="workflow_001",
            name="ML Pipeline"
        )
        
        retrieved = ctx_manager.get_workflow_context("workflow_001")
        
        assert retrieved is not None
        assert retrieved.workflow_id == "workflow_001"
        assert retrieved is workflow_ctx
        
        # 존재하지 않는 workflow_id 조회
        not_found = ctx_manager.get_workflow_context("workflow_999")
        assert not_found is None
    
    def test_create_work_context(self):
        """work context 생성 테스트"""
        ctx_manager = ContextManager()
        
        ctx_manager.create_workflow_context(
            workflow_id="workflow_001",
            name="ML Pipeline"
        )
        
        work_ctx = ctx_manager.create_work_context(
            workflow_id="workflow_001",
            work_id="work_001",
            work_type="data_collection",
            inputs={"source": "data.csv"}
        )
        
        assert isinstance(work_ctx, WorkContext)
        assert work_ctx.work_id == "work_001"
        assert work_ctx.work_type == "data_collection"
        assert work_ctx.inputs == {"source": "data.csv"}
    
    def test_create_work_context_with_dependencies(self):
        """dependencies가 있는 work context 생성 테스트"""
        ctx_manager = ContextManager()
        
        workflow_ctx = ctx_manager.create_workflow_context(
            workflow_id="workflow_001",
            name="ML Pipeline"
        )
        
        # 이전 work 추가
        prev_work = WorkContext(
            work_id="prev_work",
            work_type="data_collection"
        )
        prev_work.update_outputs({"data": [[1, 2], [3, 4]]})
        workflow_ctx.add_work_context(prev_work)
        
        # dependencies가 있는 work 생성
        work_ctx = ctx_manager.create_work_context(
            workflow_id="workflow_001",
            work_id="work_001",
            work_type="preprocessing",
            inputs={"data": None},
            dependencies=["prev_work"]
        )
        
        # dependencies가 해결되어 accumulated_context에 포함되어야 함
        assert work_ctx.metadata["dependencies"] == ["prev_work"]
        assert "prev_work" in work_ctx.accumulated_context
    
    def test_create_work_context_workflow_not_found(self):
        """존재하지 않는 workflow로 work context 생성 시도"""
        ctx_manager = ContextManager()
        
        with pytest.raises(ValueError, match="Workflow context not found"):
            ctx_manager.create_work_context(
                workflow_id="nonexistent_workflow",
                work_id="work_001",
                work_type="data_collection",
                inputs={}
            )
    
    def test_get_work_context(self):
        """work context 조회 테스트"""
        ctx_manager = ContextManager()
        
        ctx_manager.create_workflow_context(
            workflow_id="workflow_001",
            name="ML Pipeline"
        )
        
        ctx_manager.create_work_context(
            workflow_id="workflow_001",
            work_id="work_001",
            work_type="data_collection",
            inputs={}
        )
        
        retrieved = ctx_manager.get_work_context("workflow_001", "work_001")
        
        assert retrieved is not None
        assert retrieved.work_id == "work_001"
        
        # 존재하지 않는 workflow_id
        not_found = ctx_manager.get_work_context("workflow_999", "work_001")
        assert not_found is None
        
        # 존재하지 않는 work_id
        not_found2 = ctx_manager.get_work_context("workflow_001", "work_999")
        assert not_found2 is None
    
    def test_update_work_outputs(self):
        """work outputs 업데이트 테스트"""
        ctx_manager = ContextManager()
        
        ctx_manager.create_workflow_context(
            workflow_id="workflow_001",
            name="ML Pipeline"
        )
        
        ctx_manager.create_work_context(
            workflow_id="workflow_001",
            work_id="work_001",
            work_type="data_collection",
            inputs={}
        )
        
        ctx_manager.update_work_outputs(
            workflow_id="workflow_001",
            work_id="work_001",
            outputs={"rows": 100, "columns": 5}
        )
        
        work_ctx = ctx_manager.get_work_context("workflow_001", "work_001")
        assert work_ctx.outputs == {"rows": 100, "columns": 5}
    
    def test_update_work_outputs_propagate_to_global(self):
        """work outputs를 global context로 전파 테스트"""
        ctx_manager = ContextManager()
        
        ctx_manager.create_workflow_context(
            workflow_id="workflow_001",
            name="ML Pipeline"
        )
        
        ctx_manager.create_work_context(
            workflow_id="workflow_001",
            work_id="work_001",
            work_type="data_collection",
            inputs={}
        )
        
        ctx_manager.update_work_outputs(
            workflow_id="workflow_001",
            work_id="work_001",
            outputs={"data": [[1, 2], [3, 4]]},
            propagate_to_global=True
        )
        
        global_ctx = ctx_manager.get_global_context("workflow_001")
        assert "work_001" in global_ctx
        assert global_ctx["work_001"] == {"data": [[1, 2], [3, 4]]}
    
    def test_update_work_outputs_no_propagate(self):
        """global context로 전파하지 않는 테스트"""
        ctx_manager = ContextManager()
        
        ctx_manager.create_workflow_context(
            workflow_id="workflow_001",
            name="ML Pipeline"
        )
        
        ctx_manager.create_work_context(
            workflow_id="workflow_001",
            work_id="work_001",
            work_type="data_collection",
            inputs={}
        )
        
        ctx_manager.update_work_outputs(
            workflow_id="workflow_001",
            work_id="work_001",
            outputs={"data": [[1, 2], [3, 4]]},
            propagate_to_global=False
        )
        
        global_ctx = ctx_manager.get_global_context("workflow_001")
        assert "work_001" not in global_ctx
    
    def test_update_work_outputs_workflow_not_found(self):
        """존재하지 않는 workflow로 outputs 업데이트 시도"""
        ctx_manager = ContextManager()
        
        with pytest.raises(ValueError, match="Workflow context not found"):
            ctx_manager.update_work_outputs(
                workflow_id="nonexistent_workflow",
                work_id="work_001",
                outputs={}
            )
    
    def test_get_full_context_for_work(self):
        """work 전체 context 조회 테스트"""
        ctx_manager = ContextManager()
        
        ctx_manager.create_workflow_context(
            workflow_id="workflow_001",
            name="ML Pipeline"
        )
        
        ctx_manager.add_global_context("workflow_001", "project_id", "proj_123")
        
        # 이전 work 추가
        ctx_manager.create_work_context(
            workflow_id="workflow_001",
            work_id="prev_work",
            work_type="data_collection",
            inputs={}
        )
        ctx_manager.update_work_outputs(
            "workflow_001",
            "prev_work",
            {"data": [[1, 2], [3, 4]]}
        )
        
        # 현재 work 추가
        ctx_manager.create_work_context(
            workflow_id="workflow_001",
            work_id="work_001",
            work_type="preprocessing",
            inputs={"data": None},
            dependencies=["prev_work"]
        )
        
        full_ctx = ctx_manager.get_full_context_for_work("workflow_001", "work_001")
        
        assert full_ctx["work_inputs"] == {"data": None}
        assert full_ctx["global_context"]["project_id"] == "proj_123"
        assert full_ctx["global_context"]["prev_work"] == {"data": [[1, 2], [3, 4]]}
        assert "prev_work" in full_ctx["resolved_dependencies"]
        assert full_ctx["resolved_dependencies"]["prev_work"]["outputs"] == {"data": [[1, 2], [3, 4]]}
    
    def test_get_global_context(self):
        """global context 조회 테스트"""
        ctx_manager = ContextManager()
        
        ctx_manager.create_workflow_context(
            workflow_id="workflow_001",
            name="ML Pipeline"
        )
        
        ctx_manager.add_global_context("workflow_001", "project_id", "proj_123")
        
        global_ctx = ctx_manager.get_global_context("workflow_001")
        
        assert global_ctx == {"project_id": "proj_123"}
        
        # 존재하지 않는 workflow_id
        not_found = ctx_manager.get_global_context("workflow_999")
        assert not_found == {}
    
    def test_add_global_context(self):
        """global context 추가 테스트"""
        ctx_manager = ContextManager()
        
        ctx_manager.create_workflow_context(
            workflow_id="workflow_001",
            name="ML Pipeline"
        )
        
        ctx_manager.add_global_context("workflow_001", "project_id", "proj_123")
        ctx_manager.add_global_context("workflow_001", "config", {"batch_size": 32})
        
        global_ctx = ctx_manager.get_global_context("workflow_001")
        
        assert global_ctx == {
            "project_id": "proj_123",
            "config": {"batch_size": 32}
        }
    
    def test_add_global_context_workflow_not_found(self):
        """존재하지 않는 workflow로 global context 추가 시도"""
        ctx_manager = ContextManager()
        
        with pytest.raises(ValueError, match="Workflow context not found"):
            ctx_manager.add_global_context("nonexistent_workflow", "key", "value")
    
    def test_clear_workflow_context(self):
        """workflow context 삭제 테스트"""
        ctx_manager = ContextManager()
        
        ctx_manager.create_workflow_context(
            workflow_id="workflow_001",
            name="ML Pipeline"
        )
        
        assert "workflow_001" in ctx_manager._workflow_contexts
        
        ctx_manager.clear_workflow_context("workflow_001")
        
        assert "workflow_001" not in ctx_manager._workflow_contexts
    
    def test_clear_all_contexts(self):
        """모든 context 삭제 테스트"""
        ctx_manager = ContextManager()
        
        ctx_manager.create_workflow_context(
            workflow_id="workflow_001",
            name="ML Pipeline"
        )
        ctx_manager.create_workflow_context(
            workflow_id="workflow_002",
            name="Data Pipeline"
        )
        
        assert len(ctx_manager._workflow_contexts) == 2
        
        ctx_manager.clear_all_contexts()
        
        assert len(ctx_manager._workflow_contexts) == 0
    
    @pytest.mark.asyncio
    async def test_save_workflow_context_to_memory(self):
        """workflow context를 memory에 저장 테스트"""
        ctx_manager = ContextManager()
        
        memory_session = AsyncMock()
        ctx_manager.set_mcp_sessions(memory_session, None)
        
        ctx_manager.create_workflow_context(
            workflow_id="workflow_001",
            name="ML Pipeline"
        )
        
        await ctx_manager.save_workflow_context("workflow_001")
        
        # memory_store가 호출되었는지 확인
        memory_session.call_tool.assert_called_once()
        call_args = memory_session.call_tool.call_args
        
        assert call_args.args[0] == "memory_store"
        assert call_args.kwargs["arguments"]["key"] == "workflow_context_workflow_001"
    
    @pytest.mark.asyncio
    async def test_save_workflow_context_no_storage(self):
        """storage 없이 workflow context 저장 테스트 (예외 발생하지 않음)"""
        ctx_manager = ContextManager()
        
        ctx_manager.create_workflow_context(
            workflow_id="workflow_001",
            name="ML Pipeline"
        )
        
        # 예외가 발생하지 않아야 함
        await ctx_manager.save_workflow_context("workflow_001")
    
    @pytest.mark.asyncio
    async def test_save_workflow_context_memory_error(self):
        """memory 저장 오류 처리 테스트"""
        ctx_manager = ContextManager()
        
        memory_session = AsyncMock()
        memory_session.call_tool.side_effect = Exception("Storage error")
        ctx_manager.set_mcp_sessions(memory_session, None)
        
        ctx_manager.create_workflow_context(
            workflow_id="workflow_001",
            name="ML Pipeline"
        )
        
        # 예외가 발생하지 않아야 함 (에러는 내부에서 처리)
        await ctx_manager.save_workflow_context("workflow_001")
    
    @pytest.mark.asyncio
    async def test_load_workflow_context_from_memory(self):
        """memory에서 workflow context 로드 테스트"""
        ctx_manager = ContextManager()
        
        memory_session = AsyncMock()
        ctx_manager.set_mcp_sessions(memory_session, None)
        
        import json
        workflow_data = {
            "workflow_id": "workflow_001",
            "name": "ML Pipeline",
            "description": "머신러닝 파이프라인",
            "work_contexts": {},
            "global_context": {"project_id": "proj_123"},
            "dependency_chain": [],
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        
        # Mock result object
        mock_result = MagicMock()
        mock_result.content.text = json.dumps(workflow_data)
        memory_session.call_tool.return_value = mock_result
        
        loaded_ctx = await ctx_manager.load_workflow_context("workflow_001")
        
        assert loaded_ctx is not None
        assert loaded_ctx.workflow_id == "workflow_001"
        assert loaded_ctx.name == "ML Pipeline"
        assert loaded_ctx.global_context == {"project_id": "proj_123"}
    
    @pytest.mark.asyncio
    async def test_load_workflow_context_not_found(self):
        """존재하지 않는 workflow context 로드 테스트"""
        ctx_manager = ContextManager()
        
        memory_session = AsyncMock()
        ctx_manager.set_mcp_sessions(memory_session, None)
        memory_session.call_tool.return_value = MagicMock(content=None)
        
        loaded_ctx = await ctx_manager.load_workflow_context("nonexistent_workflow")
        
        assert loaded_ctx is None
    
    @pytest.mark.asyncio
    async def test_save_all_contexts(self):
        """모든 context 저장 테스트"""
        ctx_manager = ContextManager()
        
        memory_session = AsyncMock()
        ctx_manager.set_mcp_sessions(memory_session, None)
        
        ctx_manager.create_workflow_context(
            workflow_id="workflow_001",
            name="ML Pipeline"
        )
        ctx_manager.create_workflow_context(
            workflow_id="workflow_002",
            name="Data Pipeline"
        )
        
        await ctx_manager.save_all_contexts()
        
        # 두 workflow가 모두 저장되어야 함
        assert memory_session.call_tool.call_count == 2
    
    @pytest.mark.asyncio
    async def test_context_accumulation_scenario(self):
        """context 누적 시나리오 테스트"""
        ctx_manager = ContextManager()
        
        ctx_manager.create_workflow_context(
            workflow_id="workflow_001",
            name="Context Accumulation Test"
        )
        
        # Work 1: 데이터 수집
        ctx_manager.create_work_context(
            workflow_id="workflow_001",
            work_id="collect",
            work_type="collection",
            inputs={"source": "api"}
        )
        ctx_manager.update_work_outputs(
            "workflow_001",
            "collect",
            {"raw_data": [1, 2, 3, 4, 5]}
        )
        
        # Work 2: 데이터 처리 (collect에 의존)
        ctx_manager.create_work_context(
            workflow_id="workflow_001",
            work_id="process",
            work_type="processing",
            inputs={"data": None},
            dependencies=["collect"]
        )
        ctx_manager.update_work_outputs(
            "workflow_001",
            "process",
            {"processed": [1.0, 2.0, 3.0, 4.0, 5.0]}
        )
        
        # Work 3: 분석 (process에 의존)
        ctx_manager.create_work_context(
            workflow_id="workflow_001",
            work_id="analyze",
            work_type="analysis",
            inputs={"data": None},
            dependencies=["process"]
        )
        
        # analyze work에 필요한 전체 context 확인
        full_ctx = ctx_manager.get_full_context_for_work("workflow_001", "analyze")
        
        assert full_ctx["work_inputs"] == {"data": None}
        assert "process" in full_ctx["resolved_dependencies"]
        assert "collect" not in full_ctx["resolved_dependencies"]  # 직접 dependency가 아님
        
        # Global context 확인 (모든 work의 결과가 누적되어야 함)
        global_ctx = ctx_manager.get_global_context("workflow_001")
        assert "collect" in global_ctx
        assert "process" in global_ctx
        assert global_ctx["collect"] == {"raw_data": [1, 2, 3, 4, 5]}
        assert global_ctx["process"] == {"processed": [1.0, 2.0, 3.0, 4.0, 5.0]}
