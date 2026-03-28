from abc import ABC, abstractmethod
from typing import Optional, Set, List
import asyncio


class BaseQueue(ABC):
    def __init__(self):
        self._lock = asyncio.Lock()
    
    @abstractmethod
    async def enqueue(self, work) -> str:
        pass
    
    @abstractmethod
    async def dequeue(self, 
                      agent_capabilities: List[str], 
                      completed_work_ids: Optional[Set[str]] = None) -> Optional[any]:
        pass
    
    @abstractmethod
    async def peek(self) -> Optional[any]:
        pass
    
    @abstractmethod
    async def get_pending_count(self) -> int:
        pass
    
    @abstractmethod
    async def get_all_pending(self) -> List[any]:
        pass
    
    @abstractmethod
    async def remove(self, work_id: str) -> bool:
        pass
    
    @abstractmethod
    async def clear(self) -> int:
        pass
    
    async def get_size(self) -> int:
        return await self.get_pending_count()
    
    async def is_empty(self) -> bool:
        return await self.get_pending_count() == 0
