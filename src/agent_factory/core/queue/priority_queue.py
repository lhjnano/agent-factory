from enum import Enum
from typing import Optional, Set, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

from .base import BaseQueue


class PriorityLevel(Enum):
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


@dataclass
class PriorityWork:
    work_id: str
    work: Any
    priority: PriorityLevel
    enqueued_at: datetime = field(default_factory=datetime.now)
    starvation_counter: int = 0


class PriorityQueue(BaseQueue):
    def __init__(self, 
                 priority_inversion_prevention: bool = True,
                 aging_threshold: int = 10):
        super().__init__()
        self._queues: Dict[PriorityLevel, List[PriorityWork]] = {
            PriorityLevel.CRITICAL: [],
            PriorityLevel.HIGH: [],
            PriorityLevel.MEDIUM: [],
            PriorityLevel.LOW: [],
        }
        self._work_index: Dict[str, PriorityWork] = {}
        self._dequeue_count: int = 0
        self._priority_inversion_prevention = priority_inversion_prevention
        self._aging_threshold = aging_threshold
    
    def _get_priority_level(self, work) -> PriorityLevel:
        from ..work import WorkPriority
        priority_map = {
            WorkPriority.CRITICAL: PriorityLevel.CRITICAL,
            WorkPriority.HIGH: PriorityLevel.HIGH,
            WorkPriority.MEDIUM: PriorityLevel.MEDIUM,
            WorkPriority.LOW: PriorityLevel.LOW,
        }
        return priority_map.get(work.priority, PriorityLevel.MEDIUM)
    
    async def enqueue(self, work) -> str:
        async with self._lock:
            from ..work import WorkStatus
            priority = self._get_priority_level(work)
            work.status = WorkStatus.QUEUED
            priority_work = PriorityWork(
                work_id=work.work_id,
                work=work,
                priority=priority
            )
            self._queues[priority].append(priority_work)
            self._work_index[work.work_id] = priority_work
            return work.work_id
    
    async def dequeue(self, 
                      agent_capabilities: List[str],
                      completed_work_ids: Optional[Set[str]] = None) -> Optional[Any]:
        async with self._lock:
            completed_ids = completed_work_ids or set()
            
            self._apply_aging()
            
            priority_order = self._get_priority_order()
            
            for priority in priority_order:
                queue = self._queues[priority]
                for i, priority_work in enumerate(queue):
                    work = priority_work.work
                    if work.status.value not in ["queued", "pending"]:
                        continue
                    if work.agent_type not in agent_capabilities:
                        continue
                    if not work.can_start(completed_ids):
                        continue
                    
                    popped = queue.pop(i)
                    if popped.work_id in self._work_index:
                        del self._work_index[popped.work_id]
                    
                    self._dequeue_count += 1
                    return work
            
            return None
    
    def _get_priority_order(self) -> List[PriorityLevel]:
        if self._priority_inversion_prevention and self._dequeue_count > 0:
            if self._dequeue_count % 10 == 0:
                return [
                    PriorityLevel.CRITICAL,
                    PriorityLevel.LOW,
                    PriorityLevel.HIGH,
                    PriorityLevel.MEDIUM,
                ]
        
        return [
            PriorityLevel.CRITICAL,
            PriorityLevel.HIGH,
            PriorityLevel.MEDIUM,
            PriorityLevel.LOW,
        ]
    
    def _apply_aging(self):
        for priority in [PriorityLevel.LOW, PriorityLevel.MEDIUM]:
            queue = self._queues[priority]
            for priority_work in queue:
                priority_work.starvation_counter += 1
                
                if priority_work.starvation_counter >= self._aging_threshold:
                    self._promote_work(priority_work)
    
    def _promote_work(self, priority_work: PriorityWork):
        old_priority = priority_work.priority
        new_priority = PriorityLevel(old_priority.value - 1)
        
        if old_priority in self._queues:
            try:
                self._queues[old_priority].remove(priority_work)
            except ValueError:
                pass
        
        priority_work.priority = new_priority
        priority_work.starvation_counter = 0
        self._queues[new_priority].append(priority_work)
    
    async def peek(self) -> Optional[Any]:
        async with self._lock:
            for priority in [PriorityLevel.CRITICAL, PriorityLevel.HIGH, 
                           PriorityLevel.MEDIUM, PriorityLevel.LOW]:
                queue = self._queues[priority]
                for priority_work in queue:
                    if priority_work.work.status.value in ["queued", "pending"]:
                        return priority_work.work
            return None
    
    async def get_pending_count(self) -> int:
        async with self._lock:
            return sum(
                len([pw for pw in queue if pw.work.status.value in ["queued", "pending"]])
                for queue in self._queues.values()
            )
    
    async def get_all_pending(self) -> List[Any]:
        async with self._lock:
            pending = []
            for priority in [PriorityLevel.CRITICAL, PriorityLevel.HIGH,
                           PriorityLevel.MEDIUM, PriorityLevel.LOW]:
                for priority_work in self._queues[priority]:
                    if priority_work.work.status.value in ["queued", "pending"]:
                        pending.append(priority_work.work)
            return pending
    
    async def get_count_by_priority(self) -> Dict[PriorityLevel, int]:
        async with self._lock:
            return {
                priority: len([pw for pw in queue if pw.work.status.value in ["queued", "pending"]])
                for priority, queue in self._queues.items()
            }
    
    async def remove(self, work_id: str) -> bool:
        async with self._lock:
            if work_id not in self._work_index:
                return False
            
            priority_work = self._work_index[work_id]
            queue = self._queues[priority_work.priority]
            
            try:
                queue.remove(priority_work)
                del self._work_index[work_id]
                return True
            except ValueError:
                return False
    
    async def clear(self) -> int:
        async with self._lock:
            count = sum(len(queue) for queue in self._queues.values())
            for queue in self._queues.values():
                queue.clear()
            self._work_index.clear()
            return count
    
    async def get_work(self, work_id: str) -> Optional[Any]:
        async with self._lock:
            priority_work = self._work_index.get(work_id)
            return priority_work.work if priority_work else None

    def _map_work_priority_to_level(self, work_priority) -> PriorityLevel:
        from ..work import WorkPriority
        priority_map = {
            WorkPriority.CRITICAL: PriorityLevel.CRITICAL,
            WorkPriority.HIGH: PriorityLevel.HIGH,
            WorkPriority.MEDIUM: PriorityLevel.MEDIUM,
            WorkPriority.LOW: PriorityLevel.LOW,
        }
        return priority_map.get(work_priority, PriorityLevel.MEDIUM)

    async def change_priority(self, work_id: str, new_priority) -> bool:
        """우선순위 변경. _lock 내에서 원자적으로 처리하여 dequeue 경쟁 방지."""
        async with self._lock:
            if work_id not in self._work_index:
                return False
            priority_work = self._work_index[work_id]
            new_level = self._map_work_priority_to_level(new_priority)
            if priority_work.priority == new_level:
                return True
            old_level = priority_work.priority
            try:
                self._queues[old_level].remove(priority_work)
            except ValueError:
                return False
            priority_work.priority = new_level
            priority_work.work.priority = new_priority
            priority_work.starvation_counter = 0
            self._queues[new_level].append(priority_work)
            return True
