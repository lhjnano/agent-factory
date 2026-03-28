from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
from enum import Enum
import asyncio

if TYPE_CHECKING:
    from ..work import Work, WorkResult
    from ..agent_pool import AgentInstance


class WorkerType(Enum):
    LLM = "llm"
    EXECUTION = "execution"
    VALIDATION = "validation"


class WorkerStatus(Enum):
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"


@dataclass
class WorkerResult:
    success: bool
    output: Any = None
    error: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    @property
    def duration_seconds(self) -> Optional[float]:
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None


@dataclass
class WorkerConfig:
    max_concurrent_tasks: int = 1
    default_timeout: float = 300.0
    retry_count: int = 3
    retry_delay: float = 1.0
    enable_metrics: bool = True


class BaseWorker(ABC):
    def __init__(
        self,
        worker_type: WorkerType,
        agent: "AgentInstance",
        config: Optional[WorkerConfig] = None
    ):
        self.worker_type = worker_type
        self.agent = agent
        self.config = config or WorkerConfig()
        
        self._status = WorkerStatus.IDLE
        self._current_tasks: int = 0
        self._completed_tasks: int = 0
        self._failed_tasks: int = 0
        self._total_tokens: int = 0
        self._total_duration: float = 0.0
        self._last_activity: Optional[datetime] = None
    
    @property
    def status(self) -> WorkerStatus:
        return self._status
    
    @property
    def is_available(self) -> bool:
        return (
            self._status == WorkerStatus.IDLE and
            self._current_tasks < self.config.max_concurrent_tasks
        )
    
    @property
    def utilization(self) -> float:
        if self.config.max_concurrent_tasks == 0:
            return 0.0
        return self._current_tasks / self.config.max_concurrent_tasks
    
    @property
    def success_rate(self) -> float:
        total = self._completed_tasks + self._failed_tasks
        if total == 0:
            return 1.0
        return self._completed_tasks / total
    
    @abstractmethod
    async def execute(self, work: "Work") -> WorkerResult:
        pass
    
    async def run(self, work: "Work") -> WorkerResult:
        if not self.is_available:
            return WorkerResult(
                success=False,
                error="Worker is not available"
            )
        
        self._current_tasks += 1
        if self._current_tasks >= self.config.max_concurrent_tasks:
            self._status = WorkerStatus.BUSY
        
        started_at = datetime.now()
        
        try:
            result = await asyncio.wait_for(
                self.execute(work),
                timeout=self.config.default_timeout
            )
            
            if result.success:
                self._completed_tasks += 1
            else:
                self._failed_tasks += 1
            
            if result.metrics:
                self._total_tokens += result.metrics.get("tokens_used", 0)
            
            return result
            
        except asyncio.TimeoutError:
            self._failed_tasks += 1
            return WorkerResult(
                success=False,
                error=f"Task timed out after {self.config.default_timeout}s",
                started_at=started_at,
                completed_at=datetime.now()
            )
            
        except Exception as e:
            self._failed_tasks += 1
            return WorkerResult(
                success=False,
                error=str(e),
                started_at=started_at,
                completed_at=datetime.now()
            )
            
        finally:
            self._current_tasks -= 1
            self._last_activity = datetime.now()
            
            if self._current_tasks == 0:
                self._status = WorkerStatus.IDLE
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "worker_type": self.worker_type.value,
            "agent_id": self.agent.agent_id,
            "status": self._status.value,
            "current_tasks": self._current_tasks,
            "completed_tasks": self._completed_tasks,
            "failed_tasks": self._failed_tasks,
            "total_tokens": self._total_tokens,
            "utilization": self.utilization,
            "success_rate": self.success_rate,
            "last_activity": self._last_activity.isoformat() if self._last_activity else None
        }
    
    def reset(self):
        self._current_tasks = 0
        self._status = WorkerStatus.IDLE
        self._last_activity = datetime.now()
