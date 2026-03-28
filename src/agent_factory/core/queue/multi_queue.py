from typing import Optional, Set, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import asyncio

from .base import BaseQueue
from .priority_queue import PriorityQueue, PriorityLevel
from .type_queue import TypeQueue, TypeQueueConfig


class QueueStrategy(Enum):
    PRIORITY_FIRST = "priority_first"
    TYPE_FIRST = "type_first"
    BALANCED = "balanced"
    ROUND_ROBIN = "round_robin"


@dataclass
class MultiQueueConfig:
    strategy: QueueStrategy = QueueStrategy.PRIORITY_FIRST
    enable_type_queues: bool = True
    priority_queue_weight: float = 0.7
    type_queue_weight: float = 0.3
    type_specific_work_types: List[str] = field(default_factory=lambda: [
        "problem_definition",
        "data_collection",
        "design_development",
        "training_optimization",
        "evaluation_validation",
        "deployment_monitoring"
    ])
    type_queue_max_size: int = 100


class MultiQueueManager(BaseQueue):
    def __init__(self, config: Optional[MultiQueueConfig] = None):
        super().__init__()
        self.config = config or MultiQueueConfig()
        
        self._priority_queue = PriorityQueue(
            priority_inversion_prevention=True,
            aging_threshold=10
        )
        
        self._type_queues: Dict[str, TypeQueue] = {}
        if self.config.enable_type_queues:
            for work_type in self.config.type_specific_work_types:
                self._type_queues[work_type] = TypeQueue(
                    work_type=work_type,
                    config=TypeQueueConfig(max_size=self.config.type_queue_max_size)
                )
        
        self._round_robin_index = 0
        self._enqueue_count = 0
    
    def _determine_target_queue(self, work) -> str:
        if not self.config.enable_type_queues:
            return "priority"
        
        if work.work_type in self._type_queues:
            type_queue = self._type_queues[work.work_type]
            if type_queue.get_utilization() < 0.8:
                return f"type:{work.work_type}"
        
        return "priority"
    
    async def enqueue(self, work) -> str:
        async with self._lock:
            from ..work import WorkStatus
            work.status = WorkStatus.QUEUED
            self._enqueue_count += 1
            
            target = self._determine_target_queue(work)
            
            if target.startswith("type:"):
                work_type = target.split(":")[1]
                type_queue = self._type_queues.get(work_type)
                if type_queue:
                    async with type_queue._lock:
                        type_queue._queue.append(work)
                        type_queue._work_index[work.work_id] = len(type_queue._queue) - 1
                        type_queue._sort_queue()
                    return work.work_id
            
            await self._priority_queue.enqueue(work)
            return work.work_id
    
    async def dequeue(self,
                      agent_capabilities: List[str],
                      completed_work_ids: Optional[Set[str]] = None) -> Optional[Any]:
        async with self._lock:
            if self.config.strategy == QueueStrategy.PRIORITY_FIRST:
                return await self._dequeue_priority_first(agent_capabilities, completed_work_ids)
            elif self.config.strategy == QueueStrategy.TYPE_FIRST:
                return await self._dequeue_type_first(agent_capabilities, completed_work_ids)
            elif self.config.strategy == QueueStrategy.BALANCED:
                return await self._dequeue_balanced(agent_capabilities, completed_work_ids)
            elif self.config.strategy == QueueStrategy.ROUND_ROBIN:
                return await self._dequeue_round_robin(agent_capabilities, completed_work_ids)
            
            return await self._dequeue_priority_first(agent_capabilities, completed_work_ids)
    
    async def _dequeue_priority_first(self,
                                       agent_capabilities: List[str],
                                       completed_work_ids: Optional[Set[str]]) -> Optional[Any]:
        work = await self._priority_queue.dequeue(agent_capabilities, completed_work_ids)
        if work:
            return work
        
        for work_type, type_queue in self._type_queues.items():
            work = await type_queue.dequeue(agent_capabilities, completed_work_ids)
            if work:
                return work
        
        return None
    
    async def _dequeue_type_first(self,
                                   agent_capabilities: List[str],
                                   completed_work_ids: Optional[Set[str]]) -> Optional[Any]:
        for work_type, type_queue in self._type_queues.items():
            work = await type_queue.dequeue(agent_capabilities, completed_work_ids)
            if work:
                return work
        
        return await self._priority_queue.dequeue(agent_capabilities, completed_work_ids)
    
    async def _dequeue_balanced(self,
                                 agent_capabilities: List[str],
                                 completed_work_ids: Optional[Set[str]]) -> Optional[Any]:
        priority_count = await self._priority_queue.get_pending_count()
        type_counts = {wt: await tq.get_pending_count() for wt, tq in self._type_queues.items()}
        total_type_count = sum(type_counts.values())
        
        if priority_count == 0 and total_type_count == 0:
            return None
        
        if priority_count > 0 and (total_type_count == 0 or 
                                   priority_count / (total_type_count + priority_count) > self.config.priority_queue_weight):
            work = await self._priority_queue.dequeue(agent_capabilities, completed_work_ids)
            if work:
                return work
        
        for work_type, type_queue in self._type_queues.items():
            if type_counts[work_type] > 0:
                work = await type_queue.dequeue(agent_capabilities, completed_work_ids)
                if work:
                    return work
        
        return await self._priority_queue.dequeue(agent_capabilities, completed_work_ids)
    
    async def _dequeue_round_robin(self,
                                    agent_capabilities: List[str],
                                    completed_work_ids: Optional[Set[str]]) -> Optional[Any]:
        queues = [self._priority_queue] + list(self._type_queues.values())
        
        for _ in range(len(queues)):
            queue = queues[self._round_robin_index % len(queues)]
            self._round_robin_index += 1
            
            work = await queue.dequeue(agent_capabilities, completed_work_ids)
            if work:
                return work
        
        return None
    
    async def peek(self) -> Optional[Any]:
        async with self._lock:
            work = await self._priority_queue.peek()
            if work:
                return work
            
            for type_queue in self._type_queues.values():
                work = await type_queue.peek()
                if work:
                    return work
            
            return None
    
    async def get_pending_count(self) -> int:
        async with self._lock:
            priority_count = await self._priority_queue.get_pending_count()
            type_counts = 0
            for tq in self._type_queues.values():
                type_counts += await tq.get_pending_count()
            return priority_count + type_counts
    
    async def get_all_pending(self) -> List[Any]:
        async with self._lock:
            pending = await self._priority_queue.get_all_pending()
            for type_queue in self._type_queues.values():
                pending.extend(await type_queue.get_all_pending())
            return pending
    
    async def remove(self, work_id: str) -> bool:
        async with self._lock:
            if await self._priority_queue.remove(work_id):
                return True
            
            for type_queue in self._type_queues.values():
                if await type_queue.remove(work_id):
                    return True
            
            return False
    
    async def clear(self) -> int:
        async with self._lock:
            count = await self._priority_queue.clear()
            for type_queue in self._type_queues.values():
                count += await type_queue.clear()
            return count
    
    async def get_work(self, work_id: str) -> Optional[Any]:
        async with self._lock:
            work = await self._priority_queue.get_work(work_id)
            if work:
                return work
            
            for type_queue in self._type_queues.values():
                work = await type_queue.get_work(work_id)
                if work:
                    return work
            
            return None
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        async with self._lock:
            priority_counts = await self._priority_queue.get_count_by_priority()
            type_counts = {
                wt: await tq.get_pending_count()
                for wt, tq in self._type_queues.items()
            }
            
            return {
                "strategy": self.config.strategy.value,
                "priority_queue": {
                    level.name: count
                    for level, count in priority_counts.items()
                },
                "type_queues": type_counts,
                "total_pending": sum(priority_counts.values()) + sum(type_counts.values()),
                "enqueue_count": self._enqueue_count
            }
    
    def get_type_queue(self, work_type: str) -> Optional[TypeQueue]:
        return self._type_queues.get(work_type)
    
    async def get_blocked_works(self) -> List[Any]:
        async with self._lock:
            all_works = await self.get_all_pending()
            completed_ids = set()
            
            blocked = []
            for work in all_works:
                if not work.can_start(completed_ids):
                    blocked.append(work)
            
            return blocked
    
    def set_strategy(self, strategy: QueueStrategy):
        self.config.strategy = strategy
