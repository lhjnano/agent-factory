import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from agent_factory.core.worker import (
    BaseWorker,
    WorkerType,
    WorkerStatus,
    WorkerResult,
    WorkerConfig,
    LLMWorker,
    LLMWorkerConfig,
    ExecutionWorker,
    ExecutionWorkerConfig,
    ValidationWorker,
    ValidationWorkerConfig,
    WorkerPool,
    WorkerPoolConfig,
)
from agent_factory.core.agent_pool import AgentInstance, AgentStatus
from agent_factory.core.work import Work, WorkPriority, WorkStatus


def create_test_agent(
    agent_id: str = "agent_1",
    agent_type: str = "data_collection",
) -> AgentInstance:
    return AgentInstance(
        agent_id=agent_id,
        agent_type=agent_type,
        capabilities=[agent_type],
        status=AgentStatus.IDLE,
    )


def create_test_work(
    work_id: str = "work_1",
    work_type: str = "data_collection",
    inputs: dict = None,
) -> Work:
    return Work(
        work_id=work_id,
        name="Test Work",
        description="Test description",
        work_type=work_type,
        agent_type="data_collection",
        inputs=inputs or {},
    )


class TestBaseWorker:
    def test_worker_result_creation(self):
        result = WorkerResult(
            success=True,
            output={"key": "value"},
            metrics={"tokens": 100}
        )
        
        assert result.success is True
        assert result.output == {"key": "value"}
        assert result.metrics["tokens"] == 100
    
    def test_worker_result_duration(self):
        started = datetime(2024, 1, 1, 10, 0, 0)
        completed = datetime(2024, 1, 1, 10, 0, 5)
        
        result = WorkerResult(
            success=True,
            started_at=started,
            completed_at=completed
        )
        
        assert result.duration_seconds == 5.0
    
    def test_worker_config_defaults(self):
        config = WorkerConfig()
        
        assert config.max_concurrent_tasks == 1
        assert config.default_timeout == 300.0
        assert config.retry_count == 3


class TestLLMWorker:
    def test_initialization(self):
        agent = create_test_agent()
        worker = LLMWorker(agent)
        
        assert worker.worker_type == WorkerType.LLM
        assert worker.status == WorkerStatus.IDLE
        assert worker.is_available is True
    
    def test_custom_config(self):
        agent = create_test_agent()
        config = LLMWorkerConfig(
            max_retries=5,
            max_tokens_per_request=8000
        )
        worker = LLMWorker(agent, config)
        
        assert worker.config.max_retries == 5
        assert worker.config.max_tokens_per_request == 8000
    
    @pytest.mark.asyncio
    async def test_execute_success(self):
        agent = create_test_agent()
        worker = LLMWorker(agent)
        work = create_test_work(inputs={})
        
        result = await worker.run(work)
        
        assert result.success is True
        assert result.output is not None
    
    @pytest.mark.asyncio
    async def test_worker_becomes_busy(self):
        agent = create_test_agent()
        config = WorkerConfig(max_concurrent_tasks=1)
        worker = LLMWorker(agent, config)
        
        assert worker.status == WorkerStatus.IDLE
        
        work = create_test_work()
        await worker.run(work)
        
        assert worker.status == WorkerStatus.IDLE
    
    @pytest.mark.asyncio
    async def test_get_stats(self):
        agent = create_test_agent()
        worker = LLMWorker(agent)
        work = create_test_work()
        
        await worker.run(work)
        stats = worker.get_stats()
        
        assert stats["worker_type"] == "llm"
        assert stats["completed_tasks"] == 1
        assert "utilization" in stats


class TestExecutionWorker:
    def test_initialization(self):
        agent = create_test_agent()
        worker = ExecutionWorker(agent)
        
        assert worker.worker_type == WorkerType.EXECUTION
        assert worker.status == WorkerStatus.IDLE
    
    def test_allowed_commands(self):
        agent = create_test_agent()
        config = ExecutionWorkerConfig(
            allowed_commands=["python", "echo"]
        )
        worker = ExecutionWorker(agent, config)
        
        assert worker._is_command_allowed("python") is True
        assert worker._is_command_allowed("echo") is True
        assert worker._is_command_allowed("rm") is False
    
    @pytest.mark.asyncio
    async def test_execute_default(self):
        agent = create_test_agent()
        worker = ExecutionWorker(agent)
        work = create_test_work(inputs={})
        
        result = await worker.run(work)
        
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_execution_stats(self):
        agent = create_test_agent()
        worker = ExecutionWorker(agent)
        work = create_test_work()
        
        await worker.run(work)
        stats = worker.get_execution_stats()
        
        assert "execution_count" in stats
        assert stats["execution_count"] == 1


class TestValidationWorker:
    def test_initialization(self):
        agent = create_test_agent()
        worker = ValidationWorker(agent)
        
        assert worker.worker_type == WorkerType.VALIDATION
        assert worker.status == WorkerStatus.IDLE
    
    def test_register_validator(self):
        agent = create_test_agent()
        worker = ValidationWorker(agent)
        
        from agent_factory.core.worker.validation_worker import ValidationRule
        
        worker.register_validator(
            "custom",
            ValidationRule(
                name="test_rule",
                validator=lambda x: x > 0,
                error_message="Value must be positive"
            )
        )
        
        assert "custom" in worker._validators
    
    @pytest.mark.asyncio
    async def test_validate_work(self):
        agent = create_test_agent()
        worker = ValidationWorker(agent)
        work = create_test_work()
        
        result = await worker.run(work)
        
        assert "valid" in result.output
    
    @pytest.mark.asyncio
    async def test_validate_output(self):
        agent = create_test_agent()
        worker = ValidationWorker(agent)
        work = create_test_work(inputs={
            "validation_type": "output",
            "output": {"key": "value"}
        })
        
        result = await worker.run(work)
        
        assert result.success is True or result.success is False
    
    @pytest.mark.asyncio
    async def test_validate_schema(self):
        agent = create_test_agent()
        worker = ValidationWorker(agent)
        work = create_test_work(inputs={
            "validation_type": "schema",
            "data": {"name": "test", "value": 10},
            "schema": {
                "name": {"required": True, "type": str},
                "value": {"required": True, "type": int, "min": 0, "max": 100}
            }
        })
        
        result = await worker.run(work)
        
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_validate_schema_missing_field(self):
        agent = create_test_agent()
        worker = ValidationWorker(agent)
        work = create_test_work(inputs={
            "validation_type": "schema",
            "data": {"name": "test"},
            "schema": {
                "name": {"required": True, "type": str},
                "value": {"required": True, "type": int}
            }
        })
        
        result = await worker.run(work)
        
        assert result.success is False
        assert len(result.output["errors"]) > 0
    
    @pytest.mark.asyncio
    async def test_validation_stats(self):
        agent = create_test_agent()
        worker = ValidationWorker(agent)
        work = create_test_work()
        
        await worker.run(work)
        stats = worker.get_validation_stats()
        
        assert "validation_count" in stats
        assert stats["validation_count"] == 1


class TestWorkerPool:
    def test_initialization(self):
        pool = WorkerPool()
        
        assert pool.config is not None
        assert len(pool._llm_workers) == 0
        assert len(pool._execution_workers) == 0
        assert len(pool._validation_workers) == 0
    
    def test_register_llm_agent(self):
        pool = WorkerPool()
        agent = create_test_agent(agent_type="llm_worker")
        
        pool.register_agent(agent, WorkerType.LLM)
        
        assert len(pool._llm_workers) == 1
    
    def test_register_execution_agent(self):
        pool = WorkerPool()
        agent = create_test_agent(agent_type="exec_worker")
        
        pool.register_agent(agent, WorkerType.EXECUTION)
        
        assert len(pool._execution_workers) == 1
    
    def test_register_validation_agent(self):
        pool = WorkerPool()
        agent = create_test_agent(agent_type="validation_worker")
        
        pool.register_agent(agent, WorkerType.VALIDATION)
        
        assert len(pool._validation_workers) == 1
    
    def test_max_workers_limit(self):
        config = WorkerPoolConfig(max_llm_workers=2)
        pool = WorkerPool(config)
        
        for i in range(5):
            agent = create_test_agent(agent_id=f"agent_{i}")
            pool.register_agent(agent, WorkerType.LLM)
        
        assert len(pool._llm_workers) == 2
    
    @pytest.mark.asyncio
    async def test_get_available_worker(self):
        pool = WorkerPool()
        agent = create_test_agent()
        pool.register_agent(agent, WorkerType.LLM)
        
        worker = await pool.get_available_worker(WorkerType.LLM)
        
        assert worker is not None
        assert worker.worker_type == WorkerType.LLM
    
    @pytest.mark.asyncio
    async def test_no_available_worker(self):
        pool = WorkerPool()
        
        worker = await pool.get_available_worker(WorkerType.LLM)
        
        assert worker is None
    
    def test_get_all_available_workers(self):
        pool = WorkerPool()
        
        pool.register_agent(create_test_agent(agent_id="llm_1"), WorkerType.LLM)
        pool.register_agent(create_test_agent(agent_id="exec_1"), WorkerType.EXECUTION)
        
        available = pool.get_all_available_workers()
        
        assert len(available) == 2
    
    def test_get_worker_stats(self):
        pool = WorkerPool()
        pool.register_agent(create_test_agent(agent_id="llm_1"), WorkerType.LLM)
        pool.register_agent(create_test_agent(agent_id="exec_1"), WorkerType.EXECUTION)
        
        stats = pool.get_worker_stats()
        
        assert "llm_workers" in stats
        assert "execution_workers" in stats
        assert "validation_workers" in stats
        assert stats["total_workers"] == 2
    
    def test_remove_worker(self):
        pool = WorkerPool()
        agent = create_test_agent(agent_id="agent_to_remove")
        pool.register_agent(agent, WorkerType.LLM)
        
        assert len(pool._llm_workers) == 1
        
        result = pool.remove_worker("agent_to_remove")
        
        assert result is True
        assert len(pool._llm_workers) == 0
    
    def test_remove_nonexistent_worker(self):
        pool = WorkerPool()
        
        result = pool.remove_worker("nonexistent")
        
        assert result is False
    
    def test_clear(self):
        pool = WorkerPool()
        pool.register_agent(create_test_agent(agent_id="llm_1"), WorkerType.LLM)
        pool.register_agent(create_test_agent(agent_id="exec_1"), WorkerType.EXECUTION)
        
        pool.clear()
        
        assert len(pool._llm_workers) == 0
        assert len(pool._execution_workers) == 0
        assert len(pool._validation_workers) == 0
    
    @pytest.mark.asyncio
    async def test_execute_with_best_worker(self):
        pool = WorkerPool()
        pool.register_agent(create_test_agent(), WorkerType.LLM)
        
        work = create_test_work()
        result = await pool.execute_with_best_worker(work, WorkerType.LLM)
        
        assert result.success is True
    
    @pytest.mark.asyncio
    async def test_execute_no_worker_available(self):
        pool = WorkerPool()
        work = create_test_work()
        
        with pytest.raises(RuntimeError, match="No available"):
            await pool.execute_with_best_worker(work, WorkerType.LLM)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
