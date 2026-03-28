from typing import Optional, Set, List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime
import asyncio

from .base import BaseQueue


@dataclass
class TypeQueueConfig:
    max_size: int = 100
    priority_weight: float = 1.0


class TypeQueue(BaseQueue):
    def __init__(self, 
                 work_type: str,
                 config: Optional[TypeQueueConfig] = None):
        super().__init__()
        self.work_type = work_type
        self.config = config or TypeQueueConfig()
        self._queue: List[Any] = []
        self._work_index: Dict[str, int] = {}
    
    async def enqueue(self, work) -> str:
        async with self._lock:
            if len(self._queue) >= self.config.max_size:
                raise ValueError(f"Queue for type '{self.work_type}' is full (max: {self.config.max_size})")
            
            self._queue.append(work)
            self._work_index[work.work_id] = len(self._queue) - 1
            self._sort_queue()
            return work.work_id
    
    def _sort_queue(self):
        from ..work import WorkPriority
        self._queue.sort(key=lambda w: w.priority.value)
        self._work_index = {w.work_id: i for i, w in enumerate(self._queue)}
    
    async def dequeue(self,
                      agent_capabilities: List[str],
                      completed_work_ids: Optional[Set[str]] = None) -> Optional[Any]:
        async with self._lock:
            completed_ids = completed_work_ids or set()
            
            for i, work in enumerate(self._queue):
                if work.status.value not in ["queued", "pending"]:
                    continue
                if work.agent_type not in agent_capabilities:
                    continue
                if not work.can_start(completed_ids):
                    continue
                
                popped = self._queue.pop(i)
                if popped.work_id in self._work_index:
                    del self._work_index[popped.work_id]
                
                self._rebuild_index()
                return popped
            
            return None
    
    def _rebuild_index(self):
        self._work_index = {w.work_id: i for i, w in enumerate(self._queue)}
    
    async def peek(self) -> Optional[Any]:
        async with self._lock:
            for work in self._queue:
                if work.status.value in ["queued", "pending"]:
                    return work
            return None
    
    async def get_pending_count(self) -> int:
        async with self._lock:
            return sum(1 for w in self._queue if w.status.value in ["queued", "pending"])
    
    async def get_all_pending(self) -> List[Any]:
        async with self._lock:
            return [w for w in self._queue if w.status.value in ["queued", "pending"]]
    
    async def remove(self, work_id: str) -> bool:
        async with self._lock:
            if work_id not in self._work_index:
                return False
            
            idx = self._work_index[work_id]
            if 0 <= idx < len(self._queue):
                self._queue.pop(idx)
                self._rebuild_index()
                return True
            return False
    
    async def clear(self) -> int:
        async with self._lock:
            count = len(self._queue)
            self._queue.clear()
            self._work_index.clear()
            return count
    
    async def get_work(self, work_id: str) -> Optional[Any]:
        async with self._lock:
            idx = self._work_index.get(work_id)
            if idx is not None and 0 <= idx < len(self._queue):
                return self._queue[idx]
            return None
    
    def get_utilization(self) -> float:
        return len(self._queue) / self.config.max_size if self.config.max_size > 0 else 0.0
