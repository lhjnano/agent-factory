from typing import Dict, List, Optional, Any, Callable, TYPE_CHECKING
from dataclasses import dataclass, field
from enum import Enum
import asyncio

from .base_worker import BaseWorker, WorkerType, WorkerStatus
from .llm_worker import LLMWorker, LLMWorkerConfig
from .execution_worker import ExecutionWorker, ExecutionWorkerConfig
from .validation_worker import ValidationWorker, ValidationWorkerConfig

if TYPE_CHECKING:
    from ..work import Work
    from ..agent_pool import AgentInstance


@dataclass
class WorkerPoolConfig:
    max_llm_workers: int = 5
    max_execution_workers: int = 3
    max_validation_workers: int = 2
    llm_config: LLMWorkerConfig = field(default_factory=LLMWorkerConfig)
    execution_config: ExecutionWorkerConfig = field(default_factory=ExecutionWorkerConfig)
    validation_config: ValidationWorkerConfig = field(default_factory=ValidationWorkerConfig)


class WorkerPool:
    def __init__(self, config: Optional[WorkerPoolConfig] = None):
        self.config = config or WorkerPoolConfig()
        
        self._llm_workers: List[LLMWorker] = []
        self._execution_workers: List[ExecutionWorker] = []
        self._validation_workers: List[ValidationWorker] = []
        
        self._lock = asyncio.Lock()
    
    def register_agent(self, agent: "AgentInstance", worker_type: WorkerType = None):
        if worker_type is None:
            worker_type = self._infer_worker_type(agent)
        
        worker = self._create_worker(worker_type, agent)
        
        if worker_type == WorkerType.LLM:
            if len(self._llm_workers) < self.config.max_llm_workers:
                self._llm_workers.append(worker)
        elif worker_type == WorkerType.EXECUTION:
            if len(self._execution_workers) < self.config.max_execution_workers:
                self._execution_workers.append(worker)
        elif worker_type == WorkerType.VALIDATION:
            if len(self._validation_workers) < self.config.max_validation_workers:
                self._validation_workers.append(worker)
    
    def _infer_worker_type(self, agent: "AgentInstance") -> WorkerType:
        agent_type = agent.agent_type.lower()
        
        if "llm" in agent_type or "language" in agent_type:
            return WorkerType.LLM
        elif "exec" in agent_type or "run" in agent_type:
            return WorkerType.EXECUTION
        elif "valid" in agent_type or "test" in agent_type:
            return WorkerType.VALIDATION
        
        return WorkerType.LLM
    
    def _create_worker(self, worker_type: WorkerType, agent: "AgentInstance") -> BaseWorker:
        if worker_type == WorkerType.LLM:
            return LLMWorker(agent, self.config.llm_config)
        elif worker_type == WorkerType.EXECUTION:
            return ExecutionWorker(agent, self.config.execution_config)
        elif worker_type == WorkerType.VALIDATION:
            return ValidationWorker(agent, self.config.validation_config)
        
        return LLMWorker(agent)
    
    async def get_available_worker(self, worker_type: WorkerType) -> Optional[BaseWorker]:
        async with self._lock:
            workers = self._get_workers_by_type(worker_type)
            
            for worker in workers:
                if worker.is_available:
                    return worker
            
            return None
    
    def _get_workers_by_type(self, worker_type: WorkerType) -> List[BaseWorker]:
        if worker_type == WorkerType.LLM:
            return self._llm_workers
        elif worker_type == WorkerType.EXECUTION:
            return self._execution_workers
        elif worker_type == WorkerType.VALIDATION:
            return self._validation_workers
        
        return []
    
    def get_all_available_workers(self) -> List[BaseWorker]:
        available = []
        
        for workers in [self._llm_workers, self._execution_workers, self._validation_workers]:
            for worker in workers:
                if worker.is_available:
                    available.append(worker)
        
        return available
    
    def get_worker_stats(self) -> Dict[str, Any]:
        llm_stats = [w.get_stats() for w in self._llm_workers]
        execution_stats = [w.get_stats() for w in self._execution_workers]
        validation_stats = [w.get_stats() for w in self._validation_workers]
        
        return {
            "llm_workers": {
                "count": len(self._llm_workers),
                "max": self.config.max_llm_workers,
                "available": sum(1 for w in self._llm_workers if w.is_available),
                "workers": llm_stats
            },
            "execution_workers": {
                "count": len(self._execution_workers),
                "max": self.config.max_execution_workers,
                "available": sum(1 for w in self._execution_workers if w.is_available),
                "workers": execution_stats
            },
            "validation_workers": {
                "count": len(self._validation_workers),
                "max": self.config.max_validation_workers,
                "available": sum(1 for w in self._validation_workers if w.is_available),
                "workers": validation_stats
            },
            "total_workers": len(self._llm_workers) + len(self._execution_workers) + len(self._validation_workers),
            "total_available": len(self.get_all_available_workers())
        }
    
    async def execute_with_best_worker(self, work: "Work", worker_type: WorkerType = None) -> Any:
        if worker_type is None:
            worker_type = self._infer_worker_type_from_work(work)
        
        worker = await self.get_available_worker(worker_type)
        
        if not worker:
            raise RuntimeError(f"No available {worker_type.value} workers")
        
        return await worker.run(work)
    
    def _infer_worker_type_from_work(self, work: "Work") -> WorkerType:
        work_type = work.work_type.lower()
        inputs = work.inputs
        
        if "code" in inputs or "command" in inputs or "script" in inputs:
            return WorkerType.EXECUTION
        
        if "validation" in work_type or "test" in work_type or "validate" in work_type:
            return WorkerType.VALIDATION
        
        return WorkerType.LLM
    
    def remove_worker(self, worker_id: str) -> bool:
        for workers in [self._llm_workers, self._execution_workers, self._validation_workers]:
            for i, worker in enumerate(workers):
                if worker.agent.agent_id == worker_id:
                    workers.pop(i)
                    return True
        
        return False
    
    def clear(self):
        self._llm_workers.clear()
        self._execution_workers.clear()
        self._validation_workers.clear()
