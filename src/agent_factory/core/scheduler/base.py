from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Tuple, Dict, Any, TYPE_CHECKING
from enum import Enum

if TYPE_CHECKING:
    from ..work import Work
    from ..agent_pool import AgentInstance


class SchedulingStrategy(Enum):
    SJF = "sjf"
    TOKEN_AWARE = "token_aware"
    DEPENDENCY_AWARE = "dependency_aware"
    BALANCED = "balanced"


@dataclass
class SchedulingResult:
    work: Optional["Work"]
    agent: Optional["AgentInstance"]
    score: float = 0.0
    reason: str = ""
    estimated_duration: float = 0.0
    estimated_tokens: int = 0
    alternative_agents: List[str] = field(default_factory=list)


class BaseScheduler(ABC):
    def __init__(self, name: str = "base"):
        self.name = name
        self._scheduling_count = 0
        self._successful_schedules = 0
    
    @abstractmethod
    def select(
        self,
        works: List["Work"],
        agents: List["AgentInstance"],
        completed_work_ids: set = None
    ) -> SchedulingResult:
        pass
    
    @abstractmethod
    def estimate_duration(self, work: "Work") -> float:
        pass
    
    @abstractmethod
    def estimate_tokens(self, work: "Work") -> int:
        pass
    
    def calculate_score(
        self,
        work: "Work",
        agent: "AgentInstance"
    ) -> float:
        return 0.0
    
    def get_stats(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "scheduling_count": self._scheduling_count,
            "successful_schedules": self._successful_schedules,
            "success_rate": (
                self._successful_schedules / self._scheduling_count
                if self._scheduling_count > 0
                else 0.0
            )
        }
    
    def _record_success(self, success: bool):
        self._scheduling_count += 1
        if success:
            self._successful_schedules += 1
